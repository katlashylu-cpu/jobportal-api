import pytest
from django.core import mail
from django.urls import reverse

from jobs.models import Application
from tests.factories import ApplicationFactory, JobFactory


@pytest.mark.django_db
class TestApplications:
    def test_candidate_apply_success(self, candidate_client, recruiter_company, valid_pdf_file):
        job = JobFactory(company=recruiter_company, is_active=True)
        url = reverse('job-apply', kwargs={'pk': job.pk})
        data = {
            'resume': valid_pdf_file,
            'cover_letter': 'Excited to apply!',
        }
        response = candidate_client.post(url, data, format='multipart')
        assert response.status_code == 201
        assert response.data['job_id'] == job.id
        assert response.data['status'] == 'applied'
        assert response.data['company_name'] == recruiter_company.name
        assert Application.objects.filter(job=job).count() == 1

    def test_candidate_apply_to_inactive_job(self, candidate_client, recruiter_company, valid_pdf_file):
        job = JobFactory(company=recruiter_company, is_active=False)
        url = reverse('job-apply', kwargs={'pk': job.pk})
        response = candidate_client.post(url, {'resume': valid_pdf_file}, format='multipart')
        assert response.status_code == 400
        assert 'job' in response.data['error']['details']

    def test_recruiter_cannot_apply_to_job(self, recruiter_client, recruiter_company, valid_pdf_file):
        job = JobFactory(company=recruiter_company, is_active=True)
        url = reverse('job-apply', kwargs={'pk': job.pk})
        response = recruiter_client.post(url, {'resume': valid_pdf_file}, format='multipart')
        assert response.status_code == 403
        assert response.data['error']['code'] == 'permission_denied'

    def test_duplicate_application_returns_409_conflict(self, candidate_client, recruiter_company, valid_pdf_file):
        job = JobFactory(company=recruiter_company, is_active=True)
        url = reverse('job-apply', kwargs={'pk': job.pk})

        # First apply
        res1 = candidate_client.post(url, {'resume': valid_pdf_file}, format='multipart')
        assert res1.status_code == 201

        # Second apply with same candidate & job
        valid_pdf_file.seek(0)
        res2 = candidate_client.post(url, {'resume': valid_pdf_file}, format='multipart')
        assert res2.status_code == 409
        assert res2.data['error']['code'] == 'conflict'

    def test_apply_with_invalid_file_type(self, candidate_client, recruiter_company, invalid_text_file):
        job = JobFactory(company=recruiter_company, is_active=True)
        url = reverse('job-apply', kwargs={'pk': job.pk})
        response = candidate_client.post(url, {'resume': invalid_text_file}, format='multipart')
        assert response.status_code == 400
        assert 'resume' in response.data['error']['details']

    def test_apply_with_oversized_file(self, candidate_client, recruiter_company, oversized_pdf_file):
        job = JobFactory(company=recruiter_company, is_active=True)
        url = reverse('job-apply', kwargs={'pk': job.pk})
        response = candidate_client.post(url, {'resume': oversized_pdf_file}, format='multipart')
        assert response.status_code == 400
        assert 'resume' in response.data['error']['details']

    def test_candidate_list_own_applications(self, candidate_client, candidate_user, candidate_user2, recruiter_company):
        job1 = JobFactory(company=recruiter_company)
        job2 = JobFactory(company=recruiter_company)
        ApplicationFactory(job=job1, candidate=candidate_user)
        ApplicationFactory(job=job2, candidate=candidate_user2)

        url = reverse('candidate-applications-me')
        response = candidate_client.get(url)
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['candidate_id'] == candidate_user.id

    def test_recruiter_list_applications_for_own_job(self, recruiter_client, recruiter_company, candidate_user, candidate_user2):
        job = JobFactory(company=recruiter_company)
        ApplicationFactory(job=job, candidate=candidate_user)
        ApplicationFactory(job=job, candidate=candidate_user2)

        url = reverse('job-applications-list', kwargs={'pk': job.pk})
        response = recruiter_client.get(url)
        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_recruiter_cannot_list_applications_for_other_company_job(self, recruiter_client2, recruiter_company, candidate_user):
        job = JobFactory(company=recruiter_company)
        ApplicationFactory(job=job, candidate=candidate_user)

        url = reverse('job-applications-list', kwargs={'pk': job.pk})
        response = recruiter_client2.get(url)
        assert response.status_code == 403

    def test_application_status_workflow_transitions(self, recruiter_client, recruiter_company, candidate_user):
        job = JobFactory(company=recruiter_company)
        app = ApplicationFactory(job=job, candidate=candidate_user, status='applied')
        url = reverse('application-status-update', kwargs={'pk': app.pk})

        # 1. applied -> shortlisted (Valid)
        mail.outbox.clear()
        res1 = recruiter_client.patch(url, {'status': 'shortlisted'})
        assert res1.status_code == 200
        assert res1.data['status'] == 'shortlisted'
        assert len(mail.outbox) == 1
        assert 'Shortlisted' in mail.outbox[0].body

        # 2. shortlisted -> hired (Valid terminal)
        mail.outbox.clear()
        res2 = recruiter_client.patch(url, {'status': 'hired'})
        assert res2.status_code == 200
        assert res2.data['status'] == 'hired'
        assert len(mail.outbox) == 1
        assert 'Hired' in mail.outbox[0].body

        # 3. hired -> applied (Invalid: terminal state)
        res3 = recruiter_client.patch(url, {'status': 'applied'})
        assert res3.status_code == 400
        assert 'error' in res3.data

    def test_application_status_workflow_rejected(self, recruiter_client, recruiter_company, candidate_user):
        job = JobFactory(company=recruiter_company)
        app = ApplicationFactory(job=job, candidate=candidate_user, status='applied')
        url = reverse('application-status-update', kwargs={'pk': app.pk})

        # applied -> rejected (Valid terminal)
        res = recruiter_client.patch(url, {'status': 'rejected'})
        assert res.status_code == 200
        assert res.data['status'] == 'rejected'

        # rejected -> shortlisted (Invalid: terminal state)
        res_terminal = recruiter_client.patch(url, {'status': 'shortlisted'})
        assert res_terminal.status_code == 400

    def test_direct_jump_applied_to_hired_rejected(self, recruiter_client, recruiter_company, candidate_user):
        job = JobFactory(company=recruiter_company)
        app = ApplicationFactory(job=job, candidate=candidate_user, status='applied')
        url = reverse('application-status-update', kwargs={'pk': app.pk})

        # applied -> hired directly is not allowed
        res = recruiter_client.patch(url, {'status': 'hired'})
        assert res.status_code == 400

    def test_non_owner_cannot_update_application_status(self, recruiter_client2, recruiter_company, candidate_user):
        job = JobFactory(company=recruiter_company)
        app = ApplicationFactory(job=job, candidate=candidate_user, status='applied')
        url = reverse('application-status-update', kwargs={'pk': app.pk})

        res = recruiter_client2.patch(url, {'status': 'shortlisted'})
        assert res.status_code == 403

    def test_application_and_company_strings_and_corrupt_pdf(self, recruiter_company, candidate_user):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile

        from jobs.validators import validate_resume_file

        job = JobFactory(company=recruiter_company, title='Lead')
        app = ApplicationFactory(job=job, candidate=candidate_user, status='applied')

        assert str(recruiter_company) == recruiter_company.name
        assert str(app) == f"{candidate_user.username} -> {job.title} (applied)"

        corrupt_pdf = SimpleUploadedFile("fake.pdf", b"NOTAPDFHEADER", content_type="application/pdf")
        with pytest.raises(ValidationError, match="Invalid PDF file format"):
            validate_resume_file(corrupt_pdf)
