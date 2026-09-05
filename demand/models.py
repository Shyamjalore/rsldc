from django.db import models
from django.core.validators import MinValueValidator, RegexValidator, FileExtensionValidator
from django.utils import timezone
import re
import os

class Survey(models.Model):
    # System Fields
    id = models.AutoField(primary_key=True)
    company_code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    start_time = models.CharField(max_length=100, blank=True, null=True)
    completion_time = models.CharField(max_length=100, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True, auto_now_add=True)
    field_officer_name = models.CharField(max_length=255, blank=True, null=True)
    field_officer_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # 1. EMPLOYER DETAILS
    company_name = models.CharField(max_length=255, blank=False, null=False)
    organisation_type = models.CharField(max_length=100, blank=False, null=False)
    organisation_type_other = models.CharField(max_length=100, blank=True, null=True)
    product_service = models.CharField(max_length=50, blank=False, null=False)
    product_service_specify = models.CharField(max_length=255, blank=True, null=True)
    operational_sector = models.CharField(max_length=100, blank=False, null=False)
    operational_sector_other = models.CharField(max_length=100, blank=True, null=True)
    
    # Company Size
    company_size = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Micro', 'Micro'),
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large')
    ])
    
    address = models.TextField(blank=False, null=False)
    website = models.URLField(max_length=500, blank=True, null=True)
    district = models.CharField(max_length=100, blank=False, null=False)
    block = models.CharField(max_length=100, blank=False, null=False)
    
    # 1A. CONTACT DETAILS
    contact_name = models.CharField(max_length=255, blank=False, null=False)
    contact_mobile = models.CharField(max_length=10, blank=False, null=False)
    contact_email = models.EmailField(blank=False, null=False)
    
    # HR Availability
    has_hr = models.CharField(max_length=3, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    
    # 1B. CURRENT WORKFORCE PROFILE (Stored as JSON)
    workforce_profile = models.JSONField(default=list, blank=True, null=True)
    
    # 3. EMPLOYER PARTNERSHIP
    placement_willingness = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    apprenticeship_willingness = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    guest_lecture_interest = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    industrial_visit_interest = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    csr_interest = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    ojt_internship_willingness = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    
    # 4. RECRUITMENT CHALLENGES
    recruitment_challenges = models.TextField(blank=True, null=True)
    additional_remarks = models.TextField(blank=True, null=True)
    supporting_evidence = models.CharField(max_length=500, blank=True, null=True)
    
    # Supporting Document - File Upload
    supporting_document = models.FileField(
        upload_to='supporting_documents/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp'])
        ],
        help_text='Upload PDF or Image (Max 50KB)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'survey_surveys'
        ordering = ['-created_at']
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'
    
    def __str__(self):
        return f"{self.company_code} - {self.company_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate company code if not provided
        if not self.company_code and self.district:
            district_code = ''.join(word[0].upper() for word in self.district.split())[:2]
            count = Survey.objects.filter(district=self.district).count() + 1
            self.company_code = f"{district_code}{str(count).zfill(3)}"
        super().save(*args, **kwargs)
    
    # ===== PROPERTIES FOR DEMAND TOTALS =====
    @property
    def total_current_demand(self):
        return self.job_demands.aggregate(models.Sum('current_openings'))['current_openings__sum'] or 0
    
    @property
    def total_future_demand(self):
        return (self.total_demand_6_months + self.total_demand_12_months)
    
    @property
    def total_demand_6_months(self):
        return self.job_demands.aggregate(models.Sum('openings_6_months'))['openings_6_months__sum'] or 0
    
    @property
    def total_demand_12_months(self):
        return self.job_demands.aggregate(models.Sum('openings_12_months'))['openings_12_months__sum'] or 0
    
    @property
    def total_apprenticeship_demand(self):
        return self.job_demands.filter(apprentice_ojt='Yes').count()


class JobDemand(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='job_demands')
    row_no = models.IntegerField(default=1)
    
    job_role = models.CharField(max_length=255, blank=False, null=False)
    sector = models.CharField(max_length=100, blank=False, null=False)
    qualification = models.CharField(max_length=100, blank=False, null=False)
    qualification_other = models.CharField(max_length=100, blank=True, null=True)
    experience = models.CharField(max_length=50, blank=False, null=False)
    certification = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    certification_detail = models.CharField(max_length=255, blank=True, null=True)
    salary_offered = models.CharField(max_length=50, blank=False, null=False)
    current_openings = models.IntegerField(default=0)
    openings_6_months = models.IntegerField(default=0)
    openings_12_months = models.IntegerField(default=0)
    apprentice_ojt = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    apprentice_ojt_detail = models.CharField(max_length=255, blank=True, null=True)
    gender_suitability = models.CharField(max_length=50, default='Any / No Preference')
    pwd = models.CharField(max_length=10, default='NA', choices=[('Yes', 'Yes'), ('No', 'No'), ('NA', 'NA')])
    
    # Career Progression fields
    career_progression = models.CharField(max_length=3, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    career_progression_years = models.CharField(max_length=50, blank=True, null=True)
    career_next_position = models.CharField(max_length=255, blank=True, null=True)
    career_next_salary = models.CharField(max_length=50, blank=True, null=True)
    
    additional_remarks = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'survey_job_demands'
        ordering = ['survey', 'row_no']
        verbose_name = 'Job Demand'
        verbose_name_plural = 'Job Demands'
    
    def __str__(self):
        return f"{self.survey.company_code} - {self.job_role}"


class ApprenticeshipOJT(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='apprenticeships')
    row_no = models.IntegerField(default=1)
    
    job_role = models.CharField(max_length=255, blank=False, null=False)
    opportunity_type = models.CharField(max_length=50, blank=False, null=False,
                                        choices=[
                                            ('Apprenticeship', 'Apprenticeship'),
                                            ('OJT', 'OJT'),
                                            ('Internship', 'Internship')
                                        ])
    seats_capacity = models.IntegerField(default=0)
    duration_months = models.IntegerField(default=0)
    monthly_stipend = models.IntegerField(default=0)
    expected_start_month = models.CharField(max_length=50, blank=True, null=True)
    minimum_qualification = models.CharField(max_length=100, blank=False, null=False)
    minimum_qualification_other = models.CharField(max_length=100, blank=True, null=True)
    conversion_to_employment = models.CharField(max_length=10, default='No', choices=[('Yes', 'Yes'), ('No', 'No')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'survey_apprenticeships'
        ordering = ['survey', 'row_no']
        verbose_name = 'Apprenticeship/OJT'
        verbose_name_plural = 'Apprenticeships/OJTs'
    
    def __str__(self):
        return f"{self.survey.company_code} - {self.job_role}"