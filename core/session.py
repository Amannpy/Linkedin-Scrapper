"""
Session management and authentication for LinkedIn
"""
import asyncio
import logging
from typing import Optional
from pathlib import Path
from playwright.async_api import Page

from config.settings import config, URLConfig, SelectorConfig, SuccessMessages
from utils.human_behavior import HumanBehavior
from middleware.error_handler import (
    handle_errors,
    LoginException,
    CaptchaException,
    AuthenticationException
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage LinkedIn login sessions"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.behavior = human_behavior
        self.is_logged_in = False
        self.session_file = Path(config.download_dir) / "linkedin_session.json"
        self.cookies_file = Path(config.download_dir) / "linkedin_cookies.json"

    @handle_errors("Login", raise_on_error=True)
    async def login(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Login to LinkedIn with anti-detection measures

        Args:
            email: LinkedIn email
            password: LinkedIn password

        Raises:
            LoginException: If login fails
            CaptchaException: If CAPTCHA is detected
        """
        email = email or config.login_email
        password = password or config.login_password

        if not email or not password:
            raise LoginException("Email and password are required")

        logger.info("Starting LinkedIn login...")

        # Navigate to login page
        await self.page.goto(URLConfig.LOGIN_URL, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        # Check for honeypots
        await self._detect_honeypots()

        # Simulate human behavior before login
        await self.behavior.mouse_movement(num_movements=3)

        # Enter email
        logger.info("Entering email...")
        await self.behavior.human_typing(
            SelectorConfig.LOGIN_EMAIL,
            email,
            mistakes=True
        )
        await self.behavior.random_delay(1, 2)

        # Enter password (more careful, no mistakes)
        logger.info("Entering password...")
        await self.behavior.human_typing(
            SelectorConfig.LOGIN_PASSWORD,
            password,
            mistakes=False
        )
        await self.behavior.random_delay(1, 2)

        # Move mouse before submitting
        await self.behavior.mouse_movement(num_movements=2)

        # Submit login
        await self.behavior.click_with_behavior(
            SelectorConfig.LOGIN_SUBMIT,
            wait_before=True,
            wait_after=True
        )

        # Wait for navigation
        try:
            await self.page.wait_for_load_state('networkidle', timeout=30000)
        except Exception as e:
            logger.warning(f"Navigation timeout: {e}")

        await self.behavior.random_delay(3, 5)

        # Verify login
        await self._verify_login()

        self.is_logged_in = True
        logger.info(SuccessMessages.LOGIN_SUCCESS)

        # Save session
        await self.save_session()

    async def _detect_honeypots(self):
        """Detect honeypot fields on login page"""
        honeypot_selectors = [
            'input[style*="display:none"]',
            'input[style*="visibility:hidden"]',
            'input[type="hidden"][name*="bot"]',
            'input[aria-hidden="true"]',
            '.hidden-field',
        ]

        for selector in honeypot_selectors:
            try:
                count = await self.page.locator(selector).count()
                if count > 0:
                    logger.warning(f"⚠ Potential honeypot detected: {selector}")
            except Exception:
                pass

    async def _verify_login(self):
        """Verify login was successful"""
        current_url = self.page.url

        # Check for verification checkpoint
        if 'checkpoint' in current_url or 'challenge' in current_url:
            await self._handle_verification()
            current_url = self.page.url

        # Check for CAPTCHA
        if 'captcha' in current_url.lower():
            raise CaptchaException(
                "CAPTCHA detected. Please solve manually and run again."
            )

        # Verify we're on a logged-in page
        logged_in_indicators = ['feed', 'mynetwork', 'jobs', 'messaging', 'notifications']

        if not any(indicator in current_url for indicator in logged_in_indicators):
            # Try to detect if we're actually logged in by checking for profile elements
            try:
                # Check for "Me" button or profile image
                me_button = self.page.locator('[data-control-name="identity_welcome_message"]')
                if await me_button.count() > 0:
                    logger.info("Login verified via profile element")
                    return
            except Exception:
                pass

            raise LoginException(
                f"Login verification failed. Current URL: {current_url}"
            )

        logger.info("Login verified successfully")

    async def _handle_verification(self):
        """Handle verification checkpoint"""
        logger.warning("⚠ Verification checkpoint detected")
        logger.info("Please complete verification manually...")

        # Wait for user to complete verification
        max_wait = 60  # 60 seconds
        waited = 0

        while waited < max_wait:
            await asyncio.sleep(5)
            waited += 5

            current_url = self.page.url
            if not any(x in current_url for x in ['checkpoint', 'challenge']):
                logger.info("✓ Verification completed")
                return

            logger.info(f"Waiting for verification... ({waited}/{max_wait}s)")

        logger.warning("Verification timeout reached")

    async def save_session(self):
        """Save session state to file"""
        try:
            # Get browser context
            context = self.page.context

            # Save storage state (includes cookies, localStorage)
            await context.storage_state(path=str(self.session_file))

            logger.info(f"✓ Session saved to {self.session_file}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def load_session(self) -> bool:
        """
        Load existing session

        Returns:
            bool: True if session loaded successfully
        """
        if not self.session_file.exists():
            logger.info("No saved session found")
            return False

        try:
            # Note: Session loading is handled during browser context creation
            # This method just validates the session
            logger.info(f"Session file found: {self.session_file}")

            # Navigate to feed to check if session is valid
            await self.page.goto(URLConfig.FEED_URL, wait_until='domcontentloaded')
            await self.behavior.random_delay(2, 3)

            current_url = self.page.url

            # Check if we're logged in
            if 'login' in current_url or 'authwall' in current_url:
                logger.warning("Saved session expired")
                return False

            self.is_logged_in = True
            logger.info("✓ Session loaded and verified")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    async def clear_session(self):
        """Clear saved session"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("✓ Session cleared")

            if self.cookies_file.exists():
                self.cookies_file.unlink()

            self.is_logged_in = False

        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

    async def check_session_validity(self) -> bool:
        """
        Check if current session is still valid

        Returns:
            bool: True if session is valid
        """
        try:
            current_url = self.page.url

            # If we're on a login page, session is invalid
            if 'login' in current_url or 'authwall' in current_url:
                self.is_logged_in = False
                return False

            # Try to access feed
            await self.page.goto(URLConfig.FEED_URL, wait_until='domcontentloaded')
            await asyncio.sleep(2)

            current_url = self.page.url

            if 'login' in current_url:
                self.is_logged_in = False
                return False

            self.is_logged_in = True
            return True

        except Exception as e:
            logger.error(f"Session validity check failed: {e}")
            return False

    async def re_authenticate(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Re-authenticate if session expires

        Args:
            email: LinkedIn email
            password: LinkedIn password
        """
        logger.info("Re-authenticating...")

        # Clear old session
        await self.clear_session()

        # Login again
        await self.login(email, password)

    def get_session_path(self) -> Path:
        """Get path to session file"""
        return self.session_file

    @property
    def logged_in(self) -> bool:
        """Check if logged in"""
        return self.is_logged_in