# Substack2Markdown Usage Guide

## Getting Started

### 1. Configure Your Credentials (for premium content)

Create a `.env` file with your Substack credentials:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials:
SUBSTACK_EMAIL=your-email@example.com
SUBSTACK_PASSWORD=your-password
```

Note: The `.env` file is automatically ignored by git for security.

### 2. Your Subscriptions Are Already Configured

Your 5 Substack subscriptions have been added to `subscriptions.json`:
- Gary Marcus (https://garymarcus.substack.com/)
- Latent Space (https://www.latent.space/)
- Maria Sukhareva (https://msukhareva.substack.com/)
- Simon Willison (https://simonw.substack.com/)
- One Useful Thing (https://www.oneusefulthing.org/)

## Common Operations

### Scrape All Your Subscriptions

#### Initial Scrape (Last 12 Months)
```bash
# This will download all posts from the last 12 months
python batch_scraper.py scrape --initial
```

#### Update (Only New Posts)
```bash
# This will only download posts you don't already have
python batch_scraper.py scrape
```

### Scrape Individual Substacks

```bash
# Initial scrape of one substack
python scrape_manager.py initial https://garymarcus.substack.com

# Update one substack
python scrape_manager.py update https://garymarcus.substack.com
```

### Manage Subscriptions

```bash
# View all subscriptions
python batch_scraper.py list

# Add a new subscription
python batch_scraper.py add https://new.substack.com

# Temporarily disable a subscription
python batch_scraper.py toggle https://garymarcus.substack.com

# Remove a subscription
python batch_scraper.py remove https://old.substack.com
```

## Important Notes

1. **Polite Scraping**: The scraper automatically adds 2-5 second delays between posts and 10 seconds between different Substacks. This is intentional to be respectful to Substack's servers.

2. **Premium Content**: If any of your subscriptions are paid, mark them as premium in `subscriptions.json`:
   ```json
   {
     "url": "https://paid.substack.com/",
     "name": "Paid Newsletter",
     "premium": true,
     "enabled": true
   }
   ```

3. **Date Filtering**: By default, initial scrapes get the last 12 months. To get older posts:
   ```bash
   python batch_scraper.py scrape --initial --start-date 2020-01-01
   ```

4. **File Organization**: 
   - Markdown files: `substack_md_files/<newsletter-name>/`
   - HTML files: `substack_html_pages/<newsletter-name>/`
   - Browse all posts: Open `substack_html_pages/<newsletter-name>.html` in your browser

## Recommended Workflow

### First Time Setup
1. Run initial scrape to get last 12 months of all newsletters:
   ```bash
   python batch_scraper.py scrape --initial
   ```
   
2. This will take a while (5 newsletters × many posts × 2-5 seconds each)

### Regular Updates
Run this periodically (daily/weekly) to get new posts:
```bash
python batch_scraper.py scrape
```

This only downloads new posts, so it's much faster.

### Automation (Optional)
You can set up a cron job (Mac/Linux) or Task Scheduler (Windows) to run updates automatically:

```bash
# Example cron entry (runs daily at 2 AM)
0 2 * * * cd /path/to/Substack2Markdown && python batch_scraper.py scrape
```

## Troubleshooting

### If Scraping Fails
1. Check your internet connection
2. For premium content, verify your credentials in `config.py`
3. Try with `--show-browser` flag to see what's happening:
   ```bash
   python batch_scraper.py scrape --show-browser
   ```

### If You Get Blocked
1. The scraper is already very polite, but you can increase delays:
   ```bash
   python batch_scraper.py set delay_between_substacks 20
   ```
2. Try scraping one newsletter at a time instead of batch

### Missing Posts
- Some posts might be premium-only (need credentials)
- Very old posts might not be in the sitemap
- Some special content (podcasts, etc.) is filtered out

## Safety Reminder

- Only scrape content you have legitimate access to
- These tools are for personal archival of your paid subscriptions
- Be respectful of content creators' work