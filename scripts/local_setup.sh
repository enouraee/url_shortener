#!/bin/bash
# Local setup script for URL Shortener project
# This script automates the entire local environment setup

set -e  # Exit on any error

echo "============================================================"
echo "  URL SHORTENER - LOCAL SETUP"
echo "============================================================"

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo ""
    echo "⚠️  WARNING: No virtual environment detected!"
    echo "   Please activate your venv first:"
    echo "   - pyenv: pyenv activate Shorakka"
    echo "   - venv:  source venv/bin/activate"
    echo ""
    exit 1
fi

echo ""
echo "✓ Virtual environment active: $VIRTUAL_ENV"

# Step 1: Install dependencies
echo ""
echo "------------------------------------------------------------"
echo "  Step 1: Installing dependencies"
echo "------------------------------------------------------------"
pip install -r requirements.txt

# Step 2: Setup .env file
echo ""
echo "------------------------------------------------------------"
echo "  Step 2: Setting up .env file"
echo "------------------------------------------------------------"
if [ -f .env ]; then
    echo "✓ .env already exists (not overwriting)"
else
    echo "→ Copying sample.env to .env"
    cp sample.env .env
    echo "✓ Created .env from sample.env"
    echo "  ⚠️  Please review .env and update with your credentials"
fi

# Step 3: Run bootstrap check
echo ""
echo "------------------------------------------------------------"
echo "  Step 3: Running bootstrap verification"
echo "------------------------------------------------------------"
python scripts/bootstrap_check.py
BOOTSTRAP_EXIT=$?

if [ $BOOTSTRAP_EXIT -ne 0 ]; then
    echo ""
    echo "✗ Bootstrap check failed. Please fix issues above."
    exit 1
fi

# Step 4: Run migrations
echo ""
echo "------------------------------------------------------------"
echo "  Step 4: Running database migrations"
echo "------------------------------------------------------------"
echo "→ Applying migrations..."
alembic upgrade head

echo ""
echo "============================================================"
echo "  ✓ LOCAL SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Review your .env configuration"
echo "  2. Run the app: uvicorn app.main:app --reload"
echo "  3. Visit: http://localhost:8000/docs"
echo ""
