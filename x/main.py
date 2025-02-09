import schedule
import time
import logging
import sys
from scraper import TwitterScraper
from config import DATABASE_NAME

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_username(username):
    """Remove @ symbol and clean username"""
    return username.replace('@', '').strip()

def scan_accounts(accounts):
    """Scan multiple Twitter accounts"""
    scraper = TwitterScraper(DATABASE_NAME)
    for account in accounts:
        try:
            clean_account = clean_username(account)
            logger.info(f"Scanning account: {clean_account}")
            metrics = scraper.scan_account(clean_account)
            logger.info(f"Metrics for {clean_account}: {metrics}")
        except Exception as e:
            logger.error(f"Error scanning account {clean_account}: {e}")

def main():
    if len(sys.argv) < 2:
        logger.error("Please provide at least one Twitter username")
        print("Usage: python main.py username1 [username2 ...]")
        print("Note: Usernames can be with or without @ symbol")
        sys.exit(1)

    accounts = sys.argv[1:]
    
    # Initial scan
    scan_accounts(accounts)
    
    # Schedule scans every 6 hours
    schedule.every(6).hours.do(scan_accounts, accounts)
    
    logger.info("Scraper scheduled. Running continuously...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check schedule every minute
        except KeyboardInterrupt:
            logger.info("Scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying on error

if __name__ == "__main__":
    main()