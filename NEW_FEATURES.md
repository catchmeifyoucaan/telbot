# ATLAS v3.0 - New Features Guide

## 🚀 What's New

ATLAS v3.0 adds **4 powerful new commands** that make intelligence gathering faster, more targeted, and more flexible.

---

## 1. 🔍 Advanced Search (.search)

### What It Does
Search through chat history with powerful filters to find exactly what you need.

### Syntax
```
.search <target> <keyword> [--from @user] [--regex pattern] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--limit N]
```

### Examples

#### Basic Keyword Search
```
.search @channel crypto
.search @channel "bitcoin price"
```
Finds all messages containing "crypto" or "bitcoin price"

#### Search by User
```
.search @channel scam --from @john
.search @channel announcement --from @admin
```
Find messages from specific users

#### Regex Pattern Search
```
.search @channel --regex "\d{3}-\d{3}-\d{4}"
```
Find phone numbers (pattern: 123-456-7890)

```
.search @channel --regex "http[s]?://[^\s]+"
```
Find all URLs

```
.search @channel --regex "\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
```
Find email addresses

```
.search @channel --regex "\$\d+\.?\d*"
```
Find dollar amounts ($100, $99.99)

#### Date Range Search
```
.search @channel hack --after 2025-01-01
.search @channel meeting --after 2025-01-01 --before 2025-01-31
```
Find messages within a specific date range

#### Combined Filters
```
.search @channel crypto --from @john --after 2025-01-15 --limit 200
```
Find messages from @john containing "crypto" after Jan 15, 2025

### Use Cases

**1. Forensic Investigation**
```
.search @channel --regex "\d{16}"  # Credit card numbers
.search @channel password --after 2025-01-01
.search @channel leak --from @whistleblower
```

**2. Compliance Monitoring**
```
.search @channel policy_violation --limit 1000
.search @channel insider --after 2025-01-01
```

**3. Threat Detection**
```
.search @channel malware
.search @channel phishing --regex "http[s]?://[^\s]+"
```

**4. Research**
```
.search @channel --regex "@\w+"  # Find all @mentions
.search @channel #crypto --after 2025-01-01  # Hashtag tracking
```

---

## 2. 👤 User Profile Analysis (.profile)

### What It Does
Comprehensive analysis of individual user behavior in a channel.

### Syntax
```
.profile @username in <target> [limit]
```

### Example
```
.profile @john in @channel 500
```

### Output Includes

#### 📊 Statistics
- **Total Messages**: How many messages they've sent
- **Active Period**: First to last message date
- **Days Active**: Number of days they've participated
- **Avg Messages/Day**: Activity level
- **Peak Activity Hour**: When they're most active

#### 🧠 AI Behavioral Analysis
- **Main Topics**: What they discuss most
- **Role/Contribution**: Are they helpful? Spammer? Lurker?
- **Sentiment**: Positive, negative, neutral?
- **Key Relationships**: Who they interact with
- **Overall Assessment**: Summary of their behavior

#### 📝 Recent Messages
- Sample of their most recent messages
- Context for their communication style

### Use Cases

**1. Community Management**
```
.profile @newuser in @community 1000
```
Vet new members, identify potential spammers

**2. Influencer Identification**
```
.profile @activeuser in @channel
```
Find key community contributors

**3. Investigation**
```
.profile @suspect in @channel 2000
```
Track suspicious user behavior

**4. Recruitment**
```
.profile @expert in @techchannel 500
```
Identify skilled contributors for hiring

### Example Output
```
👤 USER PROFILE: @john

📊 Statistics:
• Messages: 247
• Period: 2025-01-15 to 2025-11-29
• Days Active: 319
• Avg Messages/Day: 0.8
• Peak Activity Hour: 14:00

🧠 AI ANALYSIS:
@john is a highly engaged technical contributor who primarily discusses
blockchain development and smart contract security. His tone is professional
and educational, often helping other members troubleshoot issues. He frequently
interacts with @alice and @bob, suggesting he's part of the core development team.

Sentiment: Positive (85/100)
Role: Technical Expert & Community Helper
Key Topics: Solidity, Security Audits, Gas Optimization

📝 Recent Messages (Sample):
[2025-11-28 14:23]
Great question! The issue you're seeing is likely due to reentrancy. Here's
how to fix it...

[2025-11-27 09:15]
Just published our security audit results. Found 3 medium-severity issues...
```

