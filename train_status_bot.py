import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not found in Railway Variables")

# 🔐 ADMIN TELEGRAM USER IDs
ADMINS = {123456789}  # replace with your Telegram numeric ID

# Runtime memory (lightweight)
USERS = set()
PENDING = set()
APPROVED = set()
BANNED = set()

# Train list shown in /list
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

# =========================
# HELPERS
# =========================
def is_admin(uid): return uid in ADMINS
def is_allowed(uid): return uid not in BANNED

def minutes_to_hm(m):
    if m <= 0:
        return "On Time"
    return f"{m//60}h {m%60}m"

def fetch_train_status(train_no, date):
    """
    SAFE PLACEHOLDER
    (Keeps Railway stable, no overload)
    Replace later if you add real data source.
    """
    return {
        "terminated": False,
        "last_station": "CNB",
        "passed_time": "01:42",
        "delay_min": 65,
        "terminated_station": "",
        "terminated_time": ""
    }

# =========================
# /START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in BANNED:
        return

    USERS.add(uid)
    if uid not in APPROVED and not is_admin(uid):
        PENDING.add(uid)

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

# =========================
# USER COMMANDS
# =========================
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid):
        return

    msg = "📋 Train List\n\nS.No  Train   Date\n"
    for s, t, d in TRAIN_LIST:
        msg += f"{s}.    {t}   {d}\n"

    msg += "\nUse:\n/single <TrainNo> <DD/MM/YYYY>"
    await update.message.reply_text(msg)

async def single_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid):
        return

    if uid not in APPROVED and not is_admin(uid):
        await update.message.reply_text("⏳ Waiting for admin approval")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Format:\n/single 22222 03/02/2026"
        )
        return

    train, date = context.args
    await update.message.reply_text("⏳ Fetching live status...")

    data = fetch_train_status(train, date)

    if data["terminated"]:
        msg = (
            f"🚆 Train: {train}\n"
            f"📅 Date: {date}\n\n"
            f"📍 Status: TERMINATED\n"
            f"⏹ At: {data['terminated_station']}\n"
            f"🕒 Time: {data['terminated_time']}"
        )
    else:
        msg = (
            f"🚆 Train: {train}\n"
            f"📅 Date: {date}\n\n"
            f"🚉 Last Station: {data['last_station']}\n"
            f"🕒 Passed Time: {data['passed_time']}\n"
            f"⏱ Delay: {minutes_to_hm(data['delay_min'])}\n"
            f"📍 Status: Running"
        )

    await update.message.reply_text(msg)

# =========================
# ADMIN COMMANDS
# =========================
async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🕒 Pending Users:\n" + "\n".join(map(str, PENDING)) if PENDING else "No pending users"
    )

async def approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "✅ Approved Users:\n" + "\n".join(map(str, APPROVED)) if APPROVED else "No approved users"
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    PENDING.discard(uid)
    APPROVED.add(uid)
    await update.message.reply_text(f"✅ Approved: {uid}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    USERS.discard(uid)
    APPROVED.discard(uid)
    await update.message.reply_text(f"🗑 Removed: {uid}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    BANNED.add(uid)
    await update.message.reply_text(f"🚫 Banned: {uid}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = " ".join(context.args)
    for uid in USERS:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass
    await update.message.reply_text("📢 Message sent to all users")

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("single", single_cmd))

    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approved", approved))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("admin", admin_broadcast))

    print("✅ Bot running")
    app.run_polling()

if __name__ == "__main__":
    main()
