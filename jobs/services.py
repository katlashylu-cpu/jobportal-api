import logging

from django.conf import settings
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from .models import Application

logger = logging.getLogger(__name__)

# PRD Section 9: Application Status Workflow
# applied -> shortlisted -> hired
# applied -> rejected
# shortlisted -> rejected
# Terminal states: hired, rejected.
VALID_STATUS_TRANSITIONS = {
    Application.STATUS_APPLIED: {
        Application.STATUS_SHORTLISTED,
        Application.STATUS_REJECTED,
    },
    Application.STATUS_SHORTLISTED: {
        Application.STATUS_HIRED,
        Application.STATUS_REJECTED,
    },
    Application.STATUS_HIRED: set(),     # Terminal
    Application.STATUS_REJECTED: set(),  # Terminal
}


def transition_application_status(application: Application, new_status: str) -> Application:
    """
    Validates and executes an application status transition according to the PRD state machine.
    Sends an email notification to the candidate upon successful transition.
    """
    current_status = application.status

    if current_status == new_status:
        return application

    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_transitions:
        raise ValidationError(
            f"Cannot transition application status from '{current_status}' to '{new_status}'. "
            f"Allowed transitions from '{current_status}': {list(allowed_transitions) or 'None (terminal state)'}."
        )

    old_status = application.status
    application.status = new_status
    application.save(update_fields=['status', 'updated_at'])

    send_status_update_notification(application, old_status, new_status)
    return application


def send_status_update_notification(application: Application, old_status: str, new_status: str):
    """
    Sends email notification to the candidate regarding status updates (FR-18).
    """
    candidate_email = application.candidate.email
    if not candidate_email:
        return

    job_title = application.job.title
    company_name = application.job.company.name
    subject = f"Application Status Update: {job_title} at {company_name}"
    message = (
        f"Hello {application.candidate.username},\n\n"
        f"Your application for the position '{job_title}' at '{company_name}' has been updated.\n"
        f"Previous status: {old_status.capitalize()}\n"
        f"New status: {new_status.capitalize()}\n\n"
        f"You can track your application anytime in your candidate portal.\n\n"
        f"Best regards,\n"
        f"The {company_name} Hiring Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate_email],
            fail_silently=False,
        )
        logger.info(
            f"Dispatched status update email to {candidate_email} for Application #{application.id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to dispatch status update email for Application #{application.id}: {e}"
        )