---

## 3. 💾 Raw Data Export (.export-raw)

### What It Does
Export message data instantly without AI analysis - 10x faster than regular export.

### Syntax
```
.export-raw <target> [limit] [--format json|csv]
```

### Examples

#### Export to JSON
```
.export-raw @channel 1000
.export-raw @channel 500 --format json
```

#### Export to CSV (Spreadsheet)
```
.export-raw @channel 1000 --format csv
```

### Output Formats

#### JSON Structure
```json
{
  "messages": [
    {
      "id": 12345,
      "timestamp": "2025-11-29 14:30",
      "sender_name": "John",
      "sender_username": "john",
      "sender_id": 123456789,
      "text": "Hello world",
      "date": "2025-11-29T14:30:00"
    }
  ],
  "source": "ChannelName",
  "count": 1000
}
```

#### CSV Structure
```csv
timestamp,sender_name,sender_username,message
2025-11-29 14:30,John,john,Hello world
2025-11-29 14:31,Alice,alice,Hi there!
```

### Use Cases

**1. Data Backup**
```
.export-raw @mychannel 5000 --format json
```
Archive channel history

**2. External Analysis**
```
.export-raw @channel 1000 --format csv
```
Import into Excel, R, Python for custom analysis

**3. Training Data**
```
.export-raw @channel 10000 --format json
```
Build ML training datasets

**4. Quick Extract**
```
.export-raw @channel 100 --format csv
```
Get recent messages for quick review

### Speed Comparison

| Method | 1000 Messages | AI Analysis | Speed |
|--------|---------------|-------------|-------|
| `.atlas --export` | ~30 seconds | ✅ Yes | Slow |
| `.export-raw` | ~2-3 seconds | ❌ No | **10x Faster** |

**When to use each:**
- Use `.atlas --export` when you want AI insights + data
- Use `.export-raw` when you just need raw data fast

---

## 4. 🌐 Multi-Language Translation (.translate)

### What It Does
Analyze foreign language channels with automatic translation to your preferred language.

### Syntax
```
.translate <target> <language> [limit]
```

### Examples

#### Translate Russian Channel
```
.translate @russian_channel english 100
.translate @russian_channel en 200
```

#### Translate Chinese Channel
```
.translate @chinese_channel english 150
```

#### Translate to Any Language
```
.translate @english_channel spanish 100
.translate @channel french 200
.translate @channel german 50
```

### Output Includes

1. **Translated Summary**: Main topics in your language
2. **Key Insights**: Strategic intelligence (translated)
3. **Sentiment Analysis**: Community mood
4. **Entity Extraction**: Names, organizations, locations (translated)

### Supported Languages

**All major languages**, including:
- English, Spanish, French, German, Italian
- Russian, Ukrainian, Polish
- Chinese (Simplified/Traditional), Japanese, Korean
- Arabic, Hebrew
- Portuguese, Hindi, Turkish
- And many more...

### Use Cases

**1. Global Competitor Intelligence**
```
.translate @competitor_russia english 200
.translate @competitor_china en 150
```
Monitor international competitors

**2. International News Monitoring**
```
.translate @russian_news english 100
.translate @middle_east_news en 200
```
Track foreign news sources

**3. Global Community Management**
```
.translate @spanish_community english 100
```
Understand your international users

**4. OSINT Investigations**
```
.translate @suspect_channel english 500
```
Investigate foreign language sources

