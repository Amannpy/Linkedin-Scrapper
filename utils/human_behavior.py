"""
Simulate human-like behavior to avoid detection
"""
import asyncio
import random
import logging
from typing import Optional, List
from playwright.async_api import Page

from config.settings import config

logger = logging.getLogger(__name__)


class HumanBehavior:
    """Simulate human-like interactions"""

    def __init__(self, page: Page):
        self.page = page

    async def random_delay(
            self,
            min_sec: Optional[float] = None,
            max_sec: Optional[float] = None
    ):
        """Human-like random delay"""
        min_sec = min_sec or config.min_delay
        max_sec = max_sec or config.max_delay

        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def smart_delay(self, base_delay: float = 1.0, variance: float = 0.5):
        """
        Smart delay that varies based on time of day and adds randomness
        """
        import datetime

        # Add variance based on time (slower during peak hours)
        current_hour = datetime.datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            time_multiplier = random.uniform(1.2, 1.5)
        else:
            time_multiplier = random.uniform(0.8, 1.2)

        delay = base_delay * time_multiplier
        delay += random.uniform(-variance, variance)
        delay = max(0.1, delay)  # Minimum delay

        await asyncio.sleep(delay)

    async def mouse_movement(
            self,
            num_movements: Optional[int] = None,
            smooth: bool = True
    ):
        """Simulate realistic mouse movements"""
        num_movements = num_movements or random.randint(2, 5)

        viewport = self.page.viewport_size
        max_x = viewport['width']
        max_y = viewport['height']

        current_x = random.randint(100, max_x - 100)
        current_y = random.randint(100, max_y - 100)

        for _ in range(num_movements):
            # Generate target position
            target_x = random.randint(100, max_x - 100)
            target_y = random.randint(100, max_y - 100)

            if smooth:
                # Smooth movement with bezier-like curve
                await self._smooth_move(current_x, current_y, target_x, target_y)
            else:
                # Direct movement
                await self.page.mouse.move(target_x, target_y)

            current_x, current_y = target_x, target_y

            # Random pause
            await asyncio.sleep(random.uniform(0.1, 0.4))

            # Occasionally click (like reading something)
            if random.random() > 0.8:
                await self.page.mouse.click(current_x, current_y)
                await asyncio.sleep(random.uniform(0.2, 0.5))

    async def _smooth_move(self, start_x: int, start_y: int, end_x: int, end_y: int):
        """Move mouse smoothly using quadratic bezier curve"""
        steps = random.randint(10, 20)

        # Control point for bezier curve
        control_x = (start_x + end_x) / 2 + random.randint(-100, 100)
        control_y = (start_y + end_y) / 2 + random.randint(-100, 100)

        for i in range(steps + 1):
            t = i / steps

            # Quadratic bezier formula
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y

            await self.page.mouse.move(int(x), int(y))
            await asyncio.sleep(random.uniform(0.01, 0.03))

    async def human_typing(
            self,
            selector: str,
            text: str,
            clear_first: bool = True,
            mistakes: bool = True
    ):
        """Type like a human with realistic patterns"""
        # Click and focus on element
        await self.page.click(selector)
        await self.random_delay(0.3, 0.7)

        # Clear existing text if needed
        if clear_first:
            await self.page.fill(selector, '')
            await self.random_delay(0.2, 0.4)

        # Type with human-like patterns
        typed_text = ''
        i = 0

        while i < len(text):
            char = text[i]

            # Simulate typing mistakes occasionally
            if mistakes and random.random() < 0.05 and i > 0:
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await self.page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.2))

                # Backspace to correct
                await self.page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Type the correct character
            await self.page.keyboard.type(char)
            typed_text += char

            # Variable typing speed
            if char == ' ':
                # Longer pause after space
                await asyncio.sleep(random.uniform(0.1, 0.3))
            elif char in '.,!?':
                # Pause after punctuation
                await asyncio.sleep(random.uniform(0.2, 0.4))
            else:
                # Normal typing speed with variation
                base_speed = random.uniform(0.05, 0.15)

                # Slower for complex characters
                if char.isupper() or char.isdigit():
                    base_speed *= 1.5

                await asyncio.sleep(base_speed)

            i += 1

            # Occasional longer pause (thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.5, 1.0))

    async def scroll_behavior(
            self,
            scrolls: Optional[int] = None,
            scroll_type: str = 'natural'  # 'natural', 'fast', 'slow'
    ):
        """Scroll with human-like behavior"""
        scrolls = scrolls or config.max_scrolls

        scroll_speeds = {
            'fast': (500, 1000, 0.3, 0.8),
            'natural': (300, 800, 1.0, 3.0),
            'slow': (200, 500, 2.0, 5.0)
        }

        min_dist, max_dist, min_pause, max_pause = scroll_speeds.get(
            scroll_type, scroll_speeds['natural']
        )

        for i in range(scrolls):
            # Random scroll distance
            scroll_distance = random.randint(min_dist, max_dist)

            # Smooth scroll animation
            await self.page.evaluate(f'''
                window.scrollBy({{
                    top: {scroll_distance},
                    behavior: 'smooth'
                }})
            ''')

            # Random pause
            await self.random_delay(min_pause, max_pause)

            # Occasionally scroll up (reading behavior)
            if random.random() > 0.7:
                scroll_up = random.randint(50, 200)
                await self.page.evaluate(f'''
                    window.scrollBy({{
                        top: -{scroll_up},
                        behavior: 'smooth'
                    }})
                ''')
                await self.random_delay(0.5, 1.0)

            # Occasionally hover over elements
            if random.random() > 0.6:
                await self._hover_random_element()

    async def _hover_random_element(self):
        """Hover over a random visible element"""
        try:
            # Get random clickable elements
            elements = await self.page.locator('a, button, [role="button"]').all()

            if elements:
                random_element = random.choice(elements)
                if await random_element.is_visible():
                    await random_element.hover()
                    await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass  # Silently fail if hovering fails

    async def reading_behavior(self, min_time: float = 2.0, max_time: float = 8.0):
        """Simulate reading content"""
        read_time = random.uniform(min_time, max_time)

        # Occasional mouse movements while reading
        intervals = int(read_time / 2)
        for _ in range(intervals):
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # Small mouse movements
            if random.random() > 0.5:
                viewport = self.page.viewport_size
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await self.page.mouse.move(x, y)

    async def click_with_behavior(
            self,
            selector: str,
            wait_before: bool = True,
            wait_after: bool = True
    ):
        """Click element with human-like behavior"""
        if wait_before:
            await self.random_delay(0.5, 1.5)

        # Move mouse to element first
        element = self.page.locator(selector).first
        await element.hover()
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Click
        await element.click()

        if wait_after:
            await self.random_delay(0.5, 1.5)

    async def tab_switching_behavior(self):
        """Simulate user switching tabs or checking other things"""
        # Simulate user going away briefly
        delay = random.uniform(2.0, 5.0)
        logger.debug(f"Simulating tab switching for {delay:.1f}s")
        await asyncio.sleep(delay)

    async def random_actions(self, num_actions: int = 3):
        """Perform random human-like actions"""
        actions = [
            self.mouse_movement,
            lambda: self.scroll_behavior(scrolls=2),
            lambda: self.reading_behavior(min_time=1, max_time=3),
            lambda: self._hover_random_element(),
        ]

        for _ in range(num_actions):
            action = random.choice(actions)
            try:
                await action()
            except Exception as e:
                logger.debug(f"Random action failed: {e}")

            await self.random_delay(0.5, 2.0)


