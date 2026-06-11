from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import add_points, remove_points, get_user_points, get_user_level, check_level_up
import random

# جوایز
WIN_POINTS = 15
LOSE_POINTS = 5

CHOICES = {
    "rock": "🪨 سنگ",
    "paper": "📄 کاغذ",
    "scissors": "✂️ قیچی"
}

# سنگ قیچی میزنه، کاغذ سنگ میزنه، قیچی کاغذ میزنه
WINS_AGAINST = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper"
}


async def rps_command(client, message: Message):
    """/rps — بازی سنگ کاغذ قیچی"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪨 سنگ", callback_data="rps_rock"),
            InlineKeyboardButton("📄 کاغذ", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ قیچی", callback_data="rps_scissors"),
        ]
    ])
    
    await message.reply(
        f"✊ **سنگ کاغذ قیچی!**\n\n"
        f"برد: +{WIN_POINTS} امتیاز\n"
        f"باخت: -{LOSE_POINTS} امتیاز\n"
        f"مساوی: بدون تغییر\n\n"
        f"انتخابت رو بزن 👇",
        reply_markup=keyboard
    )


async def handle_rps_callback(client, callback_query: CallbackQuery):
    """نتیجه بازی"""
    user = callback_query.from_user
    user_choice = callback_query.data.split("_")[1]  # rock / paper / scissors
    bot_choice = random.choice(list(CHOICES.keys()))
    
    user_points = get_user_points(user.id)
    
    # تعیین نتیجه
    if user_choice == bot_choice:
        result = "draw"
    elif WINS_AGAINST[user_choice] == bot_choice:
        result = "win"
    else:
        result = "lose"
    
    # اعمال امتیاز
    if result == "win":
        new_points = add_points(user.id, WIN_POINTS)
        level_up_info = check_level_up(user.id)
        current_level = get_user_level(user.id)
        
        text = (
            f"✊ **سنگ کاغذ قیچی**\n\n"
            f"تو: {CHOICES[user_choice]}\n"
            f"ربات: {CHOICES[bot_choice]}\n\n"
            f"🎉 **بردی! +{WIN_POINTS} امتیاز**\n"
            f"💰 امتیاز کل: {new_points}\n"
            f"{current_level['badge']} لول {current_level['level_num']}"
        )
        
        if level_up_info["level_up"]:
            text += f"\n\n🎊 لول‌اپ! به لول {level_up_info['new_level']} رسیدی!"
    
    elif result == "lose":
        new_points = remove_points(user.id, LOSE_POINTS)
        current_level = get_user_level(user.id)
        
        text = (
            f"✊ **سنگ کاغذ قیچی**\n\n"
            f"تو: {CHOICES[user_choice]}\n"
            f"ربات: {CHOICES[bot_choice]}\n\n"
            f"😅 **باختی! -{LOSE_POINTS} امتیاز**\n"
            f"💰 امتیاز کل: {new_points}\n"
            f"{current_level['badge']} لول {current_level['level_num']}"
        )
    
    else:  # مساوی
        current_level = get_user_level(user.id)
        text = (
            f"✊ **سنگ کاغذ قیچی**\n\n"
            f"تو: {CHOICES[user_choice]}\n"
            f"ربات: {CHOICES[bot_choice]}\n\n"
            f"🤝 **مساوی! امتیازی تغییر نکرد**\n"
            f"💰 امتیاز کل: {user_points}\n"
            f"{current_level['badge']} لول {current_level['level_num']}"
        )
    
    # دکمه دوباره بازی
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪨", callback_data="rps_rock"),
            InlineKeyboardButton("📄", callback_data="rps_paper"),
            InlineKeyboardButton("✂️", callback_data="rps_scissors"),
        ]
    ])
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)
