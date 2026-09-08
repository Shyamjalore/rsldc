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


# ============================================================
# NEW MODELS FOR ASSOCIATION CONSULTATION
# ============================================================

class AssociationConsultation(models.Model):
    """Model for Industry Association Consultation Questionnaire"""
    
    # A. Consultation Control
    consultation_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    district_region = models.CharField(max_length=255, blank=False, null=False)
    mode = models.CharField(max_length=50, blank=False, null=False, choices=[
        ('In-person', 'In-person'),
        ('Telephone', 'Telephone'),
        ('Online', 'Online'),
        ('Other', 'Other'),
    ])
    mode_other = models.CharField(max_length=100, blank=True, null=True)
    consultation_date = models.DateField(blank=False, null=False)
    surveyor_name = models.CharField(max_length=255, blank=False, null=False)
    
    # B. Association Profile
    association_name = models.CharField(max_length=255, blank=False, null=False)
    association_type = models.CharField(max_length=50, blank=False, null=False, choices=[
        ('State-level', 'State-level'),
        ('District-level', 'District-level'),
        ('Sector-specific', 'Sector-specific'),
        ('Cluster-based', 'Cluster-based'),
        ('Chamber', 'Chamber'),
        ('Other', 'Other'),
    ])
    association_type_other = models.CharField(max_length=100, blank=True, null=True)
    primary_sector = models.CharField(max_length=255, blank=False, null=False)
    geographic_coverage = models.CharField(max_length=50, blank=False, null=False, choices=[
        ('Statewide', 'Statewide'),
        ('Multi-district', 'Multi-district'),
        ('District', 'District'),
        ('Industrial cluster', 'Industrial cluster'),
    ])
    geographic_specify = models.CharField(max_length=255, blank=True, null=True)
    year_established = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1900)])
    total_members = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    active_members = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    
    # Member Composition
    comp_micro = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    comp_small = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    comp_medium = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    comp_large = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    
    key_clusters = models.CharField(max_length=500, blank=True, null=True)
    
    # Respondent Details
    respondent_name = models.CharField(max_length=255, blank=False, null=False)
    respondent_mobile = models.CharField(max_length=10, blank=False, null=False)
    respondent_email = models.EmailField(blank=False, null=False)
    
    # C. Member and Sector Profile
    major_products = models.CharField(max_length=500, blank=True, null=True)
    estimated_workforce = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    business_trend = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Expanding', 'Expanding'),
        ('Stable', 'Stable'),
        ('Contracting', 'Contracting'),
        ('Seasonal / cyclical', 'Seasonal / cyclical'),
        ('Mixed', 'Mixed'),
    ])
    growth_drivers = models.CharField(max_length=500, blank=True, null=True)
    upcoming_projects = models.CharField(max_length=500, blank=True, null=True)
    peak_hiring = models.CharField(max_length=255, blank=True, null=True)
    member_employers_count = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    member_list_attached = models.BooleanField(default=False)
    
    # F. Recruitment Challenges (stored as JSON)
    recruitment_challenges = models.JSONField(default=list, blank=True, null=True)
    difficult_roles = models.CharField(max_length=500, blank=True, null=True)
    emerging_roles = models.CharField(max_length=500, blank=True, null=True)
    changing_competencies = models.CharField(max_length=500, blank=True, null=True)
    skill_gaps = models.CharField(max_length=500, blank=True, null=True)
    high_demand_districts = models.CharField(max_length=500, blank=True, null=True)
    unfilled_reasons = models.CharField(max_length=500, blank=True, null=True)
    
    # G. Industry-Training Partnership
    mobilise_placements = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Conditional', 'Conditional'),
    ])
    support_apprenticeship = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Conditional', 'Conditional'),
    ])
    support_guest_lectures = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Conditional', 'Conditional'),
    ])
    facilitate_visits = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Conditional', 'Conditional'),
    ])
    demand_updates = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Half-yearly', 'Half-yearly'),
        ('As required', 'As required'),
        ('Not feasible', 'Not feasible'),
    ])
    nodal_officer_name = models.CharField(max_length=255, blank=True, null=True)
    nodal_officer_mobile = models.CharField(max_length=10, blank=True, null=True)
    nodal_officer_email = models.EmailField(blank=True, null=True)
    
    # H. Validation and Recommendations
    survey_reviewed = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Partly', 'Partly'),
    ])
    alignment_view = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Consistent', 'Consistent'),
        ('Partly consistent', 'Partly consistent'),
        ('Not consistent', 'Not consistent'),
        ('Insufficient evidence', 'Insufficient evidence'),
    ])
    priority_training = models.CharField(max_length=500, blank=True, null=True)
    curriculum_changes = models.CharField(max_length=500, blank=True, null=True)
    placement_actions = models.CharField(max_length=500, blank=True, null=True)
    policy_support = models.CharField(max_length=500, blank=True, null=True)
    additional_remarks = models.TextField(blank=True, null=True)
    
    # I. Evidence and Submission
    supporting_evidence = models.CharField(max_length=100, blank=True, null=True, choices=[
        ('Member list', 'Member list'),
        ('Vacancy compilation', 'Vacancy compilation'),
        ('Survey / study', 'Survey / study'),
        ('Minutes / resolution', 'Minutes / resolution'),
        ('Employer letters', 'Employer letters'),
        ('Other', 'Other'),
    ])
    demand_evidence_status = models.CharField(max_length=100, blank=True, null=True, choices=[
        ('Employer-wise list available', 'Employer-wise list available'),
        ('Aggregate only', 'Aggregate only'),
        ('Directional / expert view', 'Directional / expert view'),
    ])
    respondent_signature = models.CharField(max_length=255, blank=True, null=True)
    facilitator_signature = models.CharField(max_length=255, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    
    # Supporting Document
    supporting_document = models.FileField(
        upload_to='association_documents/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp'])
        ],
        help_text='Upload PDF or Image (Max 50KB)'
    )
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'association_consultations'
        ordering = ['-created_at']
        verbose_name = 'Association Consultation'
        verbose_name_plural = 'Association Consultations'
    
    def __str__(self):
        return f"{self.consultation_id or 'Draft'} - {self.association_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate consultation ID if not provided
        if not self.consultation_id:
            year = self.consultation_date.year if self.consultation_date else timezone.now().year
            count = AssociationConsultation.objects.filter(
                consultation_date__year=year
            ).count() + 1
            self.consultation_id = f"ASSOC-{year}-{str(count).zfill(4)}"
        super().save(*args, **kwargs)
    
    @property
    def total_job_roles(self):
        return self.job_roles.count()
    
    @property
    def total_apprenticeships(self):
        return self.apprenticeship_opportunities.count()
    
    @property
    def total_current_demand(self):
        return self.job_roles.aggregate(
            models.Sum('current_openings')
        )['current_openings__sum'] or 0
    
    @property
    def total_future_demand(self):
        return self.job_roles.aggregate(
            models.Sum('openings_6_months') + models.Sum('openings_12_months')
        )['openings_6_months__sum'] or 0 + self.job_roles.aggregate(
            models.Sum('openings_12_months')
        )['openings_12_months__sum'] or 0


