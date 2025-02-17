import os
import json
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load credentials from environment variables
try:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "0"))
    CONTROL_GROUP_ID = int(os.getenv("CONTROL_GROUP_ID", "0"))

    if not all([API_ID, API_HASH, SESSION_STRING, MAIN_ADMIN_ID, CONTROL_GROUP_ID]):
        raise ValueError("❌ Missing one or more required environment variables.")

except Exception as e:
    logger.error(f"❌ Error loading environment variables: {e}")
    raise

# File paths
ADMIN_FILE = "admins.json"
REPLACEMENT_FILE = "replacements.json"
SETTINGS_FILE = "settings.json"
MESSAGE_MAP_FILE = "message_map.json"

# Ensure essential files exist and load them
def ensure_files():
    try:
        if not os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, "w") as f:
                json.dump({"admins": [MAIN_ADMIN_ID]}, f)

        if not os.path.exists(REPLACEMENT_FILE):
            with open(REPLACEMENT_FILE, "w") as f:
                json.dump({
                    "links": {}, "texts": {}, "stickers": {}, "emojis": {},
                    "blocked": [], "blocked_content": {"videos": [], "images": [], "texts": [], "paragraphs": []}
                }, f)

        if not os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "w") as f:
                json.dump({"SOURCE_CHAT_IDS": [], "TARGET_CHAT_ID": None}, f)

        if not os.path.exists(MESSAGE_MAP_FILE):
            with open(MESSAGE_MAP_FILE, "w") as f:
                json.dump({}, f)

    except Exception as e:
        logger.error(f"❌ Error ensuring files: {e}")

ensure_files()

# Load settings
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"❌ Error loading settings: {e}")
        return {"SOURCE_CHAT_IDS": [], "TARGET_CHAT_ID": None}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"❌ Error saving settings: {e}")

# Load replacements
def load_replacements():
    try:
        with open(REPLACEMENT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"❌ Error loading replacements: {e}")
        return {
            "links": {}, "texts": {}, "stickers": {}, "emojis": {},
            "blocked": [], "blocked_content": {"videos": [], "images": [], "texts": [], "paragraphs": []}
        }

def save_replacements(data):
    try:
        with open(REPLACEMENT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"❌ Error saving replacements: {e}")

# Load admin list
def load_admins():
    try:
        with open(ADMIN_FILE, "r") as f:
            return json.load(f).get("admins", [MAIN_ADMIN_ID])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"❌ Error loading admin list: {e}")
        return [MAIN_ADMIN_ID]

