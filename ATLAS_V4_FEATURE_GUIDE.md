# ATLAS v4.0 - Complete Feature Guide

## 🚀 What's New in v4.0

ATLAS v4.0 adds **8 Tier S features** that transform it from a passive intelligence tool into a full-featured automation and moderation platform.

---

## 📋 Table of Contents

1. [Auto-Forwarding](#auto-forwarding)
2. [Advanced Event Monitoring](#advanced-event-monitoring)
3. [Message Sending](#message-sending)
4. [Global Search](#global-search)
5. [Bulk Media Download](#bulk-media-download)
6. [ML Spam/Bot Detection](#ml-spambot-detection)
7. [Auto-Moderation](#auto-moderation)
8. [Scheduled Reports](#scheduled-reports)

---

## 1. Auto-Forwarding

**Aggregate intelligence from multiple sources into a single channel.**

### Command
```
.auto-forward from <source> to <destination> [--filter keyword1,keyword2] [--media-only]
```

### Examples

**Forward all messages from one channel to another:**
```
.auto-forward from @intel_channel to me
```

**Forward only messages containing specific keywords:**
```
.auto-forward from @news_channel to @my_aggregator --filter crypto,blockchain,defi
```

**Forward only media (photos, videos, files):**
```
.auto-forward from @media_source to @my_archive --media-only
```

**Combined filters:**
```
.auto-forward from @source to @dest --filter urgent,alert --media-only
```

### Use Cases
- Aggregate news from 10+ channels into one feed
- Filter important keywords from high-volume channels
- Automatically archive media content
- Create custom intelligence feeds

### How It Works
- Sets up real-time listener on source channel
- Checks each new message against your filters
- Automatically forwards matching messages to destination
- Runs continuously in the background

---

## 2. Advanced Event Monitoring

**Track message edits, deletions, and user online status - detect censorship and manipulation.**

### Command
```
.watch-events <target> [--edits] [--deletes] [--online]
```

### Examples

**Monitor message edits (censorship detection):**
```
.watch-events @channel --edits
```

**Track deleted messages:**
```
.watch-events @channel --deletes
```

**Monitor both edits and deletes:**
```
.watch-events @channel --edits --deletes
```

**Track when a user comes online:**
```
.watch-events @username --online
```

### What You'll Receive
When an edit occurs:
```
✏️ MESSAGE EDITED
Channel: Channel Name
Sender: John Doe
Time: 2025-11-29 15:30:00
New Text: [edited content]
Edit #2
```

When a message is deleted:
```
🗑️ MESSAGE(S) DELETED
Channel: Channel Name
Time: 2025-11-29 15:30:00
Deleted Message IDs: [12345, 12346]
⚠️ Original content not recoverable
```

### Use Cases
- Detect censorship in political channels
- Track what governments/organizations try to hide
- Monitor if influencers change their statements
- Identify coordinated narrative changes

---

## 3. Message Sending

**Post messages to channels/groups (requires appropriate permissions).**

### Command
```
.send <target> <message>
```

### Examples

**Send to a channel:**
```
.send @my_channel Intelligence report ready: 15 suspicious accounts detected
```

**Send to yourself:**
```
.send me Reminder: Check sources at 3pm
```

**Send formatted messages:**
```
.send @channel 🚨 ALERT: New development in crypto sector
```

### Use Cases
- Post AI-generated intelligence reports to your channels
- Send automated alerts to team channels
- Publish aggregated intelligence summaries
- Create automated notification systems

### Requirements
- You must have permission to post in the target channel
- For channels: must be admin or have posting rights
- For groups: must be a member

---

## 4. Global Search

**Search across ALL your chats simultaneously, not just one channel.**

### Command
```
.global-search <keyword> [--limit N]
```

### Examples

**Search all chats for a keyword:**
```
.global-search crypto
```

**Search with custom result limit:**
```
.global-search "urgent meeting" --limit 50
```

**Search for usernames:**
```
.global-search @john_doe
```

### What You'll Receive
```
🔍 GLOBAL SEARCH RESULTS
Keyword: crypto
Found: 127 message(s)

#1 - Crypto News Channel
👤 Alice | 📅 2025-11-29 10:00
Bitcoin hits new high amid institutional buying...

#2 - Tech Discussion Group
👤 Bob | 📅 2025-11-29 09:45
Anyone following the crypto markets today?

... and 125 more results
```

### Use Cases
- Find that message you vaguely remember across all chats
- Track mentions of specific topics everywhere
- Research how often a keyword appears in your network
- Discover connections between different groups

---

## 5. Bulk Media Download

**Archive entire channels' photos, videos, and files automatically.**

### Command
```
.bulk-download <target> [--type photos|videos|all] [--limit N]
```

### Examples

**Download all media from a channel:**
```
.bulk-download @channel
```

**Download only photos:**
```
.bulk-download @channel --type photos
```

**Download only videos:**
```
.bulk-download @channel --type videos
```

**Download last 500 media files:**
```
.bulk-download @channel --limit 500
```

### What You'll Get
```
✅ BULK DOWNLOAD COMPLETE
Source: Channel Name
Downloaded: 437 files
Skipped: 63
Location: atlas_media_archive/Channel_Name/
```

Files are saved with format:
```
{message_id}_{timestamp}.{extension}
12345_20251129_143000.jpg
12346_20251129_143005.mp4
```

### Use Cases
- Archive entire OSINT channels for offline analysis
- Download evidence before it's deleted
- Create local backups of important media
- Build media libraries for research

### Single Media Download
For downloading specific media:
```
.download-media @channel 12345
```
(where 12345 is the message ID)

---

## 6. ML Spam/Bot Detection

**AI-powered detection of spam and bot accounts.**

### Command
```
.detect-spam <target> [--limit N]
```

### Examples

**Scan last 100 messages:**
```
.detect-spam @channel
```

**Scan last 500 messages:**
```
.detect-spam @channel --limit 500
```

### What You'll Receive
```
🛡️ SPAM DETECTION REPORT
Channel: Channel Name
Scanned: 100 messages
Spam Detected: 7

#1 - Message 12345
👤 @spam_bot_123
⚠️ Confidence: 95%
📝 Reason: Suspicious links, repetitive text pattern, known scam keywords
💬 Click here to win FREE crypto! Limited time offer...

#2 - Message 12347
👤 @suspicious_user
⚠️ Confidence: 87%
📝 Reason: Bot-like posting pattern, promotional content
💬 Join our pump group for guaranteed gains!

... and 5 more spam messages
```

### How It Works
- Analyzes message content using Gemini AI
- Checks for suspicious patterns (links, repetitive text, scam keywords)
- Evaluates sender behavior (bot indicators, posting patterns)
- Returns confidence score (0-100%) and specific reasons

### Use Cases
- Clean up your channels before they get out of hand
- Identify bot networks
- Find coordinated spam campaigns
- Protect your community from scammers

---

## 7. Auto-Moderation

**Automatically delete spam and moderate channels (requires admin rights).**

### Command
```
.auto-mod <target> [--delete-spam] [--ban-threshold 0.9]
```

### Examples

**Enable auto-deletion of spam:**
```
.auto-mod @my_channel --delete-spam
```

**Set higher confidence threshold (more aggressive):**
```
.auto-mod @my_channel --delete-spam --ban-threshold 0.95
```

**Set lower threshold (catch more potential spam):**
```
.auto-mod @my_channel --delete-spam --ban-threshold 0.85
```

### What You'll Get
Real-time alerts when spam is detected:
```
🛡️ AUTO-MOD ACTION
Channel: My Channel
Action: Deleted spam
Confidence: 93%
Reason: Suspicious links and scam keywords detected
```

### How It Works
1. Monitors all new messages in real-time
2. Runs ML spam detection on each message
3. If spam confidence exceeds threshold, automatically deletes
4. Sends you notification of the action

### Ban Threshold
- `0.7` = Very lenient (catches obvious spam only)
- `0.85` = Moderate (balanced)
- `0.9` = Default (conservative, high confidence)
- `0.95` = Very strict (only absolute certainty)

### Requirements
- You must have admin rights in the channel
- Must have permission to delete messages

### Use Cases
- Automated community moderation
- Protect channels from spam bots
- Maintain clean discussion groups
- Reduce manual moderation workload

---

## 8. Scheduled Reports

**Automated intelligence reports delivered on schedule.**

### Command
```
.schedule-report <target> <frequency> [--keywords kw1,kw2]
```

### Frequencies
- `hourly` - Every hour
- `daily` - Every day at 9:00 AM
- `weekly` - Every Monday at 9:00 AM

### Examples

**Daily intelligence report:**
```
.schedule-report @intel_channel daily
```

**Hourly updates from breaking news:**
```
.schedule-report @news_channel hourly
```

**Weekly summary with keyword filter:**
```
.schedule-report @channel weekly --keywords crypto,defi,regulation
```

### What You'll Receive
```
📊 SCHEDULED INTELLIGENCE REPORT
Source: Intel Channel
Frequency: daily
Time: 2025-11-29 09:00:00
Messages Analyzed: 487

=== EXECUTIVE SUMMARY ===
[AI-generated intelligence summary]

Key Events:
- Major announcement from...
- Emerging trend in...
- Notable discussion about...

Sentiment: 72/100 (Positive)

Key Entities:
People: John Doe, Jane Smith
Organizations: TechCorp, CryptoFund
Locations: Silicon Valley, New York
Keywords: blockchain, AI, innovation
```

### How It Works
- Runs on automated schedule in background thread
- Fetches latest messages from target channel
- Generates AI-powered intelligence summary
- Sends to your Saved Messages

### Use Cases
- Stay updated on important channels without checking manually
- Get daily intelligence briefings
- Monitor competitors automatically
- Track industry news on schedule

---

## 📊 Complete Command Reference

### Core Analysis Commands
- `.atlas <target> [limit] [--media] [--entities] [--export json|csv|txt]` - AI-powered analysis
- `.watch <target> [keywords]` - Real-time monitoring with keyword alerts
- `.compare <target1> <target2> [target3] [limit]` - Multi-channel comparison
- `.search <target> <keyword> [--from @user] [--regex pattern] [--after DATE]` - Advanced search
- `.profile @username in <target> [limit]` - User behavior analysis
- `.translate <target> <language> [limit]` - Multi-language translation

### Tier S Features (NEW)
- `.auto-forward from <source> to <dest> [--filter kw] [--media-only]` - Auto-forwarding
- `.watch-events <target> [--edits] [--deletes] [--online]` - Advanced monitoring
- `.send <target> <message>` - Send messages
- `.global-search <keyword> [--limit N]` - Search all chats
- `.bulk-download <target> [--type photos|videos|all] [--limit N]` - Bulk media download
- `.download-media <target> <message_id>` - Single media download
- `.detect-spam <target> [--limit N]` - ML spam detection
- `.auto-mod <target> [--delete-spam] [--ban-threshold 0.9]` - Auto-moderation
- `.delete <target> <msg_id>` - Delete message
- `.delete <target> --keyword <word> --last N` - Bulk delete by keyword
- `.schedule-report <target> <frequency> [--keywords kw]` - Scheduled reports

### Export & Utility
- `.export-raw <target> [limit] [--format json|csv]` - Raw data export
- `.stop` - Stop all monitoring tasks

---

## 🎯 Real-World Use Cases

### OSINT Intelligence Gathering
```bash
# Set up auto-forwarding from multiple intel sources
.auto-forward from @osint_source1 to @my_intel_feed
.auto-forward from @osint_source2 to @my_intel_feed
.auto-forward from @osint_source3 to @my_intel_feed --filter urgent,alert

# Monitor for censorship
.watch-events @government_channel --edits --deletes

# Get daily intel briefing
.schedule-report @my_intel_feed daily
```

### Community Management
```bash
# Enable auto-moderation
.auto-mod @my_community --delete-spam --ban-threshold 0.9

# Monitor for spam
.detect-spam @my_community --limit 500

# Bulk delete spam
.delete @my_community --keyword "click here to win" --last 1000
```

### Media Archiving
```bash
# Archive all media from important channels
.bulk-download @evidence_channel --type all
.bulk-download @news_media --type photos --limit 1000

# Download specific evidence
.download-media @channel 12345
```

### Research & Analysis
```bash
# Global search for topics
.global-search cryptocurrency --limit 200
.global-search "climate change" --limit 300

# Comparative analysis
.compare @source1 @source2 @source3 500

# User profiling
.profile @influencer in @their_channel 1000
```

### Automated Workflows
```bash
# Intelligence aggregation pipeline
.auto-forward from @raw_intel1 to @aggregator --filter critical,urgent
.auto-forward from @raw_intel2 to @aggregator --filter critical,urgent
.schedule-report @aggregator hourly
.watch-events @aggregator --edits --deletes

# Sends you hourly intel reports with real-time edit/delete alerts
```

---

## ⚠️ Important Notes

### Permissions
- **Auto-moderation & deletion**: Requires admin rights in target channel
- **Message sending**: Requires posting permissions
- **Event monitoring**: Works on any channel you're a member of
- **Media download**: Works on any accessible channel

### Rate Limits
- Telegram has built-in rate limiting
- Bulk operations automatically include delays
- If you hit limits, ATLAS will retry automatically

### Storage
- Media files stored in: `atlas_media_archive/<channel_name>/`
- Exports stored in: `atlas_exports/`
- Make sure you have sufficient disk space for bulk downloads

### Privacy & Ethics
- Use responsibly and ethically
- Respect channel rules and admins
- Don't spam or abuse auto-forwarding
- Follow Telegram's Terms of Service

---

## 🔧 Troubleshooting

### "Auto-forward setup failed"
- Check that source and destination are valid
- Ensure you have access to both channels
- Verify destination allows messages from you

### "Event monitoring failed"
- Make sure you're a member of the target channel
- Some private channels may restrict event access

### "Delete failed: Insufficient rights"
- You need admin permissions to delete messages
- Check your admin status in the channel

### "Download failed"
- Channel may have restricted media access
- Check your internet connection
- Ensure sufficient disk space

---

## 📈 Performance Tips

1. **Use filters** - Don't auto-forward everything, use keyword filters
2. **Set reasonable limits** - Start with smaller limits for bulk operations
3. **Monitor disk space** - Bulk downloads can consume significant storage
4. **Use scheduled reports wisely** - Hourly reports can be overwhelming

---

## 🚀 Advanced Combinations

### Ultimate Intelligence Setup
```bash
# 1. Set up aggregation
.auto-forward from @intel1 to @master_feed --filter urgent,breaking
.auto-forward from @intel2 to @master_feed --filter urgent,breaking
.auto-forward from @intel3 to @master_feed --filter urgent,breaking

# 2. Monitor the aggregator
.watch-events @master_feed --edits --deletes

# 3. Get automated reports
.schedule-report @master_feed daily

# 4. Clean up spam
.auto-mod @master_feed --delete-spam --ban-threshold 0.9

# Result: Fully automated intelligence pipeline with spam filtering
```

### Research Workflow
```bash
# 1. Find all mentions across your chats
.global-search "your research topic" --limit 500

# 2. Deep dive into specific channels
.atlas @channel1 1000 --entities --export json
.atlas @channel2 1000 --entities --export json

# 3. Download evidence
.bulk-download @channel1 --type all

# 4. Compare sources
.compare @channel1 @channel2 @channel3 500
```

---

## 📞 Getting Help

All commands show usage examples if you run them without arguments:
```
.auto-forward
.watch-events
.detect-spam
... etc
```

Check `TELEGRAM_FULL_CAPABILITIES.md` for even more possibilities!

---

**ATLAS v4.0** - The most powerful Telegram intelligence tool ever built. 🛡️
