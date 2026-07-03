import os
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from .validators import validate_symbol, validate_positive_float
from .logger import logger

SYMBOL, SIDE, ORDER_TYPE, PRICE, QUANTITY, CONFIRM = range(6)

MENU_BUTTONS = {"💰 Balance", "📋 Logs", "⚙️ Settings", "📈 Trade"}

def check_owner(user_id: int) -> bool:
    owner_ids = os.getenv("TELEGRAM_OWNER_ID", "").split(",")
    return str(user_id).strip() in [oid.strip() for oid in owner_ids]

# ---- MAIN MENU ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the welcome message and locks the custom menu to the user's keyboard."""
    menu_keyboard = [
        [KeyboardButton("📈 Trade"), KeyboardButton("💰 Balance")],
        [KeyboardButton("📋 Logs"), KeyboardButton("⚙️ Settings")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        menu_keyboard,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Choose an action..."
    )
    
    welcome_text = (
        "👋 *Welcome to the Trading Bot!*\n\n"
        "Use the menu below to navigate your trading terminal."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

# ---- BALANCE CHECK ----
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_public = context.bot_data.get('is_public', False)
    
    if not is_public and not check_owner(update.message.from_user.id):
        await update.message.reply_text("⛔ Unauthorized. The bot is in Personal Mode.")
        return

    client = context.bot_data.get('binance_client')
    if not client:
        await update.message.reply_text("⚠️ Binance client is not configured on the bot.")
        return

    try:
        balances = await client.get_balance()
        prices = await client.get_all_prices()
    except Exception as e:
        logger.exception("Failed to fetch balances or prices")
        await update.message.reply_text(f"🔴 Error fetching balances: `{str(e)}`", parse_mode='Markdown')
        return

    # Format balances: show only non-zero entries
    lines = []
    total_usdt = 0.0
    for b in balances:
        asset = b.get("asset")
        try:
            bal = float(b.get("balance", 0) or 0)
        except Exception:
            bal = 0.0
        if bal <= 0:
            continue

        pair = f"{asset}USDT"
        value = None
        if pair in prices:
            try:
                value = prices[pair] * bal
                total_usdt += value
            except Exception:
                value = None

        if value is not None:
            lines.append(f"{asset}: `{bal:g}`  (~{value:.2f} USDT)")
        else:
            lines.append(f"{asset}: `{bal:g}`")

    if not lines:
        msg = "💼 *Balance Check*\n\n_No non-zero balances found._"
    else:
        msg = "💼 *Balance Check*\n\n" + "\n".join(lines)
        if total_usdt > 0:
            msg += f"\n\n*Estimated total:* {total_usdt:.2f} USDT"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ---- PERMISSION CONTROL ENGINE ----
async def set_permission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_owner(update.message.from_user.id):
        await update.message.reply_text("⛔ Unauthorized. Only the bot owner can change permissions.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔒 Personal Bot (Owner Only Access)", callback_data="MODE_PERSONAL")],
        [InlineKeyboardButton("🌍 Public Bot (Employer & Public Access)", callback_data="MODE_PUBLIC")]
    ]
    await update.message.reply_text(
        "⚙️ **Select Bot Access Mode:**\n\n"
        "Changing this settings updates access rules for both trading (`/trade`) and viewing logs (`/logs`).", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def handle_permission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if not check_owner(query.from_user.id):
        await query.answer("⛔ You are not authorized to change this.", show_alert=True)
        return
        
    await query.answer()
    if query.data == "MODE_PUBLIC":
        context.bot_data['is_public'] = True
        await query.edit_message_text("✅ Mode set to **Public Bot**.\n\nAnyone can now use `/trade` and view system `/logs`.")
        logger.info("Bot mode changed to PUBLIC by owner.")
    elif query.data == "MODE_PERSONAL":
        context.bot_data['is_public'] = False
        await query.edit_message_text("✅ Mode set to **Personal Bot**.\n\nOnly authorized owners can trade or view logs.")
        logger.info("Bot mode changed to PERSONAL by owner.")

# ---- TRADING LOGIC PIPELINE ----
async def start_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_public = context.bot_data.get('is_public', False)
    
    if not is_public and not check_owner(update.message.from_user.id):
        logger.warning(f"Unauthorized trade attempt blocked for ID: {update.message.from_user.id}")
        await update.message.reply_text("⛔ Unauthorized. The bot is currently locked down in **Personal Mode**.")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "🤖 **New Testnet Trade**\n\nEnter symbol (e.g. `BTCUSDT`):",
        parse_mode='Markdown'
    )
    return SYMBOL

