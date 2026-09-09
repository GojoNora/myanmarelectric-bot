import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.environ.get("BOT_TOKEN")

LAST_UNIT = 0
THIS_UNIT = 1

def calculate_bill(units: int) -> int:
    bill = 0
    if units <= 0:
        return 0
    if units <= 50:
        bill = units * 50
    elif units <= 100:
        bill = (50 * 50) + ((units - 50) * 100)
    elif units <= 200:
        bill = (50 * 50) + (50 * 100) + ((units - 100) * 150)
    else:
        bill = (50 * 50) + (50 * 100) + (100 * 150) + ((units - 200) * 300)
    return bill

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ Myanmar Electric Bill Calculator ⚡\n\n"
        "Please input last month meter reading unit.\n"
        "ယခင်လမီတာဖတ်တဲ့ ယူနစ်ကို ဖြည့်ပေးပါ။"
    )
    return LAST_UNIT

async def get_last_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text(
            "❌ Please enter numbers only. / ဂဏန်းသာ ထည့်ပေးပါ။"
        )
        return LAST_UNIT
    context.user_data["last_unit"] = int(text)
    await update.message.reply_text(
        "Please input this month meter reading unit.\n"
        "ယခုလမီတာဖတ်တဲ့ ယူနစ်ကို ထည့်ပေးပါ။"
    )
    return THIS_UNIT

async def get_this_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text(
            "❌ Please enter numbers only. / ဂဏန်းသာ ထည့်ပေးပါ။"
        )
        return THIS_UNIT

    this_unit = int(text)
    last_unit = context.user_data.get("last_unit", 0)

    if this_unit <= last_unit:
        await update.message.reply_text(
            "❌ This month's unit must be higher than last month's.\n"
            "ယခုလ ယူနစ်သည် ယခင်လထက် များရပါမည်။\n\n"
            "Please start again. / ထပ်စမ်းကြည့်ပါ။ /start"
        )
        return ConversationHandler.END

    units_used = this_unit - last_unit
    total_bill = calculate_bill(units_used)

    # Build breakdown
    breakdown = ""
    remaining = units_used
    if remaining > 0:
        tier1 = min(remaining, 50)
        breakdown += f"  {1}–{min(units_used,50)} units × 50 ks = {tier1 * 50:,} ks\n"
        remaining -= tier1
    if remaining > 0:
        tier2 = min(remaining, 50)
        breakdown += f"  51–{min(units_used,100)} units × 100 ks = {tier2 * 100:,} ks\n"
        remaining -= tier2
    if remaining > 0:
        tier3 = min(remaining, 100)
        breakdown += f"  101–{min(units_used,200)} units × 150 ks = {tier3 * 150:,} ks\n"
        remaining -= tier3
    if remaining > 0:
        breakdown += f"  201+ units × 300 ks = {remaining * 300:,} ks\n"

    await update.message.reply_text(
        f"⚡ Result / ရလဒ် ⚡\n\n"
        f"Last month / ယခင်လ: {last_unit} units\n"
        f"This month / ယခုလ: {this_unit} units\n"
        f"Units used / သုံးဆောင်မှု: {units_used} units\n\n"
        f"📊 Breakdown:\n"
        f"{breakdown}\n"
        f"💰 Total Bill / စုစုပေါင်း: {total_bill:,} kyats\n\n"
        f"To calculate again / ထပ်တွက်ရန်: /start"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Type /start to begin again. / /start နှိပ်ပြီး ထပ်စမ်းပါ။")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LAST_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_unit)],
            THIS_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_this_unit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()
