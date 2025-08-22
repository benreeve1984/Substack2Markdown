#!/bin/bash

echo "Substack2Markdown Setup"
echo "========================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Substack credentials:"
    echo "   SUBSTACK_EMAIL=your-email@example.com"
    echo "   SUBSTACK_PASSWORD=your-password"
else
    echo "✓ .env file already exists"
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Failed to install dependencies"
    echo "  Try running: pip install -r requirements.txt"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Substack credentials (if you haven't already)"
echo "2. Review your subscriptions: python batch_scraper.py list"
echo "3. Run initial scrape: python batch_scraper.py scrape --initial"
echo ""
echo "For more information, see USAGE_GUIDE.md"