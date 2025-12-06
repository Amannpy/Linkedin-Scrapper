# Advanced LinkedIn Scraper - Modular Architecture

A professional, modular LinkedIn scraper with advanced anti-detection, error handling, and retry mechanisms.

## 🏗️ Architecture Overview

This scraper follows a clean, modular architecture where each component has a single responsibility:

```
linkedin_scraper/
│
├── config/                  # Configuration & Constants
│   ├── settings.py         # Main configuration with Pydantic validation
│   └── user_agents.py      # User agent pool & fingerprint generation
│
├── core/                    # Core Browser Functionality
│   ├── browser.py          # Browser initialization & management
│   ├── session.py          # Session management & authentication
│   └── anti_detection.py   # Anti-bot detection measures
│
├── scrapers/                # Scraping Modules
│   ├── profile_scraper.py  # Profile data extraction
│   ├── post_scraper.py     # Post & feed scraping
│   ├── company_scraper.py  # Company page scraping
│   └── search_scraper.py   # Search functionality
│
├── utils/                   # Utility Functions
│   ├── human_behavior.py   # Human-like interaction simulation
│   ├── data_extractor.py   # Generic data extraction utilities
│   ├── downloader.py       # Media download manager
│   └── validators.py       # Input validation
│
├── storage/                 # Data Storage
│   ├── json_handler.py     # JSON operations
│   ├── csv_handler.py      # CSV operations
│   ├── database.py         # SQLite database
│   └── cache.py            # Caching mechanism
│
├── middleware/              # Cross-cutting Concerns
│   ├── error_handler.py    # Centralized error handling
│   ├── retry_handler.py    # Retry logic with exponential backoff
│   └── rate_limiter.py     # Rate limiting
│
└── main.py                  # Main orchestrator
```

## ✨ Key Features

### 1. **Modular Design**
- Each module has a single responsibility
- Easy to maintain, test, and extend
- Components can be replaced independently

### 2. **Advanced Anti-Detection**
- Multiple user agent rotation
- Browser fingerprint randomization
- Human-like behavior simulation:
  - Realistic mouse movements (bezier curves)
  - Variable typing speeds with mistakes
  - Natural scrolling patterns
  - Random reading pauses

### 3. **Robust Error Handling**
- Custom exception hierarchy
- Centralized error logging
- Context-based error handling
- Graceful degradation

### 4. **Smart Retry Logic**
- Exponential backoff
- Error-type specific retry strategies
- Configurable retry attempts
- Batch operation support

### 5. **Configuration Management**
- Environment variable support
- Pydantic validation
- Type-safe configuration
- Easy customization

### 6. **Session Management**
- Save/load browser sessions
- Cookie persistence
- Authentication state management

## 🚀 Installation

```bash
# Clone repository
git clone <repository-url>
cd linkedin_scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Optional overrides
HEADLESS=false
MAX_RETRIES=3
REQUESTS_PER_MINUTE=20
```

### Configuration File

Modify `config/settings.py` for advanced settings:

```python
class ScraperConfig:
    headless: bool = False
    min_delay: float = 1.0
    max_delay: float = 3.0
    max_posts_per_scrape: int = 10
    download_images: bool = True
    # ... more options
```

## 📖 Usage Examples

### Basic Usage

```python
import asyncio
from main import LinkedInScraperOrchestrator

async def main():
    scraper = LinkedInScraperOrchestrator()
    
    try:
        # Initialize
        await scraper.initialize()
        
        # Login
        await scraper.login(
            email="your_email@example.com",
            password="your_password"
        )
        
        # Scrape feed
        posts = await scraper.scrape_feed_posts(num_posts=10)
        
        print(f"Scraped {len(posts)} posts")
        
    finally:
        await scraper.cleanup()

asyncio.run(main())
```

### Using Session Management

```python
# Save session after login
await scraper.login(email, password)
await scraper.save_session()

# Next time, load session (no login needed)
session_loaded = await scraper.load_session()
if session_loaded:
    print("Using saved session")
else:
    await scraper.login(email, password)
```

### Custom Error Handling

```python
from middleware.error_handler import ErrorContext, handle_errors

# Using context manager
with ErrorContext("Custom Operation", suppress=True):
    # Your code here
    result = await some_operation()

# Using decorator
@handle_errors("My Operation", raise_on_error=False)
async def my_function():
    # Your code here
    pass
```

### Custom Retry Logic

```python
from middleware.retry_handler import with_retry, RetryHandler

# Using decorator
@with_retry(max_attempts=5, min_wait=2.0, max_wait=15.0)
async def scrape_with_retry():
    # Your scraping code
    pass

# Using handler directly
retry_handler = RetryHandler(max_attempts=3)
result = await retry_handler.execute_with_retry(
    my_function,
    arg1, arg2,
    operation_name="Custom Operation"
)
```

