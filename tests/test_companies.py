import pytest
from django.urls import reverse

from jobs.models import Company
from tests.factories import CompanyFactory


@pytest.mark.django_db
class TestCompanies:
    def test_list_companies_public(self, api_client):
        CompanyFactory.create_batch(3)
        url = reverse('company-list-create')
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['count'] == 3

    def test_retrieve_company_detail_public(self, api_client, recruiter_company):
        url = reverse('company-detail', kwargs={'pk': recruiter_company.pk})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['id'] == recruiter_company.id
        assert response.data['name'] == recruiter_company.name

    def test_recruiter_create_company_success(self, recruiter_client, recruiter_user):
        url = reverse('company-list-create')
        data = {
            'name': 'Alpha Corp',
            'description': 'Leading cloud computing provider.',
            'website': 'https://alphacorp.example.com',
            'location': 'Bangalore',
        }
        response = recruiter_client.post(url, data)
        assert response.status_code == 201
        assert response.data['name'] == 'Alpha Corp'
        assert response.data['owner_id'] == recruiter_user.id
        assert Company.objects.filter(owner=recruiter_user).count() == 1

    def test_recruiter_cannot_create_second_company(self, recruiter_client, recruiter_company):
        url = reverse('company-list-create')
        data = {
            'name': 'Beta Corp',
            'description': 'Another company',
            'website': 'https://betacorp.example.com',
            'location': 'Mumbai',
        }
        response = recruiter_client.post(url, data)
        assert response.status_code == 400
        assert 'name' in response.data['error']['details']

    def test_candidate_cannot_create_company(self, candidate_client):
        url = reverse('company-list-create')
        data = {
            'name': 'Candidate Startup',
            'location': 'Remote',
        }
        response = candidate_client.post(url, data)
        assert response.status_code == 403
        assert response.data['error']['code'] == 'permission_denied'

    def test_anonymous_cannot_create_company(self, api_client):
        url = reverse('company-list-create')
        data = {'name': 'Anon Startup', 'location': 'Remote'}
        response = api_client.post(url, data)
        assert response.status_code == 401

    def test_owning_recruiter_update_company(self, recruiter_client, recruiter_company):
        url = reverse('company-detail', kwargs={'pk': recruiter_company.pk})
        data = {'name': 'TechCorp Updated', 'location': 'Hyderabad South'}
        response = recruiter_client.patch(url, data)
        assert response.status_code == 200
        assert response.data['name'] == 'TechCorp Updated'
        recruiter_company.refresh_from_db()
        assert recruiter_company.name == 'TechCorp Updated'

    def test_non_owning_recruiter_cannot_update_company(self, recruiter_client2, recruiter_company):
        url = reverse('company-detail', kwargs={'pk': recruiter_company.pk})
        data = {'name': 'Hacked Name'}
        response = recruiter_client2.patch(url, data)
        assert response.status_code == 403

    def test_owning_recruiter_delete_company(self, recruiter_client, recruiter_company):
        url = reverse('company-detail', kwargs={'pk': recruiter_company.pk})
        response = recruiter_client.delete(url)
        assert response.status_code == 204
        assert not Company.objects.filter(pk=recruiter_company.pk).exists()
