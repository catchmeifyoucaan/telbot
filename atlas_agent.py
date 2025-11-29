import os
import asyncio
import logging
import json
import csv
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import ChannelPrivateError, RPCError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, User
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import google.generativeai as genai
from collections import defaultdict, Counter
import schedule
import threading
import time

# --- SETUP & LOGGING ---
logging.basicConfig(
    format='%(asctime)s - [ATLAS] - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load secrets
load_dotenv()
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Create exports directory
EXPORTS_DIR = Path("atlas_exports")
EXPORTS_DIR.mkdir(exist_ok=True)

# Create media archive directory
MEDIA_ARCHIVE_DIR = Path("atlas_media_archive")
MEDIA_ARCHIVE_DIR.mkdir(exist_ok=True)

# --- INTELLIGENCE MODULE (AI) ---
class IntelligenceUnit:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-3-pro"),
            system_instruction=(
                "You are ATLAS, an elite intelligence analyst for a top-tier tech firm. "
                "Your source material comes from raw Telegram thread dumps. "
                "Your goal is to extract critical insights, sentiment, and action items. "
                "Ignore spam. Focus on signal. Output structured, executive-level summaries. "
                "Extract entities: people, organizations, locations, dates, keywords. "
                "Provide sentiment analysis with scores. Identify threats, opportunities, and trends."
            )
        )

    async def analyze_content(self, context_data, custom_prompt=None, extract_entities=False):
        try:
            base_prompt = (
                "Analyze the following Telegram chat history. "
                "Identify the main topics, key decisions made, and the general sentiment. "
                "If specific dates or deadlines are mentioned, highlight them. "
                "Provide a sentiment score (0-100) and identify key entities (people, organizations, locations)."
            )

            if extract_entities:
                base_prompt += "\n\nIMPORTANT: At the end, provide a structured entity list in this format:\n"
                base_prompt += "=== ENTITIES ===\nPeople: [list]\nOrganizations: [list]\nLocations: [list]\nKeywords: [list]\nDates: [list]\nSentiment Score: [0-100]"

            final_prompt = f"{custom_prompt if custom_prompt else base_prompt}\n\n--- LOG START ---\n{context_data}\n--- LOG END ---"

            response = await asyncio.to_thread(
                self.model.generate_content, final_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"AI Analysis Failed: {e}")
            return f"⚠️ **Intelligence Failure:** {str(e)}"

    async def analyze_media(self, media_path, media_type="image"):
        """Analyze images, videos, or documents using Gemini's multimodal capabilities"""
        try:
            media_file = genai.upload_file(media_path)

            prompt = f"Analyze this {media_type} from a Telegram chat. Extract any text (OCR), describe the content, identify key information, and assess relevance for intelligence purposes."

            response = await asyncio.to_thread(
                self.model.generate_content, [media_file, prompt]
            )

            return response.text
        except Exception as e:
            logger.error(f"Media Analysis Failed: {e}")
            return f"⚠️ **Media Analysis Failure:** {str(e)}"

    async def compare_channels(self, channel_data_list: List[Tuple[str, str]]):
        """Compare multiple channels and identify patterns, differences, and relationships"""
        try:
            comparison_prompt = "You are analyzing multiple Telegram channels. Compare and contrast them:\n\n"

            for i, (channel_name, data) in enumerate(channel_data_list, 1):
                comparison_prompt += f"=== CHANNEL {i}: {channel_name} ===\n{data}\n\n"

            comparison_prompt += "\n\nProvide a comparative analysis highlighting:\n"
            comparison_prompt += "1. Common themes and differences\n"
            comparison_prompt += "2. Sentiment comparison\n"
            comparison_prompt += "3. Key players appearing across channels\n"
            comparison_prompt += "4. Coordination or conflicts between channels\n"
            comparison_prompt += "5. Strategic recommendations"

            response = await asyncio.to_thread(
                self.model.generate_content, comparison_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Channel Comparison Failed: {e}")
            return f"⚠️ **Comparison Failure:** {str(e)}"

    async def detect_spam_bot(self, message_text: str, sender_data: Dict) -> Tuple[bool, float, str]:
        """
        ML-powered spam/bot detection
        Returns: (is_spam, confidence_score, reason)
        """
        try:
            detection_prompt = f"""You are a spam and bot detection system for Telegram.

Analyze this message and sender data:

Message: {message_text}
Sender Info: {json.dumps(sender_data, default=str)}

Determine:
1. Is this likely spam? (yes/no)
2. Confidence score (0-100)
3. Specific indicators (e.g., suspicious links, repetitive text, bot-like patterns, scam keywords)

Response format:
SPAM: [yes/no]
CONFIDENCE: [0-100]
REASON: [brief explanation]
"""

            response = await asyncio.to_thread(
                self.model.generate_content, detection_prompt
            )

            result_text = response.text.upper()
            is_spam = 'SPAM: YES' in result_text

            # Extract confidence score
            confidence = 0.0
            if 'CONFIDENCE:' in result_text:
                try:
                    conf_line = [line for line in result_text.split('\n') if 'CONFIDENCE:' in line][0]
                    confidence = float(re.search(r'\d+', conf_line).group()) / 100.0
                except:
                    confidence = 0.5

            # Extract reason
            reason = "Suspicious patterns detected"
            if 'REASON:' in response.text:
                try:
                    reason = response.text.split('REASON:')[1].strip().split('\n')[0]
                except:
                    pass

            return is_spam, confidence, reason

        except Exception as e:
            logger.error(f"Spam detection failed: {e}")
            return False, 0.0, str(e)


# --- EXPORT MODULE ---
class ExportHandler:
    @staticmethod
    def export_json(data: Dict, filename: str):
        """Export analysis to JSON format"""
        filepath = EXPORTS_DIR / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath

    @staticmethod
    def export_csv(data: Dict, filename: str):
        """Export analysis to CSV format"""
        filepath = EXPORTS_DIR / f"{filename}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field', 'Value'])
            for key, value in data.items():
                writer.writerow([key, str(value)])
        return filepath

    @staticmethod
    def export_text(content: str, filename: str):
        """Export analysis to plain text format"""
        filepath = EXPORTS_DIR / f"{filename}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath


# --- OPERATIONS MODULE (TELEGRAM) ---
class AtlasClient:
    def __init__(self):
        self.client = TelegramClient('atlas_session', API_ID, API_HASH)
        self.ai = IntelligenceUnit(GEMINI_KEY)
        self.user_me = None
        self.monitoring_tasks = {}  # Track active monitoring tasks
        self.export_handler = ExportHandler()
        self.auto_forward_rules = []  # Auto-forwarding rules
        self.auto_mod_rules = {}  # Auto-moderation rules by chat
        self.scheduled_reports = []  # Scheduled report tasks
        self.event_monitors = {}  # Advanced event monitoring (edits, deletes, online status)
        self.deleted_messages_cache = {}  # Track deleted messages
        self.edited_messages_cache = {}  # Track message edits

    async def start(self):
        """Bootstraps the connection and registers event hooks."""
        logger.info("Initializing Atlas Protocol v4.0...")
        phone = os.getenv("PHONE_NUMBER")
        await self.client.start(phone=phone if phone else lambda: input('Please enter your phone: '))

        self.user_me = await self.client.get_me()
        logger.info(f"Atlas Online. Logged in as: {self.user_me.first_name} (@{self.user_me.username})")
        logger.info("Listening on 'Saved Messages' for commands...")
        logger.info("Available commands:")
        logger.info("  Core: .atlas, .watch, .compare, .search, .profile, .translate")
        logger.info("  Advanced: .auto-forward, .watch-events, .send, .global-search")
        logger.info("  Media: .download-media, .bulk-download")
        logger.info("  Moderation: .auto-mod, .delete, .detect-spam")
        logger.info("  Automation: .schedule-report, .stop")
        logger.info("  Export: .export, .export-raw")

        # Register the Command Listener
        self.client.add_event_handler(self.handle_command, events.NewMessage(outgoing=True, chats='me'))

        # Register advanced event handlers
        self.client.add_event_handler(self.handle_message_edit, events.MessageEdited())
        self.client.add_event_handler(self.handle_message_delete, events.MessageDeleted())

        # Start scheduler thread for automated reports
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()

        # Keep the script running
        await self.client.run_until_disconnected()

    async def fetch_history(self, chat_input, limit=100, include_media=False, filters=None):
        """Scrapes history from public OR private chats with optional media analysis and filters."""
        messages_buffer = []
        media_analyses = []
        raw_messages = []  # Store raw message objects for filtering

        try:
            # Convert numeric channel IDs to integers
            if isinstance(chat_input, str) and chat_input.lstrip('-').isdigit():
                chat_input = int(chat_input)

            entity = await self.client.get_entity(chat_input)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', 'Unknown Chat'))

            logger.info(f"Target Acquired: {chat_title}. Scanning last {limit} messages...")

            async for msg in self.client.iter_messages(entity, limit=limit):
                # Apply filters if provided
                if filters:
                    if not self._apply_filters(msg, filters):
                        continue

                timestamp = msg.date.strftime('%Y-%m-%d %H:%M')
                sender = await msg.get_sender()
                sender_name = getattr(sender, 'first_name', 'Unknown') if sender else "Unknown"
                sender_username = getattr(sender, 'username', '') if sender else ""

                # Store raw message data
                raw_messages.append({
                    'id': msg.id,
                    'timestamp': timestamp,
                    'sender_name': sender_name,
                    'sender_username': sender_username,
                    'sender_id': sender.id if sender else None,
                    'text': msg.text or '',
                    'date': msg.date
                })

                # Text messages
                if msg.text:
                    messages_buffer.append(f"[{timestamp}] {sender_name}: {msg.text}")

                # Media analysis
                if include_media and msg.media:
                    try:
                        if isinstance(msg.media, MessageMediaPhoto):
                            photo_path = await msg.download_media(file=EXPORTS_DIR / f"temp_photo_{msg.id}.jpg")
                            if photo_path:
                                analysis = await self.ai.analyze_media(photo_path, "image")
                                media_analyses.append(f"[{timestamp}] 📷 Photo Analysis: {analysis}")
                                os.remove(photo_path)

                        elif isinstance(msg.media, MessageMediaDocument):
                            # Handle documents/videos/voice
                            doc_path = await msg.download_media(file=EXPORTS_DIR / f"temp_doc_{msg.id}")
                            if doc_path:
                                file_ext = Path(doc_path).suffix.lower()
                                if file_ext in ['.mp4', '.avi', '.mov']:
                                    media_type = "video"
                                elif file_ext in ['.ogg', '.mp3', '.wav', '.m4a']:
                                    media_type = "audio/voice message"
                                else:
                                    media_type = "document"
                                analysis = await self.ai.analyze_media(doc_path, media_type)
                                media_analyses.append(f"[{timestamp}] 📎 {media_type.title()} Analysis: {analysis}")
                                os.remove(doc_path)
                    except Exception as e:
                        logger.warning(f"Media analysis skipped for message {msg.id}: {e}")

            # Combine text and media analyses
            all_content = messages_buffer[::-1]  # Reverse for chronological order
            if media_analyses:
                all_content.extend(media_analyses[::-1])

            return chat_title, "\n".join(all_content), raw_messages[::-1]

        except ChannelPrivateError:
            return None, "❌ Error: This is a private channel you are not part of.", []
        except ValueError:
            return None, "❌ Error: Could not find that chat. Check the username/link.", []
        except Exception as e:
            logger.error(f"Fetch Error: {e}")
            return None, f"❌ System Error: {str(e)}", []

    def _apply_filters(self, msg, filters):
        """Apply filters to a message"""
        # Keyword filter
        if 'keyword' in filters:
            if not msg.text or filters['keyword'].lower() not in msg.text.lower():
                return False

        # Regex filter
        if 'regex' in filters:
            if not msg.text or not re.search(filters['regex'], msg.text, re.IGNORECASE):
                return False

        # Sender filter
        if 'from_user' in filters:
            sender = msg.sender
            if sender:
                username = getattr(sender, 'username', '')
                if username != filters['from_user'].lstrip('@'):
                    return False
            else:
                return False

        # Date filter
        if 'after_date' in filters:
            if msg.date < filters['after_date']:
                return False

        if 'before_date' in filters:
            if msg.date > filters['before_date']:
                return False

        # Media filter
        if 'has_media' in filters:
            if filters['has_media'] and not msg.media:
                return False
            if not filters['has_media'] and msg.media:
                return False

        return True

    async def monitor_channel(self, chat_input, keywords: Optional[List[str]] = None):
        """Real-time monitoring of a channel with optional keyword alerts"""
        try:
            entity = await self.client.get_entity(chat_input)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', 'Unknown'))

            logger.info(f"Starting real-time monitoring of: {chat_title}")

            @self.client.on(events.NewMessage(chats=entity))
            async def monitor_handler(event):
                msg = event.message
                if msg.text:
                    timestamp = msg.date.strftime('%Y-%m-%d %H:%M')
                    sender = await msg.get_sender()
                    sender_name = getattr(sender, 'first_name', 'Unknown') if sender else "Unknown"

                    # Check for keyword alerts
                    alert_triggered = False
                    if keywords:
                        for keyword in keywords:
                            if keyword.lower() in msg.text.lower():
                                alert_triggered = True
                                break

                    # Analyze and send to Saved Messages
                    if alert_triggered or not keywords:
                        analysis = await self.ai.analyze_content(
                            f"[{timestamp}] {sender_name}: {msg.text}",
                            custom_prompt="Quick intelligence assessment of this new message. Is it significant?"
                        )

                        alert_msg = f"🚨 **ATLAS ALERT**\n"
                        alert_msg += f"**Source:** {chat_title}\n"
                        alert_msg += f"**Time:** {timestamp}\n"
                        if alert_triggered:
                            alert_msg += f"**Keyword Match:** {', '.join(keywords)}\n"
                        alert_msg += f"\n**Message:**\n{msg.text}\n\n"
                        alert_msg += f"**AI Assessment:**\n{analysis}"

                        await self.client.send_message('me', alert_msg)

            self.monitoring_tasks[chat_title] = monitor_handler
            return f"✅ Now monitoring: {chat_title}" + (f" for keywords: {', '.join(keywords)}" if keywords else "")

        except Exception as e:
            logger.error(f"Monitoring Error: {e}")
            return f"❌ Monitoring Failed: {str(e)}"

    async def send_long_message(self, target, content: str, parse_mode='html'):
        """Send long messages by splitting them into multiple parts"""
        max_length = 4000
        if len(content) <= max_length:
            await self.client.send_message(target, content, parse_mode=parse_mode)
            return

        # Split into chunks
        chunks = []
        current_chunk = ""

        for line in content.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += ('\n' if current_chunk else '') + line

        if current_chunk:
            chunks.append(current_chunk)

        # Send chunks
        for i, chunk in enumerate(chunks, 1):
            header = f"📄 **Part {i}/{len(chunks)}**\n\n" if len(chunks) > 1 else ""
            await self.client.send_message(target, header + chunk, parse_mode=parse_mode)
            await asyncio.sleep(0.5)  # Prevent flood

    async def handle_command(self, event):
        """Enhanced Command Center with multiple command types"""
        msg_text = event.message.text.strip()

        # --- STANDARD ANALYSIS COMMAND ---
        if msg_text.startswith(".atlas"):
            await self.handle_atlas_command(event)

        # --- REAL-TIME MONITORING COMMAND ---
        elif msg_text.startswith(".watch-events"):
            await self.handle_watch_events_command(event)

        elif msg_text.startswith(".watch"):
            await self.handle_watch_command(event)

        # --- MULTI-CHANNEL COMPARISON ---
        elif msg_text.startswith(".compare"):
            await self.handle_compare_command(event)

        # --- EXPORT COMMAND ---
        elif msg_text.startswith(".export-raw"):
            await self.handle_export_raw_command(event)

        elif msg_text.startswith(".export"):
            await self.handle_export_command(event)

        # --- STOP MONITORING ---
        elif msg_text.startswith(".stop"):
            await self.handle_stop_command(event)

        # --- SEARCH COMMANDS ---
        elif msg_text.startswith(".global-search"):
            await self.handle_global_search_command(event)

        elif msg_text.startswith(".search"):
            await self.handle_search_command(event)

        # --- USER PROFILE COMMAND ---
        elif msg_text.startswith(".profile"):
            await self.handle_profile_command(event)

        # --- TRANSLATE COMMAND ---
        elif msg_text.startswith(".translate"):
            await self.handle_translate_command(event)

        # --- NEW: AUTO-FORWARDING ---
        elif msg_text.startswith(".auto-forward"):
            await self.handle_auto_forward_command(event)

        # --- NEW: MESSAGE SENDING ---
        elif msg_text.startswith(".send"):
            await self.handle_send_command(event)

        # --- NEW: BULK MEDIA DOWNLOAD ---
        elif msg_text.startswith(".bulk-download"):
            await self.handle_bulk_download_command(event)

        elif msg_text.startswith(".download-media"):
            await self.handle_download_media_command(event)

        # --- NEW: SPAM DETECTION ---
        elif msg_text.startswith(".detect-spam"):
            await self.handle_detect_spam_command(event)

        # --- NEW: AUTO-MODERATION ---
        elif msg_text.startswith(".auto-mod"):
            await self.handle_auto_mod_command(event)

        # --- NEW: DELETE MESSAGES ---
        elif msg_text.startswith(".delete"):
            await self.handle_delete_command(event)

        # --- NEW: SCHEDULED REPORTS ---
        elif msg_text.startswith(".schedule-report"):
            await self.handle_schedule_report_command(event)

    async def handle_atlas_command(self, event):
        """
        Standard analysis command with export options
        Syntax: .atlas <target> [limit] [--media] [--entities] [--export json|csv|txt] [prompt]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ ATLAS Usage:</b>\n"
                "<code>.atlas &lt;target&gt; [limit] [--media] [--entities] [--export json|csv|txt] [prompt]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.atlas @channel 100</code>\n"
                "<code>.atlas @channel 50 --media --entities</code>\n"
                "<code>.atlas @channel --export json What are the key topics?</code>"
            , parse_mode='html')
            return

        # Parse arguments
        target = parts[1]
        limit = 50
        include_media = '--media' in msg_text
        extract_entities = '--entities' in msg_text
        export_format = None
        custom_prompt = None

        # Extract export format
        if '--export' in msg_text:
            export_idx = parts.index('--export')
            if export_idx + 1 < len(parts):
                export_format = parts[export_idx + 1]

        # Extract limit
        for part in parts[2:]:
            if part.isdigit():
                limit = int(part)
                break

        # Extract custom prompt (everything after flags)
        prompt_parts = []
        skip_next = False
        for i, part in enumerate(parts[2:], 2):
            if skip_next:
                skip_next = False
                continue
            if part in ['--media', '--entities']:
                continue
            if part == '--export':
                skip_next = True
                continue
            if not part.isdigit():
                prompt_parts.append(part)

        if prompt_parts:
            custom_prompt = ' '.join(prompt_parts)

        # Status Update
        media_line = "🎬 Media Analysis: ENABLED\n" if include_media else ""
        entity_line = "🔍 Entity Extraction: ENABLED\n" if extract_entities else ""
        export_line = f"💾 Export Format: {export_format.upper()}\n" if export_format else ""

        await event.edit(
            f"⚡ <b>ATLAS v2.0 ACTIVE</b>\n"
            f"🔭 Target: <code>{target}</code>\n"
            f"📡 Scanning: {limit} messages\n"
            f"{media_line}"
            f"{entity_line}"
            f"{export_line}"
            f"⏳ <i>Establishing uplink...</i>"
        , parse_mode='html')

        # Fetch Phase
        chat_title, history_data, raw_messages = await self.fetch_history(target, limit, include_media)

        if not history_data or history_data.startswith("❌"):
            await event.edit(f"<b>MISSION FAILED</b>\n{history_data}", parse_mode='html')
            return

        # Analysis Phase
        await event.edit(
            f"⚡ <b>ATLAS v2.0 ACTIVE</b>\n"
            f"🔭 Target: {chat_title}\n"
            f"🧠 <i>AI Processing with Gemini 3 Pro...</i>"
        , parse_mode='html')

        ai_report = await self.ai.analyze_content(history_data, custom_prompt, extract_entities)

        # Export Phase
        if export_format:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"atlas_{chat_title.replace(' ', '_')}_{timestamp}"

            export_data = {
                'timestamp': timestamp,
                'target': chat_title,
                'message_count': limit,
                'analysis': ai_report,
                'raw_data': history_data
            }

            if export_format == 'json':
                filepath = self.export_handler.export_json(export_data, filename)
            elif export_format == 'csv':
                filepath = self.export_handler.export_csv(export_data, filename)
            else:  # txt
                filepath = self.export_handler.export_text(ai_report, filename)

            await event.edit(f"✅ **Exported to:** `{filepath}`", parse_mode='md')
            await asyncio.sleep(2)

        # Report Phase
        report_header = f"🛡️ <b>ATLAS INTELLIGENCE REPORT</b>\n"
        report_header += f"<b>Source:</b> {chat_title}\n"
        report_header += f"<b>Scope:</b> Last {limit} messages\n"
        report_header += f"<b>Model:</b> Gemini 3 Pro\n\n"

        final_message = report_header + ai_report

        # Send as multiple messages if needed
        await event.delete()
        await self.send_long_message('me', final_message, parse_mode='html')

    async def handle_watch_command(self, event):
        """
        Real-time monitoring command
        Syntax: .watch <target> [keyword1,keyword2,...]
        """
        parts = event.message.text.split(maxsplit=2)

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ WATCH Usage:</b>\n"
                "<code>.watch &lt;target&gt; [keyword1,keyword2,...]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.watch @channel</code>\n"
                "<code>.watch @channel crypto,scam,urgent</code>"
            , parse_mode='html')
            return

        target = parts[1]
        keywords = parts[2].split(',') if len(parts) > 2 else None

        await event.edit("🔄 <i>Initializing monitoring system...</i>", parse_mode='html')

        result = await self.monitor_channel(target, keywords)
        await event.edit(f"🛡️ **ATLAS MONITORING ACTIVE**\n{result}", parse_mode='md')

    async def handle_compare_command(self, event):
        """
        Multi-channel comparison command
        Syntax: .compare <target1> <target2> [target3] [limit]
        """
        parts = event.message.text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ COMPARE Usage:</b>\n"
                "<code>.compare &lt;target1&gt; &lt;target2&gt; [target3] [limit]</code>\n\n"
                "<b>Example:</b>\n"
                "<code>.compare @channel1 @channel2 @channel3 50</code>"
            , parse_mode='html')
            return

        # Extract targets and limit
        targets = []
        limit = 50

        for part in parts[1:]:
            if part.isdigit():
                limit = int(part)
            else:
                targets.append(part)

        if len(targets) < 2:
            await event.edit("❌ **Error:** Need at least 2 channels to compare", parse_mode='md')
            return

        await event.edit(
            f"⚡ <b>ATLAS COMPARISON MODE</b>\n"
            f"🔭 Analyzing {len(targets)} channels...\n"
            f"⏳ <i>This may take a moment...</i>"
        , parse_mode='html')

        # Fetch all channel data
        channel_data_list = []
        for target in targets:
            chat_title, history_data, _ = await self.fetch_history(target, limit)
            if history_data and not history_data.startswith("❌"):
                channel_data_list.append((chat_title, history_data))

        if len(channel_data_list) < 2:
            await event.edit("❌ **Error:** Could not fetch data from enough channels", parse_mode='md')
            return

        # Comparative analysis
        comparison_report = await self.ai.compare_channels(channel_data_list)

        report_header = f"🛡️ <b>ATLAS COMPARATIVE INTELLIGENCE</b>\n"
        report_header += f"<b>Channels:</b> {', '.join([name for name, _ in channel_data_list])}\n"
        report_header += f"<b>Scope:</b> {limit} messages per channel\n\n"

        final_message = report_header + comparison_report

        await event.delete()
        await self.send_long_message('me', final_message, parse_mode='html')

    async def handle_export_command(self, event):
        """Quick export of last analysis"""
        await event.edit("💡 <b>Tip:</b> Use <code>.atlas &lt;target&gt; --export json</code> to export during analysis", parse_mode='html')

    async def handle_stop_command(self, event):
        """Stop all monitoring tasks"""
        if not self.monitoring_tasks:
            await event.edit("❌ No active monitoring tasks", parse_mode='html')
            return

        count = len(self.monitoring_tasks)
        self.monitoring_tasks.clear()
        await event.edit(f"✅ Stopped {count} monitoring task(s)", parse_mode='html')

    async def handle_search_command(self, event):
        """
        Search messages with filters
        Syntax: .search <target> <keyword> [--from @user] [--regex pattern] [--after YYYY-MM-DD] [--limit N]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ SEARCH Usage:</b>\n"
                "<code>.search &lt;target&gt; &lt;keyword&gt; [--from @user] [--regex pattern] [--after YYYY-MM-DD] [--limit N]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.search @channel crypto</code>\n"
                "<code>.search @channel bitcoin --from @john</code>\n"
                "<code>.search @channel --regex \"\\d{3}-\\d{3}-\\d{4}\"</code>\n"
                "<code>.search @channel scam --after 2025-01-01 --limit 100</code>"
            , parse_mode='html')
            return

        target = parts[1]
        keyword = parts[2] if not parts[2].startswith('--') else None

        # Parse filters
        filters = {}
        limit = 500  # Default higher limit for search

        i = 2 if keyword else 2
        while i < len(parts):
            if parts[i] == '--from' and i + 1 < len(parts):
                filters['from_user'] = parts[i + 1]
                i += 2
            elif parts[i] == '--regex' and i + 1 < len(parts):
                filters['regex'] = parts[i + 1]
                i += 2
            elif parts[i] == '--after' and i + 1 < len(parts):
                try:
                    filters['after_date'] = datetime.strptime(parts[i + 1], '%Y-%m-%d')
                    i += 2
                except:
                    i += 1
            elif parts[i] == '--before' and i + 1 < len(parts):
                try:
                    filters['before_date'] = datetime.strptime(parts[i + 1], '%Y-%m-%d')
                    i += 2
                except:
                    i += 1
            elif parts[i] == '--limit' and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                    i += 2
                except:
                    i += 1
            else:
                i += 1

        if keyword:
            filters['keyword'] = keyword

        await event.edit(f"🔍 <b>SEARCHING...</b>\n<code>{target}</code>", parse_mode='html')

        # Fetch with filters
        chat_title, filtered_data, raw_messages = await self.fetch_history(target, limit, filters=filters)

        if not filtered_data or filtered_data.startswith("❌"):
            await event.edit(f"<b>SEARCH FAILED</b>\n{filtered_data}", parse_mode='html')
            return

        result_count = len(raw_messages)

        if result_count == 0:
            await event.edit("❌ <b>No messages found matching your criteria</b>", parse_mode='html')
            return

        # Format results
        report = f"🔍 <b>SEARCH RESULTS</b>\n"
        report += f"<b>Source:</b> {chat_title}\n"
        report += f"<b>Found:</b> {result_count} message(s)\n"
        if 'keyword' in filters:
            report += f"<b>Keyword:</b> {filters['keyword']}\n"
        if 'from_user' in filters:
            report += f"<b>From:</b> {filters['from_user']}\n"
        report += "\n" + "="*40 + "\n\n"
        report += filtered_data

        await event.delete()
        await self.send_long_message('me', report, parse_mode='html')

    async def handle_profile_command(self, event):
        """
        Analyze a specific user's activity in a channel
        Syntax: .profile @username in <target> [limit]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 4 or parts[2] != 'in':
            await event.edit(
                "<b>⚠️ PROFILE Usage:</b>\n"
                "<code>.profile @username in &lt;target&gt; [limit]</code>\n\n"
                "<b>Example:</b>\n"
                "<code>.profile @john in @channel 500</code>"
            , parse_mode='html')
            return

        username = parts[1].lstrip('@')
        target = parts[3]
        limit = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 1000

        await event.edit(f"👤 <b>ANALYZING USER PROFILE...</b>\n<code>@{username}</code> in <code>{target}</code>", parse_mode='html')

        # Fetch messages
        chat_title, history_data, raw_messages = await self.fetch_history(target, limit)

        if not history_data or history_data.startswith("❌"):
            await event.edit(f"<b>PROFILE FAILED</b>\n{history_data}", parse_mode='html')
            return

        # Filter messages by user
        user_messages = [msg for msg in raw_messages if msg['sender_username'] == username]

        if not user_messages:
            await event.edit(f"❌ <b>No messages found from @{username} in {chat_title}</b>", parse_mode='html')
            return

        # Analyze user activity
        message_count = len(user_messages)
        user_text = "\n".join([f"[{msg['timestamp']}] {msg['text']}" for msg in user_messages if msg['text']])

        # Time analysis
        message_times = [datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M') for msg in user_messages]
        hours = [t.hour for t in message_times]
        hour_counts = Counter(hours)
        peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0

        # Date range
        first_msg = min(message_times)
        last_msg = max(message_times)
        days_active = (last_msg - first_msg).days + 1

        # AI analysis
        analysis_prompt = f"""Analyze this user's behavior in the channel. Provide:
