from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone

class Survey(models.Model):
    # System Fields
    id = models.AutoField(primary_key=True)
    start_time = models.CharField(max_length=100, blank=True, null=True)
    completion_time = models.CharField(max_length=100, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    
    # Employer Information
    employer_code = models.CharField(max_length=100, blank=False, null=False)
    employer_name = models.CharField(max_length=255, blank=False, null=False)
    primary_sector = models.CharField(max_length=100, blank=False, null=False)
    district = models.CharField(max_length=100, blank=False, null=False)
    block = models.CharField(max_length=100, blank=False, null=False)
    riico_area = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=False, null=False)
    organisation_type = models.CharField(max_length=100, blank=False, null=False)
    product_service_type = models.CharField(max_length=50, blank=False, null=False)
    company_size = models.IntegerField(blank=False, null=False, default=0)
    active_status = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    
    # Contact Details
    senior_official_name = models.CharField(max_length=255, blank=False, null=False)
    mobile_number = models.CharField(max_length=10, blank=False, null=False)
    email_id = models.EmailField(blank=False, null=False)
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    hr_mobile_number = models.CharField(max_length=10, blank=True, null=True)
    
    # Readiness and Collaboration
    placement_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    apprenticeship_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    guest_lecture_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    exposure_visit_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    csr_interest = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    awareness_of_rsldc = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    local_employee_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    collaboration_ready = models.CharField(max_length=10, default='Yes', blank=True, null=True)
    
    # Challenges and Remarks
    hiring_challenges = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'survey_surveys'
        ordering = ['-created_at']
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'
    
    def __str__(self):
        return f"{self.employer_code} - {self.employer_name}"
    
    # ===== PROPERTIES FOR DEMAND TOTALS =====
    @property
    def total_current_demand(self):
        return self.job_demands.aggregate(models.Sum('current_demand'))['current_demand__sum'] or 0
    
    @property
    def total_future_demand(self):
        return self.job_demands.aggregate(models.Sum('future_demand'))['future_demand__sum'] or 0
    
    @property
    def total_demand_6_months(self):
        return self.job_demands.aggregate(models.Sum('demand_6_months'))['demand_6_months__sum'] or 0
    
    @property
    def total_demand_12_months(self):
        return self.job_demands.aggregate(models.Sum('demand_12_months'))['demand_12_months__sum'] or 0
    
    @property
    def total_apprenticeship_demand(self):
        return self.job_demands.aggregate(models.Sum('apprenticeship_demand'))['apprenticeship_demand__sum'] or 0
    
    @property
    def total_placement_demand(self):
        return self.job_demands.aggregate(models.Sum('placement_demand'))['placement_demand__sum'] or 0


class JobDemand(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='job_demands')
    row_no = models.IntegerField(default=1)
    
    sector = models.CharField(max_length=100, blank=False, null=False)
    job_role = models.CharField(max_length=255, blank=False, null=False)
    education_req = models.CharField(max_length=100, blank=False, null=False)
    experience_req = models.CharField(max_length=50, blank=False, null=False)
    salary_expected = models.CharField(max_length=50, blank=False, null=False)
    current_demand = models.IntegerField(default=0)
    future_demand = models.IntegerField(default=0)
    demand_6_months = models.IntegerField(default=0)
    demand_12_months = models.IntegerField(default=0)
    apprenticeship_demand = models.IntegerField(default=0)
    placement_demand = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'survey_job_demands'
        ordering = ['survey', 'row_no']
        verbose_name = 'Job Demand'
        verbose_name_plural = 'Job Demands'
    
    def __str__(self):
        return f"{self.survey.employer_code} - {self.job_role}"