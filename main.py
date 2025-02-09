import asyncio
import logging
import argparse
from datetime import datetime
import pytz
import importlib.util
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_scraper(platform):
    """Dynamically import the scraper module for the specified platform"""
    try:
        if platform == 'twitter':
            from x.scraper import TwitterScraper
            return TwitterScraper
        elif platform == 'telegram':
            from telegram.scraper import TelegramScraper
            return TelegramScraper
        elif platform == 'discord':
            from discord.scraper import DiscordScraper
            return DiscordScraper
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    except ImportError as e:
        logger.error(f"Failed to import {platform} scraper: {e}")
        raise

async def scan_telegram(username):
    """Scan a Telegram channel"""
    TelegramScraper = import_scraper('telegram')
    scraper = TelegramScraper()
    try:
        await scraper.start()
        metrics = await scraper.scan_channel(username)
        return metrics
    finally:
        await scraper.stop()

async def scan_discord(guild_id):
    """Scan a Discord server"""
    DiscordScraper = import_scraper('discord')
    scraper = DiscordScraper()
    try:
        await scraper.start()
        metrics = await scraper.scan_server(guild_id)
        return metrics
    finally:
        await scraper.close()

def scan_twitter(username):
    """Scan a Twitter account"""
    TwitterScraper = import_scraper('twitter')
    scraper = TwitterScraper()
    try:
        metrics = scraper.scan_account(username)
        return metrics
    except Exception as e:
        logger.error(f"Error scanning Twitter account: {e}")
        raise

async def scan_all(identifiers):
    """Scan all platforms concurrently"""
    tasks = []
    results = {}

    if 'twitter' in identifiers:
        tasks.append(('twitter', asyncio.create_task(
            asyncio.to_thread(scan_twitter, identifiers['twitter'])
        )))
    
    if 'telegram' in identifiers:
        tasks.append(('telegram', asyncio.create_task(
            scan_telegram(identifiers['telegram'])
        )))
    
    if 'discord' in identifiers:
        tasks.append(('discord', asyncio.create_task(
            scan_discord(identifiers['discord'])
        )))

    for platform, task in tasks:
        try:
            results[platform] = await task
        except Exception as e:
            logger.error(f"Error scanning {platform}: {e}")
            results[platform] = None

    return results

async def main():
    parser = argparse.ArgumentParser(description='Social Media Metrics Scraper')
    parser.add_argument('--platform', choices=['twitter', 'telegram', 'discord', 'all'],
                      help='Platform to scrape (twitter, telegram, discord, or all)')
    parser.add_argument('--twitter', help='Twitter username')
    parser.add_argument('--telegram', help='Telegram channel username')
    parser.add_argument('--discord', help='Discord server ID')
    
    args = parser.parse_args()
    
    try:
        start_time = datetime.now(pytz.UTC)
        logger.info("Starting metrics collection")

        if args.platform == 'all':
            # Collect identifiers for all specified platforms
            identifiers = {}
            if args.twitter:
                identifiers['twitter'] = args.twitter
            if args.telegram:
                identifiers['telegram'] = args.telegram
            if args.discord:
                identifiers['discord'] = args.discord

            if not identifiers:
                raise ValueError("No platform identifiers provided for 'all' scan")

            results = await scan_all(identifiers)
            
            # Log results for each platform
            for platform, metrics in results.items():
                if metrics:
                    logger.info(f"{platform.capitalize()} metrics collected successfully")
                else:
                    logger.error(f"Failed to collect {platform} metrics")

        else:
            # Single platform scan
            if args.platform == 'twitter' and args.twitter:
                metrics = scan_twitter(args.twitter)
            elif args.platform == 'telegram' and args.telegram:
                metrics = await scan_telegram(args.telegram)
            elif args.platform == 'discord' and args.discord:
                metrics = await scan_discord(args.discord)
            else:
                raise ValueError(f"No identifier provided for platform: {args.platform}")

            logger.info(f"Metrics collected successfully for {args.platform}")
        
        end_time = datetime.now(pytz.UTC)
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())