### Example Output
```
🌐 TRANSLATED ANALYSIS
Source: Russian Crypto Channel
Language: english
Messages: 100

📊 SUMMARY (Translated):
This Russian cryptocurrency channel primarily discusses Bitcoin trading
strategies and DeFi protocols. The community is highly technical, with
frequent discussions about gas optimization and smart contract vulnerabilities.

🔑 KEY INSIGHTS:
1. Major concern about upcoming regulation in Russia
2. Strong interest in privacy-focused protocols
3. Community planning a meetup in Moscow next month
4. Several members discussing exit strategies

😊 SENTIMENT: Cautiously Optimistic (65/100)
Concern about regulation but excited about new protocols

📍 ENTITIES EXTRACTED:
• People: Vitalik, Pavel Durov, Igor
• Organizations: Binance, Uniswap, Russian Central Bank
• Locations: Moscow, St. Petersburg
• Keywords: DeFi, regulation, privacy, smart contracts
```

---

## 📚 Command Quick Reference

```bash
# Search & Filter
.search @channel crypto
.search @channel bitcoin --from @john
.search @channel --regex "\d{3}-\d{3}-\d{4}"
.search @channel scam --after 2025-01-01 --limit 100

# User Profiles
.profile @username in @channel 500

# Raw Export
.export-raw @channel 1000
.export-raw @channel 500 --format csv

# Translation
.translate @russian_channel english 100
.translate @chinese_channel en 200
```

---

## 💡 Power User Tips

### Combine Commands for Maximum Intelligence

#### Investigation Workflow
```bash
# 1. Search for suspicious keywords
.search @channel scam --limit 1000

# 2. Profile the suspicious user
.profile @suspectuser in @channel 2000

# 3. Export raw data for external analysis
.export-raw @channel 2000 --format csv

# 4. Get translated analysis if foreign language
.translate @channel english 500
```

#### Competitor Intelligence Pipeline
```bash
# 1. Monitor competitor channel
.watch @competitor product,launch,release

# 2. When alert arrives, search for details
.search @competitor product_name --limit 200

# 3. Profile key employees
.profile @competitor_ceo in @competitor

# 4. Export for reporting
.export-raw @competitor 500 --format csv
```

#### Multi-Language OSINT
```bash
# 1. Translate and analyze
.translate @foreign_channel english 200

# 2. Search for specific entities
.search @foreign_channel --regex "@\w+"

# 3. Profile key users
.profile @foreignuser in @foreign_channel

# 4. Export everything
.export-raw @foreign_channel 1000 --format json
```

---

## 🎯 Best Practices

### Search Efficiently
- Start with broad searches, narrow down with filters
- Use `--limit` to control how far back to search
- Combine `--from` and `--after` for targeted user tracking

### Profile Strategically
- Use higher limits (1000+) for accurate user behavior
- Profile multiple related users to map relationships
- Export profiles to track changes over time

### Export Smartly
- Use `.export-raw` for data backups and quick exports
- Use `.atlas --export` when you want AI analysis included
- CSV for spreadsheets, JSON for programming/analysis

### Translate Effectively
- Start with smaller limits (100-200) to test
- Specify target language clearly (english, en, Spanish, es)
- Combine with search to find specific translated content

---

## 🔧 Troubleshooting

### Search Returns No Results
- Check your keyword spelling
- Try broader search terms
- Increase `--limit` (default is 500)
- Remove some filters to widen search

### Profile Shows "No Messages Found"
- Verify username spelling (case-sensitive)
- User might have no messages in that channel
- Try increasing the limit
- Check if user changed username recently

### Export Takes Long Time
- Large limits (>5000) may take a while
- Use `.export-raw` instead of `.atlas --export` for speed
- Check your internet connection

### Translation Issues
- Ensure Gemini API has enough quota
- Try smaller message limits
- Some languages may take longer to process

---

## 📈 What's Next?

These features are just the beginning! Coming soon:

- **Scheduled Reports**: Automated daily/weekly intelligence
- **Sentiment Trends**: Track mood changes over time
- **Network Analysis**: Map user relationships
- **Web Dashboard**: Browser-based interface
- **Advanced Alerts**: Complex trigger conditions

---

**Enjoy the new features! Your intelligence gathering just got 10x more powerful.** 🚀
