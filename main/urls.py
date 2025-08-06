from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.home, name='home'),
    path('cyber-crimes/', views.cyber_crimes, name='cyber_crimes'),
    path('crime/<uuid:crime_id>/', views.crime_detail, name='crime_detail'),
    path('report/', views.report_crime, name='report_crime'),
    path('contact/', views.contact, name='contact'),
    
    path('admin-access/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/crimes/', views.admin_crimes, name='admin_crimes'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/chatbot/', views.admin_chatbot, name='admin_chatbot'),
    path('admin/test-chatbot/', views.test_chatbot, name='test_chatbot'),
    
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/increment-clicks/', views.increment_clicks, name='increment_clicks'),
    path('admin/crimes/<uuid:crime_id>/data/', views.crime_data_api, name='crime_data_api'),
] 