# Load and save message ID mappings
def load_message_map():
    try:
        with open(MESSAGE_MAP_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_message_map(data):
    with open(MESSAGE_MAP_FILE, "w") as f:
        json.dump(data, f)

MESSAGE_MAP = load_message_map()

# Initialize Pyrogram Client
app = Client("bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# Check if user is admin
async def is_admin(user_id):
    return user_id in load_admins()

# Restrict commands to control group
def control_group_only():
    return filters.chat(CONTROL_GROUP_ID) if CONTROL_GROUP_ID else filters.command("")

# Load source & target chat IDs dynamically
def get_chat_ids():
    settings = load_settings()
    return settings["SOURCE_CHAT_IDS"], settings["TARGET_CHAT_ID"]

# Add source chat
@app.on_message(filters.command("addsource") & control_group_only())
async def add_source_chat(client, message: Message):
    if not await is_admin(message.from_user.id):
        return await message.reply_text("🚫 Only an admin can use this command.")

    try:
        _, chat_id = message.text.split(" ", 1)
        chat_id = int(chat_id)
        settings = load_settings()
        if chat_id not in settings["SOURCE_CHAT_IDS"]:
            settings["SOURCE_CHAT_IDS"].append(chat_id)
            save_settings(settings)
            await message.reply_text(f"✅ Source chat added: `{chat_id}`")
        else:
            await message.reply_text(f"⚠️ Source chat `{chat_id}` already exists.")
    except ValueError:
        await message.reply_text("⚠️ Invalid format! Use: `/addsource <chat_id>`")
    except Exception as e:
        logger.error(f"❌ Error adding source chat: {e}")
        await message.reply_text("⚠️ An error occurred while adding the source chat.")

# Remove source chat
@app.on_message(filters.command("removesource") & control_group_only())
async def remove_source_chat(client, message: Message):
    if not await is_admin(message.from_user.id):
        return await message.reply_text("🚫 Only an admin can use this command.")

    try:
        _, chat_id = message.text.split(" ", 1)
        chat_id = int(chat_id)
        settings = load_settings()
        if chat_id in settings["SOURCE_CHAT_IDS"]:
            settings["SOURCE_CHAT_IDS"].remove(chat_id)
            save_settings(settings)
            await message.reply_text(f"✅ Source chat removed: `{chat_id}`")
        else:
            await message.reply_text(f"⚠️ Source chat `{chat_id}` not found.")
    except ValueError:
        await message.reply_text("⚠️ Invalid format! Use: `/removesource <chat_id>`")
    except Exception as e:
        logger.error(f"❌ Error removing source chat: {e}")
        await message.reply_text("⚠️ An error occurred while removing the source chat.")

# Set target chat
@app.on_message(filters.command("settarget") & control_group_only())
async def set_target_chat(client, message: Message):
    if not await is_admin(message.from_user.id):
        return await message.reply_text("🚫 Only an admin can use this command.")

    try:
        _, chat_id = message.text.split(" ", 1)
        chat_id = int(chat_id)
        settings = load_settings()
        settings["TARGET_CHAT_ID"] = chat_id
        save_settings(settings)
        await message.reply_text(f"✅ Target chat updated to `{chat_id}`")
    except ValueError:
        await message.reply_text("⚠️ Invalid format! Use: `/settarget <chat_id>`")
    except Exception as e:
        logger.error(f"❌ Error setting target chat: {e}")
        await message.reply_text("⚠️ An error occurred while updating the target chat.")

# Forward and replace messages
@app.on_message(filters.chat(lambda _, __, message: message.chat.id in get_chat_ids()[0]))
async def forward_and_replace(client, message: Message):
    try:
        SOURCE_CHAT_IDS, TARGET_CHAT_ID = get_chat_ids()
        if not SOURCE_CHAT_IDS or not TARGET_CHAT_ID:
            return

        replacements = load_replacements()
        message_text = message.text or message.caption or ""
        for old, new in {**replacements["links"], **replacements["texts"], **replacements["emojis"]}.items():
            message_text = message_text.replace(old, new)

        sent_message = await client.send_message(TARGET_CHAT_ID, message_text) if message.text else \
                       await client.copy_message(TARGET_CHAT_ID, message.chat.id, message.message_id, caption=message_text)

        MESSAGE_MAP[str(message.message_id)] = sent_message.message_id
        save_message_map(MESSAGE_MAP)

    except Exception as e:
        logger.error(f"❌ Error forwarding message: {e}")

# Auto-edit forwarded messages
@app.on_edited_message(filters.chat(lambda _, __, message: message.chat.id in get_chat_ids()[0]))
async def edit_forwarded_message(client, message: Message):
    try:
        SOURCE_CHAT_IDS, TARGET_CHAT_ID = get_chat_ids()
        message_text = message.text or message.caption or ""
        replacements = load_replacements()

        for old, new in {**replacements["links"], **replacements["texts"], **replacements["emojis"]}.items():
            message_text = message_text.replace(old, new)

        if str(message.message_id) in MESSAGE_MAP:
            target_message_id = MESSAGE_MAP[str(message.message_id)]
            await client.edit_message_text(TARGET_CHAT_ID, target_message_id, message_text) if message.text else \
                await client.edit_message_caption(TARGET_CHAT_ID, target_message_id, caption=message_text)

    except Exception as e:
        logger.error(f"❌ Error editing message: {e}")

if __name__ == "__main__":
    logger.info("✅ Bot is starting...")
    app.run()
