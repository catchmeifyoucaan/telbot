# ATLAS v2.0 - Quick Command Reference

## Setup (One-time)
```bash
pip install -r requirements.txt
# Edit .env with your API credentials
python atlas_agent.py
```

---

## Commands Cheat Sheet

### Basic Analysis
```
.atlas @channel 100
```
Analyze last 100 messages from @channel

### With Media Analysis
```
.atlas @channel 50 --media
```
Analyze text + images/videos/documents

### With Entity Extraction
```
.atlas @channel 100 --entities
```
Extract people, organizations, locations, keywords, dates, sentiment score

### Export to JSON
```
.atlas @channel 100 --export json
```
Save analysis to `atlas_exports/` directory

### Custom Question
```
.atlas @channel 50 What are the security risks?
```
Ask AI a specific question about the chat

### Combined Flags
```
.atlas @channel 100 --media --entities --export json
```
Full-featured analysis with everything enabled

---

### Real-Time Monitoring
```
.watch @channel
```
Monitor all new messages 24/7

```
.watch @channel crypto,scam,hack
```
Alert only when keywords appear

---

### Compare Multiple Channels
```
.compare @news1 @news2 @news3 100
```
Compare sentiment, topics, and patterns across channels

---

### Stop Monitoring
```
.stop
```
Stop all active monitoring tasks

---

## Pro Tips

**Fast Analysis:** `.atlas @channel 20` (small limit = faster)

**Deep Dive:** `.atlas @channel 500 --media --entities --export json` (comprehensive)

**Security Watch:** `.watch @channel hack,breach,leak,vulnerability`

**Competitor Intel:** `.compare @yourcompany @competitor1 @competitor2 100`

**Save Everything:** Always use `--export json` for important analyses

**Long Reports:** Reports >4000 chars auto-split into multiple messages

---

## Export Locations

All exports saved to: `atlas_exports/`

Filename format: `atlas_<channel>_<timestamp>.json`

Example: `atlas_TechCrunch_20250128_143022.json`

---

## Powered by Gemini 3 Pro
Latest Google AI model - Released 2025
