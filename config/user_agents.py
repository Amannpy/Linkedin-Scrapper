"""
User agent pool for anti-detection
"""
import random
from typing import List


class UserAgentPool:
    """Manage user agents for rotation"""

    # Extensive user agent pool
    USER_AGENTS: List[str] = [
        # Chrome - Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        # Chrome - macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # Chrome - Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # Edge - Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',

        # Safari - macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',

        # Firefox - Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',

        # Firefox - macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',

        # Firefox - Linux
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]

    # Platform-specific configurations
    PLATFORMS = {
        'windows': {
            'platform': 'Win32',
            'vendor': 'Google Inc.',
            'renderer': 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)',
        },
        'macos': {
            'platform': 'MacIntel',
            'vendor': 'Apple Computer, Inc.',
            'renderer': 'Apple GPU',
        },
        'linux': {
            'platform': 'Linux x86_64',
            'vendor': 'Google Inc.',
            'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650)',
        }
    }

    # Screen resolutions
    SCREEN_RESOLUTIONS = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
        {'width': 2560, 'height': 1440},
        {'width': 1680, 'height': 1050},
    ]

    # Timezones
    TIMEZONES = [
        'America/New_York',
        'America/Chicago',
        'America/Los_Angeles',
        'America/Denver',
        'Europe/London',
        'Europe/Paris',
        'Asia/Tokyo',
        'Australia/Sydney',
    ]

    # Locales
    LOCALES = [
        'en-US',
        'en-GB',
        'en-CA',
        'en-AU',
    ]

    @classmethod
    def get_random_user_agent(cls) -> str:
        """Get a random user agent"""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def get_random_platform(cls) -> dict:
        """Get random platform configuration"""
        platform_name = random.choice(list(cls.PLATFORMS.keys()))
        return cls.PLATFORMS[platform_name]

    @classmethod
    def get_random_resolution(cls) -> dict:
        """Get random screen resolution"""
        return random.choice(cls.SCREEN_RESOLUTIONS)

    @classmethod
    def get_random_timezone(cls) -> str:
        """Get random timezone"""
        return random.choice(cls.TIMEZONES)

    @classmethod
    def get_random_locale(cls) -> str:
        """Get random locale"""
        return random.choice(cls.LOCALES)

    @classmethod
    def get_browser_fingerprint(cls) -> dict:
        """Generate a complete browser fingerprint"""
        resolution = cls.get_random_resolution()

        return {
            'user_agent': cls.get_random_user_agent(),
            'platform': cls.get_random_platform(),
            'viewport': resolution,
            'timezone': cls.get_random_timezone(),
            'locale': cls.get_random_locale(),
            'screen': {
                'width': resolution['width'],
                'height': resolution['height'],
                'color_depth': random.choice([24, 32]),
                'pixel_ratio': random.choice([1, 1.25, 1.5, 2]),
            }
        }
