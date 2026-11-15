"""
Development settings for Job Portal REST API.
"""
from .base import *  # noqa: F403

DEBUG = True

# Disable throttling during development/testing if needed or keep standard
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