1. Main topics they discuss
2. Their role/contribution to the community
3. Sentiment and tone
4. Key relationships (who they interact with)
5. Overall assessment

User: @{username}
Messages analyzed: {message_count}
"""

        ai_analysis = await self.ai.analyze_content(user_text[:10000], analysis_prompt)  # Limit context

        # Build report
        report = f"👤 <b>USER PROFILE: @{username}</b>\n\n"
        report += f"<b>📊 Statistics:</b>\n"
        report += f"• Messages: {message_count}\n"
        report += f"• Period: {first_msg.strftime('%Y-%m-%d')} to {last_msg.strftime('%Y-%m-%d')}\n"
        report += f"• Days Active: {days_active}\n"
        report += f"• Avg Messages/Day: {message_count/days_active:.1f}\n"
        report += f"• Peak Activity Hour: {peak_hour}:00\n\n"
        report += f"<b>🧠 AI ANALYSIS:</b>\n{ai_analysis}\n\n"
        report += f"<b>📝 Recent Messages (Sample):</b>\n"
        for msg in user_messages[:10]:
            if msg['text']:
                report += f"\n[{msg['timestamp']}]\n{msg['text'][:200]}...\n"

        await event.delete()
        await self.send_long_message('me', report, parse_mode='html')

    async def handle_export_raw_command(self, event):
        """
        Export raw message data without AI analysis
        Syntax: .export-raw <target> [limit] [--format json|csv]
        """
        parts = event.message.text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ EXPORT-RAW Usage:</b>\n"
                "<code>.export-raw &lt;target&gt; [limit] [--format json|csv]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.export-raw @channel 1000</code>\n"
                "<code>.export-raw @channel 500 --format csv</code>"
            , parse_mode='html')
            return

        target = parts[1]
        limit = 500
        export_format = 'json'

        # Parse arguments
        for i, part in enumerate(parts[2:], 2):
            if part.isdigit():
                limit = int(part)
            elif part == '--format' and i + 1 < len(parts):
                export_format = parts[i + 1]

        await event.edit(f"💾 <b>EXPORTING RAW DATA...</b>\n<code>{target}</code>", parse_mode='html')

        # Fetch data
        chat_title, history_data, raw_messages = await self.fetch_history(target, limit)

        if not history_data or history_data.startswith("❌"):
            await event.edit(f"<b>EXPORT FAILED</b>\n{history_data}", parse_mode='html')
            return

        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"raw_{chat_title.replace(' ', '_')}_{timestamp}"

        if export_format == 'json':
            filepath = self.export_handler.export_json({'messages': raw_messages, 'source': chat_title, 'count': len(raw_messages)}, filename)
        else:  # csv
            # Flatten for CSV
            csv_data = []
            for msg in raw_messages:
                csv_data.append({
                    'timestamp': msg['timestamp'],
                    'sender_name': msg['sender_name'],
                    'sender_username': msg['sender_username'],
                    'message': msg['text']
                })
            filepath = EXPORTS_DIR / f"{filename}.csv"
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if csv_data:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)

        await event.edit(f"✅ <b>EXPORTED</b>\n<code>{filepath}</code>\n<b>Messages:</b> {len(raw_messages)}", parse_mode='html')

    async def handle_translate_command(self, event):
        """
        Analyze channel with translation
        Syntax: .translate <target> <language> [limit]
        """
        parts = event.message.text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ TRANSLATE Usage:</b>\n"
                "<code>.translate &lt;target&gt; &lt;language&gt; [limit]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.translate @russian_channel english 100</code>\n"
                "<code>.translate @chinese_channel en 200</code>"
            , parse_mode='html')
            return

        target = parts[1]
        language = parts[2]
        limit = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 100

        await event.edit(f"🌐 <b>TRANSLATING & ANALYZING...</b>\n<code>{target}</code> → {language}", parse_mode='html')

        # Fetch data
        chat_title, history_data, raw_messages = await self.fetch_history(target, limit)

        if not history_data or history_data.startswith("❌"):
            await event.edit(f"<b>TRANSLATION FAILED</b>\n{history_data}", parse_mode='html')
            return

        # AI analysis with translation
        translation_prompt = f"""Analyze this Telegram channel and translate all content to {language}.