class ScrollManager:
    """Advanced scroll management"""

    def __init__(self, page: Page, human_behavior: HumanBehavior):
        self.page = page
        self.human_behavior = human_behavior

    async def scroll_to_bottom(self, max_scrolls: int = 10):
        """Scroll to bottom of page"""
        previous_height = 0
        scrolls = 0

        while scrolls < max_scrolls:
            # Get current scroll height
            current_height = await self.page.evaluate('document.body.scrollHeight')

            if current_height == previous_height:
                # Reached bottom
                break

            # Scroll down
            await self.human_behavior.scroll_behavior(scrolls=1)

            previous_height = current_height
            scrolls += 1

        logger.info(f"Scrolled to bottom in {scrolls} scrolls")

    async def scroll_to_load_all(
            self,
            item_selector: str,
            target_count: int,
            max_scrolls: int = 20
    ):
        """Scroll until specific number of items are loaded"""
        scrolls = 0

        while scrolls < max_scrolls:
            # Check current count
            current_count = await self.page.locator(item_selector).count()

            if current_count >= target_count:
                logger.info(f"Loaded {current_count} items")
                return current_count

            # Scroll to load more
            await self.human_behavior.scroll_behavior(scrolls=1)
            scrolls += 1

            # Wait for new content to load
            await asyncio.sleep(1)

        final_count = await self.page.locator(item_selector).count()
        logger.info(f"Loaded {final_count} items after {scrolls} scrolls")
        return final_count