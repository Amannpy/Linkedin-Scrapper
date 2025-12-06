"""
Complete usage examples showing all modules working together
"""
import asyncio
import logging
from pathlib import Path

# Core components
from core import BrowserManager, SessionManager
from config import config, URLConfig

# Scrapers
from scrapers import ProfileScraper, PostScraper, CompanyScraper, SearchScraper

# Utilities
from utils import HumanBehavior, Validator, MediaDownloader

# Storage
from storage import JSONHandler, CSVHandler, Database, Cache

# Middleware
from middleware import error_handler, rate_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Profile Scraping
# ============================================================================
async def example_basic_profile_scraping():
    """Example: Scrape a single profile"""

    browser = BrowserManager()

    try:
        # Initialize browser
        await browser.initialize()

        # Create human behavior simulator
        behavior = HumanBehavior(browser.page)

        # Create session manager
        session = SessionManager(browser.page, behavior)

        # Login
        await session.login(
            email="your_email@example.com",
            password="your_password"
        )

        # Create profile scraper
        profile_scraper = ProfileScraper(browser.page, behavior)

        # Scrape profile
        profile_data = await profile_scraper.scrape_profile(
            "https://www.linkedin.com/in/example/"
        )

        # Save to JSON
        JSONHandler.save(profile_data, "output/profile.json")

        print(f"✓ Profile scraped: {profile_data['name']}")

    finally:
        await browser.close()


# ============================================================================
# Example 2: Scraping Multiple Profiles with Database
# ============================================================================
async def example_multiple_profiles_with_database():
    """Example: Scrape multiple profiles and save to database"""

    browser = BrowserManager()
    db = Database()

    try:
        # Initialize
        await browser.initialize()
        await db.connect()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        # Load existing session or login
        if not await session.load_session():
            await session.login()

        profile_scraper = ProfileScraper(browser.page, behavior)

        # List of profiles to scrape
        profile_urls = [
            "https://www.linkedin.com/in/profile1/",
            "https://www.linkedin.com/in/profile2/",
            "https://www.linkedin.com/in/profile3/",
        ]

        for url in profile_urls:
            try:
                # Check cache first
                cache = Cache()
                cached_data = cache.get(url)

                if cached_data:
                    print(f"Using cached data for {url}")
                    profile_data = cached_data
                else:
                    # Scrape profile
                    profile_data = await profile_scraper.scrape_profile(url)
                    cache.set(url, profile_data)

                # Save to database
                await db.save_profile(profile_data)

                print(f"✓ Saved: {profile_data['name']}")

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                continue

        print("\n✓ All profiles processed!")

    finally:
        await db.close()
        await browser.close()


# ============================================================================
# Example 3: Scraping Feed with All Features
# ============================================================================
async def example_scrape_feed_complete():
    """Example: Scrape feed with comments and media"""

    browser = BrowserManager()
    downloader = MediaDownloader()

    try:
        await browser.initialize()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        # Login
        await session.login()

        # Create post scraper
        post_scraper = PostScraper(browser.page, behavior)

        # Scrape feed
        posts = await post_scraper.scrape_feed(num_posts=10)

        # Download images from posts
        for i, post in enumerate(posts, 1):
            print(f"Processing post {i}/{len(posts)}")

            # Download images if present
            if post.get('media', {}).get('images'):
                for img_url in post['media']['images']:
                    await downloader.download_image(img_url)

        # Save all posts
        JSONHandler.save(posts, "output/feed_posts.json")
        CSVHandler.save(posts, "output/feed_posts.csv")

        print(f"\n✓ Scraped {len(posts)} posts with media!")

    finally:
        await browser.close()


# ============================================================================
# Example 4: Company Research
# ============================================================================
async def example_company_research():
    """Example: Research companies"""

    browser = BrowserManager()

    try:
        await browser.initialize()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        await session.login()

        # Create scrapers
        search_scraper = SearchScraper(browser.page, behavior)
        company_scraper = CompanyScraper(browser.page, behavior)

        # Search for companies
        print("Searching for AI companies...")
        search_results = await search_scraper.search_companies(
            keywords="artificial intelligence",
            max_results=10
        )

        print(f"Found {len(search_results)} companies")

        # Scrape detailed info for each company
        companies_data = []

        for i, result in enumerate(search_results[:5], 1):
            print(f"\nScraping company {i}/5: {result['name']}")

            company_data = await company_scraper.scrape_company(result['url'])
            companies_data.append(company_data)

        # Save results
        JSONHandler.save(companies_data, "output/ai_companies.json")

        print(f"\n✓ Researched {len(companies_data)} companies!")

    finally:
        await browser.close()


# ============================================================================
# Example 5: Job Search
# ============================================================================
async def example_job_search():
    """Example: Search for jobs"""

    browser = BrowserManager()

    try:
        await browser.initialize()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        await session.login()

        search_scraper = SearchScraper(browser.page, behavior)

        # Search for jobs
        jobs = await search_scraper.search_jobs(
            keywords="Python Developer",
            location="San Francisco",
            max_results=20
        )

        print(f"\nFound {len(jobs)} job postings:")
        for job in jobs[:5]:
            print(f"  - {job['title']} at {job['company']}")

        # Save to CSV for easy viewing
        CSVHandler.save(jobs, "output/python_jobs.csv")

        print(f"\n✓ Saved {len(jobs)} job postings!")

    finally:
        await browser.close()


