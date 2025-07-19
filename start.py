from telethon import TelegramClient, events, functions
import asyncio
import datetime
import pytz
import time
import ntplib  # نحتاج لتثبيته: pip install ntplib
import socket

api_id = 23203236
api_hash = 'a6475ebfa0a805aa4c1a39f168b2e701'
session = 'mysession'

client = TelegramClient(session, api_id, api_hash)

iraq_tz = pytz.timezone('Asia/Baghdad')

bad_words = ["كلمة1", "كلمة2", "كلمة3"]
welcome_message = "🎉 أهلًا بك في المجموعة!"
fast_game_keyword = "من هو الأسرع"
fast_game_response = "🔥 أنا الأسرع!"

last_private_reply = {}  # {user_id: آخر وقت رديت عليه تلقائياً أو يدوياً}

def get_precise_iraq_time():
    try:
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org', version=3, timeout=2)
        ts = response.tx_time
        iraq_time = datetime.datetime.fromtimestamp(ts, iraq_tz)
        return iraq_time
    except (ntplib.NTPException, socket.timeout, OSError):
        # لو ماكو نت، نرجع توقيت الجهاز
        return datetime.datetime.now(iraq_tz)

async def update_name_bio():
    patterns = [
        "أشهد أن علـياً ولي الله",
        "✦ سبحان الله ✦",
        "✦ الحمد لله ✦",
        "✦ لا إله إلا الله ✦"
    ]
    while True:
        now_dt = get_precise_iraq_time()
        now = now_dt.strftime("%I:%M %p")
        pattern = patterns[int(now_dt.second/15) % len(patterns)]
        await client(functions.account.UpdateProfileRequest(
            first_name=f"SRAYA | {now}"
        ))
        await client(functions.account.UpdateProfileRequest(
            about=f"{pattern} | {now}"
        ))
        await asyncio.sleep(15)

@client.on(events.NewMessage)
async def handle_messages(event):
    global last_private_reply
    sender = await event.get_sender()
    user_id = sender.id

    if event.is_private:
        now = time.time()
        if event.out:
            last_private_reply[user_id] = now
            return

        last_time = last_private_reply.get(user_id, 0)

        if now - last_time >= 300:
            await event.respond("👋 أنتظر لحد ما أجي وقره رسالتك")
            last_private_reply[user_id] = now

    elif event.is_group or event.is_channel:
        text = event.raw_text.lower()
        if any(bad_word in text for bad_word in bad_words):
            await event.reply("🚫 رجاءً استخدم ألفاظ محترمة.")
        if fast_game_keyword in text:
            await event.reply(fast_game_response)

@client.on(events.ChatAction)
async def welcome(event):
    if event.user_joined or event.user_added:
        await event.reply(welcome_message)

async def periodic_group_reply():
    while True:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                await client.send_message(dialog.id, "🌙 أشـهد أن علـياً ولي الله 🌙")
        await asyncio.sleep(100)

async def challenge():
    while True:
        await asyncio.sleep(300)
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                await client.send_file(dialog.id, 'challenge.jpg', caption="🕷️ من يعلق أولًا؟")

async def detect_new_session():
    prev_sessions = set()
    while True:
        sessions = set()
        authorized = await client(functions.account.GetAuthorizationsRequest())
        for auth in authorized.authorizations:
            sessions.add(auth.hash)
        if not prev_sessions:
            prev_sessions = sessions
        else:
            if sessions != prev_sessions:
                await client.send_message('me', '🚨 تنبيه: تم تسجيل دخول جديد لحسابك!')
                prev_sessions = sessions
        await asyncio.sleep(30)

with client:
    client.loop.create_task(update_name_bio())
    client.loop.create_task(periodic_group_reply())
    client.loop.create_task(challenge())
    client.loop.create_task(detect_new_session())
    client.run_until_disconnected()
