import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import (
    AdminFactory,
    CandidateFactory,
    CompanyFactory,
    RecruiterFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


def get_authenticated_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def candidate_user(db):
    return CandidateFactory(username='candidate1', email='candidate1@example.com')


@pytest.fixture
def candidate_client(candidate_user):
    return get_authenticated_client(candidate_user)


@pytest.fixture
def candidate_user2(db):
    return CandidateFactory(username='candidate2', email='candidate2@example.com')


@pytest.fixture
def candidate_client2(candidate_user2):
    return get_authenticated_client(candidate_user2)


@pytest.fixture
def recruiter_user(db):
    return RecruiterFactory(username='recruiter1', email='recruiter1@example.com')


@pytest.fixture
def recruiter_client(recruiter_user):
    return get_authenticated_client(recruiter_user)


@pytest.fixture
def recruiter_company(recruiter_user):
    return CompanyFactory(name='TechCorp', owner=recruiter_user)


@pytest.fixture
def recruiter_user2(db):
    return RecruiterFactory(username='recruiter2', email='recruiter2@example.com')


@pytest.fixture
def recruiter_client2(recruiter_user2):
    return get_authenticated_client(recruiter_user2)


@pytest.fixture
def recruiter_company2(recruiter_user2):
    return CompanyFactory(name='InnovateLabs', owner=recruiter_user2)


@pytest.fixture
def admin_user(db):
    return AdminFactory(username='admin1', email='admin1@example.com')


@pytest.fixture
def admin_client(admin_user):
    return get_authenticated_client(admin_user)


@pytest.fixture
def valid_pdf_file():
    content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF'
    return SimpleUploadedFile("resume.pdf", content, content_type="application/pdf")


@pytest.fixture
def oversized_pdf_file():
    # 2.1 MB file
    content = b'%PDF-1.4\n' + b'0' * (2 * 1024 * 1024 + 1024)
    return SimpleUploadedFile("big_resume.pdf", content, content_type="application/pdf")


@pytest.fixture
def invalid_text_file():
    content = b'This is plain text and not a PDF file.'
    return SimpleUploadedFile("resume.txt", content, content_type="text/plain")
