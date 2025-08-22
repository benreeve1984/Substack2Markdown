import argparse
import json
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from time import sleep
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import html2text
import markdown
import requests
from tqdm import tqdm
from xml.etree import ElementTree as ET

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service
from config import EMAIL, PASSWORD

USE_PREMIUM: bool = True
BASE_SUBSTACK_URL: str = "https://www.thefitzwilliam.com/"
BASE_MD_DIR: str = "substack_md_files"
BASE_HTML_DIR: str = "substack_html_pages"
HTML_TEMPLATE: str = "author_template.html"
JSON_DATA_DIR: str = "data"
NUM_POSTS_TO_SCRAPE: int = 0  # Set to 0 for all posts
START_DATE: str = None  # Format: YYYY-MM-DD, e.g., "2024-01-01"
UPDATE_MODE: bool = False  # If True, only scrape new articles not already downloaded

# Polite scraping settings
MIN_DELAY: float = 2.0  # Minimum delay between requests (seconds)
MAX_DELAY: float = 5.0  # Maximum delay between requests (seconds)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


def extract_main_part(url: str) -> str:
    parts = urlparse(url).netloc.split('.')
    return parts[1] if parts[0] == 'www' else parts[0]


def generate_html_file(author_name: str) -> None:
    """
    Generates a HTML file for the given author.
    """
    if not os.path.exists(BASE_HTML_DIR):
        os.makedirs(BASE_HTML_DIR)

    json_path = os.path.join(JSON_DATA_DIR, f'{author_name}.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        essays_data = json.load(file)

    embedded_json_data = json.dumps(essays_data, ensure_ascii=False, indent=4)

    with open(HTML_TEMPLATE, 'r', encoding='utf-8') as file:
        html_template = file.read()

    html_with_data = html_template.replace('<!-- AUTHOR_NAME -->', author_name).replace(
        '<script type="application/json" id="essaysData"></script>',
        f'<script type="application/json" id="essaysData">{embedded_json_data}</script>'
    )
    html_with_author = html_with_data.replace('author_name', author_name)

    html_output_path = os.path.join(BASE_HTML_DIR, f'{author_name}.html')
    with open(html_output_path, 'w', encoding='utf-8') as file:
        file.write(html_with_author)


class BaseSubstackScraper(ABC):
    def __init__(self, base_substack_url: str, md_save_dir: str, html_save_dir: str, 
                 start_date: Optional[str] = None, update_mode: bool = False):
        if not base_substack_url.endswith("/"):
            base_substack_url += "/"
        self.base_substack_url: str = base_substack_url
        self.start_date = start_date
        self.update_mode = update_mode

        self.writer_name: str = extract_main_part(base_substack_url)
        md_save_dir: str = f"{md_save_dir}/{self.writer_name}"

        self.md_save_dir: str = md_save_dir
        self.html_save_dir: str = f"{html_save_dir}/{self.writer_name}"

        if not os.path.exists(md_save_dir):
            os.makedirs(md_save_dir)
            print(f"Created md directory {md_save_dir}")
        if not os.path.exists(self.html_save_dir):
            os.makedirs(self.html_save_dir)
            print(f"Created html directory {self.html_save_dir}")

        self.keywords: List[str] = ["about", "archive", "podcast"]
        self.existing_files = self.get_existing_files() if update_mode else set()
        self.post_urls: List[str] = self.get_all_post_urls()
        
        # Track scraped articles metadata
        self.metadata_file = os.path.join(JSON_DATA_DIR, f'{self.writer_name}_metadata.json')
        self.metadata = self.load_metadata()

    def load_metadata(self) -> Dict:
        """Load metadata about previously scraped articles."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"articles": {}, "last_update": None}
    
    def save_metadata(self) -> None:
        """Save metadata about scraped articles."""
        self.metadata["last_update"] = datetime.now().isoformat()
        os.makedirs(JSON_DATA_DIR, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def get_existing_files(self) -> set:
        """Get set of already downloaded post URLs based on existing files."""
        existing = set()
        if os.path.exists(self.md_save_dir):
            for filename in os.listdir(self.md_save_dir):
                if filename.endswith('.md'):
                    # Convert filename back to URL pattern
                    post_slug = filename[:-3]  # Remove .md extension
                    existing.add(post_slug)
        return existing

    def polite_delay(self) -> None:
        """Add a random delay between requests to be polite to the server."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        sleep(delay)

    def get_random_user_agent(self) -> str:
        """Get a random user agent for requests."""
        return random.choice(USER_AGENTS)

    def get_all_post_urls(self) -> List[str]:
        """
        Attempts to fetch URLs from sitemap.xml, falling back to feed.xml if necessary.
        Filters by date if start_date is provided.
        """
        urls = self.fetch_urls_from_sitemap()
        if not urls:
            urls = self.fetch_urls_from_feed()
        
        filtered_urls = self.filter_urls(urls, self.keywords)
        
        # Filter by existing files if in update mode
        if self.update_mode and self.existing_files:
            new_urls = []
            for url in filtered_urls:
                post_slug = url.split("/")[-1]
                if post_slug not in self.existing_files:
                    new_urls.append(url)
            print(f"Found {len(new_urls)} new articles to scrape (out of {len(filtered_urls)} total)")
            filtered_urls = new_urls
        
        return filtered_urls

    def fetch_urls_from_sitemap(self) -> List[str]:
        """
        Fetches URLs from sitemap.xml.
        """
        sitemap_url = f"{self.base_substack_url}sitemap.xml"
        headers = {'User-Agent': self.get_random_user_agent()}
        response = requests.get(sitemap_url, headers=headers)

        if not response.ok:
            print(f'Error fetching sitemap at {sitemap_url}: {response.status_code}')
            return []

        root = ET.fromstring(response.content)
        urls = []
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url_elem in root.findall('.//ns:url', namespace):
            loc = url_elem.find('ns:loc', namespace)
            lastmod = url_elem.find('ns:lastmod', namespace)
            
            if loc is not None and loc.text:
                # Check date filter if provided
                if self.start_date and lastmod is not None and lastmod.text:
                    try:
                        post_date = datetime.fromisoformat(lastmod.text.replace('Z', '+00:00'))
                        start_datetime = datetime.fromisoformat(self.start_date)
                        if post_date < start_datetime:
                            continue
                    except:
                        pass  # If date parsing fails, include the URL
                
                urls.append(loc.text)
        
        return urls

    def fetch_urls_from_feed(self) -> List[str]:
        """
        Fetches URLs from feed.xml with date filtering.
        """
        print('Falling back to feed.xml. This will only contain up to the 22 most recent posts.')
        feed_url = f"{self.base_substack_url}feed.xml"
        headers = {'User-Agent': self.get_random_user_agent()}
        response = requests.get(feed_url, headers=headers)

        if not response.ok:
            print(f'Error fetching feed at {feed_url}: {response.status_code}')
            return []

        root = ET.fromstring(response.content)
        urls = []
        
        for item in root.findall('.//item'):
            link = item.find('link')
            pubdate = item.find('pubDate')
            
            if link is not None and link.text:
                # Check date filter if provided
                if self.start_date and pubdate is not None and pubdate.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        post_date = parsedate_to_datetime(pubdate.text)
                        start_datetime = datetime.fromisoformat(self.start_date)
                        if post_date.replace(tzinfo=None) < start_datetime:
                            continue
                    except:
                        pass  # If date parsing fails, include the URL
                
                urls.append(link.text)

        return urls

    @staticmethod
    def filter_urls(urls: List[str], keywords: List[str]) -> List[str]:
        """
        This method filters out URLs that contain certain keywords
        """
        return [url for url in urls if all(keyword not in url for keyword in keywords)]

    @staticmethod
    def html_to_md(html_content: str) -> str:
        """
        This method converts HTML to Markdown
        """
        if not isinstance(html_content, str):
            raise ValueError("html_content must be a string")
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0
        return h.handle(html_content)

    @staticmethod
    def save_to_file(filepath: str, content: str) -> None:
        """
        This method saves content to a file. Can be used to save HTML or Markdown
        """
        if not isinstance(filepath, str):
            raise ValueError("filepath must be a string")

        if not isinstance(content, str):
            raise ValueError("content must be a string")

        if os.path.exists(filepath):
            print(f"File already exists: {filepath}")
            return

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)

    @staticmethod
    def md_to_html(md_content: str) -> str:
        """
        This method converts Markdown to HTML
        """
        return markdown.markdown(md_content, extensions=['extra'])

    def save_to_html_file(self, filepath: str, content: str) -> None:
        """
        This method saves HTML content to a file with a link to an external CSS file.
        """
        if not isinstance(filepath, str):
            raise ValueError("filepath must be a string")

        if not isinstance(content, str):
            raise ValueError("content must be a string")

        html_dir = os.path.dirname(filepath)
        css_path = os.path.relpath("./assets/css/essay-styles.css", html_dir)
        css_path = css_path.replace("\\", "/")

        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Markdown Content</title>
                <link rel="stylesheet" href="{css_path}">
            </head>
            <body>
                <main class="markdown-content">
                {content}
                </main>
            </body>
            </html>
        """

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(html_content)

    @staticmethod
    def get_filename_from_url(url: str, filetype: str = ".md") -> str:
        """
        Gets the filename from the URL (the ending)
        """
        if not isinstance(url, str):
            raise ValueError("url must be a string")

        if not isinstance(filetype, str):
            raise ValueError("filetype must be a string")

        if not filetype.startswith("."):
            filetype = f".{filetype}"

        return url.split("/")[-1] + filetype

    @staticmethod
    def combine_metadata_and_content(title: str, subtitle: str, date: str, like_count: str, content) -> str:
        """
        Combines the title, subtitle, and content into a single string with Markdown format
        """
        if not isinstance(title, str):
            raise ValueError("title must be a string")

        if not isinstance(content, str):
            raise ValueError("content must be a string")

        metadata = f"# {title}\n\n"
        if subtitle:
            metadata += f"## {subtitle}\n\n"
        metadata += f"**{date}**\n\n"
        metadata += f"**Likes:** {like_count}\n\n"

        return metadata + content

    def extract_post_data(self, soup: BeautifulSoup, url: str) -> Tuple[str, str, str, str, str]:
        """
        Converts substack post soup to markdown, returns metadata and content
        """
        title = soup.select_one("h1.post-title, h2").text.strip()

        subtitle_element = soup.select_one("h3.subtitle")
        subtitle = subtitle_element.text.strip() if subtitle_element else ""

        date_element = soup.find(
            "div",
            class_="pencraft pc-reset color-pub-secondary-text-hGQ02T line-height-20-t4M0El font-meta-MWBumP size-11-NuY2Zx weight-medium-fw81nC transform-uppercase-yKDgcq reset-IxiVJZ meta-EgzBVA"
        )
        date = date_element.text.strip() if date_element else "Date not found"

        like_count_element = soup.select_one("a.post-ufi-button .label")
        like_count = (
            like_count_element.text.strip()
            if like_count_element and like_count_element.text.strip().isdigit()
            else "0"
        )

        content = str(soup.select_one("div.available-content"))
        md = self.html_to_md(content)
        md_content = self.combine_metadata_and_content(title, subtitle, date, like_count, md)
        
        # Store metadata
        post_slug = url.split("/")[-1]
        self.metadata["articles"][post_slug] = {
            "url": url,
            "title": title,
            "date": date,
            "scraped_at": datetime.now().isoformat()
        }
        
        return title, subtitle, like_count, date, md_content

    @abstractmethod
    def get_url_soup(self, url: str) -> str:
        raise NotImplementedError

    def save_essays_data_to_json(self, essays_data: list) -> None:
        """
        Saves essays data to a JSON file for a specific author.
        """
        data_dir = os.path.join(JSON_DATA_DIR)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        json_path = os.path.join(data_dir, f'{self.writer_name}.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
            essays_data = existing_data + [data for data in essays_data if data not in existing_data]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(essays_data, f, ensure_ascii=False, indent=4)

    def scrape_posts(self, num_posts_to_scrape: int = 0) -> None:
        """
        Iterates over all posts and saves them as markdown and html files
        """
        essays_data = []
        count = 0
        total = num_posts_to_scrape if num_posts_to_scrape != 0 else len(self.post_urls)
        
        if len(self.post_urls) == 0:
            print("No new posts to scrape.")
            return
        
        print(f"Starting to scrape {total} posts...")
        
        for url in tqdm(self.post_urls, total=total):
            try:
                md_filename = self.get_filename_from_url(url, filetype=".md")
                html_filename = self.get_filename_from_url(url, filetype=".html")
                md_filepath = os.path.join(self.md_save_dir, md_filename)
                html_filepath = os.path.join(self.html_save_dir, html_filename)

                if not os.path.exists(md_filepath):
                    # Add polite delay before each request
                    self.polite_delay()
                    
                    soup = self.get_url_soup(url)
                    if soup is None:
                        total += 1
                        continue
                    title, subtitle, like_count, date, md = self.extract_post_data(soup, url)
                    self.save_to_file(md_filepath, md)

                    # Convert markdown to HTML and save
                    html_content = self.md_to_html(md)
                    self.save_to_html_file(html_filepath, html_content)

                    essays_data.append({
                        "title": title,
                        "subtitle": subtitle,
                        "like_count": like_count,
                        "date": date,
                        "file_link": md_filepath,
                        "html_link": html_filepath
                    })
                else:
                    print(f"File already exists: {md_filepath}")
            except Exception as e:
                print(f"Error scraping post {url}: {e}")
            count += 1
            if num_posts_to_scrape != 0 and count == num_posts_to_scrape:
                break
        
        self.save_essays_data_to_json(essays_data=essays_data)
        self.save_metadata()
        generate_html_file(author_name=self.writer_name)
        print(f"Scraping complete. Scraped {len(essays_data)} new posts.")


class SubstackScraper(BaseSubstackScraper):
    def __init__(self, base_substack_url: str, md_save_dir: str, html_save_dir: str,
                 start_date: Optional[str] = None, update_mode: bool = False):
        super().__init__(base_substack_url, md_save_dir, html_save_dir, start_date, update_mode)

    def get_url_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Gets soup from URL using requests with polite headers
        """
        try:
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, "html.parser")
            if soup.find("h2", class_="paywall-title"):
                print(f"Skipping premium article: {url}")
                return None
            return soup
        except Exception as e:
            print(f"Error fetching page {url}: {e}")
            return None


