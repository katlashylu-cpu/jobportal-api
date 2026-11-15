"""
Production settings for Job Portal REST API.
"""
from .base import *  # noqa: F403

DEBUG = False

# Enforce secure cookies and headers in production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
