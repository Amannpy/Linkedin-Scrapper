"""Input validation utilities"""
import re
from typing import Optional
from middleware.error_handler import ValidationException


class Validator:
    """Input validation utilities"""

    @staticmethod
    def validate_url(url: str, domain: str = "linkedin.com") -> bool:
        """Validate URL format"""
        if not url:
            return False

        pattern = r'^https?://(?:www\.)?{}'.format(re.escape(domain))
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_profile_url(url: str) -> str:
        """Validate and normalize LinkedIn profile URL"""
        if not url:
            raise ValidationException("Profile URL is required")

        if not Validator.validate_url(url):
            raise ValidationException(f"Invalid LinkedIn URL: {url}")

        # Remove query parameters
        if '?' in url:
            url = url.split('?')[0]

        return url.rstrip('/')

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:255]  # Max filename length