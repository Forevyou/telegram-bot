import re
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("TOKEN")

BAD_WORDS = ["хуй", "пизд", "бля", "еб", "сука"]
SPAM_LIMIT = 3
SPAM_TIME = 5

user_messages = {}

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 Правила", callback_data="rules")]
    ]
    await update.message.reply_text(
        "Привет! Я админ-бот 🤖",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- RULES ----------
async def rules_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📜 Правила чата:\n"
        "1️⃣ Без мата\n"
        "2️⃣ Без ссылок\n"
        "3️⃣ Без спама\n"
        "4️⃣ Уважение друг к другу"
    )

# ---------- WELCOME ----------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            f"👋 Добро пожаловать, {user.first_name}!"
        )

async def moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.lower()
    user_id = update.message.from_user.id
    now = time.time()

    # --- АНТИЛИНК ---
    if re.search(r"(http|https|www\.|t\.me/)", text):
        await update.message.delete()
        return

    # --- АНТИМАТ ---
    for word in BAD_WORDS:
        if word in text:
            await update.message.delete()
            return

    # --- АНТИСПАМ ---
    user_messages.setdefault(user_id, [])
    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < SPAM_TIME]
    user_messages[user_id].append(now)

    if len(user_messages[user_id]) >= SPAM_LIMIT:
        await update.message.chat.restrict_member(
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=int(now + 60)
        )
        await update.message.reply_text("⏱ Спам → мут 1 минута")
        user_messages[user_id].clear()


# ---------- CLEAR CHAT ----------
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.from_user.id in [
        admin.user.id for admin in await update.message.chat.get_administrators()
    ]:
        return

    count = int(context.args[0]) if context.args else 5
    messages = await update.message.chat.get_history(limit=count + 1)
    for msg in messages:
        await msg.delete()

# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(rules_button, pattern="^rules$"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderation))

    app.run_polling()

if __name__ == "__main__":
    main()
