from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db import connection
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
import json
import uuid
# import bcrypt
# import jwt
from datetime import datetime, timedelta
import requests
import re
from .models import (
    AdminUser, CyberCrime, ChatbotKnowledgeBase, 
    ChatbotConfig, AuditLog
)
from .utils import log_audit_action, get_client_ip, sanitize_input


def home(request):
    """Home page view"""
    # Get statistics
    total_crimes = CyberCrime.objects.count()
    
    trending_crimes = CyberCrime.objects.order_by('-learn_more_clicks')[:4]
    
    context = {
        'total_crimes': total_crimes,
        'trending_crimes': trending_crimes,
    }
    return render(request, 'main/home.html', context)


def cyber_crimes(request):
    """Cyber crimes listing page"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    crimes = CyberCrime.objects.all()
    
    if search_query:
        crimes = crimes.filter(
            Q(type__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        crimes = crimes.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(crimes, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = CyberCrime.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'main/cyber_crimes.html', context)


def crime_detail(request, crime_id):
    """Individual crime detail page"""
    crime = get_object_or_404(CyberCrime, id=crime_id)
    
    # Note: Click count is now handled by the increment_clicks API endpoint
    # to prevent double counting when users navigate directly to the URL
    
    context = {
        'crime': crime,
    }
    return render(request, 'main/crime_detail.html', context)


# def report_crime(request):
#     """Report crime page"""
#     if request.method == 'POST':
#         # Handle report submission
#         report_type = request.POST.get('report_type')
#         description = request.POST.get('description')
#         contact_name = request.POST.get('contact_name')
#         contact_email = request.POST.get('contact_email')
#         contact_phone = request.POST.get('contact_phone')
#         urgency = request.POST.get('urgency', 'medium')
        
#         # For now, just show success message without creating report
#         messages.success(request, 'Your report has been submitted successfully.')
#         return redirect('report_crime')
    
#     return render(request, 'main/report_crime.html')


def contact(request):
    """Contact page"""
    return render(request, 'main/contact.html')


def admin_login(request):
    """Admin login page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = AdminUser.objects.get(email=email)
            
            # Check if account is locked
            if user.locked_until and user.locked_until > timezone.now():
                messages.error(request, 'Account is temporarily locked. Please try again later.')
                return render(request, 'admin/login.html')
            
            # Authenticate user
            if user.check_password(password):
                # Reset login attempts
                user.login_attempts = 0
                user.locked_until = None
                user.last_login = timezone.now()
                user.save()
                
                login(request, user)
                
                # Log audit action
                log_audit_action(
                    user, 'LOGIN', 'admin_users', user.id,
                    {'ip_address': get_client_ip(request)}
                )
                
                return redirect('admin_dashboard')
            else:
                # Increment failed login attempts
                user.login_attempts += 1
                if user.login_attempts >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=30)
                user.save()
                
                messages.error(request, 'Invalid credentials.')
                
        except AdminUser.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'admin/login.html')


@login_required
def admin_logout(request):
    """Admin logout"""
    log_audit_action(
        request.user, 'LOGOUT', 'admin_users', request.user.id,
        {'ip_address': get_client_ip(request)}
    )
    logout(request)
    return redirect('home')


