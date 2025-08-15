from django import forms
from .models import ChatbotConfig


class ChatbotConfigForm(forms.ModelForm):
    """Form for ChatbotConfig model"""
    
    class Meta:
        model = ChatbotConfig
        fields = ['gemini_api_key', 'gemini_model', 'system_prompt']
        widgets = {
            'gemini_api_key': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'password',
                'placeholder': 'Enter your Gemini API key'
            }),
            'gemini_model': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
                ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
                ('gemini-2.0-flash', 'Gemini 2.0 Flash'),
                ('gemini-2.0-pro', 'Gemini 2.0 Pro'),
            ]),
            'system_prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter the system prompt for the AI assistant'
            })
        } 