#!/usr/bin/env python3
"""
Batch scraper for managing multiple Substack subscriptions.
Reads from subscriptions.json and scrapes all enabled subscriptions sequentially.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from time import sleep
from typing import Dict, List, Optional

from scrape_manager import initial_scrape, update_scrape, get_last_12_months_date
from config import EMAIL, PASSWORD


SUBSCRIPTIONS_FILE = "subscriptions.json"


def load_subscriptions() -> Dict:
    """Load subscriptions from JSON file."""
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        print(f"Error: {SUBSCRIPTIONS_FILE} not found!")
        print("Creating a default subscriptions file...")
        create_default_subscriptions()
        return load_subscriptions()
    
    with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_subscriptions(data: Dict) -> None:
    """Save subscriptions to JSON file."""
    with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_default_subscriptions() -> None:
    """Create a default subscriptions.json file."""
    default_data = {
        "subscriptions": [],
        "settings": {
            "default_start_date": None,
            "auto_detect_premium": True,
            "delay_between_substacks": 10
        }
    }
    save_subscriptions(default_data)
    print(f"Created {SUBSCRIPTIONS_FILE} - please add your subscriptions to this file.")


def add_subscription(url: str, name: Optional[str] = None, premium: bool = False) -> None:
    """Add a new subscription to the list."""
    data = load_subscriptions()
    
    # Check if already exists
    for sub in data["subscriptions"]:
        if sub["url"] == url:
            print(f"Subscription already exists: {url}")
            return
    
    # Extract name from URL if not provided
    if not name:
        from substack_scraper_enhanced import extract_main_part
        name = extract_main_part(url)
    
    new_sub = {
        "url": url,
        "name": name,
        "premium": premium,
        "enabled": True
    }
    
    data["subscriptions"].append(new_sub)
    save_subscriptions(data)
    print(f"Added subscription: {name} ({url})")


def remove_subscription(url: str) -> None:
    """Remove a subscription from the list."""
    data = load_subscriptions()
    original_count = len(data["subscriptions"])
    
    data["subscriptions"] = [s for s in data["subscriptions"] if s["url"] != url]
    
    if len(data["subscriptions"]) < original_count:
        save_subscriptions(data)
        print(f"Removed subscription: {url}")
    else:
        print(f"Subscription not found: {url}")


def list_subscriptions() -> None:
    """List all subscriptions."""
    data = load_subscriptions()
    
    if not data["subscriptions"]:
        print("No subscriptions configured.")
        print(f"Add subscriptions to {SUBSCRIPTIONS_FILE} or use: batch_scraper.py add <url>")
        return
    
    print("\nConfigured Subscriptions:")
    print("-" * 60)
    
    for i, sub in enumerate(data["subscriptions"], 1):
        status = "✓ Enabled" if sub.get("enabled", True) else "✗ Disabled"
        premium = "Premium" if sub.get("premium", False) else "Free"
        print(f"{i}. {sub['name']}")
        print(f"   URL: {sub['url']}")
        print(f"   Status: {status} | Type: {premium}")
        print()
    
    print(f"Total: {len(data['subscriptions'])} subscriptions")
    
    # Show settings
    settings = data.get("settings", {})
    print("\nSettings:")
    print(f"  Default start date: {settings.get('default_start_date', 'Last 12 months')}")
    print(f"  Delay between substacks: {settings.get('delay_between_substacks', 10)} seconds")


def toggle_subscription(url: str) -> None:
    """Enable/disable a subscription."""
    data = load_subscriptions()
    
    for sub in data["subscriptions"]:
        if sub["url"] == url:
            sub["enabled"] = not sub.get("enabled", True)
            save_subscriptions(data)
            status = "enabled" if sub["enabled"] else "disabled"
            print(f"Subscription {status}: {sub['name']}")
            return
    
    print(f"Subscription not found: {url}")


def scrape_all(mode: str = "update", start_date: Optional[str] = None, 
               headless: bool = True, dry_run: bool = False) -> None:
    """
    Scrape all enabled subscriptions sequentially.
    
    Args:
        mode: "initial" or "update"
        start_date: Override start date for initial scrape
        headless: Run browser in headless mode
        dry_run: Show what would be scraped without actually doing it
    """
    data = load_subscriptions()
    enabled_subs = [s for s in data["subscriptions"] if s.get("enabled", True)]
    
    if not enabled_subs:
        print("No enabled subscriptions to scrape.")
        return
    
    settings = data.get("settings", {})
    delay = settings.get("delay_between_substacks", 10)
    
    # Use provided start_date or fall back to settings or default
    if not start_date:
        start_date = settings.get("default_start_date")
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}Batch Scraping Started")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Start date: {start_date or 'Last 12 months'}")
    print(f"Subscriptions to scrape: {len(enabled_subs)}")
    print("=" * 60)
    
    if dry_run:
        print("\nWould scrape the following:")
        for i, sub in enumerate(enabled_subs, 1):
            print(f"{i}. {sub['name']} - {sub['url']}")
        return
    
    successful = []
    failed = []
    
    for i, sub in enumerate(enabled_subs, 1):
        print(f"\n[{i}/{len(enabled_subs)}] Scraping: {sub['name']}")
        print("-" * 40)
        
        try:
            if mode == "initial":
                # Check credentials if premium
                if sub.get("premium", False):
                    if EMAIL == "your-email@domain.com" or PASSWORD == "your-password":
                        print("✗ Skipping premium subscription - credentials not configured")
                        print("  Set SUBSTACK_EMAIL and SUBSTACK_PASSWORD in .env file")
                        failed.append(sub["name"])
                        continue
                
                success = initial_scrape(
                    url=sub["url"],
                    start_date=start_date,
                    premium=sub.get("premium", False),
                    headless=headless
                )
            else:  # update mode
                # Check credentials if premium
                if sub.get("premium", False):
                    if EMAIL == "your-email@domain.com" or PASSWORD == "your-password":
                        print("✗ Skipping premium subscription - credentials not configured")
                        print("  Set SUBSTACK_EMAIL and SUBSTACK_PASSWORD in .env file")
                        failed.append(sub["name"])
                        continue
                
                success = update_scrape(
                    url=sub["url"],
                    premium=sub.get("premium", False),
                    headless=headless
                )
            
            if success:
                successful.append(sub["name"])
                print(f"✓ Successfully scraped {sub['name']}")
            else:
                failed.append(sub["name"])
                print(f"✗ Failed to scrape {sub['name']}")
                
        except Exception as e:
            failed.append(sub["name"])
            print(f"✗ Error scraping {sub['name']}: {e}")
        
        # Add delay between substacks (except for the last one)
        if i < len(enabled_subs):
            print(f"\nWaiting {delay} seconds before next subscription...")
            sleep(delay)
    
    # Summary
    print("\n" + "=" * 60)
    print("Batch Scraping Complete")
    print("=" * 60)
    print(f"✓ Successful: {len(successful)} subscriptions")
    if successful:
        for name in successful:
            print(f"  • {name}")
    
    if failed:
        print(f"\n✗ Failed: {len(failed)} subscriptions")
        for name in failed:
            print(f"  • {name}")


def update_settings(key: str, value: str) -> None:
    """Update a setting in the subscriptions file."""
    data = load_subscriptions()
    
    if "settings" not in data:
        data["settings"] = {}
    
    # Parse value based on key
    if key == "delay_between_substacks":
        value = int(value)
    elif key == "auto_detect_premium":
        value = value.lower() in ['true', 'yes', '1']
    elif key == "default_start_date":
        # Validate date format
        if value != "null":
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format. Use YYYY-MM-DD or 'null'")
                return
        else:
            value = None
    
    data["settings"][key] = value
    save_subscriptions(data)
    print(f"Updated setting: {key} = {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch scraper for multiple Substack subscriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all subscriptions (update mode):
  python batch_scraper.py scrape
  
  # Initial scrape of all subscriptions:
  python batch_scraper.py scrape --initial
  
  # Initial scrape from specific date:
  python batch_scraper.py scrape --initial --start-date 2023-01-01
  
  # Dry run to see what would be scraped:
  python batch_scraper.py scrape --dry-run
  
  # List all subscriptions:
  python batch_scraper.py list
  
  # Add a new subscription:
  python batch_scraper.py add https://example.substack.com
  
  # Remove a subscription:
  python batch_scraper.py remove https://example.substack.com
  
  # Enable/disable a subscription:
  python batch_scraper.py toggle https://example.substack.com
  
  # Update settings:
  python batch_scraper.py set delay_between_substacks 15
  python batch_scraper.py set default_start_date 2024-01-01
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape all enabled subscriptions')
    scrape_parser.add_argument('--initial', action='store_true', help='Perform initial scrape instead of update')
    scrape_parser.add_argument('--start-date', help='Start date for initial scrape (YYYY-MM-DD)')
    scrape_parser.add_argument('--show-browser', action='store_true', help='Show browser window')
    scrape_parser.add_argument('--dry-run', action='store_true', help='Show what would be scraped without doing it')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all subscriptions')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new subscription')
    add_parser.add_argument('url', help='Substack URL to add')
    add_parser.add_argument('--name', help='Name for the subscription')
    add_parser.add_argument('--premium', action='store_true', help='Mark as premium subscription')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a subscription')
    remove_parser.add_argument('url', help='Substack URL to remove')
    
    # Toggle command
    toggle_parser = subparsers.add_parser('toggle', help='Enable/disable a subscription')
    toggle_parser.add_argument('url', help='Substack URL to toggle')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Update a setting')
    set_parser.add_argument('key', choices=['delay_between_substacks', 'default_start_date', 'auto_detect_premium'])
    set_parser.add_argument('value', help='New value for the setting')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'scrape':
        mode = 'initial' if args.initial else 'update'
        scrape_all(
            mode=mode,
            start_date=args.start_date,
            headless=not args.show_browser,
            dry_run=args.dry_run
        )
    
    elif args.command == 'list':
        list_subscriptions()
    
    elif args.command == 'add':
        add_subscription(args.url, args.name, args.premium)
    
    elif args.command == 'remove':
        remove_subscription(args.url)
    
    elif args.command == 'toggle':
        toggle_subscription(args.url)
    
    elif args.command == 'set':
        update_settings(args.key, args.value)


if __name__ == "__main__":
    main()