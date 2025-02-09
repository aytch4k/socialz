import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
import pytz
import asyncio
from discord.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_APPLICATION_ID
)
from discord.database import DiscordDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordScraper(commands.Bot):
    def __init__(self, db_name='discord_metrics.db'):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=DISCORD_APPLICATION_ID
        )
        
        self.db = DiscordDatabase(db_name)
        self.scanning = False

    async def setup_hook(self):
        """Setup hook for the bot"""
        logger.info("Bot is setting up...")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def get_channel_messages(self, channel, limit=100):
        """Get recent messages from a channel"""
        messages = []
        try:
            async for message in channel.history(limit=limit):
                messages.append(message)
        except discord.errors.Forbidden:
            logger.warning(f"No access to channel history in {channel.name}")
        except Exception as e:
            logger.error(f"Error getting messages from {channel.name}: {e}")
        return messages

    async def get_mention_count(self, guild, member, days=7):
        """Get number of mentions for a member in the last X days"""
        mention_count = 0
        after_date = datetime.now(pytz.UTC) - timedelta(days=days)
        
        for channel in guild.text_channels:
            try:
                async for message in channel.history(after=after_date):
                    if member in message.mentions:
                        mention_count += 1
            except discord.errors.Forbidden:
                continue
            except Exception as e:
                logger.error(f"Error getting mentions from {channel.name}: {e}")
                
        return mention_count

    def _calculate_metrics(self, guild, messages):
        """Calculate engagement metrics from guild data and messages"""
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        
        # Calculate message engagement
        total_reactions = sum(len(msg.reactions) for msg in messages)
        total_messages = len(messages)
        
        # Calculate active channels (channels with messages in the last day)
        active_channels = len(set(msg.channel.id for msg in messages 
                               if msg.created_at > datetime.now(pytz.UTC) - timedelta(days=1)))
        
        # Calculate engagement rate based on message participation
        engagement_rate = (total_messages / total_members * 100) if total_members > 0 else 0
        
        return {
            'total_members': total_members,
            'member_growth': 0,  # Would need historical data
            'online_members': online_members,
            'total_messages': total_messages,
            'engagement_rate': engagement_rate,
            'active_channels': active_channels,
            'reactions_count': total_reactions,
            'mentions_count': 0  # Will be updated in scan_server
        }

    async def scan_server(self, guild_id):
        """Main method to scan a Discord server"""
        if self.scanning:
            logger.warning("A scan is already in progress")
            return
        
        self.scanning = True
        try:
            guild = self.get_guild(int(guild_id))
            if not guild:
                raise ValueError(f"Server not found: {guild_id}")
            
            logger.info(f"Starting scan for server: {guild.name}")
            
            # Collect messages from all accessible text channels
            all_messages = []
            for channel in guild.text_channels:
                try:
                    messages = await self.get_channel_messages(channel)
                    all_messages.extend(messages)
                except Exception as e:
                    logger.error(f"Error collecting messages from {channel.name}: {e}")
                    continue
            
            # Calculate basic metrics
            metrics = self._calculate_metrics(guild, all_messages)
            
            # Get mention count for the server (mentions of server members)
            total_mentions = 0
            for member in guild.members:
                try:
                    mentions = await self.get_mention_count(guild, member)
                    total_mentions += mentions
                except Exception as e:
                    logger.error(f"Error getting mentions for {member.name}: {e}")
            
            metrics['mentions_count'] = total_mentions
            
            # Save metrics to database
            self.db.save_metrics(str(guild.id), metrics)
            
            # Save individual messages
            for message in all_messages:
                try:
                    message_data = {
                        'message_id': str(message.id),
                        'channel_id': str(message.channel.id),
                        'content': message.content,
                        'created_at': message.created_at,
                        'reactions_count': len(message.reactions),
                        'replies_count': len([m for m in all_messages if m.reference and m.reference.message_id == message.id]),
                        'mentions_count': len(message.mentions)
                    }
                    self.db.save_message(str(guild.id), message_data)
                except Exception as e:
                    logger.error(f"Error saving message {message.id}: {e}")
            
            # Format timestamp for logging
            timestamp_str = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S GMT')
            
            # Log metrics
            logger.info(
                f"Scan completed for server: {guild.name} at {timestamp_str}\n"
                f"Metrics: {{\n"
                f"  timestamp: {timestamp_str}\n"
                f"  total_members: {metrics['total_members']}\n"
                f"  member_growth: {metrics['member_growth']}\n"
                f"  online_members: {metrics['online_members']}\n"
                f"  total_messages: {metrics['total_messages']}\n"
                f"  engagement_rate: {metrics['engagement_rate']:.2f}%\n"
                f"  active_channels: {metrics['active_channels']}\n"
                f"  reactions_count: {metrics['reactions_count']}\n"
                f"  mentions_count: {metrics['mentions_count']}\n"
                f"}}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error scanning server {guild_id}: {e}")
            raise
        finally:
            self.scanning = False

async def main(guild_id):
    scraper = DiscordScraper()
    try:
        await scraper.start(DISCORD_BOT_TOKEN)
        await scraper.scan_server(guild_id)
    finally:
        await scraper.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scraper.py <guild_id>")
        sys.exit(1)
    
    guild_id = sys.argv[1]
    asyncio.run(main(guild_id))