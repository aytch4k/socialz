import logging
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import FloodWaitError, ChatAdminRequiredError
import asyncio
import time
from telegram.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    TELEGRAM_SESSION_NAME
)
from telegram.database import TelegramDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitHandler:
    def __init__(self):
        self.reset_time = None
        self.wait_seconds = 0

    async def handle_rate_limit(self, error):
        """Handle rate limit by sleeping if necessary"""
        if isinstance(error, FloodWaitError):
            self.wait_seconds = error.seconds
            logger.warning(f"Rate limit reached. Waiting for {self.wait_seconds} seconds.")
            await asyncio.sleep(self.wait_seconds)
            return True
        return False

class TelegramScraper:
    def __init__(self, db_name='telegram_metrics.db'):
        if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE]):
            raise ValueError("Telegram credentials not properly configured")
        
        self.client = TelegramClient(
            TELEGRAM_SESSION_NAME,
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH
        )
        self.db = TelegramDatabase(db_name)
        self.rate_limit_handler = RateLimitHandler()

    async def start(self):
        """Start the Telegram client"""
        await self.client.start(phone=TELEGRAM_PHONE)
        logger.info("Telegram client started successfully")

    async def stop(self):
        """Stop the Telegram client"""
        await self.client.disconnect()
        logger.info("Telegram client disconnected")

    async def get_channel_info(self, username):
        """Get channel information and subscriber count"""
        try:
            entity = await self.client.get_entity(username)
            full_channel = await self.client.get_full_channel(entity)
            return entity, full_channel
        except FloodWaitError as e:
            await self.rate_limit_handler.handle_rate_limit(e)
            return await self.get_channel_info(username)
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            raise

    async def get_recent_messages(self, channel, limit=100):
        """Get recent messages from the channel"""
        messages = []
        try:
            async for message in self.client.iter_messages(channel, limit=limit):
                if message and not message.deleted:
                    messages.append(message)
        except FloodWaitError as e:
            await self.rate_limit_handler.handle_rate_limit(e)
            return await self.get_recent_messages(channel, limit)
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise
        return messages

    async def get_mention_count(self, username, days=7):
        """Get number of mentions for the channel in the last X days"""
        mention_count = 0
        try:
            search_query = f'@{username}'
            async for message in self.client.iter_messages(
                None,  # Search across all accessible chats
                search=search_query,
                date=datetime.now(pytz.UTC) - timedelta(days=days)
            ):
                mention_count += 1
        except FloodWaitError as e:
            await self.rate_limit_handler.handle_rate_limit(e)
            return await self.get_mention_count(username, days)
        except Exception as e:
            logger.error(f"Error getting mentions: {e}")
            return 0
        return mention_count

    def _calculate_metrics(self, channel, full_channel, messages):
        """Calculate engagement metrics from channel data and messages"""
        total_subscribers = full_channel.full_chat.participants_count
        total_views = sum(msg.views for msg in messages if msg.views)
        total_forwards = sum(msg.forwards for msg in messages if msg.forwards)
        
        # Calculate engagement rate based on average views per post
        avg_views_per_post = total_views / len(messages) if messages else 0
        engagement_rate = (avg_views_per_post / total_subscribers * 100) if total_subscribers > 0 else 0
        
        # Calculate post reach (average views of last 10 posts)
        recent_posts = messages[:10]
        post_reach = sum(msg.views for msg in recent_posts if msg.views) / len(recent_posts) if recent_posts else 0

        return {
            'total_subscribers': total_subscribers,
            'subscriber_growth': 0,  # Would need historical data
            'total_views': total_views,
            'engagement_rate': engagement_rate,
            'forwards': total_forwards,
            'mentions': 0,  # Will be updated by scan_channel
            'post_reach': post_reach
        }

    async def scan_channel(self, username):
        """Main method to scan a Telegram channel"""
        try:
            logger.info(f"Starting scan for channel: {username}")
            
            # Get channel information
            channel, full_channel = await self.get_channel_info(username)
            
            # Get recent messages
            messages = await self.get_recent_messages(channel)
            
            # Calculate basic metrics
            metrics = self._calculate_metrics(channel, full_channel, messages)
            
            # Get mention count
            metrics['mentions'] = await self.get_mention_count(username)
            
            # Save metrics to database
            self.db.save_metrics(username, metrics)
            
            # Save individual messages
            for message in messages:
                post_data = {
                    'message_id': str(message.id),
                    'content': message.text if message.text else '',
                    'created_at': message.date,
                    'views': message.views if message.views else 0,
                    'forwards': message.forwards if message.forwards else 0,
                    'replies': message.replies.replies if message.replies else 0
                }
                self.db.save_post(username, post_data)
            
            # Format timestamp for logging
            timestamp_str = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S GMT')
            
            # Log metrics
            logger.info(
                f"Scan completed for channel: {username} at {timestamp_str}\n"
                f"Metrics: {{\n"
                f"  timestamp: {timestamp_str}\n"
                f"  total_subscribers: {metrics['total_subscribers']}\n"
                f"  subscriber_growth: {metrics['subscriber_growth']}\n"
                f"  total_views: {metrics['total_views']}\n"
                f"  engagement_rate: {metrics['engagement_rate']:.2f}%\n"
                f"  forwards: {metrics['forwards']}\n"
                f"  mentions: {metrics['mentions']}\n"
                f"  post_reach: {metrics['post_reach']}\n"
                f"}}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error scanning channel {username}: {e}")
            raise

async def main(username):
    scraper = TelegramScraper()
    try:
        await scraper.start()
        await scraper.scan_channel(username)
    finally:
        await scraper.stop()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scraper.py <channel_username>")
        sys.exit(1)
    
    channel_username = sys.argv[1]
    asyncio.run(main(channel_username))