"""
LinkedIn post and feed scraper
"""
import logging
from typing import Dict, List
from datetime import datetime
from playwright.async_api import Page

from config.settings import config, URLConfig, SelectorConfig
from utils.human_behavior import HumanBehavior, ScrollManager
from utils.data_extractor import DataExtractor
from middleware.error_handler import handle_errors
from middleware.rate_limiter import rate_limited

logger = logging.getLogger(__name__)


class PostScraper:
    """Scrape LinkedIn posts and feed"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.behavior = human_behavior
        self.scroll_manager = ScrollManager(page, human_behavior)
        self.extractor = DataExtractor(page)

    @rate_limited(weight=3)
    @handle_errors("Scrape Feed", raise_on_error=False, default_return=[])
    async def scrape_feed(self, num_posts: int = 10) -> List[Dict]:
        """
        Scrape posts from LinkedIn feed

        Args:
            num_posts: Number of posts to scrape

        Returns:
            List[Dict]: Post data
        """
        logger.info(f"Scraping {num_posts} posts from feed")

        # Navigate to feed
        await self.page.goto(URLConfig.FEED_URL, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 4)

        # Scroll to load posts
        await self.scroll_manager.scroll_to_load_all(
            item_selector=SelectorConfig.POST_CONTAINER,
            target_count=num_posts,
            max_scrolls=20
        )

        # Extract posts
        posts_data = []
        post_elements = await self.page.locator(SelectorConfig.POST_CONTAINER).all()

        for i, post_elem in enumerate(post_elements[:num_posts], 1):
            logger.info(f"Scraping post {i}/{num_posts}")

            try:
                await post_elem.scroll_into_view_if_needed()
                await self.behavior.random_delay(0.5, 1.5)

                post_data = await self._extract_post_data(post_elem)
                posts_data.append(post_data)

                # Simulate reading
                if i % 3 == 0:
                    await self.behavior.reading_behavior(min_time=1, max_time=2)

            except Exception as e:
                logger.warning(f"Error scraping post {i}: {e}")
                continue

        logger.info(f"✓ Scraped {len(posts_data)} posts")
        return posts_data

    async def _extract_post_data(self, post_elem) -> Dict:
        """Extract data from a single post"""
        post_data = {
            'scraped_at': datetime.now().isoformat()
        }

        # Author
        try:
            author_elem = post_elem.locator(SelectorConfig.POST_AUTHOR)
            post_data['author'] = await self.extractor.safe_extract_text(author_elem)
        except:
            post_data['author'] = None

        # Author profile URL
        try:
            author_link = await post_elem.locator('.update-components-actor__meta-link').get_attribute('href')
            post_data['author_url'] = author_link.split('?')[0] if author_link else None
        except:
            post_data['author_url'] = None

        # Post content
        try:
            content_elem = post_elem.locator(SelectorConfig.POST_CONTENT)

            # Click "see more" if present
            see_more = content_elem.locator('button:has-text("more")')
            if await see_more.count() > 0:
                await see_more.click()
                await self.behavior.random_delay(0.3, 0.6)

            post_data['content'] = await self.extractor.safe_extract_text(content_elem)
        except:
            post_data['content'] = None

        # Hashtags
        try:
            hashtags = []
            hashtag_elems = await post_elem.locator('a[href*="/hashtag/"]').all()
            for tag_elem in hashtag_elems:
                tag_text = await self.extractor.safe_extract_text(tag_elem)
                if tag_text:
                    hashtags.append(tag_text)
            post_data['hashtags'] = hashtags
        except:
            post_data['hashtags'] = []

        # Timestamp
        try:
            time_elem = post_elem.locator(SelectorConfig.POST_TIMESTAMP)
            post_data['timestamp'] = await self.extractor.safe_extract_text(time_elem)
        except:
            post_data['timestamp'] = None

        # Engagement metrics
        post_data['metrics'] = await self._extract_metrics(post_elem)

        # Media
        post_data['media'] = await self._extract_media(post_elem)

        # Comments (if requested)
        post_data['comments'] = await self._extract_comments(post_elem, max_comments=5)

        return post_data

    async def _extract_metrics(self, post_elem) -> Dict:
        """Extract engagement metrics"""
        metrics = {}

        # Reactions
        try:
            reactions_elem = post_elem.locator(SelectorConfig.POST_REACTIONS)
            reactions_text = await self.extractor.safe_extract_text(reactions_elem)
            metrics['reactions'] = reactions_text or '0'
        except:
            metrics['reactions'] = '0'

        # Comments
        try:
            comments_elem = post_elem.locator(SelectorConfig.POST_COMMENTS)
            comments_text = await self.extractor.safe_extract_text(comments_elem)
            metrics['comments'] = comments_text or '0'
        except:
            metrics['comments'] = '0'

        # Shares/Reposts
        try:
            shares_elem = post_elem.locator(SelectorConfig.POST_SHARES)
            shares_text = await self.extractor.safe_extract_text(shares_elem)
            metrics['shares'] = shares_text or '0'
        except:
            metrics['shares'] = '0'

        return metrics

    async def _extract_media(self, post_elem) -> Dict:
        """Extract media from post"""
        media = {
            'images': [],
            'videos': [],
            'documents': [],
            'polls': []
        }

        # Images
        try:
            img_elems = await post_elem.locator('img[src*="media"]').all()
            for img_elem in img_elems:
                img_src = await img_elem.get_attribute('src')
                if img_src:
                    media['images'].append(img_src)
        except:
            pass

        # Videos
        try:
            video_count = await post_elem.locator('video').count()
            media['has_video'] = video_count > 0
        except:
            media['has_video'] = False

        # Documents
        try:
            doc_count = await post_elem.locator('.document-card').count()
            media['has_document'] = doc_count > 0
        except:
            media['has_document'] = False

        # Polls
        try:
            poll_count = await post_elem.locator('.feed-shared-poll').count()
            media['has_poll'] = poll_count > 0
        except:
            media['has_poll'] = False

        return media

    async def _extract_comments(self, post_elem, max_comments: int = 5) -> List[Dict]:
        """Extract comments from post"""
        comments = []

        try:
            # Click to show comments
            comments_btn = post_elem.locator('button.social-details-social-counts__comments')
            if await comments_btn.count() > 0:
                await comments_btn.click()
                await self.behavior.random_delay(1, 2)

                # Get comment elements
                comment_elems = await post_elem.locator('.comments-comment-item').all()

                for comment_elem in comment_elems[:max_comments]:
                    comment_data = {}

                    try:
                        # Commenter name
                        name_elem = comment_elem.locator('.comments-post-meta__name-text')
                        comment_data['commenter'] = await self.extractor.safe_extract_text(name_elem)

                        # Comment text
                        text_elem = comment_elem.locator('.comments-comment-item__main-content')
                        comment_data['text'] = await self.extractor.safe_extract_text(text_elem)

                        # Timestamp
                        time_elem = comment_elem.locator('.comments-comment-item__timestamp')
                        comment_data['timestamp'] = await self.extractor.safe_extract_text(time_elem)

                        comments.append(comment_data)
                    except:
                        continue

        except Exception as e:
            logger.debug(f"Error extracting comments: {e}")

        return comments

    @rate_limited(weight=2)
    async def scrape_post_by_url(self, post_url: str) -> Dict:
        """
        Scrape a specific post by URL

        Args:
            post_url: LinkedIn post URL

        Returns:
            Dict: Post data
        """
        logger.info(f"Scraping post: {post_url}")

        await self.page.goto(post_url, wait_until='domcontentloaded')
        await self.behavior.random_delay(2, 3)

        post_elem = self.page.locator(SelectorConfig.POST_CONTAINER).first
        return await self._extract_post_data(post_elem)