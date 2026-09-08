from django.urls import path
from . import views

app_name = 'survey'

urlpatterns = [
    # ============================================
    # PUBLIC FORM VIEWS
    # ============================================
    path('', views.survey_form, name='survey_form'),
    path('api/submit/', views.submit_survey, name='submit_survey'),
    
    # ============================================
    # ASSOCIATION FORM VIEWS
    # ============================================
    path('association/', views.association_form, name='association_form'),
    path('api/association/submit/', views.submit_association, name='submit_association'),
    
    # ============================================
    # ADMIN PORTAL VIEWS
    # ============================================
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/surveys/', views.admin_surveys, name='admin_surveys'),
    path('admin/job-demands/', views.admin_job_demands, name='admin_job_demands'),
    
    # Association Admin Views
    path('admin/associations/', views.admin_association_list, name='admin_association_list'),
    path('admin/association/<int:consultation_id>/', views.get_association_detail, name='get_association_detail'),
    path('admin/association/<int:consultation_id>/delete/', views.delete_association, name='delete_association'),
    path('admin/export-association-csv/', views.admin_export_association_csv, name='admin_export_association_csv'),
    
    # ============================================
    # DATA VIEWS
    # ============================================
    path('api/chart-data/', views.get_chart_data, name='get_chart_data'),
    path('api/debug-data/', views.debug_data, name='debug_data'),
    path('api/survey/<int:survey_id>/', views.get_survey_detail, name='get_survey_detail'),
    path('api/export-full-csv/', views.admin_export_full_csv, name='admin_export_full_csv'),
    
    # ============================================
    # EDIT/DELETE VIEWS
    # ============================================
    path('api/survey/<int:survey_id>/update/', views.update_survey, name='update_survey'),
    path('api/survey/<int:survey_id>/delete/', views.delete_survey, name='delete_survey'),
    path('api/job-demand/<int:job_id>/update/', views.update_job_demand, name='update_job_demand'),
    path('api/job-demand/<int:job_id>/delete/', views.delete_job_demand, name='delete_job_demand'),
    path('api/apprenticeship/<int:app_id>/update/', views.update_apprenticeship, name='update_apprenticeship'),
    path('api/apprenticeship/<int:app_id>/delete/', views.delete_apprenticeship, name='delete_apprenticeship'),
]