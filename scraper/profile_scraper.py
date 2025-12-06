"""
LinkedIn profile scraper
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import Page, Locator

from config.settings import config, SelectorConfig
from utils.human_behavior import HumanBehavior
from utils.data_extractor import DataExtractor
from middleware.error_handler import handle_errors, DataExtractionException
from middleware.rate_limiter import rate_limited

logger = logging.getLogger(__name__)


class ProfileScraper:
    """Scrape LinkedIn profile data"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.behavior = human_behavior
        self.extractor = DataExtractor(page)

    @rate_limited(weight=2)
    @handle_errors("Scrape Profile", raise_on_error=False, default_return={})
    async def scrape_profile(self, profile_url: str) -> Dict:
        """
        Scrape complete profile data

        Args:
            profile_url: LinkedIn profile URL

        Returns:
            Dict: Profile data
        """
        logger.info(f"Scraping profile: {profile_url}")

        # Navigate to profile
        await self.page.goto(profile_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        # Scroll to load all sections
        await self.behavior.scroll_behavior(scrolls=3, scroll_type='natural')

        profile_data = {
            'url': profile_url,
            'scraped_at': datetime.now().isoformat(),
        }

        # Extract basic info
        profile_data.update(await self._extract_basic_info())

        # Extract about section
        profile_data['about'] = await self._extract_about()

        # Extract experience
        profile_data['experience'] = await self._extract_experience()

        # Extract education
        profile_data['education'] = await self._extract_education()

        # Extract skills
        profile_data['skills'] = await self._extract_skills()

        # Extract licenses & certifications
        profile_data['certifications'] = await self._extract_certifications()

        # Extract volunteer experience
        profile_data['volunteer'] = await self._extract_volunteer()

        # Extract recommendations
        profile_data['recommendations_count'] = await self._extract_recommendations_count()

        logger.info(f"✓ Profile scraped: {profile_data.get('name', 'Unknown')}")
        return profile_data

    async def _extract_basic_info(self) -> Dict:
        """Extract basic profile information"""
        info = {}

        # Name
        try:
            name_elem = self.page.locator(SelectorConfig.PROFILE_NAME).first
            info['name'] = await self.extractor.safe_extract_text(name_elem)
        except:
            info['name'] = None

        # Headline
        try:
            headline_elem = self.page.locator(SelectorConfig.PROFILE_HEADLINE).first
            info['headline'] = await self.extractor.safe_extract_text(headline_elem)
        except:
            info['headline'] = None

        # Location
        try:
            location_elem = self.page.locator(SelectorConfig.PROFILE_LOCATION).first
            info['location'] = await self.extractor.safe_extract_text(location_elem)
        except:
            info['location'] = None

        # Profile picture
        try:
            pic_elem = self.page.locator(SelectorConfig.PROFILE_PICTURE).first
            pic_url = await pic_elem.get_attribute('src')
            info['profile_picture'] = pic_url
        except:
            info['profile_picture'] = None

        # Connections count
        try:
            connections_elem = self.page.locator('.pv-top-card--list-bullet li').first
            connections_text = await self.extractor.safe_extract_text(connections_elem)
            info['connections'] = connections_text
        except:
            info['connections'] = None

        return info

    async def _extract_about(self) -> Optional[str]:
        """Extract about section"""
        try:
            about_section = self.page.locator('#about').locator('..').locator('..')
            await about_section.scroll_into_view_if_needed()
            await self.behavior.random_delay(0.5, 1.0)

            # Click "see more" if present
            see_more = about_section.locator('button:has-text("more")')
            if await see_more.count() > 0:
                await see_more.first.click()
                await self.behavior.random_delay(0.5, 1.0)

            about_text = await about_section.locator('.inline-show-more-text').inner_text()
            return about_text.strip()
        except:
            return None

    async def _extract_experience(self) -> List[Dict]:
        """Extract work experience"""
        experiences = []

        try:
            exp_section = self.page.locator('#experience').locator('..').locator('..')
            await exp_section.scroll_into_view_if_needed()
            await self.behavior.random_delay(0.5, 1.0)

            # Click "Show all experiences" if available
            show_all = exp_section.locator('button:has-text("Show all")').first
            if await show_all.count() > 0:
                await show_all.click()
                await self.behavior.random_delay(1, 2)

            # Get experience items
            exp_items = await exp_section.locator('li.artdeco-list__item').all()

            for item in exp_items:
                exp_data = {}

                try:
                    # Title
                    title_elem = item.locator('.mr1.t-bold')
                    exp_data['title'] = await self.extractor.safe_extract_text(title_elem)

                    # Company
                    company_elem = item.locator('.t-14.t-normal')
                    exp_data['company'] = await self.extractor.safe_extract_text(company_elem)

                    # Duration
                    duration_elem = item.locator('.t-14.t-normal.t-black--light')
                    exp_data['duration'] = await self.extractor.safe_extract_text(duration_elem)

                    # Location
                    location_elem = item.locator('.t-14.t-normal.t-black--light').nth(1)
                    exp_data['location'] = await self.extractor.safe_extract_text(location_elem)

                    # Description
                    desc_elem = item.locator('.inline-show-more-text')
                    if await desc_elem.count() > 0:
                        exp_data['description'] = await self.extractor.safe_extract_text(desc_elem)

                    experiences.append(exp_data)

                except Exception as e:
                    logger.debug(f"Error extracting experience item: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error extracting experiences: {e}")

        return experiences

    async def _extract_education(self) -> List[Dict]:
        """Extract education history"""
        education = []

        try:
            edu_section = self.page.locator('#education').locator('..').locator('..')
            await edu_section.scroll_into_view_if_needed()
            await self.behavior.random_delay(0.5, 1.0)

            edu_items = await edu_section.locator('li.artdeco-list__item').all()

            for item in edu_items:
                edu_data = {}

                try:
                    # School name
                    school_elem = item.locator('.mr1.t-bold')
                    edu_data['school'] = await self.extractor.safe_extract_text(school_elem)

                    # Degree
                    degree_elem = item.locator('.t-14.t-normal')
                    edu_data['degree'] = await self.extractor.safe_extract_text(degree_elem)

                    # Duration
                    duration_elem = item.locator('.t-14.t-normal.t-black--light')
                    edu_data['duration'] = await self.extractor.safe_extract_text(duration_elem)

                    education.append(edu_data)

                except Exception as e:
                    logger.debug(f"Error extracting education item: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error extracting education: {e}")

        return education

    async def _extract_skills(self) -> List[str]:
        """Extract skills"""
        skills = []

        try:
            skills_section = self.page.locator('#skills').locator('..').locator('..')
            await skills_section.scroll_into_view_if_needed()
            await self.behavior.random_delay(0.5, 1.0)

            # Click "Show all skills" if available
            show_all = skills_section.locator('button:has-text("Show all")').first
            if await show_all.count() > 0:
                await show_all.click()
                await self.behavior.random_delay(1, 2)

            skill_items = await skills_section.locator('.artdeco-list__item').all()

            for item in skill_items[:50]:  # Limit to 50 skills
                try:
                    skill_text = await self.extractor.safe_extract_text(item)
                    if skill_text:
                        # Extract just the skill name (before endorsements count)
                        skill_name = skill_text.split('\n')[0].strip()
                        skills.append(skill_name)
                except:
                    continue

        except Exception as e:
            logger.warning(f"Error extracting skills: {e}")

        return skills

    async def _extract_certifications(self) -> List[Dict]:
        """Extract licenses & certifications"""
        certs = []

        try:
            certs_section = self.page.locator('section:has(#licenses_and_certifications)')
            if await certs_section.count() > 0:
                await certs_section.scroll_into_view_if_needed()
                await self.behavior.random_delay(0.5, 1.0)

                cert_items = await certs_section.locator('li.artdeco-list__item').all()

                for item in cert_items:
                    cert_data = {}

                    try:
                        # Certification name
                        name_elem = item.locator('.mr1.t-bold')
                        cert_data['name'] = await self.extractor.safe_extract_text(name_elem)

                        # Issuing organization
                        org_elem = item.locator('.t-14.t-normal')
                        cert_data['organization'] = await self.extractor.safe_extract_text(org_elem)

                        # Date
                        date_elem = item.locator('.t-14.t-normal.t-black--light')
                        cert_data['date'] = await self.extractor.safe_extract_text(date_elem)

                        certs.append(cert_data)

                    except:
                        continue

        except Exception as e:
            logger.warning(f"Error extracting certifications: {e}")

        return certs

    async def _extract_volunteer(self) -> List[Dict]:
        """Extract volunteer experience"""
        volunteer = []

        try:
            volunteer_section = self.page.locator('section:has(#volunteering_experience)')
            if await volunteer_section.count() > 0:
                await volunteer_section.scroll_into_view_if_needed()
                await self.behavior.random_delay(0.5, 1.0)

                vol_items = await volunteer_section.locator('li.artdeco-list__item').all()

                for item in vol_items:
                    vol_data = {}

                    try:
                        # Role
                        role_elem = item.locator('.mr1.t-bold')
                        vol_data['role'] = await self.extractor.safe_extract_text(role_elem)

                        # Organization
                        org_elem = item.locator('.t-14.t-normal')
                        vol_data['organization'] = await self.extractor.safe_extract_text(org_elem)

                        volunteer.append(vol_data)

                    except:
                        continue

        except Exception as e:
            logger.warning(f"Error extracting volunteer experience: {e}")

        return volunteer

    async def _extract_recommendations_count(self) -> int:
        """Extract number of recommendations"""
        try:
            rec_section = self.page.locator('section:has(#recommendations)')
            if await rec_section.count() > 0:
                rec_text = await self.extractor.safe_extract_text(rec_section)
                # Try to extract number from text
                import re
                numbers = re.findall(r'\d+', rec_text)
                if numbers:
                    return int(numbers[0])
        except:
            pass

        return 0

    @rate_limited(weight=1)
    async def scrape_profile_connections(self, profile_url: str, max_connections: int = 100) -> List[Dict]:
        """
        Scrape profile connections (requires appropriate access)

        Args:
            profile_url: LinkedIn profile URL
            max_connections: Maximum number of connections to scrape

        Returns:
            List[Dict]: Connection data
        """
        # Note: This requires being connected to the person
        # Implementation would navigate to connections page and extract
        logger.warning("Connection scraping requires network access and may be limited by LinkedIn")
        return []