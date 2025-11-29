import os
import asyncio
import logging
import json
import csv
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import ChannelPrivateError, RPCError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, MessageMediaVoice, MessageMediaDocument as MessageMediaAudio
import google.generativeai as genai
from collections import defaultdict, Counter

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

    async def start(self):
        """Bootstraps the connection and registers event hooks."""
        logger.info("Initializing Atlas Protocol v2.0...")
        phone = os.getenv("PHONE_NUMBER")
        await self.client.start(phone=phone if phone else lambda: input('Please enter your phone: '))

        self.user_me = await self.client.get_me()
        logger.info(f"Atlas Online. Logged in as: {self.user_me.first_name} (@{self.user_me.username})")
        logger.info("Listening on 'Saved Messages' for commands...")
        logger.info("Available commands: .atlas, .watch, .compare, .export, .stop, .search, .profile, .export-raw, .translate")

        # Register the Command Listener
        self.client.add_event_handler(self.handle_command, events.NewMessage(outgoing=True, chats='me'))

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
        elif msg_text.startswith(".watch"):
            await self.handle_watch_command(event)

        # --- MULTI-CHANNEL COMPARISON ---
        elif msg_text.startswith(".compare"):
            await self.handle_compare_command(event)

        # --- EXPORT COMMAND ---
        elif msg_text.startswith(".export"):
            await self.handle_export_command(event)

        # --- STOP MONITORING ---
        elif msg_text.startswith(".stop"):
            await self.handle_stop_command(event)

        # --- SEARCH COMMAND ---
        elif msg_text.startswith(".search"):
            await self.handle_search_command(event)

        # --- USER PROFILE COMMAND ---
        elif msg_text.startswith(".profile"):
            await self.handle_profile_command(event)

        # --- RAW EXPORT COMMAND ---
        elif msg_text.startswith(".export-raw"):
            await self.handle_export_raw_command(event)

        # --- TRANSLATE COMMAND ---
        elif msg_text.startswith(".translate"):
            await self.handle_translate_command(event)

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


# --- EXECUTION ---
if __name__ == '__main__':
    print("=" * 60)
    print("🛡️  ATLAS v3.0 - Advanced Telegram Intelligence System")
    print("=" * 60)
    print("📡 Features:")
    print("  • AI-Powered Analysis (Gemini 3 Pro)")
    print("  • Multi-Modal Media Analysis")
    print("  • Real-Time Monitoring")
    print("  • Multi-Channel Comparison")
    print("  • Advanced Search & Filtering")
    print("  • User Profile Analysis")
    print("  • Multi-Language Translation")
    print("  • Raw Data Export")
    print("  • Export (JSON/CSV/TXT)")
    print("  • Entity Extraction")
    print("=" * 60)

    client = AtlasClient()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start())
