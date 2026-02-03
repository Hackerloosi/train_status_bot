from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import requests
from datetime import datetime

# =========================
# CONFIG
# =========================
BOT_TOKEN = "7432992828:AAGHEP1uQuhiATRA8Ns63-TylQRe4vq9crw"
ADMIN_ID = 1609002531   # your Telegram numeric ID

ADMINS = {ADMIN_ID}
USERS = set()

# =========================
# KEYBOARD (NORMAL USERS)
# =========================
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("/Single"), KeyboardButton("/List")]
        ],
        resize_keyboard=True
    )

# =========================
# HELPERS
# =========================
def is_admin(uid):
    return uid in ADMINS

def minutes_to_hm(m):
    if not m or m <= 0:
        return "On Time"
    return f"{m//60}h {m%60}m"

# =========================
# NTES LIVE FETCH (ON-DEMAND)
# =========================
def fetch_train_status(train_no, date_ddmmyyyy):
    # Convert date
    try:
        date_obj = datetime.strptime(date_ddmmyyyy, "%d/%m/%Y")
        journey_date = date_obj.strftime("%d-%m-%Y")
    except:
        return {"error": "Invalid date format (use DD/MM/YYYY)"}

    url = (
        "https://enquiry.indianrail.gov.in/ntes/"
        f"NTES?action=getTrainRunningStatus&trainNo={train_no}&journeyDate={journey_date}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://enquiry.indianrail.gov.in/ntes/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
    except:
        return {"error": "NTES not reachable"}

    if "errorMessage" in data:
        return {"error": data["errorMessage"]}

    stations = data.get("stationList", [])
    if not stations:
        return {"error": "No station data available"}

    last = None
    for s in stations:
        if s.get("actualArrival") or s.get("actualDeparture"):
            last = s

    if not last:
        return {"error": "No live update yet"}

    # TERMINATED case
    if data.get("trainStatus") == "TERMINATED":
        return {
            "terminated": True,
            "station": last.get("stationName"),
            "time": last.get("actualArrival") or last.get("actualDeparture")
        }

    return {
        "terminated": False,
        "station": last.get("stationName"),
        "time": last.get("actualArrival") or last.get("actualDeparture"),
        "delay_min": last.get("delayArrival", 0)
    }

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USERS.add(uid)

    msg = (
        "🤖 Bot Status: ONLINE 🟢\n"
        "⚡ Service: Active\n\n"
        "📱 Please Send Train No.\n"
        "To get live Running status"
    )

    await update.message.reply_text(
        msg,
        reply_markup=main_keyboard()
    )

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📋 Train List\n\n"
        "1. 22222 03/02/2026\n"
        "2. 12261 02/02/2026\n\n"
        "Use:\n/single <TrainNo> <DD/MM/YYYY>"
    )
    await update.message.reply_text(msg)

async def single_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Format:\n/single 22222 03/02/2026"
        )
        return

    train, date = context.args
    await update.message.reply_text("⏳ Fetching live status...")

    data = fetch_train_status(train, date)

    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}")
        return

    if data["terminated"]:
        msg = (
            f"🚆 Train: {train}\n"
            f"📅 Date: {date}\n\n"
            f"⛔ Status: TERMINATED\n"
            f"📍 At: {data['station']}\n"
            f"🕒 Time: {data['time']}"
        )
    else:
        msg = (
            f"🚆 Train: {train}\n"
            f"📅 Date: {date}\n\n"
            f"🚉 Last Station: {data['station']}\n"
            f"🕒 Passed Time: {data['time']}\n"
            f"⏱ Delay: {minutes_to_hm(data['delay_min'])}\n"
            f"📍 Status: Running"
        )

    await update.message.reply_text(msg)

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = " ".join(context.args)
    for uid in USERS:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass
    await update.message.reply_text("📢 Sent to all users")

# =========================
# COMMAND MENU (ADMIN ONLY)
# =========================
async def set_commands(app):
    user_cmds = [
        BotCommand("start", "Start the bot"),
        BotCommand("single", "Get live train status"),
        BotCommand("list", "Show train list"),
    ]

    admin_cmds = user_cmds + [
        BotCommand("admin", "Send message to all users"),
    ]

    await app.bot.set_my_commands(user_cmds, scope=BotCommandScopeDefault())

    for admin_id in ADMINS:
        await app.bot.set_my_commands(
            admin_cmds,
            scope=BotCommandScopeChat(chat_id=admin_id)
        )

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("single", single_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))

    app.post_init = set_commands

    print("🚀 Bot polling started")
    app.run_polling()

if __name__ == "__main__":
    main()
