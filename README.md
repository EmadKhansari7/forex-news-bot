# Forex News Bot

A Telegram bot that automatically fetches economic news from ForexFactory's
official JSON feed and publishes it to Telegram channels and groups, with
currency/impact filtering, commodity keyword filters (OIL/GOLD), duplicate
protection, per-destination posting intervals, and pre-release alerts.

> ⚠️ **Project status: Under active development.**
> This project is being built step-by-step as a learning exercise. Core
> features described below are implemented and working. See the
> [Project Roadmap](#project-roadmap) section for current progress.

---

## Features (implemented)

- 📰 **News fetching** — pulls economic calendar data from ForexFactory's official JSON feed
- 🚫 **Duplicate protection** — never publishes the same news item twice per destination
- 🎛️ **Currency filters** — enable/disable USD, EUR, GBP, JPY, CAD, AUD, NZD, CHF per channel
- 🛢️ **OIL filter** — keyword-based (Crude Oil, Natural Gas); dual-send if both USD and OIL filters are active
- 🥇 **GOLD filter** — placeholder ready; no matching events in current feed (keywords TBD)
- 📊 **Impact filters** — per-currency minimum: Low / Medium / High
- ⏱️ **Configurable check interval** — 5 / 10 / 15 / 30 / 60 / 120 / 240 minutes (global)
- 📬 **Posting interval** — per-channel throttle: Off / 5 / 15 / 30 / 60 / 120 / 240 minutes
- 📢 **Multi-destination publishing** — send to multiple Telegram channels and groups simultaneously
- 🔔 **Pre-release alert toggles** — 15 min before / 5 min before / at release time (per channel)
- ⏸️ **Deactivate / Reactivate** — pause or resume a channel without deleting it
- 🗑️ **Delete channel** — permanently remove with two-step confirmation
- 👤 **Multi-manager support** — owner can add/remove managers; each manager controls their own channels
- 🔒 **Authorization** — only registered managers can access the bot
- 🛠️ **Admin panel via inline keyboards** — manage everything with buttons, no manual commands

---

## Tech stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.10+ | Readable, beginner-friendly, great library support |
| Telegram integration | `python-telegram-bot` 21.x | Most mature Python library for Telegram bots |
| Scheduling | `APScheduler` | Reliable in-process job scheduling with live reschedule |
| Database | SQLite + SQLAlchemy 2.x | Zero-setup, file-based, clean ORM |
| News source | ForexFactory JSON feed | Stable, structured, no scraping required |

---

## Project architecture

```
forex-news-bot/
├── bot/
│   ├── handlers/
│   │   ├── admin_handlers.py       # main button callback dispatcher
│   │   ├── add_channel_handler.py  # ConversationHandler: add channel
│   │   └── add_manager_handler.py  # ConversationHandler: add manager
│   └── keyboards/
│       ├── main_menu.py            # main, channels, bot settings, posting interval menus
│       ├── filter_menu.py          # currency filter menu
│       └── alert_menu.py           # alert settings menu
├── config/
│   ├── settings.py                 # env vars loader
│   └── logger.py                   # rotating file + console logger
├── database/
│   ├── engine.py                   # SQLAlchemy engine + session
│   ├── models.py                   # ORM models (all tables)
│   └── repository.py               # all DB queries (no raw SQL in handlers)
├── scheduler/
│   ├── scheduler.py                # APScheduler setup + reschedule_news_check()
│   └── news_job.py                 # main news check loop (throttle + dual-send)
├── services/
│   ├── filter_service.py           # currency + keyword filter logic, MatchedNewsItem
│   ├── telegram_service.py         # send_message with Flood Control retry
│   └── news_provider/
│       ├── forex_factory_provider.py
│       └── news_item.py
├── main.py                         # entry point
├── requirements.txt
└── .env.example                    # template for required env vars
```

---

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
# Edit .env and fill in your values

# 5. Run
python main.py
```

### Required `.env` variables

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_IDS=your_telegram_user_id
BOT_OWNER_USERNAME=your_telegram_username   # without @
DATABASE_PATH=database/forex_news_bot.db
NEWS_FEED_URL=https://nfs.faireconomy.media/ff_calendar_thisweek.json
LOG_LEVEL=INFO
```

---

## Project roadmap

### ✅ Phase 1 — Foundation
- [x] Project setup (structure, dependencies, env config)
- [x] Config layer + logging system
- [x] News provider (ForexFactory JSON feed parser)
- [x] Database layer (SQLite, duplicate protection)
- [x] Filter engine (currency + impact level)
- [x] Telegram sending service
- [x] Scheduler (APScheduler, periodic news check)

### ✅ Phase 2 — Multi-tenant admin panel
- [x] Multi-manager architecture (owner + managers + destinations)
- [x] Authorization gate (only registered managers)
- [x] Add / Remove channel (ConversationHandler)
- [x] Add / Remove manager (owner-only)
- [x] Deactivate / Reactivate / Delete destination
- [x] Currency filter menu (per-channel, per-currency toggle)
- [x] Alert settings (15min / 5min / at release, per-channel)
- [x] Bot Settings (global check interval, live reschedule)
- [x] Posting interval throttle (per-channel: Off/5/15/30/60/120/240 min)

### ✅ Phase 3 — Commodity & interval extensions
- [x] OIL filter (keyword-matched: Crude Oil, Natural Gas)
- [x] Dual-send: one news item sends separately under USD **and** OIL if both filters active
- [x] GOLD filter (code ready, `GOLD_KEYWORDS = []` pending real feed keywords)
- [x] Extended check intervals (up to 240 minutes)
- [x] Extended posting intervals (up to 240 minutes)
- [x] Flood Control retry in telegram_service

### 🔜 Phase 4 — GOLD keywords + Indices
- [ ] Research GOLD-related event titles in ForexFactory and other feeds (XAU, Bullion, Gold)
- [ ] Populate `GOLD_KEYWORDS` in `filter_service.py` once confirmed
- [ ] Indices filter (S&P 500, DAX, Nikkei etc.) — keyword-based, same approach as OIL

### 🔜 Phase 5 — Testing
- [ ] Unit tests for filter logic (filter_service.py)
- [ ] Unit tests for repository functions
- [ ] Integration test for full news-check cycle

### 🔜 Phase 6 — Deployment
- [ ] Choose platform (Oracle Cloud Free Tier / VPS)
- [ ] systemd service or Docker setup
- [ ] GitHub Actions for CI (lint + tests)
- [ ] Deployment guide in docs/

---

## License

This project is open source. License to be added.

## Contributing

This project is being developed as a learning exercise. Contribution
guidelines will be added once the core functionality is complete.