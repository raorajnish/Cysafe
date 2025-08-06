import re
import html
from django.utils import timezone
from .models import AuditLog


def log_audit_action(admin_user, action, resource_type, resource_id=None, details=None):
    """Log admin actions for audit trail"""
    try:
        AuditLog.objects.create(
            admin_user=admin_user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else '',
            details=details or {},
            ip_address='127.0.0.1',  # Will be updated with actual IP
            user_agent='Django App'
        )
    except Exception as e:
        print(f"Failed to log audit action: {e}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def sanitize_input(text):
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return text
    
    # HTML escape
    text = html.escape(text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove other potentially dangerous tags
    dangerous_tags = ['javascript:', 'vbscript:', 'onload', 'onerror', 'onclick']
    for tag in dangerous_tags:
        text = text.replace(tag, '')
    
    return text.strip()


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^[\+]?[1-9][\d]{0,15}$'
    return re.match(pattern, phone) is not None


def get_severity_color(severity):
    """Get color class for severity level"""
    colors = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'critical': 'danger'
    }
    return colors.get(severity, 'secondary')


def get_severity_icon(severity):
    """Get icon for severity level"""
    icons = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'critical': '🔴'
    }
    return icons.get(severity, '⚪')


def format_timestamp(timestamp):
    """Format timestamp for display"""
    now = timezone.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"


def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..." 