#!/usr/bin/env python3
"""Bootstrap verification script for URL Shortener project.

This script verifies that the development environment is properly configured:
1. Settings load correctly
2. FastAPI app imports successfully
3. Database connectivity works

Usage:
    python scripts/bootstrap_check.py
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_settings():
    """Verify settings load correctly."""
    print_section("1. Settings Configuration Check")
    try:
        from app.core.setting import settings
        
        print(f"✓ Settings loaded successfully")
        print(f"  - ENV_SETTING: {settings.ENV_SETTING.value}")
        print(f"  - DB_POOL_SIZE: {settings.DB_POOL_SIZE}")
        print(f"  - DB_MAX_OVERFLOW: {settings.DB_MAX_OVERFLOW}")
        print(f"  - DB_POOL_PRE_PING: {settings.DB_POOL_PRE_PING}")
        print(f"  - DB_POOL_RECYCLE: {settings.DB_POOL_RECYCLE}")
        print(f"  - DB_ECHO: {settings.DB_ECHO}")
        print(f"  - PG_DSN: {settings.PG_DSN[:30]}... (truncated)")
        return True
    except Exception as e:
        print(f"✗ Settings loading failed: {e}")
        return False


def check_app_import():
    """Verify FastAPI app imports successfully."""
    print_section("2. FastAPI App Import Check")
    try:
        from app.main import app
        
        print(f"✓ FastAPI app imported successfully")
        print(f"  - App type: {type(app).__name__}")
        print(f"  - Routes registered: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"✗ FastAPI app import failed: {e}")
        return False


async def check_database_connectivity_and_tables():
    """Verify database connectivity and table existence."""
    print_section("3. Database Connectivity Check")
    try:
        from app.db.session import engine
        from sqlalchemy import text
        
        print(f"→ Attempting to connect to database...")
        
        async with engine.connect() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print(f"✓ Database connectivity successful")
                print(f"  - Connection test: SELECT 1 returned {row[0]}")
                
                # Get database version
                version_result = await conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                print(f"  - PostgreSQL version: {version.split(',')[0]}")
                
                # Now check for tables
                print_section("4. Database Schema Check")
                required_tables = ["urls", "url_visits", "url_daily_stats"]
                
                print(f"→ Checking for required tables...")
                
                result = await conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))
                existing_tables = [row[0] for row in result.fetchall()]
                
                missing_tables = [t for t in required_tables if t not in existing_tables]
                
                if not missing_tables:
                    print(f"✓ All required tables exist")
                    for table in required_tables:
                        print(f"  - {table}")
                    return True, True
                else:
                    print(f"✗ Missing tables: {', '.join(missing_tables)}")
                    print(f"\nTo create tables, run:")
                    print(f"  alembic upgrade head")
                    return True, False
            else:
                print(f"✗ Database connectivity failed: unexpected result")
                return False, False
                
    except Exception as e:
        print(f"✗ Database connectivity failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Ensure PostgreSQL is running")
        print(f"  2. Verify database 'Shoraka' exists")
        print(f"  3. Check credentials in .env file")
        print(f"  4. Confirm password is URL-encoded in PG_DSN")
        return False, False


def main():
    """Run all bootstrap checks."""
    print("\n" + "="*60)
    print("  URL SHORTENER - BOOTSTRAP VERIFICATION")
    print("="*60)
    
    results = []
    
    # Check 1: Settings
    results.append(check_settings())
    
    # Check 2: App Import
    results.append(check_app_import())
    
    # Check 3 & 4: Database Connectivity and Tables (async, combined)
    db_check_result, tables_check_result = asyncio.run(check_database_connectivity_and_tables())
    results.append(db_check_result)
    results.append(tables_check_result)
    
    # Summary
    print_section("Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ All checks passed! Environment is ready.")
        print("  You can now run: uvicorn app.main:app --reload")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