@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    # Get statistics
    total_crimes = CyberCrime.objects.count()
    
    # Get trending crimes
    trending_crimes = CyberCrime.objects.order_by('-learn_more_clicks')[:5]
    
    # Get recent activity
    recent_activity = AuditLog.objects.select_related('admin_user').order_by('-timestamp')[:10]
    
    context = {
        'total_crimes': total_crimes,
        'trending_crimes': trending_crimes,
        'recent_activity': recent_activity,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def admin_crimes(request):
    """Admin crimes management"""
    crimes = CyberCrime.objects.all()
    
    if request.method == 'POST':
        # Handle delete operation first
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            try:
                crime = get_object_or_404(CyberCrime, id=delete_id)
                crime_type = crime.type  # Store before deletion for audit
                crime.delete()
                
                log_audit_action(
                    request.user, 'DELETE', 'cybercrime_data', delete_id,
                    {'type': crime_type}
                )
                
                messages.success(request, 'Crime deleted successfully.')
                return redirect('admin_crimes')
            except Exception as e:
                messages.error(request, f'Error deleting crime: {str(e)}')
                return redirect('admin_crimes')
        
        # Get form data
        crime_type = request.POST.get('type')
        description = request.POST.get('description')
        category = request.POST.get('category')
        severity = request.POST.get('severity')
        
        # Get individual prevention tips
        prevention_tip_1 = request.POST.get('prevention_tip_1', '').strip()
        prevention_tip_2 = request.POST.get('prevention_tip_2', '').strip()
        prevention_tip_3 = request.POST.get('prevention_tip_3', '').strip()
        prevention_tip_4 = request.POST.get('prevention_tip_4', '').strip()
        
        # Get individual reporting steps
        reporting_step_1 = request.POST.get('reporting_step_1', '').strip()
        reporting_step_2 = request.POST.get('reporting_step_2', '').strip()
        reporting_step_3 = request.POST.get('reporting_step_3', '').strip()
        reporting_step_4 = request.POST.get('reporting_step_4', '').strip()
        
        # Debug: Print all POST data
        print(f"DEBUG - All POST data:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        
        # Debug: Print form data
        print(f"DEBUG - Form Data:")
        print(f"Type: {crime_type}")
        print(f"Description: {description}")
        print(f"Category: {category}")
        print(f"Severity: {severity}")
        print(f"Prevention Tip 1: {prevention_tip_1}")
        print(f"Prevention Tip 2: {prevention_tip_2}")
        print(f"Prevention Tip 3: {prevention_tip_3}")
        print(f"Prevention Tip 4: {prevention_tip_4}")
        print(f"Reporting Step 1: {reporting_step_1}")
        print(f"Reporting Step 2: {reporting_step_2}")
        print(f"Reporting Step 3: {reporting_step_3}")
        print(f"Reporting Step 4: {reporting_step_4}")
        
        # Sanitize inputs
        crime_type = sanitize_input(crime_type)
        description = sanitize_input(description)
        prevention_tip_1 = sanitize_input(prevention_tip_1)
        prevention_tip_2 = sanitize_input(prevention_tip_2)
        prevention_tip_3 = sanitize_input(prevention_tip_3)
        prevention_tip_4 = sanitize_input(prevention_tip_4)
        reporting_step_1 = sanitize_input(reporting_step_1)
        reporting_step_2 = sanitize_input(reporting_step_2)
        reporting_step_3 = sanitize_input(reporting_step_3)
        reporting_step_4 = sanitize_input(reporting_step_4)
        
        # Combine prevention tips and reporting steps into lists
        prevention_tips = [
            prevention_tip_1, prevention_tip_2, prevention_tip_3, prevention_tip_4
        ]
        reporting_steps = [
            reporting_step_1, reporting_step_2, reporting_step_3, reporting_step_4
        ]
        
        # Filter out empty tips/steps but keep non-empty ones
        prevention_tips = [sanitize_input(tip) for tip in prevention_tips if tip and tip.strip()]
        reporting_steps = [sanitize_input(step) for step in reporting_steps if step and step.strip()]
        
        print(f"DEBUG - After filtering:")
        print(f"  Prevention tips (filtered): {prevention_tips}")
        print(f"  Reporting steps (filtered): {reporting_steps}")
        
        # Additional debugging - check if we have any data at all
        if not prevention_tips:
            print("WARNING: No prevention tips found!")
        if not reporting_steps:
            print("WARNING: No reporting steps found!")
        
        print(f"DEBUG - Final prevention_tips count: {len(prevention_tips)}")
        print(f"DEBUG - Final reporting_steps count: {len(reporting_steps)}")
        
        # Create new crime using Django ORM with individual fields
        print(f"DEBUG - Creating crime with individual fields")
        
        # Check if this is an update (crime_id provided)
        crime_id = request.POST.get('crime_id')
        if crime_id:
            try:
                # Update existing crime
                crime = CyberCrime.objects.get(id=crime_id)
                crime.type = crime_type
                crime.description = description
                crime.category = category
                crime.severity = severity
                crime.prevention_tip_1 = prevention_tip_1
                crime.prevention_tip_2 = prevention_tip_2
                crime.prevention_tip_3 = prevention_tip_3
                crime.prevention_tip_4 = prevention_tip_4
                crime.reporting_step_1 = reporting_step_1
                crime.reporting_step_2 = reporting_step_2
                crime.reporting_step_3 = reporting_step_3
                crime.reporting_step_4 = reporting_step_4
                crime.save()
                
                print(f"DEBUG - Crime updated with ID: {crime.id}")
                messages.success(request, 'Crime updated successfully!')
                
            except CyberCrime.DoesNotExist:
                print(f"DEBUG - Crime with ID {crime_id} not found")
                messages.error(request, 'Crime not found!')
                return redirect('admin_crimes')
        else:
            # Create new crime
            crime = CyberCrime.objects.create(
                type=crime_type,
                description=description,
                category=category,
                severity=severity,
                prevention_tip_1=prevention_tip_1,
                prevention_tip_2=prevention_tip_2,
                prevention_tip_3=prevention_tip_3,
                prevention_tip_4=prevention_tip_4,
                reporting_step_1=reporting_step_1,
                reporting_step_2=reporting_step_2,
                reporting_step_3=reporting_step_3,
                reporting_step_4=reporting_step_4
            )
            
            print(f"DEBUG - Crime created with ID: {crime.id}")
            messages.success(request, 'Crime added successfully!')
        
        return redirect('admin_crimes')
    
    # Calculate statistics
    total_crimes = crimes.count()
    critical_count = crimes.filter(severity='CRITICAL').count()
    total_views = crimes.aggregate(total=Sum('learn_more_clicks'))['total'] or 0
    
    # Calculate average severity (convert to numeric for calculation)
    severity_values = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
    total_severity = sum(severity_values.get(crime.severity, 0) for crime in crimes)
    avg_severity = round(total_severity / total_crimes, 1) if total_crimes > 0 else 0
    
    context = {
        'crimes': crimes,
        'categories': CyberCrime.CATEGORY_CHOICES,
        'severity_choices': CyberCrime.SEVERITY_CHOICES,
        'total_crimes': total_crimes,
        'critical_count': critical_count,
        'total_views': total_views,
        'avg_severity': avg_severity,
    }
    return render(request, 'admin/crimes.html', context)


@login_required
def crime_data_api(request, crime_id):
    """API endpoint to get crime data for view/edit"""
    try:
        crime = get_object_or_404(CyberCrime, id=crime_id)
        
        # Convert individual fields to lists for compatibility
        prevention_tips = []
        if crime.prevention_tip_1:
            prevention_tips.append(crime.prevention_tip_1)
        if crime.prevention_tip_2:
            prevention_tips.append(crime.prevention_tip_2)
        if crime.prevention_tip_3:
            prevention_tips.append(crime.prevention_tip_3)
        if crime.prevention_tip_4:
            prevention_tips.append(crime.prevention_tip_4)
            
        reporting_steps = []
        if crime.reporting_step_1:
            reporting_steps.append(crime.reporting_step_1)
        if crime.reporting_step_2:
            reporting_steps.append(crime.reporting_step_2)
        if crime.reporting_step_3:
            reporting_steps.append(crime.reporting_step_3)
        if crime.reporting_step_4:
            reporting_steps.append(crime.reporting_step_4)
        
        data = {
            'id': str(crime.id),
            'type': crime.type,
            'description': crime.description,
            'category': crime.category,
            'severity': crime.severity,
            'prevention_tips': prevention_tips,
            'reporting_steps': reporting_steps,
            'learn_more_clicks': crime.learn_more_clicks,
            'created_at': crime.created_at.isoformat(),
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





@login_required
def admin_chatbot(request):
    """Admin chatbot management"""
    knowledge_items = ChatbotKnowledgeBase.objects.all()
    config = ChatbotConfig.objects.first()
    
    if not config:
        config = ChatbotConfig.objects.create(
            gemini_model='gemini-2.5-pro',
            system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide helpful, accurate information about cyber threats, prevention tips, and reporting procedures. Always prioritize user safety and direct them to official channels when needed."
        )
    
    if request.method == 'POST':
        if 'save_config' in request.POST:
            # Save chatbot configuration
            gemini_api_key = request.POST.get('gemini_api_key')
            gemini_model = request.POST.get('gemini_model')
            system_prompt = request.POST.get('system_prompt')
            
            # Validate required fields
            if not gemini_model:
                messages.error(request, 'AI Model is required.')
                return redirect('admin_chatbot')
            
            config.gemini_api_key = gemini_api_key
            config.gemini_model = gemini_model
            config.system_prompt = system_prompt
            config.save()
            
            log_audit_action(
                request.user, 'UPDATE', 'chatbot_config', config.id,
                {'model': gemini_model, 'has_api_key': bool(gemini_api_key)}
            )
            
            messages.success(request, 'Chatbot configuration saved successfully! The AI assistant is now ready to use.')
            
            # Refresh the config object to get updated data
            config.refresh_from_db()
            
        elif 'add_knowledge' in request.POST:
            # Add knowledge base item
            title = request.POST.get('title')
            content = request.POST.get('content')
            file_upload = request.FILES.get('file_upload')
            website_url = request.POST.get('website_url')
            
            # Sanitize inputs
            title = sanitize_input(title)
            content = sanitize_input(content)
            
            file_type = 'Text'
            if file_upload:
                file_type = file_upload.name.split('.')[-1].upper()
                # Here you would process the file and extract content
                # For now, we'll just use the filename
                content = f"File: {file_upload.name}\n\n{content}"
            
            knowledge_item = ChatbotKnowledgeBase.objects.create(
                title=title,
                content=content,
                file_type=file_type,
                file_url=website_url
            )
            
            log_audit_action(
                request.user, 'CREATE', 'chatbot_knowledge', knowledge_item.id,
                {'title': title, 'file_type': file_type}
            )
            
            messages.success(request, 'Knowledge base item added successfully.')
            
        elif 'delete_id' in request.POST:
            # Delete knowledge base item
            delete_id = request.POST.get('delete_id')
            knowledge_item = get_object_or_404(ChatbotKnowledgeBase, id=delete_id)
            knowledge_item.delete()
            
            log_audit_action(
                request.user, 'DELETE', 'chatbot_knowledge', delete_id,
                {'title': knowledge_item.title}
            )
            
            messages.success(request, 'Knowledge base item deleted successfully.')
        
        return redirect('admin_chatbot')
    
    context = {
        'knowledge_items': knowledge_items,
        'config': config,
        'total_conversations': 0,  # Placeholder
        'avg_response_time': 2.5,  # Placeholder
        'satisfaction_rate': 95,   # Placeholder
    }
    return render(request, 'admin/chatbot.html', context)


@login_required
def test_chatbot(request):
    """Test chatbot interface for admins"""
    config = ChatbotConfig.objects.first()
    knowledge_items = ChatbotKnowledgeBase.objects.all()
    
    context = {
        'config': config,
        'knowledge_items': knowledge_items,
        'knowledge_count': knowledge_items.count(),
    }
    return render(request, 'admin/test_chatbot.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_api(request):
    """Chatbot API endpoint"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # Get chatbot config
        config = ChatbotConfig.objects.first()
        if not config:
            # Create default config if none exists
            config = ChatbotConfig.objects.create(
                gemini_model='gemini-2.5-pro',
                system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor."
            )
        
        # Get knowledge base (remove is_active filter for now)
        knowledge_base = ChatbotKnowledgeBase.objects.all()
        
        # Generate response (works with or without API key)
        response = generate_chatbot_response(user_message, knowledge_base, config)
        
        return JsonResponse({
            'response': response,
            'links': []
        })
        
    except Exception as e:
        return JsonResponse({
            'response': 'Sorry, I encountered an error. Please try again.',
            'links': []
        })


def generate_chatbot_response(user_message, knowledge_base, config):
    """Generate chatbot response based on user message and knowledge base"""
    user_message_lower = user_message.lower()
    
    # Enhanced keyword-based responses with more context
    if any(word in user_message_lower for word in ['phishing', 'email fraud', 'suspicious email']):
        return """🚨 **Phishing Alert!** 

Phishing is a cyber attack where attackers impersonate legitimate organizations to steal sensitive information like passwords, credit card numbers, and personal data.

**What to do if you receive a suspicious email:**
• Never click on suspicious links
• Don't download attachments from unknown senders
• Verify sender email addresses carefully
• Don't share personal information via email
• Report phishing attempts to cybercrime.gov.in

**Emergency Contact:** Call 1930 for immediate assistance."""

    elif any(word in user_message_lower for word in ['report', 'complaint', 'file complaint']):
        return """📋 **How to Report Cyber Crime**

**Step-by-step process:**
1. **Gather Evidence:** Take screenshots, save emails, note transaction details
2. **Visit Official Portal:** Go to cybercrime.gov.in
3. **Call Helpline:** Dial 1930 for immediate assistance
4. **Contact Bank:** If financial fraud, contact your bank immediately
5. **File FIR:** Visit local police station if needed

**Important:** Always report within 24 hours for better investigation chances.

**Emergency Numbers:**
• Cyber Crime: 1930
• Police Emergency: 112
• Women Helpline: 181"""

    elif any(word in user_message_lower for word in ['password', 'security', 'strong password']):
        return """🔐 **Password Security Best Practices**

**Create Strong Passwords:**
• Use at least 12 characters
• Include uppercase and lowercase letters
• Add numbers and special characters
• Avoid personal information (birthday, name)
• Use unique passwords for each account

**Additional Security:**
• Enable two-factor authentication (2FA)
• Use password managers
• Never share passwords
• Change passwords regularly
• Monitor account activity

**Example Strong Password:** `K9#mP$2xL@vN8!`"""

    elif any(word in user_message_lower for word in ['emergency', 'urgent', 'help', 'hacked']):
        return """🚨 **EMERGENCY CYBER CRIME RESPONSE**

**Immediate Actions:**
1. **Disconnect:** Unplug from internet immediately
2. **Call Emergency:** Dial 1930 for cyber crime helpline
3. **Contact Bank:** If financial accounts compromised
4. **Change Passwords:** On a secure device
5. **Document Everything:** Screenshots, transaction details

**Emergency Contacts:**
• 🚨 Cyber Crime: **1930**
• 🚨 Police Emergency: **112**
• 🚨 Women Helpline: **181**
• 🚨 Child Helpline: **1098**

**Stay Calm:** Help is available 24/7. Don't panic!"""

    elif any(word in user_message_lower for word in ['ransomware', 'virus', 'malware']):
        return """🦠 **Ransomware & Malware Protection**

**What is Ransomware?**
Malicious software that encrypts your files and demands payment to restore access.

**Prevention Tips:**
• Keep software and systems updated
• Use reliable antivirus software
• Regularly backup important data
• Be cautious with email attachments
• Don't click on suspicious links

**If Infected:**
• Don't pay the ransom
• Disconnect from internet immediately
• Contact cybersecurity experts
• Report to cybercrime.gov.in
• Restore from clean backups if available"""

    elif any(word in user_message_lower for word in ['upi', 'payment', 'fraud', 'bank']):
        return """💳 **UPI & Payment Fraud Prevention**

**Common UPI Frauds:**
• Fake payment links
• QR code scams
• Impersonation frauds
• OTP sharing scams

**Safety Measures:**
• Never share UPI PIN with anyone
• Verify payment requests independently
• Use official banking apps only
• Enable transaction alerts
• Check payment details carefully

**If Victim:**
• Immediately block your UPI ID
• Contact your bank to freeze transactions
• File complaint with cybercrime.gov.in
• Report to bank's fraud department"""

    elif any(word in user_message_lower for word in ['social media', 'account hacked', 'facebook', 'instagram']):
        return """📱 **Social Media Account Security**

**If Account is Hacked:**
1. **Immediately change password**
2. **Enable two-factor authentication**
3. **Report to the platform**
4. **Check for unauthorized posts/messages**
5. **Monitor for identity theft signs**

**Prevention:**
• Use strong, unique passwords
• Enable 2FA on all accounts
• Be careful with third-party apps
• Regularly review account activity
• Log out from shared devices

**Report to:** cybercrime.gov.in"""

    else:
        return """🤖 **Welcome to CySafe AI Assistant!**

I'm here to help you with cybersecurity questions and concerns. You can ask me about:

**🔒 Security Topics:**
• Phishing and email fraud
• Password security
• Ransomware protection
• UPI payment fraud
• Social media security

**📞 Emergency Help:**
• How to report cyber crimes
• Emergency contact numbers
• Immediate response procedures

**💡 General Guidance:**
• Prevention tips
• Best practices
• Security awareness

**Ask me anything about cybersecurity!** 

*Note: For immediate emergency assistance, call 1930.*"""


@csrf_exempt
@require_http_methods(["POST"])
def increment_clicks(request):
    """API endpoint to increment learn more clicks"""
    try:
        data = json.loads(request.body)
        crime_id = data.get('crime_id')
        
        crime = get_object_or_404(CyberCrime, id=crime_id)
        crime.learn_more_clicks += 1
        crime.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