# ============================================================================
# Example 6: People Search and Contact
# ============================================================================
async def example_people_search():
    """Example: Search for people with specific criteria"""

    browser = BrowserManager()

    try:
        await browser.initialize()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        await session.login()

        search_scraper = SearchScraper(browser.page, behavior)
        profile_scraper = ProfileScraper(browser.page, behavior)

        # Search for people
        print("Searching for data scientists...")
        people = await search_scraper.search_people(
            keywords="Data Scientist",
            max_results=20,
            filters={'location': 'New York'}
        )

        print(f"Found {len(people)} people")

        # Get detailed profiles for top results
        detailed_profiles = []

        for i, person in enumerate(people[:3], 1):
            print(f"\nGetting detailed profile {i}/3: {person['name']}")

            profile = await profile_scraper.scrape_profile(person['url'])
            detailed_profiles.append(profile)

        # Save results
        JSONHandler.save(detailed_profiles, "output/data_scientists.json")

        print(f"\n✓ Collected {len(detailed_profiles)} detailed profiles!")

    finally:
        await browser.close()


# ============================================================================
# Example 7: Monitoring and Statistics
# ============================================================================
async def example_with_monitoring():
    """Example: Scraping with monitoring and statistics"""

    browser = BrowserManager()

    try:
        await browser.initialize()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        await session.login()

        post_scraper = PostScraper(browser.page, behavior)

        # Scrape with monitoring
        print("Scraping feed with monitoring...")
        posts = await post_scraper.scrape_feed(num_posts=20)

        # Get statistics
        rate_stats = rate_limiter.get_stats()
        error_stats = error_handler.get_error_stats()

        print("\n" + "=" * 60)
        print("SCRAPING STATISTICS")
        print("=" * 60)
        print(f"Posts scraped: {len(posts)}")
        print(f"Total requests: {rate_stats['total_requests']}")
        print(f"Rate limit hits: {rate_stats['rate_limit_hits']}")
        print(f"Total wait time: {rate_stats['total_wait_time']:.2f}s")
        print(f"Total errors: {error_stats['total_errors']}")
        print("=" * 60)

        # Save posts
        JSONHandler.save(posts, "output/monitored_posts.json")

    finally:
        await browser.close()


# ============================================================================
# Example 8: Comprehensive Research Campaign
# ============================================================================
async def example_comprehensive_campaign():
    """
    Example: Complete research campaign
    - Search companies
    - Get company details
    - Find employees
    - Scrape their profiles
    """

    browser = BrowserManager()
    db = Database()

    try:
        # Initialize
        await browser.initialize()
        await db.connect()

        behavior = HumanBehavior(browser.page)
        session = SessionManager(browser.page, behavior)

        # Login
        await session.login()

        # Create all scrapers
        search_scraper = SearchScraper(browser.page, behavior)
        company_scraper = CompanyScraper(browser.page, behavior)
        profile_scraper = ProfileScraper(browser.page, behavior)

        # Step 1: Find target companies
        print("\n" + "=" * 60)
        print("STEP 1: Finding tech companies...")
        print("=" * 60)

        companies = await search_scraper.search_companies(
            keywords="technology startup",
            max_results=5
        )

        print(f"Found {len(companies)} companies")

        # Step 2: Get detailed company info
        print("\n" + "=" * 60)
        print("STEP 2: Getting company details...")
        print("=" * 60)

        for company in companies:
            print(f"\nResearching: {company['name']}")

            company_data = await company_scraper.scrape_company(company['url'])

            # Save to database
            JSONHandler.append(company_data, "output/campaign_companies.json")

        # Step 3: Find employees at these companies
        print("\n" + "=" * 60)
        print("STEP 3: Finding key employees...")
        print("=" * 60)

        all_employees = []

        for company in companies[:2]:  # Limit to 2 companies
            print(f"\nSearching employees at {company['name']}")

            employees = await search_scraper.search_people(
                keywords=f"engineer {company['name']}",
                max_results=5
            )

            all_employees.extend(employees)

        print(f"Found {len(all_employees)} employees total")

        # Step 4: Get detailed profiles
        print("\n" + "=" * 60)
        print("STEP 4: Getting detailed profiles...")
        print("=" * 60)

        for i, employee in enumerate(all_employees[:5], 1):
            print(f"\nProfile {i}/5: {employee['name']}")

            profile = await profile_scraper.scrape_profile(employee['url'])

            # Save to database
            await db.save_profile(profile)
            JSONHandler.append(profile, "output/campaign_profiles.json")

        print("\n" + "=" * 60)
        print("CAMPAIGN COMPLETE!")
        print("=" * 60)
        print(f"Companies researched: {len(companies)}")
        print(f"Employees found: {len(all_employees)}")
        print(f"Detailed profiles: 5")
        print("=" * 60)

    finally:
        await db.close()
        await browser.close()


# ============================================================================
# Main Menu
# ============================================================================
async def main():
    """Main menu to run examples"""

    print("\n" + "=" * 60)
    print("LinkedIn Scraper - Complete Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    print("1. Basic Profile Scraping")
    print("2. Multiple Profiles with Database")
    print("3. Feed Scraping with Media Download")
    print("4. Company Research")
    print("5. Job Search")
    print("6. People Search")
    print("7. Scraping with Monitoring")
    print("8. Comprehensive Research Campaign")
    print("0. Exit")
    print("=" * 60)

    choice = input("\nSelect example (0-8): ")

    examples = {
        '1': example_basic_profile_scraping,
        '2': example_multiple_profiles_with_database,
        '3': example_scrape_feed_complete,
        '4': example_company_research,
        '5': example_job_search,
        '6': example_people_search,
        '7': example_with_monitoring,
        '8': example_comprehensive_campaign,
    }

    if choice in examples:
        print(f"\nRunning example {choice}...\n")
        await examples[choice]()
    elif choice == '0':
        print("Goodbye!")
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())