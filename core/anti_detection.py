"""
Advanced anti-detection techniques for web scraping
"""
import random
import logging
from typing import Dict, List
from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)


class AntiDetection:
    """Anti-detection utilities and configurations"""

    @staticmethod
    def get_stealth_script() -> str:
        """
        Get comprehensive JavaScript for hiding automation

        Returns:
            str: JavaScript code to inject
        """
        return """
        (() => {
            // 1. Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 2. Mock plugins with realistic data
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
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
                    ];
                },
                configurable: true
            });

            // 3. Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });

            // 4. Mock chrome object
            if (!window.chrome) {
                window.chrome = {};
            }
            window.chrome.runtime = {
                connect: () => {},
                sendMessage: () => {},
            };
            window.chrome.loadTimes = function() {
                return {
                    commitLoadTime: Date.now() / 1000 - Math.random() * 10,
                    connectionInfo: 'http/1.1',
                    finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 5,
                    finishLoadTime: Date.now() / 1000 - Math.random() * 3,
                    firstPaintAfterLoadTime: Date.now() / 1000 - Math.random() * 2,
                    firstPaintTime: Date.now() / 1000 - Math.random() * 2,
                    navigationType: 'Other',
                    npnNegotiatedProtocol: 'unknown',
                    requestTime: Date.now() / 1000 - Math.random() * 15,
                    startLoadTime: Date.now() / 1000 - Math.random() * 12,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false
                };
            };
            window.chrome.csi = function() {
                return {
                    onloadT: Date.now(),
                    pageT: Math.random() * 1000,
                    startE: Date.now() - Math.random() * 5000,
                    tran: 15
                };
            };
            window.chrome.app = {};

            // 5. Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };

            // 6. Override toString methods
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                if (this === window.chrome.loadTimes) {
                    return 'function loadTimes() { [native code] }';
                }
                if (this === window.chrome.csi) {
                    return 'function csi() { [native code] }';
                }
                return originalToString.call(this);
            };

            // 7. Mock hardware concurrency (4-16 cores)
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => Math.floor(Math.random() * 12) + 4,
                configurable: true
            });

            // 8. Mock device memory (4, 8, or 16 GB)
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => [4, 8, 16][Math.floor(Math.random() * 3)],
                configurable: true
            });

            // 9. Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50,
                    saveData: false,
                    addEventListener: () => {},
                    removeEventListener: () => {},
                    dispatchEvent: () => true
                }),
                configurable: true
            });

            // 10. Mock battery API
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 0.8 + Math.random() * 0.2,
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => true
            });

            // 11. Mock media devices
            if (navigator.mediaDevices) {
                const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                navigator.mediaDevices.enumerateDevices = () => {
                    return Promise.resolve([
                        { deviceId: 'default', kind: 'audioinput', label: 'Default - Microphone', groupId: 'default' },
                        { deviceId: 'communications', kind: 'audioinput', label: 'Communications - Microphone', groupId: 'communications' },
                        { deviceId: 'default', kind: 'audiooutput', label: 'Default - Speakers', groupId: 'default' }
                    ]);
                };
            }

            // 12. Remove automation indicators
            delete navigator.__proto__.webdriver;

            // 13. Mock platform-specific properties
            Object.defineProperty(navigator, 'platform', {
                get: () => {
                    const platforms = ['Win32', 'MacIntel', 'Linux x86_64'];
                    return platforms[Math.floor(Math.random() * platforms.length)];
                },
                configurable: true
            });

            // 14. Mock vendor
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.',
                configurable: true
            });

            // 15. Mock maxTouchPoints
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 0,
                configurable: true
            });

            // 16. Mock screen properties with realistic values
            Object.defineProperty(screen, 'availWidth', {
                get: () => window.screen.width,
                configurable: true
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => window.screen.height - 40, // Taskbar height
                configurable: true
            });

            // 17. Mock Date to avoid timezone detection
            const originalDate = Date;
            Date = class extends originalDate {
                getTimezoneOffset() {
                    return 240; // EST timezone
                }
            };
            Date.prototype = originalDate.prototype;

            // 18. Spoof canvas fingerprinting
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 280 && this.height === 60) {
                    // Likely fingerprinting attempt
                    const context = this.getContext('2d');
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    // Add slight noise
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = imageData.data[i] + Math.random() - 0.5;
                        imageData.data[i + 1] = imageData.data[i + 1] + Math.random() - 0.5;
                        imageData.data[i + 2] = imageData.data[i + 2] + Math.random() - 0.5;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };

            // 19. Spoof WebGL fingerprinting
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };

            // 20. Override iframe detection
            Object.defineProperty(window, 'top', {
                get: () => window,
                configurable: true
            });
            Object.defineProperty(window, 'frameElement', {
                get: () => null,
                configurable: true
            });

            console.log('✓ Anti-detection measures applied');
        })();
        """

    @staticmethod
    def get_browser_args() -> List[str]:
        """
        Get browser launch arguments for stealth

        Returns:
            List[str]: Browser arguments
        """
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
            '--disable-sync',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-report-upload',
            '--disable-default-apps',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
        ]

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """
        Get HTTP headers for requests

        Returns:
            Dict[str, str]: Headers dictionary
        """
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }

    @staticmethod
    async def apply_evasions(context: BrowserContext):
        """
        Apply anti-detection measures to browser context

        Args:
            context: Playwright browser context
        """
        # Inject stealth script
        await context.add_init_script(AntiDetection.get_stealth_script())

        # Set extra headers
        await context.set_extra_http_headers(AntiDetection.get_headers())

        logger.info("✓ Anti-detection measures applied to context")

    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """
        Get random viewport size

        Returns:
            Dict[str, int]: Viewport dimensions
        """
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 2560, 'height': 1440},
            {'width': 1680, 'height': 1050},
        ]
        return random.choice(viewports)

    @staticmethod
    def get_random_geolocation() -> Dict[str, float]:
        """
        Get random geolocation (US cities)

        Returns:
            Dict[str, float]: Geolocation with longitude, latitude, accuracy
        """
        locations = [
            {'longitude': -74.006, 'latitude': 40.7128, 'accuracy': 5},  # New York
            {'longitude': -118.2437, 'latitude': 34.0522, 'accuracy': 5},  # Los Angeles
            {'longitude': -87.6298, 'latitude': 41.8781, 'accuracy': 5},  # Chicago
            {'longitude': -95.3698, 'latitude': 29.7604, 'accuracy': 5},  # Houston
            {'longitude': -122.4194, 'latitude': 37.7749, 'accuracy': 5},  # San Francisco
            {'longitude': -75.1652, 'latitude': 39.9526, 'accuracy': 5},  # Philadelphia
            {'longitude': -112.074, 'latitude': 33.4484, 'accuracy': 5},  # Phoenix
            {'longitude': -98.4936, 'latitude': 29.4241, 'accuracy': 5},  # San Antonio
        ]
        return random.choice(locations)

    @staticmethod
    def get_random_timezone() -> str:
        """
        Get random timezone

        Returns:
            str: Timezone ID
        """
        timezones = [
            'America/New_York',
            'America/Chicago',
            'America/Los_Angeles',
            'America/Denver',
            'America/Phoenix',
            'America/Detroit',
            'America/Boise',
        ]
        return random.choice(timezones)