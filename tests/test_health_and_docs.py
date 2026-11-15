import pytest
from django.urls import reverse

from tests.factories import SkillFactory


@pytest.mark.django_db
class TestHealthAndDocumentation:
    def test_health_check_endpoint(self, api_client):
        url = reverse('api-health')
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['status'] == 'healthy'
        assert response.data['service'] == 'jobportal-api'

    def test_openapi_schema_endpoint(self, api_client):
        url = reverse('schema')
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'openapi' in response.data or 'openapi' in response.content.decode()

    def test_swagger_ui_endpoint(self, api_client):
        url = reverse('swagger-ui')
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'swagger-ui' in response.content.decode().lower()

    def test_skills_list_public(self, api_client):
        SkillFactory.create_batch(3)
        url = reverse('skill-list-create')
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['count'] == 3

    def test_recruiter_create_skill(self, recruiter_client):
        url = reverse('skill-list-create')
        response = recruiter_client.post(url, {'name': 'Kubernetes'})
        assert response.status_code == 201
        assert response.data['name'] == 'Kubernetes'

    def test_candidate_cannot_create_skill(self, candidate_client):
        url = reverse('skill-list-create')
        response = candidate_client.post(url, {'name': 'Hacking'})
        assert response.status_code == 403
