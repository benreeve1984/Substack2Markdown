# Substack Scraper Authentication Guide

## Overview
The enhanced Substack scraper now supports multiple authentication methods to avoid login lockouts and improve reliability.

## Authentication Methods

### 1. Cookie-Based Authentication (Default)
The scraper automatically saves cookies after successful login and reuses them for subsequent runs.

**Benefits:**
- Avoids repeated logins that can trigger account lockouts
- Faster startup (no login delay)
- Maintains session across multiple scraping runs

**Usage:**
```bash
# First run - will login and save cookies
python substack_scraper_enhanced.py -p -u https://example.substack.com

# Subsequent runs - will reuse saved cookies
python substack_scraper_enhanced.py -p -u https://example.substack.com
```

**Cookie File:**
- Default location: `substack_cookies.pkl`
- Custom location: Use `--cookies-file /path/to/cookies.pkl`

**Disable cookie usage:**
```bash
python substack_scraper_enhanced.py -p -u https://example.substack.com --no-cookies
```

### 2. Using Existing Chrome Profile
Use your existing Chrome browser profile where you're already logged into Substack.

**Benefits:**
- No need to login via script
- Uses your actual browser session
- Avoids automation detection

**Find your Chrome profile path:**
- **macOS**: `~/Library/Application Support/Google/Chrome`
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data`
- **Linux**: `~/.config/google-chrome`

**Usage:**
```bash
# macOS example
python substack_scraper_enhanced.py -p -u https://example.substack.com \
  --user-data-dir "~/Library/Application Support/Google/Chrome"

# Windows example
python substack_scraper_enhanced.py -p -u https://example.substack.com \
  --user-data-dir "%LOCALAPPDATA%\Google\Chrome\User Data"
```

**Important:** Close Chrome before running the scraper with `--user-data-dir` to avoid conflicts.

### 3. Manual Cookie Export (Alternative Method)
If automated login fails, you can manually export cookies from your browser.

**Steps:**
1. Login to Substack in your regular browser
2. Use a browser extension to export cookies (e.g., "EditThisCookie" for Chrome)
3. Save the cookies in the appropriate format
4. Place the cookie file in the script directory

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--no-cookies` | Disable cookie-based auth (force fresh login) | False |
| `--cookies-file PATH` | Path to cookies file | `substack_cookies.pkl` |
| `--user-data-dir PATH` | Chrome user data directory path | None |

## Troubleshooting

### Session Expired
If you see "Session expired, logging in again...", the scraper will automatically:
1. Perform a fresh login
2. Save new cookies for future use

### Account Lockout
If you're locked out due to too many login attempts:
1. Wait for the lockout period to expire (usually 24 hours)
2. Use the `--user-data-dir` option with your existing Chrome profile
3. Or manually login in Chrome and use the same profile

### Cookie Loading Failed
If cookies fail to load:
1. Delete the old cookie file: `rm substack_cookies.pkl`
2. Run the scraper again to create fresh cookies

### Chrome Profile Conflicts
If you get "Chrome is already running" error:
1. Close all Chrome windows
2. Or create a separate Chrome profile for scraping

## Best Practices

1. **First-time setup**: Run without `--headless` to handle any CAPTCHA or 2FA
2. **Regular use**: Let the scraper use saved cookies (default behavior)
3. **Multiple subscriptions**: Use different cookie files for different accounts:
   ```bash
   --cookies-file account1_cookies.pkl
   --cookies-file account2_cookies.pkl
   ```
4. **Avoid detection**: Use `--user-data-dir` with your regular Chrome profile

## Security Notes

- Cookie files contain sensitive session data
- Keep `substack_cookies.pkl` secure and don't share it
- Add `*.pkl` to `.gitignore` to avoid accidentally committing cookies
- Cookies expire after some time and will need refresh

## Example Workflows

### Setup and Initial Scrape
```bash
# Initial login (interactive, to handle CAPTCHA/2FA)
python substack_scraper_enhanced.py -p -u https://example.substack.com

# Future runs (automatic, uses saved cookies)
python substack_scraper_enhanced.py -p -u https://example.substack.com --update
```

### Using Existing Browser Session
```bash
# Make sure you're logged into Substack in Chrome first
# Then close Chrome and run:
python substack_scraper_enhanced.py -p -u https://example.substack.com \
  --user-data-dir "~/Library/Application Support/Google/Chrome" \
  --update
```

### Headless Scraping After Setup
```bash
# Once cookies are saved, you can run headless
python substack_scraper_enhanced.py -p -u https://example.substack.com \
  --headless --update
```