## 🔧 Advanced Features

### Human Behavior Simulation

```python
from utils.human_behavior import HumanBehavior

behavior = HumanBehavior(page)

# Realistic typing with mistakes
await behavior.human_typing(
    selector="#search",
    text="Python Developer",
    mistakes=True
)

# Natural scrolling
await behavior.scroll_behavior(
    scrolls=5,
    scroll_type='natural'  # 'fast', 'natural', 'slow'
)

# Random mouse movements
await behavior.mouse_movement(
    num_movements=5,
    smooth=True  # Uses bezier curves
)

# Reading simulation
await behavior.reading_behavior(min_time=2, max_time=8)
```

### Browser Fingerprint Randomization

```python
from config.user_agents import UserAgentPool

# Get random fingerprint
fingerprint = UserAgentPool.get_browser_fingerprint()

# Includes:
# - Random user agent
# - Platform configuration
# - Screen resolution
# - Timezone
# - Locale
```

## 🛡️ Anti-Detection Features

1. **WebDriver Property Masking**
   - Removes `navigator.webdriver`
   - Mocks browser plugins
   - Spoofs hardware specs

2. **Behavioral Patterns**
   - Variable delays between actions
   - Realistic mouse trajectories
   - Human typing patterns with mistakes
   - Natural scroll behavior

3. **Fingerprint Randomization**
   - User agent rotation
   - Screen resolution variation
   - Timezone randomization
   - Platform-specific configurations

4. **Honeypot Detection**
   - Identifies hidden form fields
   - Avoids bot traps
   - Validates page structure

## 📊 Monitoring & Statistics

```python
# Get scraper statistics
stats = await scraper.get_scraper_stats()

print(f"Total Errors: {stats['errors']['total_errors']}")
print(f"Operations with Retries: {stats['retries']['operations_with_retries']}")
```

## ⚠️ Error Handling

### Custom Exceptions

```python
from middleware.error_handler import (
    LoginException,
    CaptchaException,
    RateLimitException,
    TimeoutException,
    ElementNotFoundException
)
```

### Error Recovery

The scraper automatically handles:
- Network errors (with retry)
- Timeouts (with increased wait)
- Element not found (with retry)
- Rate limits (with exponential backoff)

Non-recoverable errors:
- CAPTCHA detection (requires manual intervention)
- Invalid credentials
- Account restrictions

## 🎯 Best Practices

1. **Rate Limiting**
   - Default: 20 requests/minute
   - Adjust in `config/settings.py`
   - Use delays between operations

2. **Session Management**
   - Save sessions to avoid repeated logins
   - Clear sessions periodically
   - Handle session expiration

3. **Error Handling**
   - Always use try-except in custom code
   - Check scraper stats regularly
   - Monitor error logs

4. **Resource Management**
   - Always call `cleanup()` in finally block
   - Close browser properly
   - Clear caches periodically

## 📝 Extending the Scraper

### Adding New Scrapers

```python
# scrapers/custom_scraper.py
from utils.human_behavior import HumanBehavior
from middleware.error_handler import handle_errors

class CustomScraper:
    def __init__(self, page, human_behavior):
        self.page = page
        self.behavior = human_behavior
    
    @handle_errors("Custom Scrape")
    async def scrape_custom_data(self):
        # Your scraping logic
        pass
```

### Adding Custom Middleware

```python
# middleware/custom_middleware.py
from functools import wraps

def custom_middleware(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Before logic
        result = await func(*args, **kwargs)
        # After logic
        return result
    return wrapper
```

## 🔒 Security Considerations

1. **Credentials**
   - Never hardcode credentials
   - Use environment variables
   - Consider using keyring

2. **Data Storage**
   - Encrypt sensitive data
   - Respect LinkedIn's ToS
   - Handle PII appropriately

3. **Rate Limiting**
   - Respect LinkedIn's servers
   - Implement appropriate delays
   - Monitor for blocks

## 📄 License

This project is for educational purposes only. Always respect LinkedIn's Terms of Service and robots.txt.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Login Fails**
- Check credentials
- Verify no CAPTCHA
- Try saving/loading session

**Elements Not Found**
- LinkedIn may have changed selectors
- Update selectors in `config/settings.py`
- Check if page fully loaded

**Rate Limited**
- Reduce requests_per_minute
- Increase delays
- Use session management

**Browser Crashes**
- Increase page_load_timeout
- Check system resources
- Try headless mode

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [LinkedIn Developer Guidelines](https://www.linkedin.com/developers/)
- [Web Scraping Best Practices](https://www.scrapingbee.com/blog/web-scraping-best-practices/)

---

**Disclaimer**: This tool is for educational purposes only. Web scraping may violate LinkedIn's Terms of Service. Use responsibly and ethically.