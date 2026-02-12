"""
MLBB Region Checker Telegram Bot
- Scrapes data from pizzoshop.com/mlchecker
- Returns nickname and region info
- Author: Generated for user
"""

import requests
from bs4 import BeautifulSoup
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ========== CONFIG ==========
BOT_TOKEN = "8439817369:AAH-Aw7m_WixsEHSPnR3U1caReT5YBeyGm0"  # @BotFather ကနေရယူပါ
# =============================

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'authority': 'pizzoshop.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://pizzoshop.com',
    'referer': 'https://pizzoshop.com/mlchecker',
    'user-agent': 'Mozilla/5.0 (Android 13; Mobile) AppleWebKit/537.36 Telegram Bot'
}

def check_mlbb_region(user_id: str, zone_id: str) -> dict:
    """Check MLBB region from pizzoshop.com and return formatted data"""
    
    url = "https://pizzoshop.com/mlchecker/check"
    data = {
        'user_id': user_id.strip(),
        'zone_id': zone_id.strip()
    }
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # First visit to get cookies
        session.get("https://pizzoshop.com/mlchecker", timeout=15)
        
        # Post the form
        response = session.post(url, data=data, timeout=20)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize result
        result = {
            'success': False,
            'nickname': None,
            'region_id': None,
            'last_login': None,
            'created_date': None,
            'error': None
        }
        
        # Check for error messages
        error_alert = soup.find('div', class_='alert-danger')
        if error_alert:
            error_text = error_alert.get_text(strip=True)
            result['error'] = error_text
            return result
        
        warning_alert = soup.find('div', class_='alert-warning')
        if warning_alert:
            warning_text = warning_alert.get_text(strip=True)
            result['error'] = warning_text
            return result
        
        # Find the result table
        table = soup.find('table', class_='table-modern')
        if not table:
            # Maybe still loading or no result
            result['error'] = "Account not found or server error"
            return result
        
        # Extract data from table
        rows = table.find_all('tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                header = th.get_text(strip=True).lower()
                value = td.get_text(strip=True)
                
                if 'nickname' in header:
                    result['nickname'] = value
                elif 'region id' in header:
                    result['region_id'] = value
                elif 'last login' in header:
                    result['last_login'] = value
                elif 'created' in header:
                    result['created_date'] = value
        
        # Check if we got any data
        if result['nickname'] or result['region_id']:
            result['success'] = True
        else:
            result['error'] = "No data found for this ID"
        
        return result
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': "⏱️ Request timeout. Server may be busy."}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': "📡 Connection error. Check your internet."}
    except Exception as e:
        logger.error(f"Error checking region: {e}")
        return {'success': False, 'error': f"❌ Unexpected error: {str(e)[:50]}"}

def format_result(result: dict, user_id: str, zone_id: str) -> str:
    """Format the result for Telegram message"""
    
    if not result['success']:
        error_msg = result.get('error', 'Unknown error')
        return f"""
❌ <b>MLBB Region Check Failed</b>

<b>ID:</b> <code>{user_id}</code> ({zone_id})
<b>Error:</b> {error_msg}

💡 Tips:
• Double-check your ID and Zone
• Make sure account exists
• Try again later
"""
    
    # Success format
    nickname = result.get('nickname', 'N/A')
    region = result.get('region_id', 'N/A')
    last_login = result.get('last_login', 'N/A')
    created = result.get('created_date', 'N/A')
    
    # Clean up nickname if it has ellipsis
    if nickname and '...' in nickname:
        nickname = nickname.replace('...', '')
    
    return f"""
✅ <b>MLBB Account Found</b>

━━━━━━━━━━━━━━━━━━━
<b>🎮 Nickname:</b> <code>{nickname}</code>
<b>🆔 User ID:</b> <code>{user_id}</code>
<b>🌍 Zone ID:</b> <code>{zone_id}</code>
━━━━━━━━━━━━━━━━━━━

<b>📍 Region ID:</b> {region}
<b>📱 Last Login:</b> {last_login}
<b>📅 Checked:</b> {created}

━━━━━━━━━━━━━━━━━━━
🔍 <i>Data from @iwillgoforwardsalone</i>
"""

# ============ TELEGRAM BOT HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    welcome_msg = f"""
🎮 <b>MLBB Region Checker Bot</b>

Hello {user.first_name}! 👋

I can check Mobile Legends account region.

━━━━━━━━━━━━━━━━━━━
<b>📌 How to use:</b>

1️⃣ Send ID and Zone like:
<code>847501216 12360</code>

2️⃣ Or use buttons below

━━━━━━━━━━━━━━━━━━━
<b>⚠️ Note:</b>
• Account must be public
• Server may be slow sometimes
• For educational purpose only
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Example ID", callback_data="example"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_msg, parse_mode='HTML', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "example":
        example_text = """
<b>📝 Example formats:</b>

• <code>847501216 12360</code>
• <code>123456789 9876</code>
• <code>552133482 2123</code>

Just send <b>UserID ZoneID</b> with space
"""
        await query.edit_message_text(example_text, parse_mode='HTML')
    
    elif query.data == "help":
        help_text = """
<b>❓ Help & Info</b>

This bot checks MLBB account region from PizzoShop.com.

<b>⚠️ Disclaimer:</b>
• Not official MLBB tool
• Data may not be 100% accurate
• For personal use only

<b>🛠 Commands:</b>
/start - Welcome message
/help - This help

<b>📮 Contact:</b> @your_username
"""
        await query.edit_message_text(help_text, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
<b>🔍 MLBB Region Checker</b>

<b>Usage:</b>
Send User ID and Zone ID separated by space.

<b>Examples:</b>
<code>847501216 12360</code>
<code>12345678 2123</code>

<b>Features:</b>
✅ Real-time check
✅ Nickname & Region
✅ Last login location
✅ Simple & fast
"""
    await update.message.reply_text(help_text, parse_mode='HTML')

async def check_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler - check MLBB region"""
    
    text = update.message.text.strip()
    
    # Check if it's ID and Zone format
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ <b>Invalid format!</b>\n\n"
            "Send <code>UserID ZoneID</code>\n"
            "Example: <code>847501216 12360</code>",
            parse_mode='HTML'
        )
        return
    
    user_id, zone_id = parts[0], parts[1]
    
    # Validate numeric
    if not user_id.isdigit() or not zone_id.isdigit():
        await update.message.reply_text(
            "❌ <b>Only numbers allowed!</b>\n\n"
            "User ID and Zone ID must contain only digits.",
            parse_mode='HTML'
        )
        return
    
    # Send "typing" action
    await update.message.chat.send_action(action="typing")
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔍 Checking MLBB account <code>{user_id}</code> ({zone_id})...\nPlease wait ⏳",
        parse_mode='HTML'
    )
    
    # Perform the check
    result = check_mlbb_region(user_id, zone_id)
    
    # Format and send result
    formatted_result = format_result(result, user_id, zone_id)
    
    # Add inline button for quick recheck
    keyboard = [[InlineKeyboardButton("🔄 Check Again", callback_data="none")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await processing_msg.edit_text(
        formatted_result,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

def main():
    """Start the bot"""
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ ERROR: Please set your BOT_TOKEN in the script!")
        print("Get token from @BotFather on Telegram")
        return
    
    # Create Application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_region))
    
    print("✅ MLBB Region Bot is running...")
    print("Press Ctrl+C to stop")
    
    # Start the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
