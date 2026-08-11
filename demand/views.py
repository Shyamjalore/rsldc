import json
import logging
import traceback
from datetime import datetime
import csv
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum, Count, Max, Q
from django.db.models.functions import TruncDate
from django.contrib import messages
from django.template.loader import render_to_string

from .models import Survey, JobDemand, ApprenticeshipOJT

from datetime import datetime, timedelta
# Set up logging
logger = logging.getLogger(__name__)

# ============================================
# PUBLIC FORM VIEWS (No login required)
# ============================================

def survey_form(request):
    """Main survey form page - directly accessible without login"""
    return render(request, 'form.html')


@csrf_exempt
@require_http_methods(["POST"])
def submit_survey(request):
    """API endpoint for survey form submission"""
    
    print("="*60)
    print("🔵 SUBMIT SURVEY API CALLED")
    print("="*60)
    
    try:
        data = json.loads(request.body)
        print(f"✅ JSON Parsed Successfully")
        print(f"📋 Data Keys: {list(data.keys())}")
        
        with transaction.atomic():
            # Create Survey
            survey = Survey.objects.create(
                company_code=data.get('company_code', '').strip(),
                start_time=data.get('start_time', ''),
                completion_time=data.get('completion_time', ''),
                submission_date=data.get('submission_date') or datetime.now().date(),
                field_officer_name=data.get('field_officer_name', '').strip(),
                
                # Employer Details
                company_name=data.get('company_name', '').strip(),
                organisation_type=data.get('organisation_type', '').strip(),
                organisation_type_other=data.get('organisation_type_other', '').strip(),
                product_service=data.get('product_service', '').strip(),
                product_service_specify=data.get('product_service_specify', '').strip(),
                operational_sector=data.get('operational_sector', '').strip(),
                operational_sector_other=data.get('operational_sector_other', '').strip(),
                address=data.get('address', '').strip(),
                website=data.get('website', '').strip(),
                district=data.get('district', '').strip(),
                block=data.get('block', '').strip(),
                
                # Contact Details
                contact_name=data.get('contact_name', '').strip(),
                contact_mobile=data.get('contact_mobile', '').strip(),
                contact_email=data.get('contact_email', '').strip(),
                
                # Workforce Profile
                workforce_profile=data.get('workforce_profile', '').strip(),
                
                # Employer Partnership
                placement_willingness=data.get('placement_willingness', 'No'),
                apprenticeship_willingness=data.get('apprenticeship_willingness', 'No'),
                guest_lecture_interest=data.get('guest_lecture_interest', 'No'),
                industrial_visit_interest=data.get('industrial_visit_interest', 'No'),
                csr_interest=data.get('csr_interest', 'No'),
                ojt_internship_willingness=data.get('ojt_internship_willingness', 'No'),
                
                # Recruitment Challenges
                recruitment_challenges=data.get('recruitment_challenges', '').strip(),
                additional_remarks=data.get('additional_remarks', '').strip(),
                supporting_evidence=data.get('supporting_evidence', '').strip(),
            )
            
            print(f"✅ Survey Created! ID: {survey.id}")
            
            # Create Job Demands
            for idx, job_data in enumerate(data.get('job_demands', []), 1):
                JobDemand.objects.create(
                    survey=survey,
                    row_no=idx,
                    job_role=job_data.get('job_role', '').strip(),
                    sector=job_data.get('sector', '').strip(),
                    qualification=job_data.get('qualification', '').strip(),
                    qualification_other=job_data.get('qualification_other', '').strip(),
                    experience=job_data.get('experience', '').strip(),
                    certification=job_data.get('certification', 'No'),
                    certification_detail=job_data.get('certification_detail', '').strip(),
                    salary_offered=job_data.get('salary_offered', '').strip(),
                    current_openings=int(job_data.get('current_openings', 0)),
                    openings_6_months=int(job_data.get('openings_6_months', 0)),
                    openings_12_months=int(job_data.get('openings_12_months', 0)),
                    apprentice_ojt=job_data.get('apprentice_ojt', 'No'),
                    apprentice_ojt_detail=job_data.get('apprentice_ojt_detail', '').strip(),
                    gender_suitability=job_data.get('gender_suitability', 'Any / No Preference'),
                    pwd=job_data.get('pwd', 'NA'),
                    additional_remarks=job_data.get('additional_remarks', '').strip()
                )
                print(f"  ✅ Job Demand #{idx} Created!")
            
            # Create Apprenticeships/OJT
            for idx, app_data in enumerate(data.get('apprenticeships', []), 1):
                ApprenticeshipOJT.objects.create(
                    survey=survey,
                    row_no=idx,
                    job_role=app_data.get('job_role', '').strip(),
                    opportunity_type=app_data.get('opportunity_type', ''),
                    seats_capacity=int(app_data.get('seats_capacity', 0)),
                    duration_months=int(app_data.get('duration_months', 0)),
                    monthly_stipend=int(app_data.get('monthly_stipend', 0)),
                    expected_start_month=app_data.get('expected_start_month', ''),
                    minimum_qualification=app_data.get('minimum_qualification', '').strip(),
                    minimum_qualification_other=app_data.get('minimum_qualification_other', '').strip(),
                    conversion_to_employment=app_data.get('conversion_to_employment', 'No')
                )
                print(f"  ✅ Apprenticeship #{idx} Created!")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Survey submitted successfully',
            'survey_id': survey.id
        }, status=201)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ============================================
