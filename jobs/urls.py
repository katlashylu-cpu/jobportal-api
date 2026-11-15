from django.urls import path

from .views import (
    ApplicationStatusUpdateView,
    CandidateApplicationsListView,
    CompanyDetailView,
    CompanyListCreateView,
    JobApplicationsListView,
    JobApplyView,
    JobDetailView,
    JobListCreateView,
    SkillListView,
)

urlpatterns = [
    # Companies
    path('companies/', CompanyListCreateView.as_view(), name='company-list-create'),
    path('companies/<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),

    # Jobs
    path('jobs/', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view(), name='job-apply'),
    path('jobs/<int:pk>/applications/', JobApplicationsListView.as_view(), name='job-applications-list'),

    # Applications
    path('applications/me/', CandidateApplicationsListView.as_view(), name='candidate-applications-me'),
    path('applications/<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),

    # Skills
    path('skills/', SkillListView.as_view(), name='skill-list-create'),
]
