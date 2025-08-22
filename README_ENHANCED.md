# Substack2Markdown - Enhanced Version

This enhanced version adds polite scraping features, date-based filtering, and incremental update capabilities to safely scrape your paid Substack subscriptions.

## New Features

### 🎯 Core Enhancements
- **Date-based filtering**: Scrape posts from a specific date onwards (e.g., last 12 months)
- **Incremental updates**: Only download new posts not already in your collection
- **Polite scraping**: Built-in rate limiting and random delays to avoid detection
- **User-agent rotation**: Randomly rotates user agents to appear more natural
- **Metadata tracking**: Keeps track of what's been scraped and when
- **Improved error handling**: Gracefully handles failures and continues scraping

### 🛡️ Anti-Detection Features
- Random delays between requests (2-5 seconds by default)
- Rotating user-agent strings
- Proper HTTP headers that mimic real browser behavior
- Respects robots.txt implicitly through polite delays
- No parallel requests - all scraping is sequential

## Batch Scraping Multiple Subscriptions

### Managing Your Subscriptions

All your Substack subscriptions are stored in `subscriptions.json`. You can manage them using the `batch_scraper.py` tool:

```bash
# List all subscriptions
python batch_scraper.py list

# Add a new subscription
python batch_scraper.py add https://example.substack.com
python batch_scraper.py add https://paid.substack.com --premium

# Remove a subscription
python batch_scraper.py remove https://example.substack.com

# Enable/disable a subscription without removing it
python batch_scraper.py toggle https://example.substack.com
```

### Scraping All Subscriptions

```bash
# Update all subscriptions (only new posts)
python batch_scraper.py scrape

# Initial scrape of all subscriptions (last 12 months)
python batch_scraper.py scrape --initial

# Initial scrape from specific date
python batch_scraper.py scrape --initial --start-date 2023-01-01

# Dry run to see what would be scraped
python batch_scraper.py scrape --dry-run

# Show browser window (for debugging)
python batch_scraper.py scrape --show-browser
```

### Configuration

Edit `subscriptions.json` to manage your subscriptions and settings:

```json
{
  "subscriptions": [
    {
      "url": "https://example.substack.com/",
      "name": "Example Newsletter",
      "premium": false,
      "enabled": true
    }
  ],
  "settings": {
    "default_start_date": null,  // null = last 12 months
    "delay_between_substacks": 10  // seconds between each substack
  }
}
```

You can also update settings via command line:

```bash
# Set delay between substacks
python batch_scraper.py set delay_between_substacks 15

# Set default start date
python batch_scraper.py set default_start_date 2024-01-01
```

## Quick Start

### 1. Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your credentials (for premium content)
cp .env.example .env
# Edit .env and update:
# SUBSTACK_EMAIL=your-email@example.com
# SUBSTACK_PASSWORD=your-password
```

### 2. Easy Scraping with scrape_manager.py

The easiest way to use the enhanced scraper:

```bash
# Initial scrape - last 12 months of posts (default)
python scrape_manager.py initial https://example.substack.com

# Initial scrape - from specific date
python scrape_manager.py initial https://example.substack.com --start-date 2023-01-01

# Update - only download new posts
python scrape_manager.py update https://example.substack.com

# List all scraped Substacks
python scrape_manager.py list

# Scrape free content only (no login required)
python scrape_manager.py initial https://example.substack.com --free
```

### 3. Direct Usage with Enhanced Scraper

For more control, use the enhanced scraper directly:

```bash
# Scrape posts from last 12 months
python substack_scraper_enhanced.py -u https://example.substack.com --premium --start-date 2024-01-01

# Update mode - only new posts
python substack_scraper_enhanced.py -u https://example.substack.com --premium --update

# Scrape specific number of recent posts
python substack_scraper_enhanced.py -u https://example.substack.com --premium -n 10

# Combine date filter with update mode
python substack_scraper_enhanced.py -u https://example.substack.com --premium --start-date 2024-01-01 --update
```

## Command Line Options

### scrape_manager.py Commands

```
initial <url>     Perform initial scrape
  --start-date    Start date (YYYY-MM-DD), default: 12 months ago
  --free          Only scrape free content
  --num-posts     Number of posts to scrape (0 for all)
  --show-browser  Show browser window (for debugging)

update <url>      Scrape only new posts
  --free          Only scrape free content
  --show-browser  Show browser window (for debugging)

list              List all scraped Substacks
```

### substack_scraper_enhanced.py Options

```
-u, --url         Substack URL to scrape
-p, --premium     Use premium scraper (for paid content)
--start-date      Only scrape posts from this date (YYYY-MM-DD)
--update          Only scrape new posts not already downloaded
-n, --number      Number of posts to scrape (0 for all)
--headless        Run browser in headless mode
--edge-path       Path to Edge browser executable
--edge-driver-path Path to Edge WebDriver executable
```

## Polite Scraping Details

The enhanced scraper implements several measures to be respectful to Substack's servers:

1. **Rate Limiting**: 2-5 second random delay between each request
2. **User Agent Rotation**: Randomly selects from a pool of real browser user agents
3. **Sequential Processing**: No parallel requests, one post at a time
4. **Intelligent Caching**: Checks for existing files before downloading
5. **Metadata Tracking**: Maintains a record of what's been scraped

## File Organization

```
substack_md_files/
├── newsletter-name/
│   ├── post-1.md
│   ├── post-2.md
│   └── ...

substack_html_pages/
├── newsletter-name/
│   ├── post-1.html
│   ├── post-2.html
│   └── ...
└── newsletter-name.html  (Index page)

data/
├── newsletter-name.json  (Essay data for index)
└── newsletter-name_metadata.json  (Scraping metadata)
```

## Safety Tips

1. **Use Your Own Subscriptions**: Only scrape content you have paid for
2. **Respect Rate Limits**: Don't modify the delay settings to be too aggressive
3. **Monitor Your Scraping**: Use `--show-browser` flag if you encounter issues
4. **Keep Credentials Secure**: Never commit your config.py with real credentials
5. **Be Patient**: The scraper is intentionally slow to be respectful

## Troubleshooting

### Login Issues
- Make sure your credentials in `config.py` are correct
- Try running without `--headless` to see if there's a captcha
- Check if your account requires 2FA

### Missing Posts
- Premium posts require the `--premium` flag and valid credentials
- Check the date filter if using `--start-date`
- Some posts might be excluded (podcasts, about pages, etc.)

### Performance
- The scraper is intentionally slow (2-5 seconds per post)
- This is by design to avoid detection and be respectful
- For faster scraping of free content, you can modify delay settings (not recommended)

## Original vs Enhanced

The enhanced version (`substack_scraper_enhanced.py`) includes all features from the original plus:
- Date filtering
- Update mode
- Polite scraping
- Better error handling
- Metadata tracking

The original scraper (`substack_scraper.py`) is still available if you prefer the simpler version.

## License

Same as original - see LICENSE file.