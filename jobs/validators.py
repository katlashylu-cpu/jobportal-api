from django.core.exceptions import ValidationError

MAX_RESUME_SIZE = 2 * 1024 * 1024  # 2 MB


def validate_resume_file(file):
    """
    Validate that the uploaded resume is a valid PDF and does not exceed 2MB.
    """
    # 1. Check file size
    if file.size > MAX_RESUME_SIZE:
        raise ValidationError(
            f"File size exceeds the 2 MB limit. Current size is {file.size / (1024 * 1024):.2f} MB."
        )

    # 2. Check file extension
    file_name = file.name.lower()
    if not file_name.endswith('.pdf'):
        raise ValidationError("Only PDF files are accepted for resume uploads.")

    # 3. Check magic bytes (%PDF-)
    initial_pos = file.tell()
    try:
        header = file.read(5)
        if not header.startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF file format. The file is corrupted or not a true PDF.")
    finally:
        file.seek(initial_pos)
