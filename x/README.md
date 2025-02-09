# Twitter Account Metrics Scraper

A robust Python-based Twitter account metrics scraper that collects and stores comprehensive analytics data for specified Twitter accounts. This tool is designed for tracking engagement metrics, follower growth, and other key performance indicators over time.

## Features

- **Comprehensive Metrics Collection:**
  - Total followers
  - Follower growth
  - Tweet impressions
  - Engagement rates
  - Link clicks
  - Profile visits
  - Reposts
  - Mentions

- **Data Management:**
  - SQLite3 database storage
  - GMT timestamp tracking
  - Historical data retention
  - Relationship tracking between accounts and posts

- **Robust Implementation:**
  - Automatic rate limit handling
  - Error recovery
  - Scheduled scanning (every 6 hours)
  - Detailed logging

## Prerequisites

- Python 3.9+
- Twitter Developer Account with API credentials
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd twitter-metrics-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your Twitter API credentials:
```bash
cp .env.template .env
```

4. Edit `.env` file with your Twitter API credentials:
```
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

## Getting Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign in and create a new project/app
3. Navigate to "Keys and Tokens"
4. Generate the required credentials:
   - API Key and Secret
   - Access Token and Secret
   - Bearer Token

## Usage

### Basic Usage

Run the scraper for one or more Twitter accounts:
```bash
python main.py username1 [username2 username3 ...]
```

Example:
```bash
python main.py Autheo_Network
```

### Output

The scraper provides real-time console output:
```
Scan completed for account: username at 2025-02-08 20:27:00 GMT
Metrics: {
  timestamp: 2025-02-08 20:27:00 GMT
  total_followers: 447
  follower_growth: 0
  impressions: 18143
  engagement_rate: 2.94%
  link_clicks: 0
  profile_visits: 0
  reposts: 258
  mentions: 100
}
```

### Database Structure

The SQLite database (`twitter_metrics.db`) contains three main tables:

1. **accounts**
   - Account information
   - Creation timestamp

2. **metrics**
   - All collected metrics
   - GMT timestamps
   - Relationship to accounts

3. **posts**
   - Individual tweet data
   - Engagement metrics
   - GMT timestamps

## Rate Limits

The scraper handles Twitter API rate limits automatically:
- Tracks remaining API calls
- Calculates wait times
- Provides clear waiting messages
- Automatically retries after limits reset

When rate limits are hit, you'll see:
```
WARNING: Rate limit reached. Waiting for X seconds. Reset time: YYYY-MM-DD HH:MM:SS GMT
```

## Error Handling

The scraper includes comprehensive error handling for:
- Network issues
- API rate limits
- Authentication errors
- Invalid usernames
- Database errors

All errors are logged to both console and `twitter_scraper.log`.

## Scheduling

By default, the scraper:
- Runs immediately for specified accounts
- Continues running in the background
- Rescans accounts every 6 hours
- Maintains continuous operation with error recovery

## Logging

Detailed logs are written to `twitter_scraper.log`, including:
- Scan operations
- Collected metrics
- Error messages
- Rate limit information
- Database operations

## Database Queries

Example SQL queries for data analysis:

```sql
-- Get latest metrics for an account
SELECT * FROM metrics 
WHERE account_id = (SELECT id FROM accounts WHERE username = 'username')
ORDER BY timestamp_gmt DESC LIMIT 1;

-- Get follower growth over time
SELECT 
    timestamp_gmt,
    total_followers
FROM metrics
WHERE account_id = (SELECT id FROM accounts WHERE username = 'username')
ORDER BY timestamp_gmt;
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU GPL v3.0 - see the LICENSE file for details.

## Disclaimer

This tool is intended for legitimate use cases only. Please ensure you comply with Twitter's Terms of Service and API usage guidelines.