# ADMIN PORTAL VIEWS (Login required)
# ============================================

def admin_login(request):
    """Admin login page"""
    if request.user.is_authenticated:
        return redirect('survey:admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('survey:admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'portal/login.html')


@login_required
def admin_dashboard(request):
    """Admin dashboard with statistics and filters"""
    try:
        # Get filter parameters
        district_filter = request.GET.get('district', '')
        block_filter = request.GET.get('block', '')
        sector_filter = request.GET.get('sector', '')
        
        # Base querysets with filters
        survey_qs = Survey.objects.all()
        job_qs = JobDemand.objects.all()
        
        # Apply filters
        if district_filter:
            survey_qs = survey_qs.filter(district=district_filter)
            job_qs = job_qs.filter(survey__district=district_filter)
        
        if block_filter:
            survey_qs = survey_qs.filter(block=block_filter)
            job_qs = job_qs.filter(survey__block=block_filter)
        
        if sector_filter:
            survey_qs = survey_qs.filter(primary_sector=sector_filter)
            job_qs = job_qs.filter(sector=sector_filter)
        
        # KPI Stats
        total_surveys = survey_qs.count()
        total_jobs = job_qs.count()
        
        current_aggregate = job_qs.aggregate(total=Sum('current_demand'))
        future_aggregate = job_qs.aggregate(total=Sum('future_demand'))
        
        total_current = current_aggregate['total'] or 0
        total_future = future_aggregate['total'] or 0
        
        # Latest 5 Surveys
        latest_surveys = survey_qs.order_by('-created_at')[:5]
        latest_surveys_data = []
        for survey in latest_surveys:
            latest_surveys_data.append({
                'id': survey.id,
                'employer_name': survey.employer_name,
                'district': survey.district,
                'block': survey.block,
                'primary_sector': survey.primary_sector,
                'total_demand': survey.total_current_demand + survey.total_future_demand,
                'created_at': survey.created_at.strftime('%d %b %Y, %I:%M %p')
            })
        
        # District-wise Statistics
        district_stats = []
        districts = survey_qs.values('district').annotate(
            count=Count('id'),
            total_demand=Sum('job_demands__current_demand') + Sum('job_demands__future_demand')
        ).order_by('-total_demand')
        
        for d in districts:
            if d['district']:
                district_stats.append({
                    'district': d['district'],
                    'count': d['count'],
                    'total_demand': d['total_demand'] or 0
                })
        
        # Block-wise Statistics (for selected district)
        block_stats = []
        if district_filter:
            blocks = survey_qs.filter(district=district_filter).values('block').annotate(
                count=Count('id'),
                total_demand=Sum('job_demands__current_demand') + Sum('job_demands__future_demand')
            ).order_by('-total_demand')
            
            for b in blocks:
                if b['block']:
                    block_stats.append({
                        'block': b['block'],
                        'count': b['count'],
                        'total_demand': b['total_demand'] or 0
                    })
        else:
            # Top 10 blocks overall
            blocks = survey_qs.values('block').annotate(
                count=Count('id'),
                total_demand=Sum('job_demands__current_demand') + Sum('job_demands__future_demand')
            ).order_by('-total_demand')[:10]
            
            for b in blocks:
                if b['block']:
                    block_stats.append({
                        'block': b['block'],
                        'count': b['count'],
                        'total_demand': b['total_demand'] or 0
                    })
        
        # Product/Service Type Statistics
        product_service_stats = job_qs.values('survey__product_service_type').annotate(
            count=Count('id'),
            total_current=Sum('current_demand'),
            total_future=Sum('future_demand')
        )
        
        product_service_data = []
        for ps in product_service_stats:
            if ps['survey__product_service_type']:
                product_service_data.append({
                    'type': ps['survey__product_service_type'],
                    'count': ps['count'],
                    'total_current': ps['total_current'] or 0,
                    'total_future': ps['total_future'] or 0
                })
        
        # Sector-wise Demand (Top 10)
        sector_stats = job_qs.values('sector').annotate(
            count=Count('id'),
            total_current=Sum('current_demand'),
            total_future=Sum('future_demand')
        ).order_by('-total_current')[:10]
        
        sector_data = []
        for s in sector_stats:
            if s['sector']:
                sector_data.append({
                    'sector': s['sector'],
                    'count': s['count'],
                    'total_current': s['total_current'] or 0,
                    'total_future': s['total_future'] or 0
                })
        
        # Get all districts and blocks for filters
        all_districts = Survey.objects.values_list('district', flat=True).distinct().order_by('district')
        all_districts = [d for d in all_districts if d]
        
        all_blocks = Survey.objects.values_list('block', flat=True).distinct().order_by('block')
        all_blocks = [b for b in all_blocks if b]
        
        all_sectors = JobDemand.objects.values_list('sector', flat=True).distinct().order_by('sector')
        all_sectors = [s for s in all_sectors if s]
        
        # Monthly trend data (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = survey_qs.filter(created_at__gte=six_months_ago).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        monthly_trend = []
        for m in monthly_data:
            monthly_trend.append({
                'month': m['month'],
                'count': m['count']
            })
        
        context = {
            'total_surveys': total_surveys,
            'total_jobs': total_jobs,
            'total_current': total_current,
            'total_future': total_future,
            'latest_surveys': latest_surveys_data,
            'district_stats': district_stats,
            'block_stats': block_stats,
            'product_service_data': product_service_data,
            'sector_data': sector_data,
            'monthly_trend': monthly_trend,
            'all_districts': all_districts,
            'all_blocks': all_blocks,
            'all_sectors': all_sectors,
            'selected_district': district_filter,
            'selected_block': block_filter,
            'selected_sector': sector_filter,
        }
        
        return render(request, 'portal/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        context = {
            'total_surveys': 0,
            'total_jobs': 0,
            'total_current': 0,
            'total_future': 0,
            'latest_surveys': [],
            'district_stats': [],
            'block_stats': [],
            'product_service_data': [],
            'sector_data': [],
            'monthly_trend': [],
            'all_districts': [],
            'all_blocks': [],
            'all_sectors': [],
        }
        return render(request, 'portal/dashboard.html', context)


