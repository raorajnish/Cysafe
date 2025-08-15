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
from dotenv import load_dotenv
import google.generativeai as genai
from .models import (
    AdminUser, CyberCrime, 
    ChatbotConfig, AuditLog
)
from .forms import ChatbotConfigForm
from .utils import log_audit_action, get_client_ip, sanitize_input

load_dotenv()


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


def report_crime(request):
    """Report crime page"""
    if request.method == 'POST':
        # For now, just show success message without creating a persistent record
        messages.success(request, 'Your report has been submitted successfully.')
        return redirect('report_crime')
    
    return render(request, 'main/report_crime.html')


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
    """Admin chatbot management - test interface only"""
    config = ChatbotConfig.objects.first()
    
    if not config:
        config = ChatbotConfig.objects.create(
            gemini_model='gemini-1.5-flash',
            system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide helpful, accurate information about cyber threats, prevention tips, and reporting procedures. Always prioritize user safety and direct them to official channels when needed."
        )
    
    context = {
        'config': config,
        'total_conversations': 0,  # Placeholder
        'avg_response_time': 2.5,  # Placeholder
        'satisfaction_rate': 95,   # Placeholder
    }
    return render(request, 'admin/chatbot.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_api(request):
    """Chatbot API endpoint - forwards user prompt to Gemini with system prompt from config"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'response': 'Please enter a message.'})

        # Load or create config
        config = ChatbotConfig.objects.first()
        if not config:
            config = ChatbotConfig.objects.create(
                gemini_model='gemini-1.5-pro',
                system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide short, crisp responses about cyber threats, prevention tips, and reporting procedures. Only elaborate when specifically asked by the user. Always prioritize user safety and direct them to official channels when needed. Use bullet points for clarity and keep responses concise."
            )

        if not config.gemini_api_key:
            return JsonResponse({
                'response': 'The AI assistant is not configured yet. Please ask an admin to set the Gemini API key in the Chatbot settings.'
            })

        # Configure Gemini with stored API key
        genai.configure(api_key=config.gemini_api_key)
        print(f"Gemini configured with API key: {config.gemini_api_key[:20]}...")

        # Use the saved model from config
        model_id = config.gemini_model or 'gemini-1.5-flash'
        print(f"Using model: {model_id}")
        print(f"System prompt: {config.system_prompt[:100]}...")
        
        try:
            # Create model without system instruction for better compatibility
            model = genai.GenerativeModel(model_id)
            print("Model created successfully")
        except Exception as e:
            print(f"Error creating model: {e}")
            return JsonResponse({
                'response': f'Error creating AI model: {str(e)}. Please try again.'
            }, status=500)
        
        try:
            # Prepare the full message with system prompt
            full_message = f"{config.system_prompt}\n\nUser: {user_message}\n\nAssistant:"
            print(f"Sending message to Gemini: {full_message[:100]}...")
            
            # Generate response
            response = model.generate_content(full_message)
            print("Response received from Gemini")
            
            # Extract text from response
            if response and response.text:
                text = response.text.strip()
                print(f"Extracted text: {text[:100]}...")
                return JsonResponse({'response': text, 'links': []})
            else:
                print("No text in response")
                return JsonResponse({'response': 'Sorry, I received an empty response. Please try again.'})
                
        except Exception as e:
            print(f"Error generating content: {e}")
            
            # Handle specific quota errors
            if "429" in str(e) or "quota" in str(e).lower():
                return JsonResponse({
                    'response': 'I\'m currently experiencing high demand. Please wait a moment and try again, or contact support if this persists.'
                })
            elif "400" in str(e) or "invalid" in str(e).lower():
                return JsonResponse({
                    'response': 'I encountered an issue with your request. Please try rephrasing your question.'
                })
            else:
                return JsonResponse({
                    'response': f'Sorry, I encountered an error: {str(e)}. Please try again or check the server logs.'
                })

    except Exception as e:
        import traceback
        print(f"Chatbot API Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'response': f'Sorry, I encountered an error: {str(e)}. Please try again or check the server logs.'
        }, status=500)


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


@login_required
def customize_bot(request):
    """Customize bot configuration page"""
    # Get or create config instance
    config = ChatbotConfig.objects.first()
    if not config:
        config = ChatbotConfig.objects.create(
            gemini_model='gemini-1.5-flash',
            system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide helpful, accurate information about cyber threats, prevention tips, and reporting procedures. Always prioritize user safety and direct them to official channels when needed."
        )
    
    if request.method == 'POST':
        form = ChatbotConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bot configuration updated successfully!')
            return redirect('customize_bot')
    else:
        form = ChatbotConfigForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
    }
    return render(request, 'admin/customize_bot.html', context)

