"""LinkedIn search scraper"""
import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode
from playwright.async_api import Page

from config.settings import config, URLConfig
from utils.human_behavior import HumanBehavior, ScrollManager
from utils.data_extractor import DataExtractor
from middleware.error_handler import handle_errors
from middleware.rate_limiter import rate_limited

logger = logging.getLogger(__name__)


class SearchScraper:
    """Scrape LinkedIn search results"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.behavior = human_behavior
        self.scroll_manager = ScrollManager(page, human_behavior)
        self.extractor = DataExtractor(page)

    @rate_limited(weight=2)
    @handle_errors("Search", raise_on_error=False, default_return=[])
    async def search_people(
            self,
            keywords: str,
            max_results: int = 20,
            filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for people on LinkedIn

        Args:
            keywords: Search keywords
            max_results: Maximum number of results
            filters: Optional filters (location, company, etc.)

        Returns:
            List[Dict]: Search results
        """
        logger.info(f"Searching people: {keywords}")

        # Build search URL
        search_url = self._build_search_url('people', keywords, filters)

        # Navigate to search
        await self.page.goto(search_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        # Scroll to load results
        await self.scroll_manager.scroll_to_load_all(
            item_selector='.entity-result',
            target_count=max_results,
            max_scrolls=10
        )

        # Extract results
        results = []
        result_elements = await self.page.locator('.entity-result').all()

        for result_elem in result_elements[:max_results]:
            result_data = await self._extract_person_result(result_elem)
            if result_data:
                results.append(result_data)

        logger.info(f"✓ Found {len(results)} results")
        return results

    @rate_limited(weight=2)
    async def search_companies(
            self,
            keywords: str,
            max_results: int = 20,
            filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for companies on LinkedIn

        Args:
            keywords: Search keywords
            max_results: Maximum number of results
            filters: Optional filters

        Returns:
            List[Dict]: Company search results
        """
        logger.info(f"Searching companies: {keywords}")

        search_url = self._build_search_url('companies', keywords, filters)

        await self.page.goto(search_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        await self.scroll_manager.scroll_to_load_all(
            item_selector='.entity-result',
            target_count=max_results,
            max_scrolls=10
        )

        results = []
        result_elements = await self.page.locator('.entity-result').all()

        for result_elem in result_elements[:max_results]:
            result_data = await self._extract_company_result(result_elem)
            if result_data:
                results.append(result_data)

        logger.info(f"✓ Found {len(results)} company results")
        return results

    @rate_limited(weight=1)
    async def search_jobs(
            self,
            keywords: str,
            location: Optional[str] = None,
            max_results: int = 20
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn

        Args:
            keywords: Job search keywords
            location: Job location
            max_results: Maximum number of results

        Returns:
            List[Dict]: Job search results
        """
        logger.info(f"Searching jobs: {keywords}")

        filters = {'location': location} if location else None
        search_url = self._build_search_url('jobs', keywords, filters)

        await self.page.goto(search_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        await self.scroll_manager.scroll_to_load_all(
            item_selector='.job-search-card',
            target_count=max_results,
            max_scrolls=10
        )

        results = []
        result_elements = await self.page.locator('.job-search-card').all()

        for result_elem in result_elements[:max_results]:
            result_data = await self._extract_job_result(result_elem)
            if result_data:
                results.append(result_data)

        logger.info(f"✓ Found {len(results)} job results")
        return results

    def _build_search_url(
            self,
            search_type: str,
            keywords: str,
            filters: Optional[Dict] = None
    ) -> str:
        """Build search URL with parameters"""
        base_url = f"{URLConfig.SEARCH_URL}/{search_type}/"

        params = {'keywords': keywords}

        if filters:
            params.update(filters)

        return f"{base_url}?{urlencode(params)}"

    async def _extract_person_result(self, result_elem) -> Optional[Dict]:
        """Extract person from search result"""
        try:
            data = {}

            # Name
            name_elem = result_elem.locator('.entity-result__title-text a')
            data['name'] = await self.extractor.safe_extract_text(name_elem)

            # Profile URL
            data['url'] = await self.extractor.safe_extract_attribute(name_elem, 'href')
            if data['url']:
                data['url'] = data['url'].split('?')[0]

            # Headline
            headline_elem = result_elem.locator('.entity-result__primary-subtitle')
            data['headline'] = await self.extractor.safe_extract_text(headline_elem)

            # Location
            location_elem = result_elem.locator('.entity-result__secondary-subtitle')
            data['location'] = await self.extractor.safe_extract_text(location_elem)

            return data if data.get('name') else None

        except Exception as e:
            logger.debug(f"Error extracting person result: {e}")
            return None

    async def _extract_company_result(self, result_elem) -> Optional[Dict]:
        """Extract company from search result"""
        try:
            data = {}

            # Company name
            name_elem = result_elem.locator('.entity-result__title-text')
            data['name'] = await self.extractor.safe_extract_text(name_elem)

            # Company URL
            link_elem = result_elem.locator('a.app-aware-link')
            data['url'] = await self.extractor.safe_extract_attribute(link_elem, 'href')
            if data['url']:
                data['url'] = data['url'].split('?')[0]

            # Industry
            industry_elem = result_elem.locator('.entity-result__primary-subtitle')
            data['industry'] = await self.extractor.safe_extract_text(industry_elem)

            # Location
            location_elem = result_elem.locator('.entity-result__secondary-subtitle')
            data['location'] = await self.extractor.safe_extract_text(location_elem)

            return data if data.get('name') else None

        except Exception as e:
            logger.debug(f"Error extracting company result: {e}")
            return None

    async def _extract_job_result(self, result_elem) -> Optional[Dict]:
        """Extract job from search result"""
        try:
            data = {}

            # Job title
            title_elem = result_elem.locator('.base-search-card__title')
            data['title'] = await self.extractor.safe_extract_text(title_elem)

            # Company
            company_elem = result_elem.locator('.base-search-card__subtitle')
            data['company'] = await self.extractor.safe_extract_text(company_elem)

            # Location
            location_elem = result_elem.locator('.job-search-card__location')
            data['location'] = await self.extractor.safe_extract_text(location_elem)

            # Job URL
            link_elem = result_elem.locator('a.base-card__full-link')
            data['url'] = await self.extractor.safe_extract_attribute(link_elem, 'href')

            return data if data.get('title') else None

        except Exception as e:
            logger.debug(f"Error extracting job result: {e}")
            return None