@login_required
def admin_surveys(request):
    """View all surveys"""
    surveys = Survey.objects.all().prefetch_related('job_demands')
    
    # Calculate unique districts
    unique_districts = surveys.values_list('district', flat=True).distinct().count()
    total_jobs = JobDemand.objects.count()
    
    return render(request, 'portal/surveys.html', {
        'surveys': surveys,
        'total_jobs': total_jobs,
        'unique_districts': unique_districts,
    })


@login_required
def admin_job_demands(request):
    """View all job demands"""
    job_demands = JobDemand.objects.all().select_related('survey')
    return render(request, 'portal/job_demands.html', {'job_demands': job_demands})


@login_required
def admin_logout(request):
    """Logout from admin portal"""
    logout(request)
    return redirect('survey:admin_login')


@login_required
def get_chart_data(request):
    """API endpoint for chart data"""
    total_current = JobDemand.objects.aggregate(total=Sum('current_demand'))['total'] or 0
    total_future = JobDemand.objects.aggregate(total=Sum('future_demand'))['total'] or 0
    
    return JsonResponse({
        'current_demand': total_current,
        'future_demand': total_future
    })


@login_required
def debug_data(request):
    """Debug view to check data"""
    surveys = Survey.objects.all()
    jobs = JobDemand.objects.all()
    
    data = {
        'survey_count': surveys.count(),
        'job_count': jobs.count(),
        'surveys': [
            {
                'id': s.id,
                'employer': s.employer_name,
                'code': s.employer_code,
                'jobs': s.job_demands.count()
            } for s in surveys
        ],
        'jobs': [
            {
                'id': j.id,
                'survey_id': j.survey_id,
                'role': j.job_role,
                'current': j.current_demand,
                'future': j.future_demand
            } for j in jobs
        ]
    }
    return JsonResponse(data)


