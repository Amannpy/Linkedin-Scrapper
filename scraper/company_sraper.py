"""LinkedIn company page scraper"""
import logging
from typing import Dict, List
from datetime import datetime
from playwright.async_api import Page

from config.settings import config, SelectorConfig
from utils.human_behavior import HumanBehavior
from utils.data_extractor import DataExtractor
from middleware.error_handler import handle_errors
from middleware.rate_limiter import rate_limited

logger = logging.getLogger(__name__)


class CompanyScraper:
    """Scrape LinkedIn company pages"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.behavior = human_behavior
        self.extractor = DataExtractor(page)

    @rate_limited(weight=2)
    @handle_errors("Scrape Company", raise_on_error=False, default_return={})
    async def scrape_company(self, company_url: str) -> Dict:
        """
        Scrape complete company page data

        Args:
            company_url: LinkedIn company page URL

        Returns:
            Dict: Company data
        """
        logger.info(f"Scraping company: {company_url}")

        # Navigate to company page
        await self.page.goto(company_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        # Scroll to load content
        await self.behavior.scroll_behavior(scrolls=3, scroll_type='natural')

        company_data = {
            'url': company_url,
            'scraped_at': datetime.now().isoformat(),
        }

        # Extract basic info
        company_data.update(await self._extract_basic_info())

        # Extract about section
        company_data['about'] = await self._extract_about()

        # Extract company details
        company_data['details'] = await self._extract_details()

        # Extract recent posts
        company_data['recent_posts'] = await self._extract_recent_posts()

        logger.info(f"✓ Company scraped: {company_data.get('name', 'Unknown')}")
        return company_data

    async def _extract_basic_info(self) -> Dict:
        """Extract basic company information"""
        info = {}

        # Company name
        try:
            name_elem = self.page.locator(SelectorConfig.COMPANY_NAME).first
            info['name'] = await self.extractor.safe_extract_text(name_elem)
        except:
            info['name'] = None

        # Tagline
        try:
            tagline_elem = self.page.locator(SelectorConfig.COMPANY_TAGLINE).first
            info['tagline'] = await self.extractor.safe_extract_text(tagline_elem)
        except:
            info['tagline'] = None

        # Logo
        try:
            logo_elem = self.page.locator(SelectorConfig.COMPANY_LOGO).first
            logo_url = await logo_elem.get_attribute('src')
            info['logo'] = logo_url
        except:
            info['logo'] = None

        # Industry
        try:
            industry_elem = self.page.locator('.org-top-card-summary-info-list__info-item')
            info['industry'] = await self.extractor.safe_extract_text(industry_elem)
        except:
            info['industry'] = None

        # Followers count
        try:
            followers_elem = self.page.locator('.org-top-card-secondary-content__follower-count')
            info['followers'] = await self.extractor.safe_extract_text(followers_elem)
        except:
            info['followers'] = None

        return info

    async def _extract_about(self) -> str:
        """Extract about section"""
        try:
            about_section = self.page.locator('.org-page-details__definition-text').first
            return await self.extractor.safe_extract_text(about_section)
        except:
            return None

    async def _extract_details(self) -> Dict:
        """Extract company details"""
        details = {}

        try:
            detail_items = await self.page.locator('.org-page-details__definition-text').all()

            labels = ['Website', 'Industry', 'Company size', 'Headquarters',
                      'Type', 'Founded', 'Specialties']

            for i, item in enumerate(detail_items[:len(labels)]):
                text = await self.extractor.safe_extract_text(item)
                if text and i < len(labels):
                    details[labels[i].lower().replace(' ', '_')] = text

        except Exception as e:
            logger.warning(f"Error extracting company details: {e}")

        return details

    async def _extract_recent_posts(self, max_posts: int = 5) -> List[Dict]:
        """Extract recent posts from company page"""
        posts = []

        try:
            # Scroll to posts section
            await self.behavior.scroll_behavior(scrolls=2)

            post_elements = await self.page.locator('.feed-shared-update-v2').all()

            for post_elem in post_elements[:max_posts]:
                post_data = {}

                try:
                    # Content
                    content_elem = post_elem.locator('.feed-shared-update-v2__description')
                    post_data['content'] = await self.extractor.safe_extract_text(content_elem)

                    # Timestamp
                    time_elem = post_elem.locator('.update-components-actor__sub-description')
                    post_data['timestamp'] = await self.extractor.safe_extract_text(time_elem)

                    # Reactions
                    reactions_elem = post_elem.locator('.social-details-social-counts__reactions-count')
                    post_data['reactions'] = await self.extractor.safe_extract_text(reactions_elem)

                    posts.append(post_data)

                except:
                    continue

        except Exception as e:
            logger.warning(f"Error extracting recent posts: {e}")

        return posts