import tweepy
import logging
from datetime import datetime
import pytz
import time
from config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_BEARER_TOKEN
)
from database import TwitterDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitHandler:
    def __init__(self):
        self.reset_time = None
        self.remaining_calls = None

    def update(self, response):
        """Update rate limit info from response"""
        if response and hasattr(response, 'rate_limit'):
            self.reset_time = response.rate_limit.reset
            self.remaining_calls = response.rate_limit.remaining

    def handle_rate_limit(self):
        """Handle rate limit by sleeping if necessary"""
        if self.reset_time:
            current_time = datetime.now(pytz.UTC).timestamp()
            if current_time < self.reset_time:
                sleep_time = self.reset_time - current_time + 1
                logger.warning(
                    f"Rate limit reached. Waiting for {sleep_time:.0f} seconds. "
                    f"Reset time: {datetime.fromtimestamp(self.reset_time, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S GMT')}"
                )
                time.sleep(sleep_time)

class TwitterScraper:
    def __init__(self, db_name='twitter_metrics.db'):
        self.client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        self.db = TwitterDatabase(db_name)
        self.rate_limit_handler = RateLimitHandler()

    def get_user_id(self, username):
        """Get Twitter user ID from username"""
        try:
            response = self.client.get_user(username=username)
            self.rate_limit_handler.update(response)
            return response.data.id if response.data else None
        except tweepy.TooManyRequests as e:
            logger.warning(f"Rate limit exceeded while getting user ID: {e}")
            self.rate_limit_handler.handle_rate_limit()
            return self.get_user_id(username)  # Retry after waiting
        except tweepy.TweepyException as e:
            logger.error(f"Error getting user ID: {e}")
            raise

    def get_user_metrics(self, username):
        """Get user metrics including followers, engagement, etc."""
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                raise ValueError(f"User not found: {username}")

            # Get user profile information with rate limit handling
            try:
                user = self.client.get_user(
                    id=user_id,
                    user_fields=['public_metrics', 'created_at']
                )
                self.rate_limit_handler.update(user)
            except tweepy.TooManyRequests as e:
                logger.warning(f"Rate limit exceeded while getting user data: {e}")
                self.rate_limit_handler.handle_rate_limit()
                return self.get_user_metrics(username)  # Retry after waiting

            # Get recent tweets with rate limit handling
            try:
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=100,
                    tweet_fields=['public_metrics', 'created_at']
                )
                self.rate_limit_handler.update(tweets)
            except tweepy.TooManyRequests as e:
                logger.warning(f"Rate limit exceeded while getting tweets: {e}")
                self.rate_limit_handler.handle_rate_limit()
                return self.get_user_metrics(username)  # Retry after waiting

            # Calculate metrics
            metrics = self._calculate_metrics(user.data, tweets.data if tweets.data else [])
            
            # Add timestamp in GMT
            metrics['timestamp_gmt'] = datetime.now(pytz.UTC)
            
            # Save metrics to database
            self.db.save_metrics(username, metrics)
            
            # Save individual tweets
            if tweets.data:
                for tweet in tweets.data:
                    post_data = {
                        'tweet_id': tweet.id,
                        'content': tweet.text,
                        'created_at': tweet.created_at,
                        'likes': tweet.public_metrics['like_count'],
                        'retweets': tweet.public_metrics['retweet_count'],
                        'replies': tweet.public_metrics['reply_count']
                    }
                    self.db.save_post(username, post_data)

            return metrics

        except tweepy.TweepyException as e:
            if isinstance(e, tweepy.TooManyRequests):
                logger.warning(f"Rate limit exceeded: {e}")
                self.rate_limit_handler.handle_rate_limit()
                return self.get_user_metrics(username)  # Retry after waiting
            logger.error(f"Error fetching metrics: {e}")
            raise

    def _calculate_metrics(self, user_data, tweets):
        """Calculate engagement metrics from user data and tweets"""
        total_followers = user_data.public_metrics['followers_count']
        
        # Calculate engagement metrics from recent tweets
        total_impressions = 0
        total_engagements = 0
        total_reposts = 0
        link_clicks = 0  # Note: Link clicks require elevated access
        profile_visits = 0  # Note: Profile visits require elevated access
        
        for tweet in tweets:
            metrics = tweet.public_metrics
            impressions = metrics['impression_count'] if 'impression_count' in metrics else 0
            engagements = (
                metrics['like_count'] +
                metrics['retweet_count'] +
                metrics['reply_count'] +
                metrics['quote_count']
            )
            
            total_impressions += impressions
            total_engagements += engagements
            total_reposts += metrics['retweet_count']

        # Calculate engagement rate
        engagement_rate = (
            (total_engagements / len(tweets)) / total_followers * 100
        ) if tweets and total_followers > 0 else 0

        # Get mentions with rate limit handling
        mentions = self._get_mentions_count(user_data.username)

        # Follower growth (Note: This is approximate and would need historical data)
        follower_growth = 0  # This would need to be calculated from historical data

        return {
            'total_followers': total_followers,
            'follower_growth': follower_growth,
            'impressions': total_impressions,
            'engagement_rate': engagement_rate,
            'link_clicks': link_clicks,
            'profile_visits': profile_visits,
            'reposts': total_reposts,
            'mentions': mentions
        }

    def _get_mentions_count(self, username):
        """Get count of mentions for the user"""
        try:
            # Search for mentions in the last 7 days (free API limitation)
            query = f"@{username} -from:{username}"
            response = self.client.search_recent_tweets(
                query=query,
                max_results=100
            )
            self.rate_limit_handler.update(response)
            return len(response.data) if response.data else 0
        except tweepy.TooManyRequests as e:
            logger.warning(f"Rate limit exceeded while getting mentions: {e}")
            self.rate_limit_handler.handle_rate_limit()
            return self._get_mentions_count(username)  # Retry after waiting
        except tweepy.TweepyException as e:
            logger.error(f"Error getting mentions: {e}")
            return 0

    def scan_account(self, username):
        """Main method to scan a Twitter account"""
        try:
            logger.info(f"Starting scan for account: {username}")
            metrics = self.get_user_metrics(username)
            
            # Format timestamp for logging
            timestamp_str = metrics['timestamp_gmt'].strftime('%Y-%m-%d %H:%M:%S GMT')
            
            # Log metrics with timestamp
            logger.info(
                f"Scan completed for account: {username} at {timestamp_str}\n"
                f"Metrics: {{\n"
                f"  timestamp: {timestamp_str}\n"
                f"  total_followers: {metrics['total_followers']}\n"
                f"  follower_growth: {metrics['follower_growth']}\n"
                f"  impressions: {metrics['impressions']}\n"
                f"  engagement_rate: {metrics['engagement_rate']:.2f}%\n"
                f"  link_clicks: {metrics['link_clicks']}\n"
                f"  profile_visits: {metrics['profile_visits']}\n"
                f"  reposts: {metrics['reposts']}\n"
                f"  mentions: {metrics['mentions']}\n"
                f"}}"
            )
            
            return metrics
        except Exception as e:
            logger.error(f"Error scanning account {username}: {e}")
            raise