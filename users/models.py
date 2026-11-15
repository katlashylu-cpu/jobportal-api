from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CANDIDATE = 'candidate'
    ROLE_RECRUITER = 'recruiter'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = (
        (ROLE_CANDIDATE, 'Candidate'),
        (ROLE_RECRUITER, 'Recruiter'),
        (ROLE_ADMIN, 'Admin'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CANDIDATE,
        db_index=True,
    )

    REQUIRED_FIELDS = ['email']

    def is_candidate(self):
        return self.role == self.ROLE_CANDIDATE

    def is_recruiter(self):
        return self.role == self.ROLE_RECRUITER

    def is_administrator(self):
        return self.role == self.ROLE_ADMIN or self.is_staff or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.role})"
