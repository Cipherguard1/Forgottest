import os
import re
import asyncio
import uvicorn
from fastapi import FastAPI
from telethon import TelegramClient, events
from telegram import Bot, InputMediaPhoto, InputMediaVideo

# --- CONFIG (hardcoded values) ---
api_id = 24878661
api_hash = "7fd279b83c40a0d4228b89978685638a"
bot_token = "8004684118:AAF0zw_lxsk93uNOnD3M7CCgM70Rmdr76Q4"

# Channels
source_channel = "@Signals_Pumps_Free"          # Copy FROM
target_channel = "@aixauusdbtcusd_trade"        # Copy TO

# Replace all links/mentions with this
replace_link = "@aimanagementteambot"

# --- TELEGRAM CLIENT (for reading) ---
client = TelegramClient("session", api_id, api_hash)

# --- BOT CLIENT (for sending) ---
bot = Bot(token=bot_token)

# --- WEB APP (for Render health check) ---
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

# --- HELPERS ---
def replace_links_and_mentions(text: str) -> str:
    """Replace all URLs and @mentions with custom link."""
    if not text:
        return ""
    text = re.sub(r"(https?://\S+|www\.\S+|t\.me/\S+)", replace_link, text)
    text = re.sub(r"@\w+", replace_link, text)
    return text

# --- MESSAGE HANDLER ---
@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    msg = event.message
    caption = replace_links_and_mentions(msg.text or msg.message or "")

    if msg.text and not msg.media:
        await bot.send_message(chat_id=target_channel, text=caption)

    elif msg.photo:
        file = await msg.download_media(file="temp.jpg")
        await bot.send_photo(chat_id=target_channel, photo=open(file, "rb"), caption=caption)
        os.remove(file)

    elif msg.video:
        file = await msg.download_media(file="temp.mp4")
        await bot.send_video(chat_id=target_channel, video=open(file, "rb"), caption=caption)
        os.remove(file)

    elif msg.document:
        file = await msg.download_media(file="temp_file")
        await bot.send_document(chat_id=target_channel, document=open(file, "rb"), caption=caption)
        os.remove(file)

    elif msg.voice:
        file = await msg.download_media(file="temp.ogg")
        await bot.send_voice(chat_id=target_channel, voice=open(file, "rb"), caption=caption)
        os.remove(file)

    elif msg.sticker:
        file = await msg.download_media(file="sticker.webp")
        await bot.send_sticker(chat_id=target_channel, sticker=open(file, "rb"))
        os.remove(file)

# --- ALBUM HANDLER (multiple media in one post) ---
@client.on(events.Album(chats=source_channel))
async def album_handler(event):
    media_group = []
    caption = replace_links_and_mentions(event.messages[0].text or "")

    for msg in event.messages:
        file = await msg.download_media()
        media_group.append((file, msg))

    media = []
    for idx, (file, msg) in enumerate(media_group):
        if msg.photo:
            media.append(InputMediaPhoto(open(file, "rb"), caption=caption if idx == 0 else None))
        elif msg.video:
            media.append(InputMediaVideo(open(file, "rb"), caption=caption if idx == 0 else None))

    if media:
        await bot.send_media_group(chat_id=target_channel, media=media)

    for file, _ in media_group:
        try:
            os.remove(file)
        except:
            pass

# --- RUN BOT + WEB SERVER ---
async def start_bot():
    await client.start()   # first run will ask for phone + code
    print("Telegram bot is running...")
    await client.run_until_disconnected()

def start():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    start()
