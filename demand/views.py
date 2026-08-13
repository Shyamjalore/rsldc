import json
import logging
import traceback
from datetime import datetime, timedelta
import csv

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum, Count, Max, Q
from django.contrib import messages

from .models import Survey, JobDemand, ApprenticeshipOJT

logger = logging.getLogger(__name__)

# ============================================
# PUBLIC FORM VIEWS
# ============================================

def survey_form(request):
    return render(request, 'form.html')


@csrf_exempt
@require_http_methods(["POST"])
def submit_survey(request):
    print("="*60)
    print("🔵 SUBMIT SURVEY API CALLED")
    print("="*60)
    
    try:
        data = json.loads(request.body)
        print(f"✅ JSON Parsed Successfully")
        
        with transaction.atomic():
            survey = Survey.objects.create(
                company_code=data.get('company_code', '').strip(),
                start_time=data.get('start_time', ''),
                completion_time=data.get('completion_time', ''),
                submission_date=data.get('submission_date') or datetime.now().date(),
                field_officer_name=data.get('field_officer_name', '').strip(),
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
                contact_name=data.get('contact_name', '').strip(),
                contact_mobile=data.get('contact_mobile', '').strip(),
                contact_email=data.get('contact_email', '').strip(),
                workforce_profile=data.get('workforce_profile', '').strip(),
                placement_willingness=data.get('placement_willingness', 'No'),
                apprenticeship_willingness=data.get('apprenticeship_willingness', 'No'),
                guest_lecture_interest=data.get('guest_lecture_interest', 'No'),
                industrial_visit_interest=data.get('industrial_visit_interest', 'No'),
                csr_interest=data.get('csr_interest', 'No'),
                ojt_internship_willingness=data.get('ojt_internship_willingness', 'No'),
                recruitment_challenges=data.get('recruitment_challenges', '').strip(),
                additional_remarks=data.get('additional_remarks', '').strip(),
                supporting_evidence=data.get('supporting_evidence', '').strip(),
            )
            
            print(f"✅ Survey Created! ID: {survey.id}")
            
            # Job Demands
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
            
            # Apprenticeships
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
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ============================================
# ADMIN PORTAL VIEWS
# ============================================

