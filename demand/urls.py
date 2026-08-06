from django.urls import path
from . import views

app_name = 'survey'

urlpatterns = [
    # ============================================
    # PUBLIC FORM URLs (No login required)
    # ============================================
    path('', views.survey_form, name='survey_form'),
    path('api/submit-survey/', views.submit_survey, name='submit_survey'),
    
    # ============================================
    # ADMIN PORTAL URLs (Login required)
    # ============================================
    path('admin-portal/', views.admin_login, name='admin_login'),
    path('admin-portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/surveys/', views.admin_surveys, name='admin_surveys'),
    path('admin-portal/job-demands/', views.admin_job_demands, name='admin_job_demands'),
    path('admin-portal/export-csv/', views.admin_export_full_csv, name='admin_export_csv'),  # Changed to full export
    path('admin-portal/logout/', views.admin_logout, name='admin_logout'),
    path('api/chart-data/', views.get_chart_data, name='chart_data'),
    path('debug-data/', views.debug_data, name='debug_data'),
    path('api/survey-detail/<int:survey_id>/', views.get_survey_detail, name='get_survey_detail'),
]