class PremiumSubstackScraper(BaseSubstackScraper):
    def __init__(
            self,
            base_substack_url: str,
            md_save_dir: str,
            html_save_dir: str,
            start_date: Optional[str] = None,
            update_mode: bool = False,
            headless: bool = False,
            edge_path: str = '',
            edge_driver_path: str = '',
            user_agent: str = ''
    ) -> None:
        super().__init__(base_substack_url, md_save_dir, html_save_dir, start_date, update_mode)

        options = EdgeOptions()
        if headless:
            options.add_argument("--headless")
        if edge_path:
            options.binary_location = edge_path
        if user_agent:
            options.add_argument(f'user-agent={user_agent}')
        else:
            options.add_argument(f'user-agent={self.get_random_user_agent()}')

        if edge_driver_path:
            service = Service(executable_path=edge_driver_path)
        else:
            service = Service(EdgeChromiumDriverManager().install())

        self.driver = webdriver.Edge(service=service, options=options)
        self.login()

    def login(self) -> None:
        """
        This method logs into Substack using Selenium
        """
        self.driver.get("https://substack.com/sign-in")
        sleep(3)

        signin_with_password = self.driver.find_element(
            By.XPATH, "//a[@class='login-option substack-login__login-option']"
        )
        signin_with_password.click()
        sleep(3)

        # Email and password
        email = self.driver.find_element(By.NAME, "email")
        password = self.driver.find_element(By.NAME, "password")
        email.send_keys(EMAIL)
        password.send_keys(PASSWORD)

        # Find the submit button and click it.
        submit = self.driver.find_element(By.XPATH, "//*[@id=\"substack-login\"]/div[2]/div[2]/form/button")
        submit.click()
        sleep(30)  # Wait for the page to load

        if self.is_login_failed():
            raise Exception(
                "Warning: Login unsuccessful. Please check your email and password, or your account status.\n"
                "Use the non-premium scraper for the non-paid posts. \n"
                "If running headless, run non-headlessly to see if blocked by Captcha."
            )

    def is_login_failed(self) -> bool:
        """
        Check for the presence of the 'error-container' to indicate a failed login attempt.
        """
        error_container = self.driver.find_elements(By.ID, 'error-container')
        return len(error_container) > 0 and error_container[0].is_displayed()

    def get_url_soup(self, url: str) -> BeautifulSoup:
        """
        Gets soup from URL using logged in selenium driver with polite delays
        """
        try:
            self.driver.get(url)
            # Add small delay to let page fully load
            sleep(2)
            return BeautifulSoup(self.driver.page_source, "html.parser")
        except Exception as e:
            print(f"Error fetching page {url}: {e}")
            return None

    def __del__(self):
        """Clean up the driver when the scraper is destroyed"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape a Substack site.")
    parser.add_argument(
        "-u", "--url", type=str, help="The base URL of the Substack site to scrape."
    )
    parser.add_argument(
        "-d", "--directory", type=str, help="The directory to save scraped posts."
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=0,
        help="The number of posts to scrape. If 0 or not provided, all posts will be scraped.",
    )
    parser.add_argument(
        "-p",
        "--premium",
        action="store_true",
        help="Include -p in command to use the Premium Substack Scraper with selenium.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Include --headless in command to run browser in headless mode when using the Premium Substack Scraper.",
    )
    parser.add_argument(
        "--edge-path",
        type=str,
        default="",
        help='Optional: The path to the Edge browser executable (i.e. "path_to_msedge.exe").',
    )
    parser.add_argument(
        "--edge-driver-path",
        type=str,
        default="",
        help='Optional: The path to the Edge WebDriver executable (i.e. "path_to_msedgedriver.exe").',
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="",
        help="Optional: Specify a custom user agent for selenium browser automation.",
    )
    parser.add_argument(
        "--html-directory",
        type=str,
        help="The directory to save scraped posts as HTML files.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Only scrape posts from this date onwards (format: YYYY-MM-DD, e.g., 2024-01-01)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update mode: only scrape new posts not already downloaded",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.directory is None:
        args.directory = BASE_MD_DIR

    if args.html_directory is None:
        args.html_directory = BASE_HTML_DIR

    # Use command line arguments if provided, otherwise use hardcoded values
    start_date = args.start_date if args.start_date else START_DATE
    update_mode = args.update if args.update else UPDATE_MODE

    if args.url:
        if args.premium:
            scraper = PremiumSubstackScraper(
                args.url,
                md_save_dir=args.directory,
                html_save_dir=args.html_directory,
                start_date=start_date,
                update_mode=update_mode,
                headless=args.headless,
                edge_path=args.edge_path,
                edge_driver_path=args.edge_driver_path,
                user_agent=args.user_agent
            )
        else:
            scraper = SubstackScraper(
                args.url,
                md_save_dir=args.directory,
                html_save_dir=args.html_directory,
                start_date=start_date,
                update_mode=update_mode
            )
        scraper.scrape_posts(args.number)

    else:  # Use the hardcoded values at the top of the file
        if USE_PREMIUM:
            scraper = PremiumSubstackScraper(
                base_substack_url=BASE_SUBSTACK_URL,
                md_save_dir=args.directory,
                html_save_dir=args.html_directory,
                start_date=start_date,
                update_mode=update_mode,
                edge_path=args.edge_path,
                edge_driver_path=args.edge_driver_path
            )
        else:
            scraper = SubstackScraper(
                base_substack_url=BASE_SUBSTACK_URL,
                md_save_dir=args.directory,
                html_save_dir=args.html_directory,
                start_date=start_date,
                update_mode=update_mode
            )
        scraper.scrape_posts(num_posts_to_scrape=NUM_POSTS_TO_SCRAPE)


if __name__ == "__main__":
    main()