def admin_login(request):
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
    try:
        district_filter = request.GET.get('district', '')
        block_filter = request.GET.get('block', '')
        sector_filter = request.GET.get('sector', '')
        
        survey_qs = Survey.objects.all()
        job_qs = JobDemand.objects.all()
        
        if district_filter:
            survey_qs = survey_qs.filter(district=district_filter)
            job_qs = job_qs.filter(survey__district=district_filter)
        
        if block_filter:
            survey_qs = survey_qs.filter(block=block_filter)
            job_qs = job_qs.filter(survey__block=block_filter)
        
        if sector_filter:
            survey_qs = survey_qs.filter(operational_sector=sector_filter)
            job_qs = job_qs.filter(sector=sector_filter)
        
        total_surveys = survey_qs.count()
        total_jobs = job_qs.count()
        
        total_current = job_qs.aggregate(total=Sum('current_openings'))['total'] or 0
        total_future_6 = job_qs.aggregate(total=Sum('openings_6_months'))['total'] or 0
        total_future_12 = job_qs.aggregate(total=Sum('openings_12_months'))['total'] or 0
        total_future = total_future_6 + total_future_12
        
        # Latest 5 Surveys
        latest_surveys = survey_qs.order_by('-created_at')[:5]
        latest_surveys_data = []
        for survey in latest_surveys:
            latest_surveys_data.append({
                'id': survey.id,
                'company_name': survey.company_name,
                'district': survey.district,
                'block': survey.block,
                'operational_sector': survey.operational_sector,
                'total_demand': survey.total_current_demand + survey.total_future_demand,
                'created_at': survey.created_at.strftime('%d %b %Y, %I:%M %p')
            })
        
        # District-wise Statistics
        district_stats = []
        districts = survey_qs.values('district').annotate(
            count=Count('id'),
            total_demand=Sum('job_demands__current_openings') + Sum('job_demands__openings_6_months') + Sum('job_demands__openings_12_months')
        ).order_by('-total_demand')
        
        for d in districts:
            if d['district']:
                district_stats.append({
                    'district': d['district'],
                    'count': d['count'],
                    'total_demand': d['total_demand'] or 0
                })
        
        # Block-wise Statistics
        block_stats = []
        if district_filter:
            blocks = survey_qs.filter(district=district_filter).values('block').annotate(
                count=Count('id'),
                total_demand=Sum('job_demands__current_openings') + Sum('job_demands__openings_6_months') + Sum('job_demands__openings_12_months')
            ).order_by('-total_demand')
        else:
            blocks = survey_qs.values('block').annotate(
                count=Count('id'),
                total_demand=Sum('job_demands__current_openings') + Sum('job_demands__openings_6_months') + Sum('job_demands__openings_12_months')
            ).order_by('-total_demand')[:10]
        
        for b in blocks:
            if b['block']:
                block_stats.append({
                    'block': b['block'],
                    'count': b['count'],
                    'total_demand': b['total_demand'] or 0
                })
        
        # Product/Service Type Statistics
        product_service_stats = job_qs.values('survey__product_service').annotate(
            count=Count('id'),
            total_current=Sum('current_openings'),
            total_future=Sum('openings_6_months') + Sum('openings_12_months')
        )
        
        product_service_data = []
        for ps in product_service_stats:
            if ps['survey__product_service']:
                product_service_data.append({
                    'type': ps['survey__product_service'],
                    'count': ps['count'],
                    'total_current': ps['total_current'] or 0,
                    'total_future': ps['total_future'] or 0
                })
        
        # Sector-wise Demand
        sector_stats = job_qs.values('sector').annotate(
            count=Count('id'),
            total_current=Sum('current_openings'),
            total_future=Sum('openings_6_months') + Sum('openings_12_months')
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
        
        all_districts = Survey.objects.values_list('district', flat=True).distinct().order_by('district')
        all_districts = [d for d in all_districts if d]
        
        all_blocks = Survey.objects.values_list('block', flat=True).distinct().order_by('block')
        all_blocks = [b for b in all_blocks if b]
        
        all_sectors = JobDemand.objects.values_list('sector', flat=True).distinct().order_by('sector')
        all_sectors = [s for s in all_sectors if s]
        
        # Monthly trend
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = survey_qs.filter(created_at__gte=six_months_ago).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        monthly_trend = [{'month': m['month'], 'count': m['count']} for m in monthly_data]
        
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
        traceback.print_exc()
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
    surveys = Survey.objects.all().prefetch_related('job_demands')
    unique_districts = surveys.values_list('district', flat=True).distinct().count()
    total_jobs = JobDemand.objects.count()
    
    return render(request, 'portal/surveys.html', {
        'surveys': surveys,
        'total_jobs': total_jobs,
        'unique_districts': unique_districts,
    })


@login_required
def admin_job_demands(request):
    job_demands = JobDemand.objects.all().select_related('survey')
    return render(request, 'portal/job_demands.html', {'job_demands': job_demands})


@login_required
def admin_logout(request):
    logout(request)
    return redirect('survey:admin_login')


@login_required
def get_chart_data(request):
    total_current = JobDemand.objects.aggregate(total=Sum('current_openings'))['total'] or 0
    total_future_6 = JobDemand.objects.aggregate(total=Sum('openings_6_months'))['total'] or 0
    total_future_12 = JobDemand.objects.aggregate(total=Sum('openings_12_months'))['total'] or 0
    
    return JsonResponse({
        'current_demand': total_current,
        'future_demand': total_future_6 + total_future_12
    })


@login_required
def debug_data(request):
    surveys = Survey.objects.all()
    jobs = JobDemand.objects.all()
    
    data = {
        'survey_count': surveys.count(),
        'job_count': jobs.count(),
        'surveys': [{'id': s.id, 'company': s.company_name, 'code': s.company_code, 'jobs': s.job_demands.count()} for s in surveys],
        'jobs': [{'id': j.id, 'survey_id': j.survey_id, 'role': j.job_role, 'current': j.current_openings, 'future': j.openings_6_months + j.openings_12_months} for j in jobs]
    }
    return JsonResponse(data)


@login_required
def get_survey_detail(request, survey_id):
    try:
        survey = Survey.objects.get(id=survey_id)
        job_demands = survey.job_demands.all()
        
        data = {
            'id': survey.id,
            'company_code': survey.company_code or '',
            'company_name': survey.company_name,
            'organisation_type': survey.organisation_type,
            'product_service': survey.product_service,
            'operational_sector': survey.operational_sector,
            'district': survey.district,
            'block': survey.block,
            'address': survey.address,
            'website': survey.website or '',
            'contact_name': survey.contact_name,
            'contact_mobile': survey.contact_mobile,
            'contact_email': survey.contact_email,
            'workforce_profile': survey.workforce_profile or '',
            'placement_willingness': survey.placement_willingness,
            'apprenticeship_willingness': survey.apprenticeship_willingness,
            'guest_lecture_interest': survey.guest_lecture_interest,
            'industrial_visit_interest': survey.industrial_visit_interest,
            'csr_interest': survey.csr_interest,
            'ojt_internship_willingness': survey.ojt_internship_willingness,
            'recruitment_challenges': survey.recruitment_challenges or '',
            'additional_remarks': survey.additional_remarks or '',
            'supporting_evidence': survey.supporting_evidence or '',
            'created_at': survey.created_at.strftime('%d %b %Y, %I:%M %p'),
            'submission_date': survey.submission_date.strftime('%Y-%m-%d') if survey.submission_date else '',
            'field_officer_name': survey.field_officer_name or '',
            
            'job_demands': [
                {
                    'row_no': job.row_no,
                    'job_role': job.job_role,
                    'sector': job.sector,
                    'qualification': job.qualification,
                    'experience': job.experience,
                    'salary_offered': job.salary_offered,
                    'current_openings': job.current_openings,
                    'openings_6_months': job.openings_6_months,
                    'openings_12_months': job.openings_12_months,
                    'apprentice_ojt': job.apprentice_ojt,
                    'gender_suitability': job.gender_suitability,
                    'pwd': job.pwd,
                    'additional_remarks': job.additional_remarks or ''
                }
                for job in job_demands
            ],
            
            'totals': {
                'current_demand': survey.total_current_demand,
                'future_demand': survey.total_future_demand,
                'demand_6_months': survey.total_demand_6_months,
                'demand_12_months': survey.total_demand_12_months,
            }
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Survey.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Survey not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def admin_export_full_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="survey_full_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Main Headers
    main_headers = [
        'Survey ID', 'Company Code', 'Company Name', 'Organisation Type',
        'District', 'Block', 'Address', 'Website',
        'Contact Name', 'Contact Mobile', 'Contact Email',
        'Operational Sector', 'Product/Service',
        'Placement Willingness', 'Apprenticeship Willingness',
        'Guest Lecture Interest', 'Industrial Visit Interest',
        'CSR Interest', 'OJT/Internship Willingness',
        'Recruitment Challenges', 'Additional Remarks', 'Supporting Evidence',
        'Submission Date', 'Field Officer Name', 'Created At'
    ]
    
    # Job Demand Headers - Dynamic
    max_jobs = JobDemand.objects.values('survey').annotate(job_count=Count('id')).aggregate(Max('job_count'))['job_count__max'] or 0
    
    job_headers = []
    for i in range(1, max_jobs + 1):
        job_headers.extend([
            f'Job Demand-{i} (Job Role)',
            f'Job Demand-{i} (Sector)',
            f'Job Demand-{i} (Qualification)',
            f'Job Demand-{i} (Experience)',
            f'Job Demand-{i} (Salary Offered)',
            f'Job Demand-{i} (Current Openings)',
            f'Job Demand-{i} (6 Months)',
            f'Job Demand-{i} (12 Months)',
            f'Job Demand-{i} (Apprentice/OJT)',
            f'Job Demand-{i} (Gender)',
            f'Job Demand-{i} (PwD)'
        ])
    
    writer.writerow(main_headers + job_headers)
    
    for survey in Survey.objects.all().prefetch_related('job_demands'):
        row = [
            survey.id,
            survey.company_code or '',
            survey.company_name,
            survey.organisation_type,
            survey.district,
            survey.block,
            survey.address,
            survey.website or '',
            survey.contact_name,
            survey.contact_mobile,
            survey.contact_email,
            survey.operational_sector,
            survey.product_service,
            survey.placement_willingness,
            survey.apprenticeship_willingness,
            survey.guest_lecture_interest,
            survey.industrial_visit_interest,
            survey.csr_interest,
            survey.ojt_internship_willingness,
            survey.recruitment_challenges or '',
            survey.additional_remarks or '',
            survey.supporting_evidence or '',
            survey.submission_date.strftime('%Y-%m-%d') if survey.submission_date else '',
            survey.field_officer_name or '',
            survey.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        job_list = list(survey.job_demands.all())
        for i in range(max_jobs):
            if i < len(job_list):
                job = job_list[i]
                row.extend([
                    job.job_role,
                    job.sector,
                    job.qualification,
                    job.experience,
                    job.salary_offered,
                    job.current_openings,
                    job.openings_6_months,
                    job.openings_12_months,
                    job.apprentice_ojt,
                    job.gender_suitability,
                    job.pwd
                ])
            else:
                row.extend([''] * 11)
        
        writer.writerow(row)
    
    return response