# ATLAS v4.0 - Quick Start Guide

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 🔑 Setup

Create `.env` file:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
PHONE_NUMBER=your_phone_number
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp
```

## ▶️ Run

```bash
python3 atlas_agent.py
```

## 📱 Basic Usage

All commands are sent to **Saved Messages** (your personal Telegram chat).

### 1️⃣ Analyze a Channel
```
.atlas @channel 100
```

### 2️⃣ Auto-Forward Intel Sources
```
.auto-forward from @source to me --filter crypto,urgent
```

### 3️⃣ Monitor for Censorship
```
.watch-events @channel --edits --deletes
```

### 4️⃣ Search Everything
```
.global-search bitcoin
```

### 5️⃣ Download All Media
```
.bulk-download @channel --type photos
```

### 6️⃣ Detect Spam
```
.detect-spam @channel
```

### 7️⃣ Auto-Moderate (requires admin)
```
.auto-mod @channel --delete-spam
```

### 8️⃣ Schedule Daily Reports
```
.schedule-report @channel daily
```

## 🎯 Most Useful Combinations

### Intelligence Aggregation
```
.auto-forward from @intel1 to @my_feed
.auto-forward from @intel2 to @my_feed
.schedule-report @my_feed daily
```

### Community Management
```
.auto-mod @my_group --delete-spam
.detect-spam @my_group --limit 500
```

### Research & OSINT
```
.global-search "your topic"
.bulk-download @channel
.watch-events @channel --edits --deletes
```

## 📚 Full Documentation

- **Complete Guide**: `ATLAS_V4_FEATURE_GUIDE.md`
- **All Capabilities**: `TELEGRAM_FULL_CAPABILITIES.md`
- **Upgrade Notes**: `ATLAS_UPGRADE_SUMMARY.md`

## ⚡ Command Cheat Sheet

### Core
- `.atlas <target> [limit]` - AI analysis
- `.watch <target>` - Monitor new messages
- `.search <target> <keyword>` - Search in channel
- `.profile @user in <target>` - User analysis
- `.compare <ch1> <ch2>` - Compare channels

### Tier S (NEW)
- `.auto-forward from <src> to <dst>` - Auto-forward
- `.watch-events <target> --edits --deletes` - Advanced monitoring
- `.send <target> <message>` - Send message
- `.global-search <keyword>` - Search all chats
- `.bulk-download <target>` - Download media
- `.detect-spam <target>` - Spam detection
- `.auto-mod <target> --delete-spam` - Auto-moderation
- `.schedule-report <target> daily` - Scheduled reports

### Utility
- `.translate <target> english` - Translate & analyze
- `.export-raw <target>` - Export data
- `.stop` - Stop monitoring

## 🛡️ You're Ready!

ATLAS v4.0 is now 8x more powerful than v3.0. Enjoy! 🚀