async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Check if a menu button was pressed instead of a symbol
    if text in MENU_BUTTONS:
        if text == "💰 Balance":
            await check_balance(update, context)
        elif text == "📋 Logs":
            await print_logs(update, context)
        elif text == "⚙️ Settings":
            await set_permission(update, context)
        elif text == "📈 Trade":
            await start_trade(update, context)
            return SYMBOL
        return ConversationHandler.END
    
    try:
        symbol = validate_symbol(text)
        context.user_data['symbol'] = symbol
        
        keyboard = [
            [InlineKeyboardButton("🟢 BUY", callback_data="BUY"),
             InlineKeyboardButton("🔴 SELL", callback_data="SELL")]
        ]
        await update.message.reply_text(f"Symbol: **{symbol}**\nSelect Side:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SIDE
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}\nEnter a valid symbol:")
        return SYMBOL

async def handle_side(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['side'] = query.data

    keyboard = [
        [InlineKeyboardButton("⚡ MARKET", callback_data="MARKET"),
         InlineKeyboardButton("⏳ LIMIT", callback_data="LIMIT")]
    ]
    await query.edit_message_text(f"Side: **{query.data}**\nSelect Type:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ORDER_TYPE

async def handle_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['type'] = query.data

    if query.data == "LIMIT":
        await query.edit_message_text("Type: **LIMIT**\nEnter Limit Price:")
        return PRICE
    else:
        await query.edit_message_text("Type: **MARKET**\nEnter Quantity:")
        return QUANTITY

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Check if a menu button was pressed
    if text in MENU_BUTTONS:
        if text == "💰 Balance":
            await check_balance(update, context)
        elif text == "📋 Logs":
            await print_logs(update, context)
        elif text == "⚙️ Settings":
            await set_permission(update, context)
        elif text == "📈 Trade":
            await start_trade(update, context)
            return SYMBOL
        return ConversationHandler.END
    
    try:
        context.user_data['price'] = validate_positive_float(text, "Price")
        await update.message.reply_text("Enter Quantity:")
        return QUANTITY
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}\nEnter valid price:")
        return PRICE

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Check if a menu button was pressed
    if text in MENU_BUTTONS:
        if text == "💰 Balance":
            await check_balance(update, context)
        elif text == "📋 Logs":
            await print_logs(update, context)
        elif text == "⚙️ Settings":
            await set_permission(update, context)
        elif text == "📈 Trade":
            await start_trade(update, context)
            return SYMBOL
        return ConversationHandler.END
    
    try:
        context.user_data['quantity'] = validate_positive_float(text, "Quantity")
        
        d = context.user_data
        summary = f"📋 **Order Summary**\n▪️ {d['symbol']} | {d['side']} | {d['type']}\n▪️ Qty: {d['quantity']}\n"
        if d['type'] == 'LIMIT':
            summary += f"▪️ Price: {d['price']}\n"

        keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM"), InlineKeyboardButton("❌ Cancel", callback_data="CANCEL")]]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return CONFIRM
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}\nEnter valid quantity:")
        return QUANTITY

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "CANCEL":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END

    await query.edit_message_text("🚀 Placing order...")
    client = context.bot_data['binance_client']
    d = context.user_data
    
    try:
        res = await client.place_order(d['symbol'], d['side'], d['type'], d['quantity'], d.get('price'))
        msg = f"🟢 **Success**\nID: `{res.get('orderId')}`\nStatus: `{res.get('status')}`\nFilled: `{res.get('executedQty')}`"
        await query.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await query.message.reply_text(f"🔴 **Failed**\n`{str(e)}`", parse_mode='Markdown')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Session ended. Use the menu to start again.")
    return ConversationHandler.END

# ---- DYNAMIC LOG PRINTING FEATURE ----
async def print_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_public = context.bot_data.get('is_public', False)
    
    if not is_public and not check_owner(update.message.from_user.id):
        await update.message.reply_text("⛔ Unauthorized. Logs are hidden while the bot is in Personal Mode.")
        return

    log_path = "bot.log"
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            recent_logs = "".join(lines[-25:])
            
        safe_logs = html.escape(recent_logs)
        await update.message.reply_text(f"<b>Recent System Logs:</b>\n<pre>{safe_logs}</pre>", parse_mode='HTML')
    else:
        await update.message.reply_text("📭 Log file is currently empty or missing.")

# ---- ROUTER EXPORTS ----
def get_trade_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler('trade', start_trade),
            MessageHandler(filters.Regex('^📈 Trade$'), start_trade)
        ],
        states={
            SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol)],
            SIDE: [CallbackQueryHandler(handle_side, pattern='^(BUY|SELL)$')],
            ORDER_TYPE: [CallbackQueryHandler(handle_type, pattern='^(MARKET|LIMIT)$')],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            CONFIRM: [CallbackQueryHandler(handle_confirm, pattern='^(CONFIRM|CANCEL)$')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

def get_permission_handlers():
    return [
        CommandHandler('permission', set_permission),
        MessageHandler(filters.Regex('^⚙️ Settings$'), set_permission),
        CallbackQueryHandler(handle_permission_callback, pattern='^MODE_')
    ]