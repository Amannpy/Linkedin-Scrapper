"""
Browser initialization and management with advanced anti-detection
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from config.settings import config, SuccessMessages
from config.user_agents import UserAgentPool
from middleware.error_handler import handle_errors, NetworkException

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manage browser lifecycle and anti-detection measures"""

    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else config.headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_initialized = False

    @handle_errors("Browser Initialization", raise_on_error=True)
    async def initialize(self):
        """Initialize browser with stealth settings"""
        if self._is_initialized:
            logger.warning("Browser already initialized")
            return

        logger.info("Initializing browser...")

        # Get random fingerprint
        fingerprint = UserAgentPool.get_browser_fingerprint()

        # Start playwright
        self.playwright = await async_playwright().start()

        # Launch browser with anti-detection args
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=self._get_browser_args(),
            ignore_default_args=['--enable-automation'],
        )

        # Create context with fingerprint
        self.context = await self.browser.new_context(
            viewport=fingerprint['viewport'],
            user_agent=fingerprint['user_agent'],
            locale=fingerprint['locale'],
            timezone_id=fingerprint['timezone'],
            permissions=['geolocation', 'notifications'],
            geolocation=self._get_random_geolocation(),
            accept_downloads=True,
            ignore_https_errors=True,
            device_scale_factor=fingerprint['screen']['pixel_ratio'],
            has_touch=False,
            is_mobile=False,
        )

        # Add anti-detection scripts
        await self._inject_anti_detection_scripts()

        # Set extra headers
        await self.context.set_extra_http_headers(self._get_headers())

        # Create page
        self.page = await self.context.new_page()

        # Configure page
        await self._configure_page()

        self._is_initialized = True
        logger.info(SuccessMessages.BROWSER_INITIALIZED)

    def _get_browser_args(self) -> list:
        """Get browser launch arguments"""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--start-maximized',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-extensions',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-notifications',
        ]

    def _get_headers(self) -> dict:
        """Get HTTP headers"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def _get_random_geolocation(self) -> dict:
        """Get random geolocation"""
        # Major US cities
        locations = [
            {'longitude': -74.006, 'latitude': 40.7128, 'accuracy': 5},  # New York
            {'longitude': -118.2437, 'latitude': 34.0522, 'accuracy': 5},  # Los Angeles
            {'longitude': -87.6298, 'latitude': 41.8781, 'accuracy': 5},  # Chicago
            {'longitude': -95.3698, 'latitude': 29.7604, 'accuracy': 5},  # Houston
            {'longitude': -122.4194, 'latitude': 37.7749, 'accuracy': 5},  # San Francisco
        ]
        import random
        return random.choice(locations)

    async def _inject_anti_detection_scripts(self):
        """Inject JavaScript to mask automation"""
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                        1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                        description: "",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Override the plugins toString
            Object.defineProperty(navigator.plugins, 'length', {
                get: () => 3,
            });
            
            // Mock hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => Math.floor(Math.random() * 4) + 4,  // 4-8 cores
            });
            
            // Mock device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => Math.pow(2, Math.floor(Math.random() * 3) + 2),  // 4, 8, or 16 GB
            });
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50,
                    saveData: false,
                }),
            });
            
            // Override toString methods
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalToString.call(this);
            };
            
            // Mock battery API
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1,
                addEventListener: () => {},
                removeEventListener: () => {},
            });
            
            // Remove automation indicators
            delete navigator.__proto__.webdriver;
        """)

    async def _configure_page(self):
        """Configure page settings"""
        # Set default timeout
        self.page.set_default_timeout(config.page_load_timeout)

        # Block unnecessary resources to speed up
        await self.page.route("**/*", self._route_handler)

    async def _route_handler(self, route):
        """Handle resource routing"""
        request = route.request

        # Block certain resource types to speed up
        block_resources = ['stylesheet', 'font', 'media']

        if config.download_images is False:
            block_resources.append('image')

        if config.download_videos is False:
            block_resources.append('video')

        if request.resource_type in block_resources:
            await route.abort()
        else:
            await route.continue_()

    async def new_page(self) -> Page:
        """Create a new page in the same context"""
        if not self.context:
            raise NetworkException("Browser context not initialized")

        page = await self.context.new_page()
        page.set_default_timeout(config.page_load_timeout)
        return page

    async def clear_cookies(self):
        """Clear all cookies"""
        if self.context:
            await self.context.clear_cookies()
            logger.info("Cookies cleared")

    async def save_state(self, path: str):
        """Save browser state (cookies, local storage)"""
        if self.context:
            await self.context.storage_state(path=path)
            logger.info(f"Browser state saved to {path}")

    async def load_state(self, path: str):
        """Load browser state"""
        if self.context:
            await self.context.close()

        # Create new context with saved state
        self.context = await self.browser.new_context(
            storage_state=path,
            viewport=config.viewport_width,
            user_agent=UserAgentPool.get_random_user_agent(),
        )
        self.page = await self.context.new_page()
        logger.info(f"Browser state loaded from {path}")

    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        self._is_initialized = False
        logger.info("✓ Browser closed")

    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
        return False