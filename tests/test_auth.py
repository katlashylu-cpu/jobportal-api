import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
class TestAuthentication:
    def test_register_candidate_success(self, api_client):
        url = reverse('auth-register')
        data = {
            'username': 'newcandidate',
            'email': 'newcandidate@example.com',
            'password': 'SecurePassword123!',
            'role': 'candidate',
        }
        response = api_client.post(url, data)
        assert response.status_code == 201
        assert response.data['username'] == 'newcandidate'
        assert response.data['email'] == 'newcandidate@example.com'
        assert response.data['role'] == 'candidate'
        assert User.objects.filter(email='newcandidate@example.com').exists()

    def test_register_recruiter_success(self, api_client):
        url = reverse('auth-register')
        data = {
            'username': 'newrecruiter',
            'email': 'newrecruiter@example.com',
            'password': 'SecurePassword123!',
            'role': 'recruiter',
        }
        response = api_client.post(url, data)
        assert response.status_code == 201
        assert response.data['role'] == 'recruiter'

    def test_register_admin_rejected(self, api_client):
        url = reverse('auth-register')
        data = {
            'username': 'fakeadmin',
            'email': 'fakeadmin@example.com',
            'password': 'SecurePassword123!',
            'role': 'admin',
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error']['code'] == 'validation_error'

    def test_register_duplicate_email(self, api_client, candidate_user):
        url = reverse('auth-register')
        data = {
            'username': 'anotheruser',
            'email': candidate_user.email,
            'password': 'SecurePassword123!',
            'role': 'candidate',
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert 'email' in response.data['error']['details']

    def test_register_duplicate_username(self, api_client, candidate_user):
        url = reverse('auth-register')
        data = {
            'username': candidate_user.username,
            'email': 'different@example.com',
            'password': 'SecurePassword123!',
            'role': 'candidate',
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert 'username' in response.data['error']['details']

    def test_register_weak_password(self, api_client):
        url = reverse('auth-register')
        data = {
            'username': 'userweak',
            'email': 'weak@example.com',
            'password': '123',
            'role': 'candidate',
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert 'password' in response.data['error']['details']

    def test_login_success(self, api_client, candidate_user):
        url = reverse('auth-login')
        data = {
            'username': candidate_user.username,
            'password': 'StrongPass123!',
        }
        response = api_client.post(url, data)
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['username'] == candidate_user.username
        assert response.data['user']['role'] == 'candidate'

    def test_login_invalid_credentials(self, api_client, candidate_user):
        url = reverse('auth-login')
        data = {
            'username': candidate_user.username,
            'password': 'WrongPassword!',
        }
        response = api_client.post(url, data)
        assert response.status_code == 401
        assert response.data['error']['code'] == 'not_authenticated'

    def test_refresh_token_success(self, api_client, candidate_user):
        login_url = reverse('auth-login')
        login_resp = api_client.post(login_url, {
            'username': candidate_user.username,
            'password': 'StrongPass123!',
        })
        refresh_token = login_resp.data['refresh']

        refresh_url = reverse('auth-refresh')
        response = api_client.post(refresh_url, {'refresh': refresh_token})
        assert response.status_code == 200
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        refresh_url = reverse('auth-refresh')
        response = api_client.post(refresh_url, {'refresh': 'invalid.token.here'})
        assert response.status_code == 401
        assert response.data['error']['code'] == 'not_authenticated'

    def test_current_user_profile(self, candidate_client, candidate_user):
        url = reverse('auth-me')
        response = candidate_client.get(url)
        assert response.status_code == 200
        assert response.data['id'] == candidate_user.id
        assert response.data['username'] == candidate_user.username
        assert response.data['role'] == candidate_user.role

    def test_current_user_unauthenticated(self, api_client):
        url = reverse('auth-me')
        response = api_client.get(url)
        assert response.status_code == 401
        assert response.data['error']['code'] == 'not_authenticated'

    def test_user_model_methods_and_string_representation(self, candidate_user, recruiter_user, admin_user):
        assert candidate_user.is_candidate() is True
        assert candidate_user.is_recruiter() is False
        assert candidate_user.is_administrator() is False

        assert recruiter_user.is_candidate() is False
        assert recruiter_user.is_recruiter() is True
        assert recruiter_user.is_administrator() is False

        assert admin_user.is_candidate() is False
        assert admin_user.is_recruiter() is False
        assert admin_user.is_administrator() is True

        assert str(candidate_user) == f"{candidate_user.username} (candidate)"
