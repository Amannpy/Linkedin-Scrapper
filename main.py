"""
Main orchestrator demonstrating modular LinkedIn scraper usage

This shows how all modules work together in a clean, maintainable way.
"""
import asyncio
import logging
from pathlib import Path

# Import configuration
from config.settings import config, URLConfig, SuccessMessages

# Import core components
from core.browser import BrowserManager

# Import utilities  
from utils.human_behavior import HumanBehavior, ScrollManager

# Import middleware
from middleware.error_handler import (
    error_handler,
    ErrorContext,
    LoginException,
    CaptchaException
)
from middleware.retry_handler import RetryHandler, with_retry

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file) if config.log_file else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInScraperOrchestrator:
    """
    Main orchestrator that coordinates all scraping operations

    This class demonstrates the modular architecture where each component
    has a single responsibility and can be easily maintained or replaced.
    """

    def __init__(self):
        self.browser_manager = None
        self.human_behavior = None
        self.scroll_manager = None
        self.retry_handler = RetryHandler(
            max_attempts=config.max_retries
        )
        self.is_logged_in = False

    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 80)
        logger.info("LinkedIn Scraper - Modular Architecture")
        logger.info("=" * 80)

        # Initialize browser
        self.browser_manager = BrowserManager(headless=config.headless)
        await self.browser_manager.initialize()

        # Initialize behavior simulator
        self.human_behavior = HumanBehavior(self.browser_manager.page)
        self.scroll_manager = ScrollManager(
            self.browser_manager.page,
            self.human_behavior
        )

        logger.info("✓ All components initialized")

    @with_retry(max_attempts=3, operation_name="Login")
    async def login(self, email: str = None, password: str = None):
        """
        Login to LinkedIn with retry logic and error handling

        This demonstrates:
        - Automatic retry on failure
        - Error handling with context
        - Human-like behavior simulation
        """
        email = email or config.login_email
        password = password or config.login_password

        if not email or not password:
            raise LoginException("Email and password required")

        with ErrorContext("LinkedIn Login", suppress=False):
            page = self.browser_manager.page

            # Navigate to login
            logger.info("Navigating to LinkedIn login...")
            await page.goto(URLConfig.LOGIN_URL, wait_until='domcontentloaded')
            await self.human_behavior.random_delay(2, 4)

            # Check for honeypots
            await self._check_honeypots()

            # Simulate mouse movement
            await self.human_behavior.mouse_movement(num_movements=3)

            # Type credentials with human-like behavior
            logger.info("Entering credentials...")
            await self.human_behavior.human_typing(
                '#username',
                email,
                mistakes=True
            )
            await self.human_behavior.random_delay(1, 2)

            await self.human_behavior.human_typing(
                '#password',
                password,
                mistakes=False  # Usually more careful with password
            )
            await self.human_behavior.random_delay(1, 2)

            # Move mouse before clicking submit
            await self.human_behavior.mouse_movement(num_movements=2)

            # Click submit
            await self.human_behavior.click_with_behavior(
                'button[type="submit"]'
            )

            # Wait for navigation
            await page.wait_for_load_state('networkidle', timeout=30000)
            await self.human_behavior.random_delay(3, 5)

            # Check login success
            await self._verify_login()

            logger.info(SuccessMessages.LOGIN_SUCCESS)
            self.is_logged_in = True

    async def _check_honeypots(self):
        """Check for honeypot fields"""
        page = self.browser_manager.page

        honeypot_selectors = [
            'input[style*="display:none"]',
            'input[style*="visibility:hidden"]',
            'input[type="hidden"][name*="bot"]',
        ]

        for selector in honeypot_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                logger.warning(f"⚠ Potential honeypot detected: {selector}")

    async def _verify_login(self):
        """Verify login was successful"""
        page = self.browser_manager.page
        current_url = page.url

        # Check for various login states
        if 'checkpoint' in current_url:
            logger.warning("⚠ Verification checkpoint detected")
            logger.info("Please complete manual verification...")
            # Wait for user to complete verification
            await asyncio.sleep(30)

            # Re-check URL
            current_url = page.url

        if 'challenge' in current_url:
            raise CaptchaException("CAPTCHA detected - manual intervention required")

        # Verify we're on a logged-in page
        if not any(x in current_url for x in ['feed', 'mynetwork', 'jobs', 'messaging']):
            raise LoginException("Login verification failed - unexpected URL")

    async def scrape_feed_posts(self, num_posts: int = 10) -> list:
        """
        Scrape feed posts with all modular components

        This demonstrates:
        - Error handling per operation
        - Human behavior simulation
        - Structured data extraction
        """
        if not self.is_logged_in:
            raise LoginException("Must be logged in to scrape feed")

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Scraping {num_posts} posts from feed")
        logger.info(f"{'=' * 80}\n")

        page = self.browser_manager.page

        # Navigate to feed
        await page.goto(URLConfig.FEED_URL, wait_until='domcontentloaded')
        await self.human_behavior.random_delay(2, 4)

        # Scroll to load posts
        await self.scroll_manager.scroll_to_load_all(
            item_selector='.feed-shared-update-v2',
            target_count=num_posts,
            max_scrolls=20
        )

        # Get posts
        posts_data = []
        post_elements = await page.locator('.feed-shared-update-v2').all()

        for i, post_element in enumerate(post_elements[:num_posts], 1):
            logger.info(f"Processing post {i}/{num_posts}")

            with ErrorContext(f"Scrape post {i}", suppress=True):
                # Scroll post into view
                await post_element.scroll_into_view_if_needed()
                await self.human_behavior.random_delay(0.5, 1.5)

                # Extract post data (simplified for example)
                post_data = await self._extract_post_data(post_element)
                posts_data.append(post_data)

                # Simulate reading
                await self.human_behavior.reading_behavior(min_time=1, max_time=3)

                # Random actions occasionally
                if i % 3 == 0:
                    await self.human_behavior.random_actions(num_actions=2)

        logger.info(f"\n✓ Scraped {len(posts_data)} posts successfully")
        return posts_data

    async def _extract_post_data(self, post_element) -> dict:
        """Extract data from a post element"""
        post_data = {
            'scraped_at': __import__('datetime').datetime.now().isoformat()
        }

        # Extract author
        try:
            author = await post_element.locator('.update-components-actor__name').inner_text()
            post_data['author'] = author.strip()
        except:
            post_data['author'] = None

        # Extract content
        try:
            content_elem = post_element.locator('.feed-shared-update-v2__description')

            # Click "see more" if present
            see_more = content_elem.locator('button:has-text("more")')
            if await see_more.count() > 0:
                await see_more.click()
                await asyncio.sleep(0.5)

            content = await content_elem.inner_text()
            post_data['content'] = content.strip()
        except:
            post_data['content'] = None

        # Extract metrics
        try:
            reactions = await post_element.locator(
                '.social-details-social-counts__reactions-count'
            ).inner_text()
            post_data['reactions'] = reactions.strip()
        except:
            post_data['reactions'] = '0'

        return post_data

    async def save_session(self):
        """Save login session for reuse"""
        session_path = Path(config.download_dir) / 'session.json'
        await self.browser_manager.save_state(str(session_path))
        logger.info(f"✓ Session saved to {session_path}")

    async def load_session(self):
        """Load existing session"""
        session_path = Path(config.download_dir) / 'session.json'

        if session_path.exists():
            await self.browser_manager.load_state(str(session_path))
            self.is_logged_in = True
            logger.info("✓ Session loaded")
            return True

        return False

    async def get_scraper_stats(self) -> dict:
        """Get statistics about scraping session"""
        return {
            'errors': error_handler.get_error_stats(),
            'retries': self.retry_handler.get_retry_stats(),
            'is_logged_in': self.is_logged_in,
        }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("\nCleaning up...")

        if self.browser_manager:
            await self.browser_manager.close()

        # Print final stats
        stats = await self.get_scraper_stats()
        logger.info(f"\nFinal Statistics:")
        logger.info(f"  Total Errors: {stats['errors']['total_errors']}")
        logger.info(f"  Operations with Retries: {stats['retries']['operations_with_retries']}")

        logger.info("\n✓ Cleanup complete")