class AssociationJobRole(models.Model):
    """Job roles reported by association (D. Sector and Cluster Demand)"""
    
    consultation = models.ForeignKey(
        AssociationConsultation,
        on_delete=models.CASCADE,
        related_name='job_roles'
    )
    row_no = models.IntegerField(default=1)
    
    # Job Role Details
    job_role = models.CharField(max_length=255, blank=False, null=False)
    sector = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=500, blank=True, null=True)
    qualification = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Below 10th', 'Below 10th'),
        ('10th', '10th'),
        ('12th', '12th'),
        ('ITI', 'ITI'),
        ('Diploma', 'Diploma'),
        ('Graduate', 'Graduate'),
        ('Postgraduate', 'Postgraduate'),
        ('Other', 'Other'),
    ])
    qualification_other = models.CharField(max_length=100, blank=True, null=True)
    experience = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Fresher', 'Fresher'),
        ('0-1 year', '0-1 year'),
        ('1-3 years', '1-3 years'),
        ('3-5 years', '3-5 years'),
        ('5+ years', '5+ years'),
    ])
    certification = models.CharField(max_length=10, default='No', choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
    ])
    certification_detail = models.CharField(max_length=255, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    salary_period = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('Month', 'Month'),
        ('Day', 'Day'),
        ('Hour', 'Hour'),
        ('Other', 'Other'),
    ])
    employment_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Permanent', 'Permanent'),
        ('Fixed-term', 'Fixed-term'),
        ('Contractual', 'Contractual'),
        ('Seasonal', 'Seasonal'),
        ('Gig / Task-based', 'Gig / Task-based'),
    ])
    
    # Demand Numbers
    current_openings = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    openings_6_months = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    openings_12_months = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Skills
    tech_skills = models.CharField(max_length=500, blank=True, null=True)
    employability_skills = models.CharField(max_length=500, blank=True, null=True)
    
    # Suitability
    women_suitable = models.CharField(max_length=20, default='Yes', choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Depends', 'Depends'),
    ])
    pwd = models.CharField(max_length=20, default='Yes', choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Depends', 'Depends'),
    ])
    
    # Mobility (stored as JSON)
    mobility = models.JSONField(default=list, blank=True, null=True)
    
    # Apprenticeship/OJT Potential
    apprentice_seats = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    ojt_seats = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    internship_seats = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Source/Validation
    reporting_employers = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    employer_list_attached = models.BooleanField(default=False)
    
    remarks = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'association_job_roles'
        ordering = ['consultation', 'row_no']
        verbose_name = 'Association Job Role'
        verbose_name_plural = 'Association Job Roles'
    
    def __str__(self):
        return f"{self.consultation.consultation_id} - {self.job_role}"
    
    @property
    def total_openings(self):
        return self.current_openings + self.openings_6_months + self.openings_12_months


class AssociationApprenticeship(models.Model):
    """Apprenticeship/OJT opportunities reported by association (F. Aggregate Apprenticeship/OJT Potential)"""
    
    consultation = models.ForeignKey(
        AssociationConsultation,
        on_delete=models.CASCADE,
        related_name='apprenticeship_opportunities'
    )
    row_no = models.IntegerField(default=1)
    
    job_role = models.CharField(max_length=255, blank=False, null=False)
    opportunity_type = models.CharField(max_length=50, blank=False, null=False, choices=[
        ('Apprenticeship', 'Apprenticeship'),
        ('OJT', 'OJT'),
        ('Internship', 'Internship'),
    ])
    employers_interested = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    seats = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    duration = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stipend = models.CharField(max_length=100, blank=True, null=True)
    start_period = models.CharField(max_length=100, blank=True, null=True)
    conversion = models.CharField(max_length=20, default='Not known', choices=[
        ('High', 'High'),
        ('Moderate', 'Moderate'),
        ('Low', 'Low'),
        ('Not known', 'Not known'),
    ])
    employer_list = models.CharField(max_length=20, default='No', choices=[
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('To be compiled', 'To be compiled'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'association_apprenticeships'
        ordering = ['consultation', 'row_no']
        verbose_name = 'Association Apprenticeship'
        verbose_name_plural = 'Association Apprenticeships'
    
    def __str__(self):
        return f"{self.consultation.consultation_id} - {self.job_role}"