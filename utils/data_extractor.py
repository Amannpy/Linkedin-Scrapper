"""Generic data extraction utilities"""
import logging
import re
from typing import Optional, List, Dict
from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)


class DataExtractor:
    """Generic data extraction utilities"""

    def __init__(self, page: Page):
        self.page = page

    async def safe_extract_text(self, locator: Locator, timeout: int = 5000) -> Optional[str]:
        """Safely extract text from element"""
        try:
            text = await locator.inner_text(timeout=timeout)
            return text.strip() if text else None
        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
            return None

    async def safe_extract_attribute(self, locator: Locator, attribute: str) -> Optional[str]:
        """Safely extract attribute from element"""
        try:
            value = await locator.get_attribute(attribute)
            return value
        except Exception as e:
            logger.debug(f"Attribute extraction failed: {e}")
            return None

    async def extract_all_links(self, locator: Locator) -> List[str]:
        """Extract all links from element"""
        links = []
        try:
            link_elems = await locator.locator('a[href]').all()
            for elem in link_elems:
                href = await self.safe_extract_attribute(elem, 'href')
                if href:
                    links.append(href)
        except Exception as e:
            logger.debug(f"Link extraction failed: {e}")
        return links

    async def extract_all_images(self, locator: Locator) -> List[Dict]:
        """Extract all images from element"""
        images = []
        try:
            img_elems = await locator.locator('img').all()
            for elem in img_elems:
                src = await self.safe_extract_attribute(elem, 'src')
                alt = await self.safe_extract_attribute(elem, 'alt')
                if src:
                    images.append({'src': src, 'alt': alt or ''})
        except Exception as e:
            logger.debug(f"Image extraction failed: {e}")
        return images

    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """Extract numbers from text"""
        return [int(n) for n in re.findall(r'\d+', text)]

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
