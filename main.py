from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ChatJoinRequest

from config import LEVEL_CONFIG, BOX_CONFIG, BET_CONFIG, ADMINS, MAIN_ADMIN_ID, GROUP_LINK
from database import (
    get_user_points, add_points, remove_points, set_points,
    get_user_level, get_progress_bar, check_level_up, load_points,
    get_active_bet, create_bet, cancel_bet, resolve_bet
)

import commands
import betting
import box_game
import ai
import events
import movie_search
import rps_game

# ========== ایجاد کلاینت ربات ==========
app = Client("SM")

# ========== ثبت دستورات عمومی ==========
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await commands.start_command(client, message)

@app.on_message(filters.command("help"))
async def help_handler(client, message):
    await commands.help_command(client, message)

@app.on_message(filters.command("points"))
async def points_handler(client, message):
    await commands.points_command(client, message)

@app.on_message(filters.command("leaderboard"))
async def leaderboard_handler(client, message):
    await commands.leaderboard_command(client, message)

# ========== ثبت دستورات ادمین ==========
@app.on_message(filters.command("addpoints") & filters.user(ADMINS))
async def addpoints_handler(client, message):
    await commands.admin_add_points(client, message)

@app.on_message(filters.command("removepoints") & filters.user(ADMINS))
async def removepoints_handler(client, message):
    await commands.admin_remove_points(client, message)

@app.on_message(filters.command("setpoints") & filters.user(ADMINS))
async def setpoints_handler(client, message):
    await commands.admin_set_points(client, message)

# ========== ثبت هندلرهای شرط‌بندی ==========
@app.on_message(filters.command("bet"))
async def bet_handler(client, message):
    await betting.bet_command(client, message)

@app.on_message(filters.command("cancelbet"))
async def cancelbet_handler(client, message):
    await betting.cancelbet_command(client, message)

@app.on_message(filters.command("mybets"))
async def mybets_handler(client, message):
    await betting.mybets_command(client, message)

@app.on_callback_query(filters.regex(r"^bet_"))
async def bet_callback_handler(client, callback_query):
    await betting.handle_bet_callback(client, callback_query)

@app.on_message(filters.dice)
async def dice_game_handler(client, message):
    await betting.dice_handler(client, message)

# ========== ثبت هندلر AI (در گروه و پیوی) ==========
@app.on_message(filters.command("ai") & (filters.group | filters.private))
async def ai_handler(client, message):
    await ai.ai_command(client, message)

# ========== ثبت هندلر جستجوی فیلم ==========
@app.on_message(filters.command("movie") & (filters.group | filters.private))
async def movie_handler(client, message):
    await movie_search.movie_command(client, message)

@app.on_callback_query(filters.regex(r"^mv_"))
async def movie_callback_handler(client, callback_query):
    await movie_search.handle_movie_callback(client, callback_query)

# ========== ثبت هندلر سنگ کاغذ قیچی ==========
@app.on_message(filters.command("rps") & (filters.group | filters.private))
async def rps_handler(client, message):
    await rps_game.rps_command(client, message)

@app.on_callback_query(filters.regex(r"^rps_"))
async def rps_callback_handler(client, callback_query):
    await rps_game.handle_rps_callback(client, callback_query)

# ========== ثبت هندلر جعبه (باید آخرین هندلر باشه) ==========
@app.on_message(filters.group & filters.text)
async def box_message_handler(client, message):
    # فقط پیام‌های معمولی رو بگیر (نه دستورات)
    if not message.text.startswith('/'):
        await box_game.auto_box_handler(client, message)

@app.on_callback_query(filters.regex(r"^box_"))
async def box_callback_handler(client, callback_query):
    await box_game.handle_box_callback(client, callback_query)

# ========== ثبت هندلرهای رویدادها ==========
@app.on_chat_join_request()
async def join_request_event_handler(client, chat_join_request):
    await events.join_request_handler(client, chat_join_request)

@app.on_callback_query(filters.regex(r"^(approve|reject)_"))
async def join_request_callback_handler(client, callback_query):
    await events.handle_join_request_callback(client, callback_query)

@app.on_message(filters.command("pending") & filters.user([MAIN_ADMIN_ID]))
async def pending_requests_handler(client, message):
    await events.pending_requests_command(client, message)

# ========== اجرای ربات ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Shahmoradi Bot is Running...")
    print("=" * 50)
    print(f"📊 Level System: {len(LEVEL_CONFIG)} levels")
    print(f"🎲 Betting System: Active")
    print(f"   └─ Min Bet: {BET_CONFIG['min_bet']} | Max Bet: {BET_CONFIG['max_bet']}")
    print(f"📦 Box System: Every {BOX_CONFIG['message_threshold']} messages")
    print(f"   └─ Reward: {BOX_CONFIG['min_reward']}-{BOX_CONFIG['max_reward']} points")
    print(f"🤖 AI System: Gemini 2.5 Flash")
    print(f"✊ Rock Paper Scissors: Active")
    print(f"🎬 Movie System: {len(movie_search.load_movies())} titles loaded")
    print(f"👥 Admins: {len(ADMINS)} registered")
    print("=" * 50)
    print("✅ All handlers registered successfully!")
    print("🔄 Bot is now listening for messages...")
    print("=" * 50)
    
    app.run()