from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from .validators import validate_resume_file


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='companies',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Companies'
        constraints = [
            # FR-6: A recruiter can create one company profile
            UniqueConstraint(fields=['owner'], name='unique_recruiter_company')
        ]

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPE_FULL_TIME = 'full_time'
    JOB_TYPE_PART_TIME = 'part_time'
    JOB_TYPE_INTERNSHIP = 'internship'
    JOB_TYPE_CONTRACT = 'contract'

    JOB_TYPE_CHOICES = (
        (JOB_TYPE_FULL_TIME, 'Full Time'),
        (JOB_TYPE_PART_TIME, 'Part Time'),
        (JOB_TYPE_INTERNSHIP, 'Internship'),
        (JOB_TYPE_CONTRACT, 'Contract'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs',
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=255, db_index=True)
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default=JOB_TYPE_FULL_TIME,
        db_index=True,
    )
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        related_name='jobs',
        blank=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title'], name='job_title_idx'),
            models.Index(fields=['location'], name='job_location_idx'),
            models.Index(fields=['created_at'], name='job_created_at_idx'),
        ]
        constraints = [
            CheckConstraint(
                condition=(
                    Q(salary_min__isnull=True)
                    | Q(salary_max__isnull=True)
                    | Q(salary_min__lte=F('salary_max'))
                ),
                name='check_salary_min_lte_salary_max'
            )
        ]

    def __str__(self):
        return f"{self.title} at {self.company.name}"


class Application(models.Model):
    STATUS_APPLIED = 'applied'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_REJECTED = 'rejected'
    STATUS_HIRED = 'hired'

    STATUS_CHOICES = (
        (STATUS_APPLIED, 'Applied'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_HIRED, 'Hired'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        db_index=True,
    )
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[validate_resume_file],
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_APPLIED,
        db_index=True,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['status'], name='app_status_idx'),
            models.Index(fields=['candidate'], name='app_candidate_idx'),
        ]
        constraints = [
            UniqueConstraint(
                fields=['job', 'candidate'],
                name='unique_job_candidate_application'
            )
        ]

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title} ({self.status})"
