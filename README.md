# 🤖 Telegram Binance Futures Trading Bot

A production-ready Telegram bot engineered with the `python-telegram-bot` framework. It features a persistent app-like button control panel grid, conversational wizard pipelines for executing Testnet trades, remote live environment log streaming, and strict multi-tier owner verification access security profiles.

---

## ⚡ Main Technical Features

* **🎛️ Persistent Action Panel Keyboard:** Provides a persistent, app-like 2x2 grid user interface overlay (`📈 Trade`, `💰 Balance`, `📋 Logs`, `⚙️ Settings`) built with `ReplyKeyboardMarkup`.
* **🏗️ State-Driven Conversational Workflows:** Manages sequential trading state transitions (Symbol ➡️ Side ➡️ Execution Type ➡️ Price ➡️ Quantity ➡️ Confirm) without mixing message tracking.
* **🔌 Hybrid Message Routing UI Engine:** Unified pipeline inputs that respond identically to typed manual terminal text `/commands` or native bottom layout button triggers.
* **🌍 Multi-Tier Permission Engine:** Toggle dynamic runtime global operating context behaviors:
* **🔒 Personal Mode:** Secure strict lock down state. Restricts trading pipelines and diagnostic workspace text dumps exclusively to validated `TELEGRAM_OWNER_ID` entries.
* **🌍 Public Mode:** Opens access to the terminal functions, allowing third-party testers or employers to run trade operations.


* **🛠️ Robust Resilience System:** Outfitted with structural custom connection timeout pool configurations (30-second handshake limits) and deep exception capture safety blankets to stop unhandled network drops (`httpx.ReadTimeout`).
* **🌐 Integral Keep-Alive Web Server:** Built-in multi-threaded background HTTP server parsing internal endpoints (`PORT 8080`) to provide instant health monitoring indicators for continuous cloud hosting (e.g., Render, Railway).

---

## 📂 Project Architecture Blueprint

```text
telegram-trading-bot/
│
├── main.py                 # Central core lifecycle loader & networking router
├── .env                    # System-level sensitive environment storage keys
├── bot.log                 # Standard text stream diagnostic log target file
│
└── bot/
    ├── __init__.py         # Package identification anchor
    ├── telegram_ui.py      # Core workflow states, layouts, and button routing
    ├── binance_client.py   # Binance Futures secure API signature connection methods
    ├── validators.py       # Input data filters (Symbol/Float normalization)
    └── logger.py           # Stream terminal output formatter

```

---

## 🛠️ Installation & Environment Configuration

### 1. Clone Project Context and Workspace Dependencies

Ensure your workspace is running Python 3.10+. Open your terminal console inside the project repository folder and install dependencies:

```bash
pip install python-telegram-bot httpx python-dotenv

```

### 2. Configure Environment Secrets

Create a `.env` file in the root execution directory (`telegram-trading-bot/.env`):

```env
# --- TELEGRAM DEPLOYMENT CONFIGURATIONS ---
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_OWNER_ID="5728967994" # Paste your numeric account ID string here

# --- BINANCE TESTNET API KEY CONFIGURATIONS ---
BINANCE_TESTNET_API_KEY="your_binance_testnet_api_key"
TELEGRAM_OWNER_ID="5728967994"  # comma-separated string for multiple owners

# --- BINANCE TESTNET API KEY CONFIGURATIONS ---
BINANCE_TESTNET_API_KEY="your_binance_testnet_api_key"
BINANCE_TESTNET_SECRET_KEY="your_binance_testnet_secret_key"

# --- INFRASTRUCTURE CONFIGURATIONS ---
PORT=8080

```

---

## 🚀 Execution & Command Operations

Launch the local execution terminal loop by running:

```bash
python main.py

```

### Direct Terminal Interaction Grid

Once activated, navigate to your Telegram chat app. Enter `/start` to display the custom navigation deck.

| Visual Interface Grid | Slash Command Variant | Operational Action Response |
| --- | --- | --- |
| **`📈 Trade`** | `/trade` | Erases temporary data buffers and calls the step-by-step order entry process. |
| **`💰 Balance`** | `/balance` | Accesses `binance_client` to print account wallet structures. |
| **`📋 Logs`** | `/logs` | Escapes and prints the last 25 lines from `bot.log` as HTML code blocks. |
| **`⚙️ Settings`** | `/permission` | Renders inline interactive switches to toggle security states. |

---

## ⏱️ Critical Synchronization Troubleshooting Note

If trade placements throw a `Timestamp for this request is outside of the recvWindow` error from the Binance matching engine, your machine's system clock is out of sync with the internet.

### Fix on Windows Systems:

1. Right-click the system clock in your bottom taskbar and choose **Adjust date/time**.
2. Find the **Additional settings** heading section.
3. Click **Sync now** to recalibrate with internet time servers.
4. Restart your terminal application (`python main.py`).
