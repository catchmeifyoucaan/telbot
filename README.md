# ATLAS v2.0 - Advanced Telegram Intelligence System

**Elite AI-powered intelligence analysis for Telegram channels and groups**

Powered by **Gemini 3 Pro** - The latest Google AI model released in 2025

---

## Features

### Core Intelligence Capabilities
- **AI-Powered Analysis** - Deep content analysis using Gemini 3 Pro
- **Multi-Modal Media Analysis** - Analyze images, videos, and documents with OCR
- **Entity Extraction** - Automatically identify people, organizations, locations, dates, keywords
- **Sentiment Scoring** - Get sentiment scores (0-100) for conversations
- **Real-Time Monitoring** - 24/7 channel surveillance with keyword alerts
- **Multi-Channel Comparison** - Compare and contrast multiple sources
- **Smart Export System** - Export to JSON, CSV, or TXT formats
- **Long Report Handling** - Automatically splits reports longer than 4000 chars

---

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create or edit `.env` file:
```env
# Get from https://my.telegram.org
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Get from https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key

# System Settings
DEFAULT_SCAN_LIMIT=100
GEMINI_MODEL=gemini-3-pro
```

### 3. Run ATLAS
```bash
python atlas_agent.py
```

---

## Commands

All commands are sent to **Saved Messages** in Telegram.

### Standard Analysis
```
.atlas <target> [limit] [--media] [--entities] [--export format] [prompt]
```

**Examples:**
```
.atlas @TechCrunch 100
.atlas @channel 50 --media --entities
.atlas @channel --export json What are the main topics?
.atlas -1001234567890 200 Summarize the key decisions
```

**Flags:**
- `--media` - Analyze images, videos, and documents in chat
- `--entities` - Extract people, organizations, locations, keywords, dates
- `--export json|csv|txt` - Export analysis to file

---

### Real-Time Monitoring
```
.watch <target> [keyword1,keyword2,...]
```

**Examples:**
```
.watch @channel
.watch @channel crypto,scam,urgent,breaking
```

Monitor channels 24/7 and get instant AI-analyzed alerts in Saved Messages when:
- New messages are posted (if no keywords specified)
- Messages contain specified keywords

---

### Multi-Channel Comparison
```
.compare <target1> <target2> [target3] [limit]
```

**Examples:**
```
.compare @channel1 @channel2 50
.compare @news1 @news2 @news3 100
```

Get comparative intelligence reports highlighting:
- Common themes and differences
- Sentiment comparison
- Key players appearing across channels
- Coordination or conflicts between sources
- Strategic recommendations

---

### Stop Monitoring
```
.stop
```

Stops all active monitoring tasks.

---

## Export System

All exports are saved to `atlas_exports/` directory with timestamps.

### Export Formats

**JSON** - Machine-readable structured data
```json
{
  "timestamp": "20250128_143022",
  "target": "TechCrunch",
  "message_count": 100,
  "analysis": "...",
  "raw_data": "..."
}
```

**CSV** - Spreadsheet-compatible
```csv
Field,Value
timestamp,20250128_143022
target,TechCrunch
analysis,...
```

**TXT** - Plain text report
```
AI analysis content...
```

---

## Advanced Features

### Entity Extraction
When using `--entities` flag, ATLAS extracts:
- **People** - Names mentioned in conversations
- **Organizations** - Companies, groups, institutions
- **Locations** - Cities, countries, places
- **Keywords** - Important terms and topics
- **Dates** - Mentioned dates and deadlines
- **Sentiment Score** - 0-100 numerical sentiment

### Media Analysis
When using `--media` flag, ATLAS:
- Performs OCR on images to extract text
- Analyzes photo content and context
- Processes video content
- Extracts text from documents
- Assesses intelligence value of media

### Real-Time Intelligence
Monitoring mode provides:
- Instant notifications for new messages
- AI assessment of message significance
- Keyword-based filtering
- Continuous 24/7 surveillance
- Non-intrusive background operation

---

## Use Cases

### Intelligence Gathering
- Monitor competitor channels
- Track industry news and trends
- Identify emerging threats/opportunities
- Sentiment analysis of communities

### Security & Compliance
- Detect suspicious activity patterns
- Monitor for policy violations
- Track keyword mentions (scams, threats)
- Analyze coordination between groups

### Market Research
- Track brand mentions across channels
- Monitor customer sentiment
- Identify influencers and key players
- Compare competitor messaging

### Investigative Research
- Timeline reconstruction with date extraction
- Entity relationship mapping
- Multi-source verification
- Pattern detection across channels

---

## Technical Details

### Architecture
```
┌─────────────────────────────────────────┐
│    Command Interface (Saved Messages)    │
├─────────────────────────────────────────┤
│   AtlasClient (Orchestration Layer)     │
│  • Command parsing & routing             │
│  • Multi-message handling                │
│  • Export management                     │
├─────────────────────────────────────────┤
│  IntelligenceUnit (AI Analysis)         │
│  • Gemini 3 Pro integration              │
│  • Multi-modal processing                │
│  • Entity extraction                     │
│  • Sentiment analysis                    │
├─────────────────────────────────────────┤
│  TelegramClient (Data Layer)            │
│  • Message retrieval                     │
│  • Media downloading                     │
│  • Real-time event handling              │
└─────────────────────────────────────────┘
```

### Performance
- **Async/await** architecture for non-blocking operations
- **Concurrent processing** for multi-channel analysis
- **Smart message splitting** for reports >4000 characters
- **Efficient media handling** with temporary file cleanup
- **Rate limiting protection** with flood prevention

### Security
- **Environment variables** for sensitive credentials
- **No data persistence** (unless exported manually)
- **Temporary media files** auto-deleted after analysis
- **Local session storage** for Telegram auth

---

## Troubleshooting

### "Invalid model name" error
Ensure `.env` has:
```env
GEMINI_MODEL=gemini-3-pro
```

### "ChannelPrivateError"
You must be a member of private channels to analyze them.

### Long response times
- Reduce message limit for faster analysis
- Disable `--media` flag if not needed
- Use monitoring mode for real-time instead of batch analysis

### Media analysis fails
- Ensure sufficient disk space in `atlas_exports/`
- Check Gemini API quota limits
- Some media types may not be supported

---

## Roadmap

### Planned Features
- [ ] Sentiment trend graphs/visualizations
- [ ] Web dashboard interface
- [ ] Scheduled periodic reports
- [ ] Advanced search and filtering
- [ ] Network analysis graphs
- [ ] REST API for integrations
- [ ] Machine learning pattern detection
- [ ] Multi-language translation

---

## Credits

**Built with:**
- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram API client
- [Google Gemini AI](https://ai.google.dev/) - Advanced AI analysis
- Python asyncio - Concurrent operations

**Model:** Gemini 3 Pro (Latest Google AI - 2025)

---

## License

For intelligence gathering, research, and authorized monitoring purposes only.

**Disclaimer:** Use responsibly and in compliance with applicable laws and Telegram's Terms of Service.
