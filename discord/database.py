import sqlite3
from datetime import datetime
import logging
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordDatabase:
    def __init__(self, db_name='discord_metrics.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Create accounts table (servers in Discord context)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_id TEXT UNIQUE NOT NULL,
                        server_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create metrics table with explicit GMT timestamp
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        timestamp_gmt TIMESTAMP NOT NULL,
                        total_members INTEGER,
                        member_growth INTEGER,
                        online_members INTEGER,
                        total_messages INTEGER,
                        engagement_rate REAL,
                        active_channels INTEGER,
                        reactions_count INTEGER,
                        mentions_count INTEGER,
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    )
                ''')

                # Create messages table for storing individual messages
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        message_id TEXT UNIQUE,
                        channel_id TEXT NOT NULL,
                        content TEXT,
                        created_at_gmt TIMESTAMP NOT NULL,
                        reactions_count INTEGER,
                        replies_count INTEGER,
                        mentions_count INTEGER,
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    )
                ''')

                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def get_gmt_timestamp(self):
        """Get current timestamp in GMT"""
        return datetime.now(pytz.UTC)

    def add_account(self, server_id, server_name):
        """Add a new Discord server to track"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO accounts (server_id, server_name, created_at) VALUES (?, ?, ?)",
                    (server_id, server_name, self.get_gmt_timestamp())
                )
                conn.commit()
                return cursor.lastrowid or self.get_account_id(server_id)
        except sqlite3.Error as e:
            logger.error(f"Error adding account: {e}")
            raise

    def get_account_id(self, server_id):
        """Get account ID from server ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM accounts WHERE server_id = ?",
                    (server_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting account ID: {e}")
            raise

    def save_metrics(self, server_id, metrics_data):
        """Save metrics for a Discord server with GMT timestamp"""
        try:
            account_id = self.get_account_id(server_id)
            if not account_id:
                raise ValueError(f"Server not found: {server_id}")

            gmt_timestamp = self.get_gmt_timestamp()
            metrics_data['timestamp_gmt'] = gmt_timestamp

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO metrics (
                        account_id, timestamp_gmt, total_members, member_growth,
                        online_members, total_messages, engagement_rate,
                        active_channels, reactions_count, mentions_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    metrics_data['timestamp_gmt'],
                    metrics_data['total_members'],
                    metrics_data['member_growth'],
                    metrics_data['online_members'],
                    metrics_data['total_messages'],
                    metrics_data['engagement_rate'],
                    metrics_data['active_channels'],
                    metrics_data['reactions_count'],
                    metrics_data['mentions_count']
                ))
                conn.commit()
                logger.info(f"Metrics saved for server: {server_id} at {gmt_timestamp} GMT")
        except sqlite3.Error as e:
            logger.error(f"Error saving metrics: {e}")
            raise

    def save_message(self, server_id, message_data):
        """Save individual message data with GMT timestamp"""
        try:
            account_id = self.get_account_id(server_id)
            if not account_id:
                raise ValueError(f"Server not found: {server_id}")

            # Convert timestamp to GMT if it's not already
            if isinstance(message_data['created_at'], str):
                created_at = datetime.fromisoformat(message_data['created_at'].replace('Z', '+00:00'))
            else:
                created_at = message_data['created_at']
            
            if created_at.tzinfo is None:
                created_at = pytz.UTC.localize(created_at)

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO messages (
                        account_id, message_id, channel_id, content, created_at_gmt,
                        reactions_count, replies_count, mentions_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    message_data['message_id'],
                    message_data['channel_id'],
                    message_data['content'],
                    created_at,
                    message_data['reactions_count'],
                    message_data['replies_count'],
                    message_data['mentions_count']
                ))
                conn.commit()
                logger.info(f"Message saved for server: {server_id} at {created_at} GMT")
        except sqlite3.Error as e:
            logger.error(f"Error saving message: {e}")
            raise