import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()

class ScraperConfig(BaseModel):
    """Main Configuration for scraper"""

    #Browser Settings
    headless: bool = Field(default=False, description="Run briwser in headless mode")
    viewport_width: int = Field(default=1920, ge=1024, le=3840)
    viewport_height: int = Field(default=1080, ge=768, le=2160)

    # Timing Settings (in secs)
    min_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    max_delay: float = Field(default=3.0, ge=0.5, le=15.0)
    page_load_timeout: int = Field(default=30000, ge=5000, le=60000)

    # Scraping Settings
    max_scrolls: int = Field(default=5, ge=1, le=20)
    max_posts_per_scrape: int = Field(default=10, ge=1, le=100)
    max_comments_per_post: int = Field(default=50, ge=0, le=200)
    max_retries: int = Field(default=3, ge=1, le=10)

    # Rate Limiting
    requests_per_minute: int = Field(default=20, ge=1, le=60)
    requests_per_hour: int = Field(default=200, ge=10, le=1000)

    # Storage Settings
    download_dir: str = Field(default="./linkedin_downloads", description="Download directory for scraped data")
    download_images: bool = Field(default=True, description="Download images after scraping")
    download_video: bool = Field(default=False, description="Download video after scraping")
    max_image_size_mb: int = Field(default=10, ge=1, le=50)

    # Database Settings
    use_database: bool = Field(default=True, description="Use sqlite database")
    db_path: str = Field(default="./linkedin_data.db", description="Path to sqlite database")

    # Caching
    use_cache: bool = Field(default=True)
    cache_expiry_hours: int = Field(default=24, ge=1, le=168)

    # Security
    login_email: Optional[str] = Field(default=None, env="LINKEDIN_EMAIL")
    login_password: Optional[str] = Field(default=None, env="LINKEDIN_PASSWORD")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="scraper.log")

    @validator('download_dir')
    def create_download_dir(cls, v):
        Path(v).mkdir(exist_ok=True, parents=True)
        return v

    @validator('login_email', 'login_password')
    def check_credentials(cls, v):
        if v is None:
            return os.getenv('LINKEDIN_EMAIL') if cls.__name__ == 'login_email' else os.getenv('LINKEDIN_PASSWORD')
        return v


    class URLConfig:
        """LinkedIn URL patterns"""
        BASE_URL = "https://www.linkedin.com/"
        LOGIN_URL = f"{BASE_URL}/login"
        FEED_URL = f"{BASE_URL}/feed"
        SEARCH_URL = f"{BASE_URL}/search/results"

        @staticmethod
        def is_valid_linkedin_url(url: str) -> bool:
            """Check if url is valid LinkedIn URL"""
            return url.startswith(URLConfig.BASE_URL)

        @staticmethod
        def normalize_profile_url(url: str) -> str:
            """Normalize LinkedIn profile URL"""
            if '?' in url:
                url = url.split('?')[0]
            return url.rstrip('/')

    class SelectorConfig:
        """CSS selectors used in scraping"""

        # Login selectors
        LOGIN_EMAIL = "#username"
        LOGIN_PASSWORD = "#password"
        LOGIN_SUBMIT = 'button[type="submit"]'

        # Profile selectors
        PROFILE_NAME = "h1.text-heading-xlarge"
        PROFILE_HEADLINE = ".text-body-medium.break-words"
        PROFILE_LOCATION = ".text-body-small.inline.t-black--light.break-words"
        PROFILE_PICTURE = ".pv-top-card-profile-picture__image"
        PROFILE_ABOUT = "#about"
        PROFILE_EXPERIENCE = "#experience"
        PROFILE_EDUCATION = "#education"
        PROFILE_SKILLS = "#skills"

        # Post selectors
        POST_CONTAINER = ".feed-shared-update-v2"
        POST_AUTHOR = ".update-components-actor__name"
        POST_CONTENT = ".feed-shared-update-v2__description"
        POST_TIMESTAMP = ".update-components-actor__sub-description"
        POST_REACTIONS = ".social-details-social-counts__reactions-count"
        POST_COMMENTS = ".social-details-social-counts__comments"
        POST_SHARES = ".social-details-social-counts__reposts"

        # Comment selectors
        COMMENT_ITEM = ".comments-comment-item"
        COMMENT_AUTHOR = ".comments-post-meta__name-text"
        COMMENT_TEXT = ".comments-comment-item__main-content"
        COMMENT_TIMESTAMP = ".comments-comment-item__timestamp"

        # Company selectors
        COMPANY_NAME = "h1.org-top-card-summary__title"
        COMPANY_LOGO = ".org-top-card-primary-content__logo"
        COMPANY_TAGLINE = ".org-top-card-summary__tagline"
        COMPANY_DETAILS = ".org-page-details__definition-text"

    # Global config instance
    config = ScraperConfig()

    # Error messages
    class ErrorMessages:
        LOGIN_FAILED = "Failed to login to LinkedIn. Please check credentials."
        NETWORK_ERROR = "Network error occurred. Retrying..."
        ELEMENT_NOT_FOUND = "Element not found on page."
        TIMEOUT_ERROR = "Page load timeout exceeded."
        RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Waiting..."
        CAPTCHA_DETECTED = "CAPTCHA detected. Manual intervention required."
        SESSION_EXPIRED = "Session expired. Re-authentication required."

    # Success messages
    class SuccessMessages:
        LOGIN_SUCCESS = "✓ Login successful!"
        SCRAPE_COMPLETE = "✓ Scraping completed successfully!"
        DATA_SAVED = "✓ Data saved to {}"
        BROWSER_INITIALIZED = "✓ Browser initialized with anti-detection measures"
