import os
import json
import requests

from telegram import (
    Update,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

ADMIN_ID = 1609002531
API_URL = "https://giga-seven.vercel.app/api?key=NIGHTFALLHUB&num="

APPROVED_FILE = "approved_users.json"
PENDING_FILE = "pending_users.json"
BANNED_FILE = "banned_users.json"

# ================= STORAGE =================

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

approved_users = load_json(APPROVED_FILE)
pending_users = load_json(PENDING_FILE)
banned_users = load_json(BANNED_FILE)

def user_text(uid, info):
    name = info.get("name", "Unknown")
    username = info.get("username")
    uname = f"@{username}" if username else "NoUsername"
    return f"{name} ({uname})\nID: {uid}"

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    status = (
        "🤖 Bot Status: ONLINE 🟢\n"
        "⚡ Service: Active\n\n"
    )

    if uid in banned_users:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    if user.id == ADMIN_ID or uid in approved_users:
        await update.message.reply_text(
            status +
            "📱 Please Send Mobile No.\n"
            "Without +91\n"
            "In 10 Digit\n\n"
            "[ Note : Only Indian No. Allowed ]"
        )
        return

    if uid not in pending_users:
        pending_users[uid] = {
            "name": user.full_name,
            "username": user.username
        }
        save_json(PENDING_FILE, pending_users)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 New User Approval Request\n\n"
                f"{user_text(uid, pending_users[uid])}\n\n"
                f"Approve using:\n/approve {uid}"
            )
        )

    await update.message.reply_text(
        status +
        "⏳ Awaiting for approval from owner...\n"
        "🕒 Please wait, you will be notified once approved."
    )

# ================= ADMIN =================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return

    uid = context.args[0]

    if uid not in pending_users:
        await update.message.reply_text("User not found in pending list.")
        return

    approved_users[uid] = pending_users[uid]
    pending_users.pop(uid)

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)

    await update.message.reply_text(
        f"✅ Approved:\n{user_text(uid, approved_users[uid])}"
    )

    await context.bot.send_message(
        chat_id=int(uid),
        text=(
            "✅ Owner approved you!\n\n"
            "🎉 Now you can use this bot.\n"
            "📱 Send /start to begin."
        )
    )

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return

    uid = context.args[0]

    info = approved_users.pop(uid, None) or pending_users.pop(uid, None)
    if not info:
        await update.message.reply_text("User not found.")
        return

    banned_users[uid] = info

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)
    save_json(BANNED_FILE, banned_users)

    await update.message.reply_text(
        f"🚫 Banned:\n{user_text(uid, info)}"
    )

async def approved_list(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    if not approved_users:
        await update.message.reply_text("No approved users.")
        return

    msg = "✅ Approved Users:\n\n"
    for uid, info in approved_users.items():
        msg += user_text(uid, info) + "\n\n"

    await update.message.reply_text(msg)

async def pending_list(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    if not pending_users:
        await update.message.reply_text("No pending users.")
        return

    msg = "⏳ Pending Users:\n\n"
    for uid, info in pending_users.items():
        msg += user_text(uid, info) + "\n\n"

    await update.message.reply_text(msg)

# ================= DELETE USER =================

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    all_users = {}
    all_users.update(approved_users)
    all_users.update(pending_users)
    all_users.update(banned_users)

    if not all_users:
        await update.message.reply_text("No users found.")
        return

    buttons = []
    for uid, info in all_users.items():
        uname = f"@{info['username']}" if info.get("username") else "NoUsername"
        label = f"{info.get('name','User')} ({uname})"
        buttons.append([
            InlineKeyboardButton(
                text=f"Delete {label}",
                callback_data=f"delete:{uid}"
            )
        ])

    await update.message.reply_text(
        "🗑️ Delete User (Reset to New):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split(":")[1]

    approved_users.pop(uid, None)
    pending_users.pop(uid, None)
    banned_users.pop(uid, None)

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)
    save_json(BANNED_FILE, banned_users)

    await query.edit_message_text(
        f"🗑️ User deleted\nID: {uid}\n\n🔄 User is now NEW again."
    )

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in approved_users and update.effective_user.id != ADMIN_ID:
        return

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ Send valid 10-digit Indian number.")
        return

    await update.message.reply_text("🔍 Fetching details, please wait...")

    try:
        data = requests.get(API_URL + number, timeout=15).json()
    except:
        await update.message.reply_text("❌ API error.")
        return

    if not data.get("success") or not data.get("result"):
        await update.message.reply_text("❌ No data found.")
        return

    msg = ""
    for i, p in enumerate(data["result"], 1):
        email = p.get("EMAIL") or ""
        email_text = email.strip().lower() if email else "Email Not Found ❌"

        msg += (
            f"👤 Person {i} Details\n"
            f"Name : {p.get('NAME','')}\n"
            f"Father Name : {p.get('FATHER_NAME','')}\n"
            f"Address : {p.get('ADDRESS','').replace('!', ', ')}\n"
            f"Sim : {p.get('CIRCLE/SIM','')}\n"
            f"Mobile No. : {p.get('MOBILE','')}\n"
            f"Alternative No. : {p.get('ALTERNATIVE_MOBILE','')}\n"
            f"Aadhaar No. : {p.get('AADHAR_NUMBER','')}\n"
            f"Email ID : {email_text}\n\n"
        )

    msg += "━━━━━━━━━━━━━━\n🤖 Bot Made by @Mafiakabaap"
    await update.message.reply_text(msg)

# ================= COMMAND MENU =================

async def set_admin_commands(app):
    await app.bot.set_my_commands(
        [BotCommand("start", "Start the bot")],
        scope=BotCommandScopeDefault()
    )

    await app.bot.set_my_commands(
        [
            BotCommand("approve", "Approve user"),
            BotCommand("ban", "Ban user"),
            BotCommand("delete", "Delete / reset user"),
            BotCommand("approved", "Approved users"),
            BotCommand("pending", "Pending users"),
        ],
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

# ================= MAIN =================

def main():
    token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("delete", delete_user))
    app.add_handler(CommandHandler("approved", approved_list))
    app.add_handler(CommandHandler("pending", pending_list))
    app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.post_init = set_admin_commands
    app.run_polling()

if __name__ == "__main__":
    main()
