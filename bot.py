import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.environ.get("BOT_TOKEN")

LAST_UNIT = 0
THIS_UNIT = 1

SERVICE_FEE = 500

def calculate_bill(units: int):
    tiers = []
    remaining = units

    tier1 = min(remaining, 50)
    if tier1 > 0:
        tiers.append((1, min(units, 50), 50, tier1 * 50))
        remaining -= tier1

    tier2 = min(remaining, 50)
    if tier2 > 0:
        tiers.append((51, min(units, 100), 100, tier2 * 100))
        remaining -= tier2

    tier3 = min(remaining, 100)
    if tier3 > 0:
        tiers.append((101, min(units, 200), 150, tier3 * 150))
        remaining -= tier3

    if remaining > 0:
        tiers.append((201, units, 300, remaining * 300))

    subtotal = sum(t[3] for t in tiers)
    total = subtotal + SERVICE_FEE
    return tiers, subtotal, total

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
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
    tiers, subtotal, total = calculate_bill(units_used)

    breakdown = ""
    for (start_u, end_u, rate, cost) in tiers:
        count = end_u - start_u + 1
        breakdown += (
            f"  • {start_u}–{end_u} units → {count} units × {rate:,} ks = {cost:,} ks\n"
            f"    ({start_u} မှ {end_u} ယူနစ်အတွက် တစ်ယူနစ် {rate:,} ကျပ်နှုန်းဖြင့် တွက်ထားပါသည်။)\n"
        )

    await update.message.reply_text(
        f"Last month / ယခင်လ: {last_unit} units\n"
        f"This month / ယခုလ: {this_unit} units\n"
        f"Units used / သုံးစွဲထားသော ပမာဏ: {units_used} units\n\n"
        f"📊 Breakdown / တွက်ချက်ပုံ:\n"
        f"(Myanmar electricity uses a tiered rate — the more you use, the higher the rate per unit.)\n"
        f"(မြန်မာနိုင်ငံ၏ လျှပ်စစ်ဓာတ်အားခွဲတမ်းနှုန်းထားများသည် သုံးစွဲမှုပမာဏပေါ်မူတည်၍ တိုးလာပါသည်။)\n\n"
        f"{breakdown}\n"
        f"Subtotal / ကြေးငွေပေါင်း: {subtotal:,} ks\n"
        f"Service fee / ဝန်ဆောင်ကြေး: {SERVICE_FEE:,} ks\n"
        f"──────────────────\n"
        f"💰 Total Bill / စုစုပေါင်း ပေးချေရမည့်ငွေ: {total:,} kyats\n\n"
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
