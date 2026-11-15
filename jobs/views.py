from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.exceptions import ConflictException
from core.permissions import IsCandidate, IsOwnerOrReadOnly, IsRecruiter

from .filters import JobFilter
from .models import Application, Company, Job, Skill
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    CompanySerializer,
    JobSerializer,
    SkillSerializer,
)
from .services import transition_application_status


# ----------------------------------------------------------------------
# Skills
# ----------------------------------------------------------------------
@extend_schema(
    tags=['Skills'],
    summary='List all skills',
    description='Public endpoint to retrieve the catalog of available skills for job filtering and posting.',
)
class SkillListView(generics.ListCreateAPIView):
    queryset = Skill.objects.all().order_by('name')
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), (IsRecruiter | permissions.IsAdminUser)()]
        return [permissions.AllowAny()]


# ----------------------------------------------------------------------
# Companies
# ----------------------------------------------------------------------
@extend_schema(
    tags=['Companies'],
    summary='List companies or create a new company',
    description='Public list of companies. Authenticated recruiters may register a company (maximum one per recruiter).',
)
class CompanyListCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.all().select_related('owner')
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsRecruiter()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema(
    tags=['Companies'],
    summary='Retrieve, update, or delete a company',
    description='Public read access. Updates and deletion are strictly limited to the owning recruiter.',
)
class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all().select_related('owner')
    serializer_class = CompanySerializer
    permission_classes = [IsOwnerOrReadOnly]


# ----------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------
@extend_schema(
    tags=['Jobs'],
    summary='List or create job postings',
    description=(
        'Public list of jobs with full search, filtering, ordering, and pagination. '
        'Recruiters may post new jobs linked to their registered company.'
    ),
)
class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'company__name', 'location']
    ordering_fields = ['created_at', 'salary_min', 'salary_max', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsRecruiter()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        # Prevent N+1 queries by selecting company and prefetching skills
        return Job.objects.select_related('company', 'company__owner').prefetch_related('skills').all()

    def perform_create(self, serializer):
        recruiter = self.request.user
        company = recruiter.companies.first()
        if not company:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {"company": ["You must create a company profile before you can post job openings."]}
            )
        serializer.save(company=company)


@extend_schema(
    tags=['Jobs'],
    summary='Retrieve, update, or delete a job posting',
    description='Public read access. Updates and deletion are strictly restricted to the owning recruiter.',
)
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Job.objects.select_related('company', 'company__owner').prefetch_related('skills').all()


# ----------------------------------------------------------------------
# Applications
# ----------------------------------------------------------------------
@extend_schema(
    tags=['Applications'],
    summary='Apply to a job',
    description='Candidate submits an application with PDF resume (max 2MB) and optional cover letter. Duplicate applications return 409 Conflict.',
    responses={
        201: ApplicationSerializer,
        400: OpenApiResponse(description='Validation error or inactive job'),
        403: OpenApiResponse(description='Recruiters cannot apply to jobs'),
        409: OpenApiResponse(description='Candidate has already applied to this job'),
    }
)
class JobApplyView(generics.CreateAPIView):
    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsCandidate]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        job = get_object_or_404(Job, pk=self.kwargs['pk'])

        if not job.is_active:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"job": ["This job posting is closed and no longer accepting applications."]})

        # Check duplicate application (FR-14)
        if Application.objects.filter(job=job, candidate=request.user).exists():
            raise ConflictException("You have already applied for this job.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save(job=job, candidate=request.user)

        output_serializer = ApplicationSerializer(application, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Applications'],
    summary='List applications for a job',
    description='Owning recruiter retrieves all applications submitted to their job posting.',
)
class JobApplicationsListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiter]
    queryset = Application.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()

        job = get_object_or_404(Job.objects.select_related('company__owner'), pk=self.kwargs['pk'])
        if job.company.owner != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view applications for this job.")

        return (
            Application.objects.filter(job=job)
            .select_related('candidate', 'job', 'job__company')
            .order_by('-applied_at')
        )


@extend_schema(
    tags=['Applications'],
    summary='List my applications',
    description='Candidate retrieves all applications they have submitted.',
)
class CandidateApplicationsListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]
    queryset = Application.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Application.objects.none()

        return (
            Application.objects.filter(candidate=self.request.user)
            .select_related('job', 'job__company', 'candidate')
            .order_by('-applied_at')
        )


@extend_schema(
    tags=['Applications'],
    summary='Update application status',
    description=(
        'Owning recruiter updates candidate application status following the workflow: '
        'applied -> shortlisted -> (hired | rejected). Rejects invalid transitions.'
    ),
    request=ApplicationStatusUpdateSerializer,
    responses={
        200: ApplicationSerializer,
        400: OpenApiResponse(description='Invalid status transition'),
        403: OpenApiResponse(description='Only the owning recruiter can update status'),
    }
)
class ApplicationStatusUpdateView(generics.GenericAPIView):
    permission_classes = [IsRecruiter]
    serializer_class = ApplicationStatusUpdateSerializer

    def patch(self, request, pk=None):
        application = get_object_or_404(
            Application.objects.select_related('job__company__owner', 'candidate', 'job__company'),
            pk=pk
        )

        # Check ownership
        if application.job.company.owner != request.user and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update application statuses for jobs belonging to your company.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        updated_application = transition_application_status(application, new_status)
        output_serializer = ApplicationSerializer(updated_application, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)