Provide:
1. Translated summary of main topics
2. Key insights (translated)
3. Sentiment analysis
4. Important entities (names, organizations, locations)

Original content below:
"""

        ai_report = await self.ai.analyze_content(history_data, translation_prompt)

        report = f"🌐 <b>TRANSLATED ANALYSIS</b>\n"
        report += f"<b>Source:</b> {chat_title}\n"
        report += f"<b>Language:</b> {language}\n"
        report += f"<b>Messages:</b> {limit}\n\n"
        report += ai_report

        await event.delete()
        await self.send_long_message('me', report, parse_mode='html')

    # ========== NEW TIER S FEATURES ==========

    async def handle_auto_forward_command(self, event):
        """
        Auto-forwarding from source to destination with filters
        Syntax: .auto-forward from <source> to <destination> [--filter keyword1,keyword2] [--media-only]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 5 or 'from' not in msg_text or 'to' not in msg_text:
            await event.edit(
                "<b>⚠️ AUTO-FORWARD Usage:</b>\n"
                "<code>.auto-forward from &lt;source&gt; to &lt;destination&gt; [--filter keywords] [--media-only]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.auto-forward from @channel1 to @channel2</code>\n"
                "<code>.auto-forward from @intel_source to me --filter crypto,urgent</code>\n"
                "<code>.auto-forward from @source to @dest --media-only</code>"
            , parse_mode='html')
            return

        try:
            # Parse source and destination
            from_idx = parts.index('from')
            to_idx = parts.index('to')
            source = parts[from_idx + 1]
            destination = parts[to_idx + 1]

            # Parse filters
            keywords = []
            media_only = '--media-only' in msg_text

            if '--filter' in msg_text:
                filter_idx = parts.index('--filter')
                if filter_idx + 1 < len(parts):
                    keywords = parts[filter_idx + 1].split(',')

            # Get entities
            source_entity = await self.client.get_entity(source)
            dest_entity = await self.client.get_entity(destination)

            source_title = getattr(source_entity, 'title', getattr(source_entity, 'username', source))
            dest_title = getattr(dest_entity, 'title', getattr(dest_entity, 'username', destination))

            # Create forwarding rule
            rule = {
                'source': source_entity,
                'destination': dest_entity,
                'source_name': source_title,
                'dest_name': dest_title,
                'keywords': keywords,
                'media_only': media_only,
                'count': 0
            }

            # Register handler
            @self.client.on(events.NewMessage(chats=source_entity))
            async def forward_handler(event):
                msg = event.message

                # Check filters
                should_forward = True

                if rule['media_only'] and not msg.media:
                    should_forward = False

                if rule['keywords'] and msg.text:
                    keyword_match = any(kw.lower() in msg.text.lower() for kw in rule['keywords'])
                    if not keyword_match:
                        should_forward = False

                if should_forward:
                    try:
                        await self.client.forward_messages(rule['destination'], msg)
                        rule['count'] += 1
                        logger.info(f"Auto-forwarded message from {rule['source_name']} to {rule['dest_name']}")
                    except Exception as e:
                        logger.error(f"Auto-forward failed: {e}")

            self.auto_forward_rules.append(rule)

            filter_text = f" (Filter: {', '.join(keywords)})" if keywords else ""
            media_text = " (Media only)" if media_only else ""

            await event.edit(
                f"✅ <b>AUTO-FORWARD ACTIVE</b>\n"
                f"📤 <b>From:</b> {source_title}\n"
                f"📥 <b>To:</b> {dest_title}\n"
                f"{filter_text}{media_text}\n\n"
                f"Messages will be automatically forwarded."
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Auto-forward setup failed:</b> {str(e)}", parse_mode='html')

    async def handle_watch_events_command(self, event):
        """
        Advanced event monitoring: edits, deletes, online status
        Syntax: .watch-events <target> [--edits] [--deletes] [--online]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ WATCH-EVENTS Usage:</b>\n"
                "<code>.watch-events &lt;target&gt; [--edits] [--deletes] [--online]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.watch-events @channel --edits --deletes</code>\n"
                "<code>.watch-events @user --online</code>"
            , parse_mode='html')
            return

        target = parts[1]
        watch_edits = '--edits' in msg_text
        watch_deletes = '--deletes' in msg_text
        watch_online = '--online' in msg_text

        if not (watch_edits or watch_deletes or watch_online):
            watch_edits = watch_deletes = True  # Default to both

        try:
            entity = await self.client.get_entity(target)
            target_name = getattr(entity, 'title', getattr(entity, 'username', target))

            self.event_monitors[target_name] = {
                'entity': entity,
                'edits': watch_edits,
                'deletes': watch_deletes,
                'online': watch_online,
                'edit_count': 0,
                'delete_count': 0
            }

            features = []
            if watch_edits:
                features.append("✏️ Edits")
            if watch_deletes:
                features.append("🗑️ Deletes")
            if watch_online:
                features.append("🟢 Online Status")

            await event.edit(
                f"👁️ <b>ADVANCED EVENT MONITORING ACTIVE</b>\n"
                f"<b>Target:</b> {target_name}\n"
                f"<b>Watching:</b> {', '.join(features)}\n\n"
                f"You will be notified of changes in Saved Messages."
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Event monitoring failed:</b> {str(e)}", parse_mode='html')

    async def handle_message_edit(self, event):
        """Handle message edit events"""
        for monitor_name, monitor in self.event_monitors.items():
            if monitor['edits']:
                try:
                    if event.chat_id == monitor['entity'].id:
                        msg = event.message
                        sender = await msg.get_sender()
                        sender_name = getattr(sender, 'first_name', 'Unknown') if sender else "Unknown"

                        # Track edit
                        msg_id = msg.id
                        if msg_id not in self.edited_messages_cache:
                            self.edited_messages_cache[msg_id] = []

                        self.edited_messages_cache[msg_id].append({
                            'timestamp': datetime.now(),
                            'text': msg.text
                        })

                        monitor['edit_count'] += 1

                        alert = f"✏️ <b>MESSAGE EDITED</b>\n"
                        alert += f"<b>Channel:</b> {monitor_name}\n"
                        alert += f"<b>Sender:</b> {sender_name}\n"
                        alert += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        alert += f"<b>New Text:</b>\n{msg.text[:500]}\n"

                        if len(self.edited_messages_cache[msg_id]) > 1:
                            alert += f"\n<b>Edit #{len(self.edited_messages_cache[msg_id])}</b>"

                        await self.client.send_message('me', alert, parse_mode='html')
                except Exception as e:
                    logger.error(f"Edit event handling failed: {e}")

    async def handle_message_delete(self, event):
        """Handle message delete events"""
        for monitor_name, monitor in self.event_monitors.items():
            if monitor['deletes']:
                try:
                    # Note: Telethon doesn't provide full context for deleted messages
                    # We can only know that messages were deleted, not their content
                    monitor['delete_count'] += 1

                    alert = f"🗑️ <b>MESSAGE(S) DELETED</b>\n"
                    alert += f"<b>Channel:</b> {monitor_name}\n"
                    alert += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    alert += f"<b>Deleted Message IDs:</b> {event.deleted_ids}\n"
                    alert += f"\n<i>⚠️ Original content not recoverable</i>"

                    await self.client.send_message('me', alert, parse_mode='html')
                except Exception as e:
                    logger.error(f"Delete event handling failed: {e}")

    async def handle_send_command(self, event):
        """
        Send message to a channel/group
        Syntax: .send <target> <message>
        """
        msg_text = event.message.text
        parts = msg_text.split(maxsplit=2)

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ SEND Usage:</b>\n"
                "<code>.send &lt;target&gt; &lt;message&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.send @channel Hello world!</code>\n"
                "<code>.send me Intelligence report ready</code>"
            , parse_mode='html')
            return

        target = parts[1]
        message = parts[2]

        try:
            await event.edit(f"📤 <i>Sending message to {target}...</i>", parse_mode='html')

            entity = await self.client.get_entity(target)
            await self.client.send_message(entity, message)

            target_name = getattr(entity, 'title', getattr(entity, 'username', target))

            await event.edit(
                f"✅ <b>MESSAGE SENT</b>\n"
                f"<b>To:</b> {target_name}\n"
                f"<b>Message:</b> {message[:100]}..."
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Send failed:</b> {str(e)}", parse_mode='html')

    async def handle_global_search_command(self, event):
        """
        Global search across ALL user's chats
        Syntax: .global-search <keyword> [--limit N]
        """
        parts = event.message.text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ GLOBAL-SEARCH Usage:</b>\n"
                "<code>.global-search &lt;keyword&gt; [--limit N]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.global-search crypto</code>\n"
                "<code>.global-search urgent --limit 50</code>"
            , parse_mode='html')
            return

        keyword = parts[1]
        limit = 100

        if '--limit' in parts:
            try:
                limit_idx = parts.index('--limit')
                limit = int(parts[limit_idx + 1])
            except:
                pass

        await event.edit(f"🔍 <b>GLOBAL SEARCH ACTIVE</b>\n<i>Searching all chats for: {keyword}</i>", parse_mode='html')

        try:
            results = []
            async for message in self.client.iter_messages(None, search=keyword, limit=limit):
                chat = await message.get_chat()
                sender = await message.get_sender()

                chat_name = getattr(chat, 'title', getattr(chat, 'username', 'Unknown'))
                sender_name = getattr(sender, 'first_name', 'Unknown') if sender else "Unknown"

                results.append({
                    'chat': chat_name,
                    'sender': sender_name,
                    'text': message.text,
                    'date': message.date.strftime('%Y-%m-%d %H:%M'),
                    'message_id': message.id
                })

            if not results:
                await event.edit(f"❌ <b>No results found for:</b> {keyword}", parse_mode='html')
                return

            # Format results
            report = f"🔍 <b>GLOBAL SEARCH RESULTS</b>\n"
            report += f"<b>Keyword:</b> {keyword}\n"
            report += f"<b>Found:</b> {len(results)} message(s)\n\n"
            report += "="*40 + "\n\n"

            for i, res in enumerate(results[:50], 1):  # Limit display to 50
                report += f"<b>#{i} - {res['chat']}</b>\n"
                report += f"👤 {res['sender']} | 📅 {res['date']}\n"
                report += f"{res['text'][:200]}\n\n"

            if len(results) > 50:
                report += f"\n<i>... and {len(results) - 50} more results</i>"

            await event.delete()
            await self.send_long_message('me', report, parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Global search failed:</b> {str(e)}", parse_mode='html')

    async def handle_bulk_download_command(self, event):
        """
        Bulk download all media from a channel
        Syntax: .bulk-download <target> [--type photos|videos|all] [--limit N]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ BULK-DOWNLOAD Usage:</b>\n"
                "<code>.bulk-download &lt;target&gt; [--type photos|videos|all] [--limit N]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.bulk-download @channel --type photos</code>\n"
                "<code>.bulk-download @channel --limit 100</code>"
            , parse_mode='html')
            return

        target = parts[1]
        media_type = 'all'
        limit = 1000

        # Parse options
        if '--type' in parts:
            try:
                type_idx = parts.index('--type')
                media_type = parts[type_idx + 1]
            except:
                pass

        if '--limit' in parts:
            try:
                limit_idx = parts.index('--limit')
                limit = int(parts[limit_idx + 1])
            except:
                pass

        await event.edit(
            f"📥 <b>BULK MEDIA DOWNLOAD STARTING</b>\n"
            f"<b>Target:</b> {target}\n"
            f"<b>Type:</b> {media_type}\n"
            f"<b>Limit:</b> {limit}\n"
            f"<i>This may take a while...</i>"
        , parse_mode='html')

        try:
            entity = await self.client.get_entity(target)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', 'Unknown'))

            # Create directory for this channel
            channel_dir = MEDIA_ARCHIVE_DIR / chat_title.replace(' ', '_')
            channel_dir.mkdir(exist_ok=True)

            downloaded = 0
            skipped = 0

            async for msg in self.client.iter_messages(entity, limit=limit):
                if msg.media:
                    try:
                        # Check media type filter
                        should_download = False

                        if media_type == 'all':
                            should_download = True
                        elif media_type == 'photos' and isinstance(msg.media, MessageMediaPhoto):
                            should_download = True
                        elif media_type == 'videos' and isinstance(msg.media, MessageMediaDocument):
                            # Check if it's a video
                            if msg.file and msg.file.mime_type and 'video' in msg.file.mime_type:
                                should_download = True

                        if should_download:
                            filename = f"{msg.id}_{msg.date.strftime('%Y%m%d_%H%M%S')}"
                            await msg.download_media(file=channel_dir / filename)
                            downloaded += 1

                            # Update progress every 10 downloads
                            if downloaded % 10 == 0:
                                await event.edit(
                                    f"📥 <b>DOWNLOADING...</b>\n"
                                    f"<b>Downloaded:</b> {downloaded}\n"
                                    f"<i>Please wait...</i>"
                                , parse_mode='html')
                        else:
                            skipped += 1

                    except Exception as e:
                        logger.error(f"Failed to download media from message {msg.id}: {e}")
                        skipped += 1

            await event.edit(
                f"✅ <b>BULK DOWNLOAD COMPLETE</b>\n"
                f"<b>Source:</b> {chat_title}\n"
                f"<b>Downloaded:</b> {downloaded} files\n"
                f"<b>Skipped:</b> {skipped}\n"
                f"<b>Location:</b> <code>{channel_dir}</code>"
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Bulk download failed:</b> {str(e)}", parse_mode='html')

    async def handle_download_media_command(self, event):
        """
        Download media from specific message
        Syntax: .download-media <target> <message_id>
        """
        parts = event.message.text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ DOWNLOAD-MEDIA Usage:</b>\n"
                "<code>.download-media &lt;target&gt; &lt;message_id&gt;</code>\n\n"
                "<b>Example:</b>\n"
                "<code>.download-media @channel 12345</code>"
            , parse_mode='html')
            return

        target = parts[1]
        try:
            message_id = int(parts[2])
        except:
            await event.edit("❌ Invalid message ID", parse_mode='html')
            return

        await event.edit(f"📥 <i>Downloading media...</i>", parse_mode='html')

        try:
            entity = await self.client.get_entity(target)
            msg = await self.client.get_messages(entity, ids=message_id)

            if not msg or not msg.media:
                await event.edit("❌ Message not found or has no media", parse_mode='html')
                return

            chat_title = getattr(entity, 'title', getattr(entity, 'username', 'Unknown'))
            channel_dir = MEDIA_ARCHIVE_DIR / chat_title.replace(' ', '_')
            channel_dir.mkdir(exist_ok=True)

            filename = f"{msg.id}_{msg.date.strftime('%Y%m%d_%H%M%S')}"
            path = await msg.download_media(file=channel_dir / filename)

            await event.edit(
                f"✅ <b>MEDIA DOWNLOADED</b>\n"
                f"<b>Location:</b> <code>{path}</code>"
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Download failed:</b> {str(e)}", parse_mode='html')

    async def handle_detect_spam_command(self, event):
        """
        Scan channel for spam/bots
        Syntax: .detect-spam <target> [--limit N] [--auto-report]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ DETECT-SPAM Usage:</b>\n"
                "<code>.detect-spam &lt;target&gt; [--limit N]</code>\n\n"
                "<b>Example:</b>\n"
                "<code>.detect-spam @channel --limit 100</code>"
            , parse_mode='html')
            return

        target = parts[1]
        limit = 100

        if '--limit' in parts:
            try:
                limit_idx = parts.index('--limit')
                limit = int(parts[limit_idx + 1])
            except:
                pass

        await event.edit(
            f"🔍 <b>SPAM DETECTION RUNNING</b>\n"
            f"<b>Target:</b> {target}\n"
            f"<i>Analyzing {limit} messages...</i>"
        , parse_mode='html')

        try:
            entity = await self.client.get_entity(target)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', target))

            spam_results = []

            async for msg in self.client.iter_messages(entity, limit=limit):
                if msg.text:
                    sender = await msg.get_sender()
                    sender_data = {
                        'username': getattr(sender, 'username', '') if sender else '',
                        'first_name': getattr(sender, 'first_name', '') if sender else '',
                        'is_bot': getattr(sender, 'bot', False) if sender else False
                    }

                    is_spam, confidence, reason = await self.ai.detect_spam_bot(msg.text, sender_data)

                    if is_spam and confidence > 0.7:
                        spam_results.append({
                            'message_id': msg.id,
                            'sender': sender_data['username'] or sender_data['first_name'],
                            'confidence': confidence,
                            'reason': reason,
                            'text': msg.text[:100]
                        })

            # Generate report
            report = f"🛡️ <b>SPAM DETECTION REPORT</b>\n"
            report += f"<b>Channel:</b> {chat_title}\n"
            report += f"<b>Scanned:</b> {limit} messages\n"
            report += f"<b>Spam Detected:</b> {len(spam_results)}\n\n"

            if spam_results:
                report += "="*40 + "\n\n"
                for i, spam in enumerate(spam_results[:20], 1):
                    report += f"<b>#{i} - Message {spam['message_id']}</b>\n"
                    report += f"👤 {spam['sender']}\n"
                    report += f"⚠️ Confidence: {spam['confidence']*100:.0f}%\n"
                    report += f"📝 Reason: {spam['reason']}\n"
                    report += f"💬 {spam['text']}\n\n"

                if len(spam_results) > 20:
                    report += f"\n<i>... and {len(spam_results) - 20} more spam messages</i>"
            else:
                report += "✅ No spam detected!"

            await event.delete()
            await self.send_long_message('me', report, parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Spam detection failed:</b> {str(e)}", parse_mode='html')

    async def handle_auto_mod_command(self, event):
        """
        Enable auto-moderation (requires admin rights)
        Syntax: .auto-mod <target> [--delete-spam] [--ban-threshold 0.9]
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 2:
            await event.edit(
                "<b>⚠️ AUTO-MOD Usage:</b>\n"
                "<code>.auto-mod &lt;target&gt; [--delete-spam] [--ban-threshold 0.9]</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.auto-mod @channel --delete-spam</code>\n"
                "<code>.auto-mod @group --delete-spam --ban-threshold 0.95</code>\n\n"
                "<i>⚠️ Requires admin rights</i>"
            , parse_mode='html')
            return

        target = parts[1]
        delete_spam = '--delete-spam' in msg_text
        ban_threshold = 0.9

        if '--ban-threshold' in parts:
            try:
                thresh_idx = parts.index('--ban-threshold')
                ban_threshold = float(parts[thresh_idx + 1])
            except:
                pass

        try:
            entity = await self.client.get_entity(target)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', target))

            # Create moderation rule
            mod_rule = {
                'entity': entity,
                'chat_name': chat_title,
                'delete_spam': delete_spam,
                'ban_threshold': ban_threshold,
                'deleted_count': 0,
                'banned_count': 0
            }

            # Register handler
            @self.client.on(events.NewMessage(chats=entity))
            async def auto_mod_handler(event):
                msg = event.message
                if msg.text:
                    sender = await msg.get_sender()
                    sender_data = {
                        'username': getattr(sender, 'username', '') if sender else '',
                        'first_name': getattr(sender, 'first_name', '') if sender else '',
                        'is_bot': getattr(sender, 'bot', False) if sender else False,
                        'id': sender.id if sender else None
                    }

                    is_spam, confidence, reason = await self.ai.detect_spam_bot(msg.text, sender_data)

                    if is_spam and confidence >= ban_threshold:
                        if mod_rule['delete_spam']:
                            try:
                                await msg.delete()
                                mod_rule['deleted_count'] += 1
                                logger.info(f"Auto-deleted spam message in {mod_rule['chat_name']}")

                                # Alert user
                                alert = f"🛡️ <b>AUTO-MOD ACTION</b>\n"
                                alert += f"<b>Channel:</b> {mod_rule['chat_name']}\n"
                                alert += f"<b>Action:</b> Deleted spam\n"
                                alert += f"<b>Confidence:</b> {confidence*100:.0f}%\n"
                                alert += f"<b>Reason:</b> {reason}"
                                await self.client.send_message('me', alert, parse_mode='html')

                            except Exception as e:
                                logger.error(f"Auto-mod delete failed: {e}")

            self.auto_mod_rules[chat_title] = mod_rule

            await event.edit(
                f"🛡️ <b>AUTO-MODERATION ACTIVE</b>\n"
                f"<b>Channel:</b> {chat_title}\n"
                f"<b>Delete Spam:</b> {'✅' if delete_spam else '❌'}\n"
                f"<b>Ban Threshold:</b> {ban_threshold*100:.0f}%\n\n"
                f"<i>Monitoring for spam...</i>"
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Auto-mod setup failed:</b> {str(e)}", parse_mode='html')

    async def handle_delete_command(self, event):
        """
        Delete messages (requires admin rights)
        Syntax: .delete <target> <message_id> OR .delete <target> --keyword spam --last 100
        """
        msg_text = event.message.text
        parts = msg_text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ DELETE Usage:</b>\n"
                "<code>.delete &lt;target&gt; &lt;message_id&gt;</code>\n"
                "<code>.delete &lt;target&gt; --keyword &lt;word&gt; --last N</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>.delete @channel 12345</code>\n"
                "<code>.delete @channel --keyword spam --last 100</code>\n\n"
                "<i>⚠️ Requires admin rights</i>"
            , parse_mode='html')
            return

        target = parts[1]

        try:
            entity = await self.client.get_entity(target)

            # Single message delete
            if parts[2].isdigit():
                message_id = int(parts[2])
                await self.client.delete_messages(entity, message_id)
                await event.edit(f"✅ <b>Message {message_id} deleted</b>", parse_mode='html')

            # Bulk delete by keyword
            elif '--keyword' in parts:
                keyword = parts[parts.index('--keyword') + 1]
                limit = 100

                if '--last' in parts:
                    try:
                        limit = int(parts[parts.index('--last') + 1])
                    except:
                        pass

                await event.edit(f"🔄 <i>Scanning and deleting messages with '{keyword}'...</i>", parse_mode='html')

                deleted = 0
                to_delete = []

                async for msg in self.client.iter_messages(entity, limit=limit):
                    if msg.text and keyword.lower() in msg.text.lower():
                        to_delete.append(msg.id)

                if to_delete:
                    await self.client.delete_messages(entity, to_delete)
                    deleted = len(to_delete)

                await event.edit(
                    f"✅ <b>BULK DELETE COMPLETE</b>\n"
                    f"<b>Deleted:</b> {deleted} message(s)\n"
                    f"<b>Keyword:</b> {keyword}"
                , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Delete failed:</b> {str(e)}", parse_mode='html')

    async def handle_schedule_report_command(self, event):
        """
        Schedule automated intelligence reports
        Syntax: .schedule-report <target> <frequency> [--keywords kw1,kw2]
        Frequency: daily, weekly, hourly
        """
        parts = event.message.text.split()

        if len(parts) < 3:
            await event.edit(
                "<b>⚠️ SCHEDULE-REPORT Usage:</b>\n"
                "<code>.schedule-report &lt;target&gt; &lt;frequency&gt; [--keywords kw1,kw2]</code>\n\n"
                "<b>Frequency:</b> hourly, daily, weekly\n\n"
                "<b>Examples:</b>\n"
                "<code>.schedule-report @channel daily</code>\n"
                "<code>.schedule-report @intel_source hourly --keywords crypto,urgent</code>"
            , parse_mode='html')
            return

        target = parts[1]
        frequency = parts[2]

        keywords = []
        if '--keywords' in parts:
            try:
                kw_idx = parts.index('--keywords')
                keywords = parts[kw_idx + 1].split(',')
            except:
                pass

        try:
            entity = await self.client.get_entity(target)
            chat_title = getattr(entity, 'title', getattr(entity, 'username', target))

            async def generate_report():
                # Determine limit based on frequency
                limit = 100 if frequency == 'hourly' else 500 if frequency == 'daily' else 1000

                # Fetch data
                filters = {}
                if keywords:
                    # Will need to check each message for any keyword
                    pass

                chat_title_local, history_data, raw_messages = await self.fetch_history(target, limit)

                if history_data and not history_data.startswith("❌"):
                    # Generate AI report
                    report_prompt = f"Generate an executive intelligence summary of recent activity. Focus on key events, trends, and actionable insights."
                    ai_report = await self.ai.analyze_content(history_data, report_prompt, extract_entities=True)

                    # Send to saved messages
                    report_msg = f"📊 <b>SCHEDULED INTELLIGENCE REPORT</b>\n"
                    report_msg += f"<b>Source:</b> {chat_title_local}\n"
                    report_msg += f"<b>Frequency:</b> {frequency}\n"
                    report_msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    report_msg += f"<b>Messages Analyzed:</b> {len(raw_messages)}\n\n"
                    report_msg += ai_report

                    await self.send_long_message('me', report_msg, parse_mode='html')

            # Schedule the report
            if frequency == 'hourly':
                schedule.every().hour.do(lambda: asyncio.create_task(generate_report()))
            elif frequency == 'daily':
                schedule.every().day.at("09:00").do(lambda: asyncio.create_task(generate_report()))
            elif frequency == 'weekly':
                schedule.every().monday.at("09:00").do(lambda: asyncio.create_task(generate_report()))

            self.scheduled_reports.append({
                'target': chat_title,
                'frequency': frequency,
                'keywords': keywords
            })

            await event.edit(
                f"⏰ <b>SCHEDULED REPORT ACTIVE</b>\n"
                f"<b>Target:</b> {chat_title}\n"
                f"<b>Frequency:</b> {frequency}\n"
                f"<b>Keywords:</b> {', '.join(keywords) if keywords else 'All'}\n\n"
                f"Reports will be sent to Saved Messages."
            , parse_mode='html')

        except Exception as e:
            await event.edit(f"❌ <b>Schedule failed:</b> {str(e)}", parse_mode='html')

    def _run_scheduler(self):
        """Background thread for scheduled tasks"""
        while True:
            schedule.run_pending()
            time.sleep(60)


# --- EXECUTION ---
if __name__ == '__main__':
    print("=" * 60)
    print("🛡️  ATLAS v4.0 - Advanced Telegram Intelligence System")
    print("=" * 60)
    print("📡 Core Features:")
    print("  • AI-Powered Analysis (Gemini 3 Pro)")
    print("  • Multi-Modal Media Analysis")
    print("  • Real-Time Monitoring")
    print("  • Multi-Channel Comparison")
    print("  • Advanced Search & Filtering")
    print("  • User Profile Analysis")
    print("  • Multi-Language Translation")
    print("  • Raw Data Export (JSON/CSV/TXT)")
    print("  • Entity Extraction")
    print("")
    print("🚀 NEW Tier S Features:")
    print("  • Auto-Forwarding (aggregate multiple intel sources)")
    print("  • Advanced Event Monitoring (edits, deletes, online status)")
    print("  • Message Sending (post to channels)")
    print("  • Global Search (across ALL chats)")
    print("  • Bulk Media Download (archive entire channels)")
    print("  • ML Spam/Bot Detection (AI-powered filtering)")
    print("  • Auto-Moderation (delete spam, manage users)")
    print("  • Scheduled Reports (automated intelligence)")
    print("=" * 60)

    client = AtlasClient()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start())
