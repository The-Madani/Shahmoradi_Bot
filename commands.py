from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import GROUP_LINK, BET_CONFIG, ADMINS
from database import (
    get_user_points, add_points, remove_points, set_points,
    get_user_level, get_progress_bar, check_level_up, load_points
)

# ========== دستورات عمومی ==========

async def start_command(client, message: Message):
    """دستور شروع ربات"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("شاهمرادی کلاب", url=GROUP_LINK)]
    ])

    await message.reply_text(
        "به ما بپیوند! 👇",
        reply_markup=keyboard
    )


async def help_command(client, message: Message):
    """راهنمای دستورات ربات"""
    help_text = """
📚 **راهنمای دستورات ربات**

**🎮 بازی و سرگرمی:**
🎲 ارسال تاس (Dice) - شرط‌بندی روی نتیجه
📦 جعبه شانس هر 50 پیام - حل معادله و برد امتیاز
✊ /rps - سنگ کاغذ قیچی با ربات

**💰 شرط‌بندی:**
/bet [مقدار] - شروع شرط‌بندی
/cancelbet - لغو شرط فعال
/mybets - مشاهده شرط‌های فعال

**انواع شرط:**
• زوج/فرد (ضریب 2)
• عدد دقیق (ضریب 6)
• محدوده پایین 1-3 (ضریب 3)
• محدوده بالا 4-6 (ضریب 3)

**📊 امتیاز و لول:**
/points - چک کردن امتیاز خودت
/leaderboard - جدول برترین‌ها

**🤖 هوش مصنوعی:**
/ai [سوال] - سوال از Gemini AI

**🎬 فیلم و سریال:**
/movie [نام] - جستجو + لینک دانلود (زیرنویس / دوبله)

**👑 دستورات ادمین:**
/addpoints [مقدار] - اضافه کردن امتیاز
/removepoints [مقدار] - کم کردن امتیاز
/setpoints [مقدار] - تنظیم امتیاز مستقیم

**🔐 دستورات مدیر اصلی:**
/pending - مشاهده درخواست‌های عضویت در انتظار
    """
    
    await message.reply(help_text)


async def points_command(client, message: Message):
    """چک کردن امتیاز و لول خودت یا کاربر دیگه"""
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        points = get_user_points(user.id)
        level_info = get_user_level(user.id)
        progress = get_progress_bar(user.id)
        
        await message.reply(
            f"{level_info['badge']} **{level_info['title']}**\n"
            f"💎 امتیاز {user.mention}: **{points}**\n\n"
            f"{progress}"
        )
    else:
        user = message.from_user
        points = get_user_points(user.id)
        level_info = get_user_level(user.id)
        progress = get_progress_bar(user.id)
        
        await message.reply(
            f"{level_info['badge']} **{level_info['title']}**\n"
            f"💎 امتیاز شما: **{points}**\n\n"
            f"{progress}"
        )


async def leaderboard_command(client, message: Message):
    """نمایش جدول برترین‌ها با لول"""
    points_data = load_points()
    
    if not points_data:
        await message.reply("❌ هنوز هیچ کاربری امتیازی نداره!")
        return
    
    sorted_users = sorted(points_data.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = "🏆 **جدول برترین‌ها**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, points) in enumerate(sorted_users):
        try:
            user = await client.get_users(int(user_id))
            name = user.first_name or "Unknown"
            level_info = get_user_level(int(user_id))
            medal = medals[i] if i < 3 else f"{i+1}."
            
            text += f"{medal} {level_info['badge']} {name}\n"
            text += f"   💎 {points} امتیاز | لول {level_info['level_num']}\n\n"
        except:
            continue
    
    await message.reply(text)


# ========== دستورات ادمین ==========

async def admin_add_points(client, message: Message):
    """اضافه کردن امتیاز توسط ادمین"""
    if not message.reply_to_message:
        await message.reply("❌ روی پیام کاربر ریپلای کن!")
        return
    
    try:
        amount = int(message.text.split()[1])
        user = message.reply_to_message.from_user
        new_points = add_points(user.id, amount)
        
        level_up_info = check_level_up(user.id)
        
        text = f"✅ {amount} امتیاز به {user.mention} اضافه شد!\n💎 امتیاز جدید: **{new_points}**"
        
        if level_up_info["level_up"]:
            text += f"\n\n🎉 **تبریک! لول‌اپ شدید!**\n"
            text += f"{level_up_info['badge']} **از لول {level_up_info['old_level']} به لول {level_up_info['new_level']}**\n"
            text += f"🏅 {level_up_info['level_title']}"
        
        await message.reply(text)
    except (IndexError, ValueError):
        await message.reply("❌ فرمت: `/addpoints 10` (روی پیام کاربر ریپلای کن)")


async def admin_remove_points(client, message: Message):
    """کم کردن امتیاز توسط ادمین"""
    if not message.reply_to_message:
        await message.reply("❌ روی پیام کاربر ریپلای کن!")
        return
    
    try:
        amount = int(message.text.split()[1])
        user = message.reply_to_message.from_user
        new_points = remove_points(user.id, amount)
        
        await message.reply(f"✅ {amount} امتیاز از {user.mention} کم شد!\n💎 امتیاز جدید: **{new_points}**")
    except (IndexError, ValueError):
        await message.reply("❌ فرمت: `/removepoints 10` (روی پیام کاربر ریپلای کن)")


async def admin_set_points(client, message: Message):
    """تنظیم دستی امتیاز توسط ادمین"""
    if not message.reply_to_message:
        await message.reply("❌ روی پیام کاربر ریپلای کن!")
        return
    
    try:
        amount = int(message.text.split()[1])
        user = message.reply_to_message.from_user
        set_points(user.id, amount)
        
        await message.reply(f"✅ امتیاز {user.mention} به **{amount}** تنظیم شد!")
    except (IndexError, ValueError):
        await message.reply("❌ فرمت: `/setpoints 100` (روی پیام کاربر ریپلای کن)")


# ========== پایان فایل ==========
# هندلرها در main.py ثبت می‌شوند
