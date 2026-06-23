# Forex News Bot

A Telegram bot that automatically fetches economic news from ForexFactory's
official JSON feed and publishes it to Telegram channels and groups, with
currency/impact filtering, duplicate protection, and pre-release alerts.

> ⚠️ **Project status: Under active development.**
> This project is being built step-by-step as a learning exercise. Core
> features described below are part of the planned architecture and are
> being implemented incrementally. See the [Project Roadmap](#project-roadmap)
> section for current progress.

## Features (planned)

- 📰 **News fetching** — pulls economic calendar data (title, currency,
  impact level, release time) from ForexFactory's official JSON feed
- 🚫 **Duplicate protection** — never publishes the same news item twice
- 🎛️ **Currency filters** — enable/disable specific currencies
  (USD, EUR, GBP, JPY, CAD, AUD, NZD, CHF)
- 📊 **Impact filters** — filter by Low / Medium / High impact
- ⏱️ **Configurable scheduling** — check for news every 5, 15, 30, or 60 minutes
- 📢 **Multi-destination publishing** — send to multiple Telegram channels and groups
- 🔔 **Pre-release alerts** — notify 15 minutes before, 5 minutes before,
  or at release time
- 🛠️ **Admin panel via inline keyboards** — manage everything with buttons,
  no manual commands required

## Tech stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.10+ | Readable, beginner-friendly, great library support |
| Telegram integration | `python-telegram-bot` | Most mature Python library for Telegram bots |
| Scheduling | `APScheduler` | Reliable in-process job scheduling |
| Database | SQLite | Zero-setup, file-based, easy to later migrate to PostgreSQL |
| News source | ForexFactory's official JSON feed | Stable, structured, no scraping required |

## Project architecture

```
forex-news-bot/
├── bot/                    # Telegram-facing code (handlers, keyboards)
├── services/               # Core business logic (news fetching, filters, alerts)
├── database/                # Database models and queries
├── scheduler/               # Periodic job scheduling
├── config/                  # Environment-based configuration
├── logs/                     # Runtime log files (not committed)
├── tests/                    # Automated tests
├── docs/                      # Additional documentation
├── .env.example                # Template for required environment variables
└── main.py                     # Application entry point
```

Full architecture documentation: see [`docs/architecture.md`](docs/architecture.md)
*(coming in a later development phase)*.

## Getting started (local development)

### Prerequisites
- Python 3.10 or higher
- A Telegram account (to create a bot via [@BotFather](https://t.me/BotFather))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/EmadKhansari7/forex-news-bot.git
cd forex-news-bot

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
# Then edit .env and fill in your actual values
```

Detailed installation and deployment guides will be added to the `docs/`
folder as the project matures.

## Project roadmap

- [x] Project planning and architecture design
- [x] Project setup (folder structure, dependencies, environment config)
- [x] GitHub repository setup
- [ ] Core development (in progress)
  - [x] Config layer (environment variable loading)
  - [x] Logging system (file + console output, log levels)
  - [ ] News provider (fetching from ForexFactory JSON feed)
  - [ ] Database layer (duplicate protection, SQLite models)
  - [ ] Filter engine (currency / impact filters)
  - [ ] Telegram bot (basic message sending)
  - [ ] Scheduler (periodic news checks)
  - [ ] Admin menu (inline keyboards)
  - [ ] Alert system (pre-release notifications)
  - [ ] Multi-destination publishing
- [ ] Testing
- [ ] Deployment (local, GitHub Actions, Oracle Cloud Free Tier, VPS)
- [ ] Maintenance documentation



## License

This project is open source. License to be added.

## Contributing

This project is being developed as a learning exercise. Contribution
guidelines will be added once the core functionality is complete.