async def main():
    """
    Example usage of the modular scraper

    This demonstrates a complete scraping workflow using all modules.
    """
    scraper = LinkedInScraperOrchestrator()

    try:
        # Initialize
        await scraper.initialize()

        # Try to load existing session
        session_loaded = await scraper.load_session()

        if not session_loaded:
            # Login with credentials
            await scraper.login(
                email="your_email@example.com",
                password="your_password"
            )

            # Save session for next time
            await scraper.save_session()
        else:
            logger.info("✓ Using saved session")

        # Scrape feed
        posts = await scraper.scrape_feed_posts(num_posts=5)

        # Save data (would use storage modules in full implementation)
        logger.info(f"\n✓ Scraped {len(posts)} posts")

        # Show sample data
        if posts:
            logger.info(f"\nSample post:")
            first_post = posts[0]
            logger.info(f"  Author: {first_post.get('author', 'Unknown')}")
            logger.info(f"  Content: {first_post.get('content', 'No content')[:100]}...")
            logger.info(f"  Reactions: {first_post.get('reactions', '0')}")

        logger.info("\n" + "=" * 80)
        logger.info("✓✓✓ SCRAPING COMPLETED SUCCESSFULLY! ✓✓✓")
        logger.info("=" * 80)

    except CaptchaException as e:
        logger.error(f"\n❌ CAPTCHA detected: {e}")
        logger.info("Please complete CAPTCHA manually and run again")

    except LoginException as e:
        logger.error(f"\n❌ Login failed: {e}")
        logger.info("Please check your credentials")

    except KeyboardInterrupt:
        logger.info("\n\n⚠ Interrupted by user")

    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}", exc_info=True)

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())