import sqlite3
from datetime import datetime
import logging
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Create accounts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create metrics table with explicit GMT timestamp
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        timestamp_gmt TIMESTAMP NOT NULL,
                        total_followers INTEGER,
                        follower_growth INTEGER,
                        impressions INTEGER,
                        engagement_rate REAL,
                        link_clicks INTEGER,
                        profile_visits INTEGER,
                        reposts INTEGER,
                        mentions INTEGER,
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    )
                ''')

                # Create posts table for storing individual tweets
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        tweet_id TEXT UNIQUE,
                        content TEXT,
                        created_at_gmt TIMESTAMP NOT NULL,
                        likes INTEGER,
                        retweets INTEGER,
                        replies INTEGER,
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

    def add_account(self, username):
        """Add a new account to track"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO accounts (username, created_at) VALUES (?, ?)",
                    (username, self.get_gmt_timestamp())
                )
                conn.commit()
                return cursor.lastrowid or self.get_account_id(username)
        except sqlite3.Error as e:
            logger.error(f"Error adding account: {e}")
            raise

    def get_account_id(self, username):
        """Get account ID from username"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM accounts WHERE username = ?",
                    (username,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting account ID: {e}")
            raise

    def save_metrics(self, username, metrics_data):
        """Save metrics for an account with GMT timestamp"""
        try:
            account_id = self.get_account_id(username)
            if not account_id:
                account_id = self.add_account(username)

            gmt_timestamp = self.get_gmt_timestamp()
            metrics_data['timestamp_gmt'] = gmt_timestamp

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO metrics (
                        account_id, timestamp_gmt, total_followers, follower_growth,
                        impressions, engagement_rate, link_clicks,
                        profile_visits, reposts, mentions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    metrics_data['timestamp_gmt'],
                    metrics_data['total_followers'],
                    metrics_data['follower_growth'],
                    metrics_data['impressions'],
                    metrics_data['engagement_rate'],
                    metrics_data['link_clicks'],
                    metrics_data['profile_visits'],
                    metrics_data['reposts'],
                    metrics_data['mentions']
                ))
                conn.commit()
                logger.info(f"Metrics saved for account: {username} at {gmt_timestamp} GMT")
        except sqlite3.Error as e:
            logger.error(f"Error saving metrics: {e}")
            raise

    def save_post(self, username, post_data):
        """Save individual post data with GMT timestamp"""
        try:
            account_id = self.get_account_id(username)
            if not account_id:
                account_id = self.add_account(username)

            # Convert timestamp to GMT if it's not already
            if isinstance(post_data['created_at'], str):
                created_at = datetime.fromisoformat(post_data['created_at'].replace('Z', '+00:00'))
            else:
                created_at = post_data['created_at']
            
            if created_at.tzinfo is None:
                created_at = pytz.UTC.localize(created_at)

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO posts (
                        account_id, tweet_id, content, created_at_gmt,
                        likes, retweets, replies
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    post_data['tweet_id'],
                    post_data['content'],
                    created_at,
                    post_data['likes'],
                    post_data['retweets'],
                    post_data['replies']
                ))
                conn.commit()
                logger.info(f"Post saved for account: {username} at {created_at} GMT")
        except sqlite3.Error as e:
            logger.error(f"Error saving post: {e}")
            raise