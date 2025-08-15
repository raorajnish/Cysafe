from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class AdminUser(AbstractUser):
    """Custom admin user model with enhanced security"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'admin_users'


class CyberCrime(models.Model):
    """Model for storing cyber crime information"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    CATEGORY_CHOICES = [
        ('email_fraud', 'Email Fraud'),
        ('personal_data', 'Personal Data'),
        ('financial_fraud', 'Financial Fraud'),
        ('harassment', 'Harassment'),
        ('system_attack', 'System Attack'),
        ('social_media', 'Social Media Fraud'),
        ('job_fraud', 'Online Job Fraud'),
        ('cryptocurrency', 'Cryptocurrency Fraud'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Prevention Tips - Individual fields
    prevention_tip_1 = models.CharField(max_length=500, blank=True, null=True)
    prevention_tip_2 = models.CharField(max_length=500, blank=True, null=True)
    prevention_tip_3 = models.CharField(max_length=500, blank=True, null=True)
    prevention_tip_4 = models.CharField(max_length=500, blank=True, null=True)
    
    # Reporting Steps - Individual fields
    reporting_step_1 = models.CharField(max_length=500, blank=True, null=True)
    reporting_step_2 = models.CharField(max_length=500, blank=True, null=True)
    reporting_step_3 = models.CharField(max_length=500, blank=True, null=True)
    reporting_step_4 = models.CharField(max_length=500, blank=True, null=True)
    
    learn_more_clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cybercrime_data'
        ordering = ['-created_at']

    def __str__(self):
        return self.type
    
    def get_prevention_tips_count(self):
        """Count non-empty prevention tips"""
        count = 0
        if self.prevention_tip_1: count += 1
        if self.prevention_tip_2: count += 1
        if self.prevention_tip_3: count += 1
        if self.prevention_tip_4: count += 1
        return count
    
    def get_reporting_steps_count(self):
        """Count non-empty reporting steps"""
        count = 0
        if self.reporting_step_1: count += 1
        if self.reporting_step_2: count += 1
        if self.reporting_step_3: count += 1
        if self.reporting_step_4: count += 1
        return count
    
    def get_prevention_tips_list(self):
        """Get prevention tips as a list"""
        tips = []
        if self.prevention_tip_1: tips.append(self.prevention_tip_1)
        if self.prevention_tip_2: tips.append(self.prevention_tip_2)
        if self.prevention_tip_3: tips.append(self.prevention_tip_3)
        if self.prevention_tip_4: tips.append(self.prevention_tip_4)
        return tips
    
    def get_reporting_steps_list(self):
        """Get reporting steps as a list"""
        steps = []
        if self.reporting_step_1: steps.append(self.reporting_step_1)
        if self.reporting_step_2: steps.append(self.reporting_step_2)
        if self.reporting_step_3: steps.append(self.reporting_step_3)
        if self.reporting_step_4: steps.append(self.reporting_step_4)
        return steps


class ChatbotConfig(models.Model):
    """Model for storing chatbot configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gemini_api_key = models.CharField(max_length=500, blank=True)
    gemini_model = models.CharField(max_length=100, default='gemini-pro')
    system_prompt = models.TextField(default="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide helpful, accurate information about cyber threats, prevention tips, and reporting procedures. Always prioritize user safety and direct them to official channels when needed.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chatbot_config'

    def __str__(self):
        return f"Chatbot Config - {self.gemini_model}"


class AuditLog(models.Model):
    """Model for storing admin action audit logs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.resource_type} by {self.admin_user.email}"