@login_required
def get_survey_detail(request, survey_id):
    """Get survey details for popup"""
    try:
        survey = Survey.objects.get(id=survey_id)
        job_demands = survey.job_demands.all()
        
        data = {
            'id': survey.id,
            'start_time': survey.start_time or '',
            'completion_time': survey.completion_time or '',
            'submission_date': survey.submission_date.strftime('%Y-%m-%d') if survey.submission_date else '',
            
            # Employer Information
            'employer_code': survey.employer_code,
            'employer_name': survey.employer_name,
            'primary_sector': survey.primary_sector,
            'district': survey.district,
            'block': survey.block,
            'riico_area': survey.riico_area or '',
            'address': survey.address,
            'organisation_type': survey.organisation_type,
            'product_service_type': survey.product_service_type,
            'company_size': survey.company_size,
            'active_status': survey.active_status,
            
            # Contact Details
            'senior_official_name': survey.senior_official_name,
            'mobile_number': survey.mobile_number,
            'email_id': survey.email_id,
            'email': survey.email or '',
            'name': survey.name or '',
            'hr_mobile_number': survey.hr_mobile_number or '',
            
            # Readiness and Collaboration
            'placement_ready': survey.placement_ready,
            'apprenticeship_ready': survey.apprenticeship_ready,
            'guest_lecture_ready': survey.guest_lecture_ready,
            'exposure_visit_ready': survey.exposure_visit_ready,
            'csr_interest': survey.csr_interest,
            'awareness_of_rsldc': survey.awareness_of_rsldc,
            'local_employee_ready': survey.local_employee_ready,
            'collaboration_ready': survey.collaboration_ready,
            
            # Challenges and Remarks
            'hiring_challenges': survey.hiring_challenges or '',
            'remarks': survey.remarks or '',
            
            # System Info
            'created_at': survey.created_at.strftime('%d %b %Y, %I:%M %p'),
            
            # Job Demands
            'job_demands': [
                {
                    'row_no': job.row_no,
                    'sector': job.sector,
                    'job_role': job.job_role,
                    'education_req': job.education_req,
                    'experience_req': job.experience_req,
                    'salary_expected': job.salary_expected,
                    'current_demand': job.current_demand,
                    'future_demand': job.future_demand,
                    'demand_6_months': job.demand_6_months,
                    'demand_12_months': job.demand_12_months,
                    'apprenticeship_demand': job.apprenticeship_demand,
                    'placement_demand': job.placement_demand
                }
                for job in job_demands
            ],
            
            # Totals using model properties
            'totals': {
                'current_demand': survey.total_current_demand,
                'future_demand': survey.total_future_demand,
                'demand_6_months': survey.total_demand_6_months,
                'demand_12_months': survey.total_demand_12_months,
                'apprenticeship_demand': survey.total_apprenticeship_demand,
                'placement_demand': survey.total_placement_demand
            }
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Survey.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Survey not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def admin_export_full_csv(request):
    """Export complete survey data with job demands in separate columns"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="survey_full_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Main Headers
    main_headers = [
        'Survey ID', 'Start Time', 'Completion Time', 'Submission Date',
        'Employer Code', 'Employer Name', 'Primary Sector', 'District', 'Block',
        'RIICO Area', 'Address', 'Organisation Type', 'Product/Service Type',
        'Company Size', 'Active Status',
        'Senior Official Name', 'Mobile Number', 'Email ID', 'HR Email', 'HR Name', 'HR Mobile',
        'Placement Ready', 'Apprenticeship Ready', 'Guest Lecture Ready',
        'Exposure Visit Ready', 'CSR Interest', 'Awareness of RSLDC',
        'Local Employee Ready', 'Collaboration Ready',
        'Hiring Challenges', 'Remarks',
        'Created At', 'Updated At'
    ]
    
    # First, find maximum number of job demands for any survey
    max_jobs = JobDemand.objects.values('survey').annotate(
        job_count=Count('id')
    ).aggregate(Max('job_count'))['job_count__max'] or 0
    
    # Job Demand Headers - Dynamic columns
    job_headers = []
    for i in range(1, max_jobs + 1):
        job_headers.extend([
            f'Job Demand-{i} (Sector)',
            f'Job Demand-{i} (Job Role)',
            f'Job Demand-{i} (Education)',
            f'Job Demand-{i} (Experience)',
            f'Job Demand-{i} (Salary)',
            f'Job Demand-{i} (Current Demand)',
            f'Job Demand-{i} (Future Demand)',
            f'Job Demand-{i} (6 Months)',
            f'Job Demand-{i} (12 Months)',
            f'Job Demand-{i} (Apprenticeship)',
            f'Job Demand-{i} (Placement)'
        ])
    
    # Combine headers
    all_headers = main_headers + job_headers
    writer.writerow(all_headers)
    
    # Data
    for survey in Survey.objects.all().prefetch_related('job_demands'):
        row = [
            survey.id,
            survey.start_time or '',
            survey.completion_time or '',
            survey.submission_date.strftime('%Y-%m-%d') if survey.submission_date else '',
            survey.employer_code,
            survey.employer_name,
            survey.primary_sector,
            survey.district,
            survey.block,
            survey.riico_area or '',
            survey.address,
            survey.organisation_type,
            survey.product_service_type,
            survey.company_size,
            survey.active_status,
            survey.senior_official_name,
            survey.mobile_number,
            survey.email_id,
            survey.email or '',
            survey.name or '',
            survey.hr_mobile_number or '',
            survey.placement_ready,
            survey.apprenticeship_ready,
            survey.guest_lecture_ready,
            survey.exposure_visit_ready,
            survey.csr_interest,
            survey.awareness_of_rsldc,
            survey.local_employee_ready,
            survey.collaboration_ready,
            survey.hiring_challenges or '',
            survey.remarks or '',
            survey.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            survey.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Add job demands data
        job_list = list(survey.job_demands.all())
        
        # For each job demand, add its fields
        for i in range(max_jobs):
            if i < len(job_list):
                job = job_list[i]
                row.extend([
                    job.sector,
                    job.job_role,
                    job.education_req,
                    job.experience_req,
                    job.salary_expected,
                    job.current_demand,
                    job.future_demand,
                    job.demand_6_months,
                    job.demand_12_months,
                    job.apprenticeship_demand,
                    job.placement_demand
                ])
            else:
                # Empty columns for surveys with fewer job demands
                row.extend([''] * 11)  # 11 fields per job demand
        
        writer.writerow(row)
    
    return response