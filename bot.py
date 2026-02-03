from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
BOT_TOKEN = "7432992828:AAGHEP1uQuhiATRA8Ns63-TylQRe4vq9crw"     # BotFather token
ADMIN_ID = 1609002531                  # your Telegram numeric ID

ADMINS = {ADMIN_ID}

USERS = set()
PENDING = set()
APPROVED = set()
BANNED = set()

TRAIN_LIST = [
    (1, "22222", "03/02/2026"),
    (2, "12261", "02/02/2026"),
    (3, "12951", "04/02/2026"),
]

# =========================
# KEYBOARD
# =========================
def main_keyboard(is_admin=False):
    rows = [[KeyboardButton("/Single"), KeyboardButton("/List")]]
    if is_admin:
        rows.append([KeyboardButton("/Admin")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def is_admin(uid): return uid in ADMINS

def minutes_to_hm(m):
    if m <= 0:
        return "On Time"
    return f"{m//60}h {m%60}m"

# =========================
# DUMMY STATUS (SAFE)
# =========================
def fetch_train_status(train, date):
    return {
        "last_station": "CNB",
        "passed_time": "01:42",
        "delay": 65
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
        reply_markup=main_keyboard(is_admin(uid))
    )

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 Train List\n\nS.No  Train   Date\n"
    for s, t, d in TRAIN_LIST:
        msg += f"{s}.    {t}   {d}\n"
    msg += "\nUse:\n/single <TrainNo> <DD/MM/YYYY>"
    await update.message.reply_text(msg)

async def single_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("/single 22222 03/02/2026")
        return

    train, date = context.args
    data = fetch_train_status(train, date)

    msg = (
        f"🚆 Train: {train}\n"
        f"📅 Date: {date}\n\n"
        f"🚉 Last Station: {data['last_station']}\n"
        f"🕒 Passed Time: {data['passed_time']}\n"
        f"⏱ Delay: {minutes_to_hm(data['delay'])}\n"
        f"📍 Status: Running"
    )
    await update.message.reply_text(msg)

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    for uid in USERS:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass
    await update.message.reply_text("📢 Sent to all users")

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("single", single_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))

    print("🚀 Bot polling started")
    app.run_polling()

if __name__ == "__main__":
    main()
