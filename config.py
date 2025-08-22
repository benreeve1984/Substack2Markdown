import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
EMAIL = os.getenv("SUBSTACK_EMAIL", "your-email@domain.com")
PASSWORD = os.getenv("SUBSTACK_PASSWORD", "your-password")

# Warn if credentials are not set
if EMAIL == "your-email@domain.com" or PASSWORD == "your-password":
    print("⚠️  Warning: Substack credentials not configured!")
    print("   Please set SUBSTACK_EMAIL and SUBSTACK_PASSWORD in your .env file")
    print("   Copy .env.example to .env and update with your credentials")