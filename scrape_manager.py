#!/usr/bin/env python3
"""
Convenience script for managing Substack scraping operations.
Provides easy commands for initial scraping and incremental updates.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
import json

# Import the enhanced scraper
from substack_scraper_enhanced import (
    SubstackScraper, 
    PremiumSubstackScraper,
    BASE_MD_DIR,
    BASE_HTML_DIR,
    JSON_DATA_DIR
)
from config import EMAIL, PASSWORD


def get_last_12_months_date() -> str:
    """Get the date 12 months ago from today."""
    today = datetime.now()
    twelve_months_ago = today - timedelta(days=365)
    return twelve_months_ago.strftime("%Y-%m-%d")


def initial_scrape(url: str, start_date: Optional[str] = None, premium: bool = True,
                  num_posts: int = 0, headless: bool = True):
    """
    Perform initial scrape of a Substack for posts from start_date onwards.
    
    Args:
        url: The Substack URL to scrape
        start_date: Start date in YYYY-MM-DD format (default: 12 months ago)
        premium: Whether to use premium scraper for paid content
        num_posts: Number of posts to scrape (0 for all)
        headless: Run browser in headless mode for premium scraping
    """
    if not start_date:
        start_date = get_last_12_months_date()
    
    print(f"Starting initial scrape of {url}")
    print(f"Scraping posts from {start_date} onwards")
    print(f"Mode: {'Premium' if premium else 'Free'} content")
    
    if premium:
        if EMAIL == "your-email@domain.com" or PASSWORD == "your-password":
            print("\nERROR: Please set your Substack credentials in .env file!")
            print("Copy .env.example to .env and update SUBSTACK_EMAIL and SUBSTACK_PASSWORD")
            return False
        
        scraper = PremiumSubstackScraper(
            base_substack_url=url,
            md_save_dir=BASE_MD_DIR,
            html_save_dir=BASE_HTML_DIR,
            start_date=start_date,
            update_mode=False,
            headless=headless
        )
    else:
        scraper = SubstackScraper(
            base_substack_url=url,
            md_save_dir=BASE_MD_DIR,
            html_save_dir=BASE_HTML_DIR,
            start_date=start_date,
            update_mode=False
        )
    
    scraper.scrape_posts(num_posts)
    print(f"\nInitial scrape complete!")
    return True


def update_scrape(url: str, premium: bool = True, headless: bool = True):
    """
    Perform incremental update, only scraping new posts not already downloaded.
    
    Args:
        url: The Substack URL to scrape
        premium: Whether to use premium scraper for paid content
        headless: Run browser in headless mode for premium scraping
    """
    print(f"Starting update scrape of {url}")
    print(f"Mode: {'Premium' if premium else 'Free'} content")
    print("Only new posts will be downloaded")
    
    if premium:
        if EMAIL == "your-email@domain.com" or PASSWORD == "your-password":
            print("\nERROR: Please set your Substack credentials in .env file!")
            print("Copy .env.example to .env and update SUBSTACK_EMAIL and SUBSTACK_PASSWORD")
            return False
        
        scraper = PremiumSubstackScraper(
            base_substack_url=url,
            md_save_dir=BASE_MD_DIR,
            html_save_dir=BASE_HTML_DIR,
            start_date=None,
            update_mode=True,
            headless=headless
        )
    else:
        scraper = SubstackScraper(
            base_substack_url=url,
            md_save_dir=BASE_MD_DIR,
            html_save_dir=BASE_HTML_DIR,
            start_date=None,
            update_mode=True
        )
    
    scraper.scrape_posts(0)  # Scrape all new posts
    print(f"\nUpdate scrape complete!")
    return True


def list_scraped_substacks():
    """List all Substacks that have been scraped."""
    if not os.path.exists(BASE_MD_DIR):
        print("No Substacks have been scraped yet.")
        return
    
    substacks = [d for d in os.listdir(BASE_MD_DIR) 
                 if os.path.isdir(os.path.join(BASE_MD_DIR, d))]
    
    if not substacks:
        print("No Substacks have been scraped yet.")
        return
    
    print("\nScraped Substacks:")
    print("-" * 50)
    
    for substack in substacks:
        md_dir = os.path.join(BASE_MD_DIR, substack)
        post_count = len([f for f in os.listdir(md_dir) if f.endswith('.md')])
        
        # Try to get last update time from metadata
        metadata_file = os.path.join(JSON_DATA_DIR, f'{substack}_metadata.json')
        last_update = "Unknown"
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if 'last_update' in metadata:
                        last_update = metadata['last_update'][:10]  # Just the date part
            except:
                pass
        
        print(f"  • {substack}: {post_count} posts (Last updated: {last_update})")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Substack scraping operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initial scrape of last 12 months (default):
  python scrape_manager.py initial https://example.substack.com
  
  # Initial scrape from specific date:
  python scrape_manager.py initial https://example.substack.com --start-date 2023-01-01
  
  # Update with only new posts:
  python scrape_manager.py update https://example.substack.com
  
  # List all scraped Substacks:
  python scrape_manager.py list
  
  # Scrape free content only:
  python scrape_manager.py initial https://example.substack.com --free
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Initial scrape command
    initial_parser = subparsers.add_parser('initial', help='Perform initial scrape')
    initial_parser.add_argument('url', help='Substack URL to scrape')
    initial_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD), default: 12 months ago')
    initial_parser.add_argument('--free', action='store_true', help='Only scrape free content')
    initial_parser.add_argument('--num-posts', type=int, default=0, help='Number of posts to scrape (0 for all)')
    initial_parser.add_argument('--show-browser', action='store_true', help='Show browser window (for debugging)')
    
    # Update scrape command  
    update_parser = subparsers.add_parser('update', help='Scrape only new posts')
    update_parser.add_argument('url', help='Substack URL to update')
    update_parser.add_argument('--free', action='store_true', help='Only scrape free content')
    update_parser.add_argument('--show-browser', action='store_true', help='Show browser window (for debugging)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List scraped Substacks')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'initial':
        success = initial_scrape(
            url=args.url,
            start_date=args.start_date,
            premium=not args.free,
            num_posts=args.num_posts,
            headless=not args.show_browser
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'update':
        success = update_scrape(
            url=args.url,
            premium=not args.free,
            headless=not args.show_browser
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        list_scraped_substacks()


if __name__ == "__main__":
    main()