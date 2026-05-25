import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.logger import logger
from bot.binance_client import BinanceFuturesClient
from bot.telegram_ui import (
    get_trade_handler, 
    get_permission_handlers, 
    print_logs, 
    start, 
    check_balance
)

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ("", port)
    
    class HealthCheckHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot status: ONLINE")

    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"Background web server running on port {port}")
    httpd.serve_forever()

def main():
    load_dotenv()
    logger.info("Initializing Telegram Trading Bot...")
    
    API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
    API_SECRET = os.getenv("BINANCE_TESTNET_SECRET_KEY")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OWNER_ID = os.getenv("TELEGRAM_OWNER_ID")

    if not all([API_KEY, API_SECRET, BOT_TOKEN, OWNER_ID]):
        logger.error("Missing environment variables! Check configurations.")
        return

    # Start dummy web server for Render keep-alive
    threading.Thread(target=run_health_server, daemon=True).start()

    binance_client = BinanceFuturesClient(API_KEY, API_SECRET)

    app = Application.builder().token(BOT_TOKEN).build()
    
    # Inject variables into bot memory
    app.bot_data['binance_client'] = binance_client
    app.bot_data['is_public'] = False  # Default to securely locked (Personal) on startup
    
    # --- HANDLER ROUTING ---
    
    # 1. Start Command (Generates the Bottom Menu)
    app.add_handler(CommandHandler("start", start))
    
    # 2. Trade Handler (Handles /trade and "📈 Trade" button)
    app.add_handler(get_trade_handler())
    
    # 3. Logs Handler (Handles /logs and "📋 Logs" button)
    app.add_handler(CommandHandler('logs', print_logs))
    app.add_handler(MessageHandler(filters.Regex('^📋 Logs$'), print_logs))
    
    # 4. Balance Handler (Handles /balance and "💰 Balance" button)
    app.add_handler(CommandHandler('balance', check_balance))
    app.add_handler(MessageHandler(filters.Regex('^💰 Balance$'), check_balance))
    
    # 5. Permission/Settings Handlers (Handles /permission, "⚙️ Settings", and Inline button callbacks)
    for handler in get_permission_handlers():
        app.add_handler(handler)

    logger.info("Bot is active. Waiting for commands...")
    app.run_polling()

if __name__ == '__main__':
    main()