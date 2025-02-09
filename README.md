# Social Media Metrics Scraper

A comprehensive tool for collecting metrics from Twitter, Telegram, and Discord. Each platform operates independently with its own configuration and can be used separately or together through the main orchestrator.

## Features

### Twitter (X) Metrics
- Follower count and growth
- Engagement rates
- Impression counts
- Mention tracking
- Individual tweet performance

### Telegram Metrics
- Subscriber count and growth
- Message views and forwards
- Channel engagement rates
- Mention tracking
- Individual post performance

### Discord Metrics
- Member count and growth
- Message engagement
- Active channels
- Reaction tracking
- Server activity metrics

## Platform Setup

Each platform can be set up and used independently:

### Twitter Setup
1. Navigate to the Twitter directory:
```bash
cd x
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.template` to `.env`
- Add your Twitter API credentials:
```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

4. Run the scraper:
```bash
python scraper.py username
```

### Telegram Setup
1. Navigate to the Telegram directory:
```bash
cd telegram
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.template` to `.env`
- Add your Telegram API credentials:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number
TELEGRAM_SESSION_NAME=telegram_scraper
```

4. Run the scraper:
```bash
python scraper.py channel_username
```

### Discord Setup
1. Navigate to the Discord directory:
```bash
cd discord
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.template` to `.env`
- Add your Discord bot credentials:
```
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_APPLICATION_ID=your_application_id
```

4. Run the scraper:
```bash
python scraper.py server_id
```

## Using the Main Orchestrator

The main script can run scrapers for multiple platforms concurrently:

### Single Platform
```bash
# Twitter
python main.py --platform twitter --twitter username

# Telegram
python main.py --platform telegram --telegram channel_username

# Discord
python main.py --platform discord --discord server_id
```

### All Platforms
```bash
python main.py --platform all --twitter username --telegram channel_username --discord server_id
```

## Data Storage

Each platform maintains its own SQLite database:
- Twitter: `x/twitter_metrics.db`
- Telegram: `telegram/telegram_metrics.db`
- Discord: `discord/discord_metrics.db`

Each database contains:
- Account/server information
- Historical metrics
- Individual post/message data

## Platform-Specific Features

### Twitter
- Uses Twitter API v2
- Handles rate limiting
- Tracks tweet engagement

### Telegram
- Uses Telethon client
- Handles flood wait restrictions
- Tracks message views and forwards

### Discord
- Uses discord.py
- Handles server permissions
- Tracks channel activity

## Error Handling

Each platform implements its own error handling:
- Rate limit management
- Network error recovery
- API error handling
- Comprehensive logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
