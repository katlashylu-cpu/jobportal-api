import pytest
from django.urls import reverse

from jobs.models import Job
from tests.factories import JobFactory, SkillFactory


@pytest.mark.django_db
class TestJobs:
    def test_recruiter_create_job_success(self, recruiter_client, recruiter_company):
        skill1 = SkillFactory(name='Python')
        skill2 = SkillFactory(name='Django')

        url = reverse('job-list-create')
        data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for an experienced backend engineer.',
            'location': 'Hyderabad',
            'job_type': 'full_time',
            'salary_min': '800000.00',
            'salary_max': '1500000.00',
            'skill_ids': [skill1.id, skill2.id],
            'is_active': True,
        }
        response = recruiter_client.post(url, data)
        assert response.status_code == 201
        assert response.data['title'] == 'Senior Python Developer'
        assert response.data['company']['id'] == recruiter_company.id
        assert len(response.data['skills']) == 2

    def test_recruiter_without_company_cannot_create_job(self, recruiter_client2):
        # recruiter2 has no company yet
        url = reverse('job-list-create')
        data = {
            'title': 'Orphan Job',
            'description': 'No company',
            'location': 'Remote',
            'job_type': 'full_time',
        }
        response = recruiter_client2.post(url, data)
        assert response.status_code == 400
        assert 'company' in response.data['error']['details']

    def test_candidate_cannot_create_job(self, candidate_client):
        url = reverse('job-list-create')
        data = {'title': 'Candidate Job', 'location': 'Remote'}
        response = candidate_client.post(url, data)
        assert response.status_code == 403

    def test_job_salary_validation(self, recruiter_client, recruiter_company):
        url = reverse('job-list-create')
        data = {
            'title': 'Dev',
            'description': 'Desc',
            'location': 'Remote',
            'job_type': 'full_time',
            'salary_min': '1000000.00',
            'salary_max': '500000.00',  # Invalid: min > max
        }
        response = recruiter_client.post(url, data)
        assert response.status_code == 400
        assert 'salary_min' in response.data['error']['details']

    def test_job_list_public_and_paginated(self, api_client, recruiter_company):
        JobFactory.create_batch(5, company=recruiter_company)
        url = reverse('job-list-create')
        response = api_client.get(f"{url}?page_size=2&page=1")
        assert response.status_code == 200
        assert response.data['count'] == 5
        assert len(response.data['results']) == 2

    def test_job_search(self, api_client, recruiter_company):
        JobFactory(company=recruiter_company, title='React Frontend Wizard')
        JobFactory(company=recruiter_company, title='Python Django Backend Engineer')
        JobFactory(company=recruiter_company, title='DevOps Specialist', description='Automate with Python pipelines')

        url = reverse('job-list-create')
        response = api_client.get(f"{url}?search=Python")
        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_job_filters(self, api_client, recruiter_company):
        skill_python = SkillFactory(name='Python')
        skill_go = SkillFactory(name='Go')

        job1 = JobFactory(
            company=recruiter_company,
            title='Hyderabad Python Lead',
            location='Hyderabad',
            job_type='full_time',
            salary_min=900000,
            salary_max=1400000,
            is_active=True,
            skills=[skill_python],
        )
        job2 = JobFactory(
            company=recruiter_company,
            title='Bangalore Go Lead',
            location='Bangalore',
            job_type='contract',
            salary_min=700000,
            salary_max=1100000,
            is_active=True,
            skills=[skill_go],
        )

        url = reverse('job-list-create')

        # Filter by location
        resp_loc = api_client.get(f"{url}?location=Hyderabad")
        assert resp_loc.data['count'] == 1
        assert resp_loc.data['results'][0]['id'] == job1.id

        # Filter by job_type
        resp_type = api_client.get(f"{url}?job_type=contract")
        assert resp_type.data['count'] == 1
        assert resp_type.data['results'][0]['id'] == job2.id

        # Filter by salary range
        resp_salary = api_client.get(f"{url}?salary_min=800000")
        assert resp_salary.data['count'] == 1
        assert resp_salary.data['results'][0]['id'] == job1.id

        # Filter by skills
        resp_skill = api_client.get(f"{url}?skills=Python")
        assert resp_skill.data['count'] == 1
        assert resp_skill.data['results'][0]['id'] == job1.id

    def test_owning_recruiter_update_job(self, recruiter_client, recruiter_company):
        job = JobFactory(company=recruiter_company, title='Junior Dev')
        url = reverse('job-detail', kwargs={'pk': job.pk})
        data = {'title': 'Senior Dev', 'is_active': False}
        response = recruiter_client.patch(url, data)
        assert response.status_code == 200
        assert response.data['title'] == 'Senior Dev'
        assert response.data['is_active'] is False

    def test_non_owning_recruiter_cannot_update_job(self, recruiter_client2, recruiter_company):
        job = JobFactory(company=recruiter_company, title='Protected Job')
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = recruiter_client2.patch(url, {'title': 'Hijacked Job'})
        assert response.status_code == 403

    def test_owning_recruiter_delete_job(self, recruiter_client, recruiter_company):
        job = JobFactory(company=recruiter_company)
        url = reverse('job-detail', kwargs={'pk': job.pk})
        response = recruiter_client.delete(url)
        assert response.status_code == 204
        assert not Job.objects.filter(pk=job.pk).exists()

    def test_job_list_no_n_plus_one_queries(self, api_client, recruiter_company, django_assert_num_queries):
        skills = SkillFactory.create_batch(3)
        # Create 10 jobs with multiple skills
        for _ in range(10):
            JobFactory(company=recruiter_company, skills=skills)

        url = reverse('job-list-create')
        # Queries expected:
        # 1. COUNT(*) for pagination
        # 2. SELECT jobs JOIN company JOIN user
        # 3. SELECT skills WHERE job_id IN (...)
        # Total <= 3 queries, regardless of whether 10 or 100 jobs are listed!
        with django_assert_num_queries(3):
            response = api_client.get(url)
            assert response.status_code == 200
            assert response.data['count'] == 10

    def test_job_and_skill_string_representations(self, recruiter_company):
        skill = SkillFactory(name='Rust')
        job = JobFactory(company=recruiter_company, title='Systems Engineer')
        assert str(skill) == 'Rust'
        assert str(job) == f"Systems Engineer at {recruiter_company.name}"
