import json
import re
import os
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ========== بارگذاری دیتابیس فیلم‌ها ==========

MOVIES_FILE = "archive_full.json"
_movies_cache = None

def load_movies():
    """بارگذاری دیتابیس فیلم‌ها (با کش برای سرعت بیشتر)"""
    global _movies_cache
    if _movies_cache is not None:
        return _movies_cache
    
    if not os.path.exists(MOVIES_FILE):
        print(f"❌ فایل {MOVIES_FILE} پیدا نشد!")
        return []
    
    try:
        with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
            _movies_cache = json.load(f)
        print(f"✅ دیتابیس فیلم‌ها بارگذاری شد: {len(_movies_cache)} عنوان")
        return _movies_cache
    except Exception as e:
        print(f"❌ خطا در بارگذاری دیتابیس: {e}")
        return []


# ========== توابع کمکی پارس اطلاعات ==========

def parse_movie_info(movie: dict) -> dict:
    """پارس اطلاعات فیلم از فیلد info"""
    info_list = movie.get("info", [])
    result = {
        "imdb_code": "",
        "type": "movie",
        "votes": "",
        "rate": "",
        "has_softsub": False,
        "has_dubbed": False,
    }
    
    for item in info_list:
        if item.startswith("IMDb Code:"):
            result["imdb_code"] = item.replace("IMDb Code:", "").strip()
        elif item.startswith("Title Type:"):
            result["type"] = item.replace("Title Type:", "").strip()
        elif item.startswith("IMDb Votes:"):
            result["votes"] = item.replace("IMDb Votes:", "").strip()
        elif item.startswith("IMDb Rates:"):
            result["rate"] = item.replace("IMDb Rates:", "").strip()
        elif item == "SoftSub":
            result["has_softsub"] = True
        elif item == "Dubbed":
            result["has_dubbed"] = True
    
    return result


def get_type_emoji(type_str: str) -> str:
    """نمایش ایموجی بر اساس نوع عنوان"""
    return {
        "movie": "🎬",
        "tvSeries": "📺",
        "tvMiniSeries": "🎞",
        "tvMovie": "🎥",
    }.get(type_str, "🎬")


def get_type_label(type_str: str) -> str:
    """برچسب فارسی برای نوع عنوان"""
    return {
        "movie": "فیلم",
        "tvSeries": "سریال",
        "tvMiniSeries": "مینی‌سریال",
        "tvMovie": "فیلم TV",
    }.get(type_str, "فیلم")


def search_movies(query: str, limit: int = 8) -> list:
    """جستجو در دیتابیس فیلم‌ها"""
    movies = load_movies()
    query_lower = query.lower().strip()
    
    exact_matches = []
    partial_matches = []
    
    for i, movie in enumerate(movies):
        title_lower = movie["title"].lower()
        
        if title_lower == query_lower:
            exact_matches.append((i, movie))
        elif query_lower in title_lower:
            partial_matches.append((i, movie))
    
    results = exact_matches + partial_matches
    return results[:limit]


def get_downloads_by_type(movie: dict) -> dict:
    """دسته‌بندی لینک‌های دانلود به SoftSub و Dubbed"""
    downloads = movie.get("downloads", [])
    softsub = []
    dubbed = []
    
    for d in downloads:
        url = d.get("url", "")
        text = d.get("text", "")
        
        if "SoftSub" in url:
            # برای سریال، فصل رو هم استخراج کن
            season_match = re.search(r'/S(\d+)/', url)
            if season_match:
                season = int(season_match.group(1))
                softsub.append({"text": text, "url": url, "season": season})
            else:
                softsub.append({"text": text, "url": url, "season": None})
        elif "Dubbed" in url:
            season_match = re.search(r'/S(\d+)/', url)
            if season_match:
                season = int(season_match.group(1))
                dubbed.append({"text": text, "url": url, "season": season})
            else:
                dubbed.append({"text": text, "url": url, "season": None})
    
    return {"softsub": softsub, "dubbed": dubbed}


def get_seasons(downloads_list: list) -> list:
    """لیست فصل‌های موجود از لینک‌های دانلود"""
    seasons = sorted(set(d["season"] for d in downloads_list if d["season"] is not None))
    return seasons


# ========== موقت‌سازی داده‌های callback ==========

# ذخیره موقت نتایج جستجو و انتخاب‌های کاربر
# {user_id: {"results": [...], "selected_idx": int, "selected_type": str, "selected_season": int}}
_search_sessions = {}


# ========== دستور /movie ==========

async def movie_command(client, message: Message):
    """/movie [نام فیلم] - جستجوی فیلم"""
    query = message.text[7:].strip()  # حذف "/movie "
    
    if not query:
        await message.reply(
            "🎬 **جستجوی فیلم و سریال**\n\n"
            "📝 فرمت: `/movie [نام فیلم یا سریال]`\n\n"
            "مثال:\n"
            "• `/movie inception`\n"
            "• `/movie game of thrones`\n"
            "• `/movie dark knight`"
        )
        return
    
    # نمایش پیام در حال جستجو
    searching_msg = await message.reply("🔍 در حال جستجو...")
    
    results = search_movies(query)
    
    await searching_msg.delete()
    
    if not results:
        await message.reply(
            f"❌ **نتیجه‌ای پیدا نشد!**\n\n"
            f"🔍 جستجو برای: `{query}`\n\n"
            f"💡 نکات:\n"
            f"• نام رو به انگلیسی بنویس\n"
            f"• از نام اصلی استفاده کن\n"
            f"• سال رو حذف کن (مثلاً `inception` نه `inception 2010`)"
        )
        return
    
    if len(results) == 1:
        # فقط یه نتیجه → مستقیم برو به صفحه فیلم
        idx, movie = results[0]
        _search_sessions[message.from_user.id] = {
            "results": results,
            "selected_movie_idx": 0
        }
        await show_movie_detail(client, message, movie, message.from_user.id, reply=True)
    else:
        # چند نتیجه → لیست دکمه‌ای
        _search_sessions[message.from_user.id] = {"results": results}
        
        buttons = []
        for i, (idx, movie) in enumerate(results):
            info = parse_movie_info(movie)
            emoji = get_type_emoji(info["type"])
            rate = f"⭐{info['rate']}" if info["rate"] else ""
            label = f"{emoji} {movie['title']} {rate}"
            # محدود کردن طول برچسب
            if len(label) > 55:
                label = label[:52] + "..."
            buttons.append([InlineKeyboardButton(label, callback_data=f"mv_select_{i}")])
        
        await message.reply(
            f"🎬 **{len(results)} نتیجه برای:** `{query}`\n\n"
            f"👇 فیلم یا سریال مورد نظرت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# ========== نمایش جزئیات فیلم ==========

async def show_movie_detail(client, message_or_query, movie: dict, user_id: int, reply: bool = False):
    """نمایش اطلاعات فیلم با دکمه‌های SoftSub / Dubbed"""
    info = parse_movie_info(movie)
    downloads = get_downloads_by_type(movie)
    
    emoji = get_type_emoji(info["type"])
    type_label = get_type_label(info["type"])
    
    # ساخت متن اطلاعات
    text = f"{emoji} **{movie['title']}**\n"
    text += f"━━━━━━━━━━━━━━━━━\n"
    
    if info["rate"]:
        text += f"⭐ **امتیاز IMDb:** {info['rate']}"
        if info["votes"]:
            text += f" ({info['votes']} رای)"
        text += "\n"
    
    text += f"📂 **نوع:** {type_label}\n"
    
    if info["imdb_code"]:
        text += f"🔗 **IMDb:** `{info['imdb_code']}`\n"
    
    text += "\n📥 **لینک‌های دانلود موجود:**\n"
    
    # نمایش موجودیت SoftSub / Dubbed
    has_softsub = len(downloads["softsub"]) > 0
    has_dubbed = len(downloads["dubbed"]) > 0
    
    if has_softsub:
        text += "✅ زیرنویس (SoftSub)\n"
    if has_dubbed:
        text += "✅ دوبله فارسی (Dubbed)\n"
    
    # دکمه‌های انتخاب نوع
    buttons = []
    
    sub_buttons = []
    if has_softsub:
        sub_buttons.append(
            InlineKeyboardButton("🎬 زیرنویس (SoftSub)", callback_data=f"mv_type_softsub_{user_id}")
        )
    if has_dubbed:
        sub_buttons.append(
            InlineKeyboardButton("🗣 دوبله فارسی", callback_data=f"mv_type_dubbed_{user_id}")
        )
    
    if sub_buttons:
        buttons.append(sub_buttons)
    
    buttons.append([InlineKeyboardButton("🔙 برگشت به نتایج", callback_data=f"mv_back_{user_id}")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    if reply:
        await message_or_query.reply(text, reply_markup=keyboard)
    else:
        await message_or_query.edit_message_text(text, reply_markup=keyboard)


# ========== نمایش لینک‌های دانلود ==========

async def show_download_links(client, callback_query: CallbackQuery, movie: dict, sub_type: str, user_id: int, season: int = None):
    """نمایش لینک‌های دانلود بر اساس نوع (SoftSub/Dubbed) و فصل"""
    info = parse_movie_info(movie)
    downloads = get_downloads_by_type(movie)
    
    links = downloads[sub_type]
    type_label = "زیرنویس" if sub_type == "softsub" else "دوبله فارسی"
    type_emoji = "🎬" if sub_type == "softsub" else "🗣"
    
    is_series = info["type"] in ("tvSeries", "tvMiniSeries")
    
    if is_series:
        seasons = get_seasons(links)
        
        if season is None and seasons:
            # ابتدا فصل رو انتخاب کن
            buttons = []
            row = []
            for s in seasons:
                row.append(InlineKeyboardButton(
                    f"فصل {s}", 
                    callback_data=f"mv_season_{sub_type}_{s}_{user_id}"
                ))
                if len(row) == 4:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            
            buttons.append([InlineKeyboardButton("🔙 برگشت", callback_data=f"mv_detail_{user_id}")])
            
            await callback_query.edit_message_text(
                f"{type_emoji} **{movie['title']}** - {type_label}\n\n"
                f"📅 فصل مورد نظرت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        
        # فصل انتخاب شده، نمایش لینک‌ها
        season_links = [l for l in links if l["season"] == season]
        
        text = f"{type_emoji} **{movie['title']}**\n"
        text += f"📅 فصل {season} - {type_label}\n"
        text += f"━━━━━━━━━━━━━━━━━\n\n"
        
        if season_links:
            text += "📥 **لینک‌های دانلود:**\n\n"
            for link in season_links:
                text += f"[⬇️ {link['text']}]({link['url']})\n"
        else:
            text += "❌ لینکی برای این فصل موجود نیست."
        
        back_type = f"mv_type_{sub_type}_{user_id}"
        buttons = [
            [InlineKeyboardButton("🔙 انتخاب فصل دیگه", callback_data=back_type)],
            [InlineKeyboardButton("🏠 برگشت به فیلم", callback_data=f"mv_detail_{user_id}")]
        ]
        
    else:
        # فیلم - مستقیم لینک‌ها رو نشون بده
        text = f"{type_emoji} **{movie['title']}**\n"
        text += f"{type_label}\n"
        text += f"━━━━━━━━━━━━━━━━━\n\n"
        
        if links:
            text += "📥 **لینک‌های دانلود:**\n\n"
            for link in links:
                text += f"[⬇️ {link['text']}]({link['url']})\n"
        else:
            text += "❌ لینک دانلودی موجود نیست."
        
        buttons = [
            [InlineKeyboardButton("🔙 برگشت به فیلم", callback_data=f"mv_detail_{user_id}")]
        ]
    
    await callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


# ========== مدیریت callback‌های فیلم ==========

async def handle_movie_callback(client, callback_query: CallbackQuery):
    """مدیریت تمام callback‌های مربوط به سیستم جستجوی فیلم"""
    data = callback_query.data
    clicker_id = callback_query.from_user.id
    
    # ── انتخاب فیلم از لیست نتایج ──
    if data.startswith("mv_select_"):
        result_index = int(data.split("_")[2])
        session = _search_sessions.get(clicker_id)
        
        if not session or "results" not in session:
            await callback_query.answer("❌ جلسه منقضی شده! دوباره سرچ کن.", show_alert=True)
            return
        
        if result_index >= len(session["results"]):
            await callback_query.answer("❌ خطا در انتخاب!", show_alert=True)
            return
        
        session["selected_movie_idx"] = result_index
        _search_sessions[clicker_id] = session
        
        _, movie = session["results"][result_index]
        await show_movie_detail(client, callback_query, movie, clicker_id)
    
    # ── نمایش جزئیات فیلم (برگشت به صفحه فیلم) ──
    elif data.startswith("mv_detail_"):
        uid = int(data.split("_")[2])
        if uid != clicker_id:
            await callback_query.answer("❌ این دکمه مال تو نیست!", show_alert=True)
            return
        
        session = _search_sessions.get(clicker_id)
        if not session:
            await callback_query.answer("❌ جلسه منقضی شده!", show_alert=True)
            return
        
        idx = session.get("selected_movie_idx", 0)
        _, movie = session["results"][idx]
        await show_movie_detail(client, callback_query, movie, clicker_id)
    
    # ── انتخاب نوع (SoftSub / Dubbed) ──
    elif data.startswith("mv_type_"):
        parts = data.split("_")
        sub_type = parts[2]  # softsub یا dubbed
        uid = int(parts[3])
        
        if uid != clicker_id:
            await callback_query.answer("❌ این دکمه مال تو نیست!", show_alert=True)
            return
        
        session = _search_sessions.get(clicker_id)
        if not session:
            await callback_query.answer("❌ جلسه منقضی شده!", show_alert=True)
            return
        
        idx = session.get("selected_movie_idx", 0)
        _, movie = session["results"][idx]
        session["selected_sub_type"] = sub_type
        _search_sessions[clicker_id] = session
        
        await show_download_links(client, callback_query, movie, sub_type, clicker_id)
    
    # ── انتخاب فصل ──
    elif data.startswith("mv_season_"):
        parts = data.split("_")
        sub_type = parts[2]  # softsub یا dubbed
        season = int(parts[3])
        uid = int(parts[4])
        
        if uid != clicker_id:
            await callback_query.answer("❌ این دکمه مال تو نیست!", show_alert=True)
            return
        
        session = _search_sessions.get(clicker_id)
        if not session:
            await callback_query.answer("❌ جلسه منقضی شده!", show_alert=True)
            return
        
        idx = session.get("selected_movie_idx", 0)
        _, movie = session["results"][idx]
        
        await show_download_links(client, callback_query, movie, sub_type, clicker_id, season=season)
    
    # ── برگشت به لیست نتایج ──
    elif data.startswith("mv_back_"):
        uid = int(data.split("_")[2])
        if uid != clicker_id:
            await callback_query.answer("❌ این دکمه مال تو نیست!", show_alert=True)
            return
        
        session = _search_sessions.get(clicker_id)
        if not session or "results" not in session:
            await callback_query.answer("❌ جلسه منقضی شده! دوباره سرچ کن.", show_alert=True)
            return
        
        results = session["results"]
        
        if len(results) == 1:
            await callback_query.answer("فقط یه نتیجه داری!", show_alert=False)
            return
        
        buttons = []
        for i, (_, movie) in enumerate(results):
            info = parse_movie_info(movie)
            emoji = get_type_emoji(info["type"])
            rate = f"⭐{info['rate']}" if info["rate"] else ""
            label = f"{emoji} {movie['title']} {rate}"
            if len(label) > 55:
                label = label[:52] + "..."
            buttons.append([InlineKeyboardButton(label, callback_data=f"mv_select_{i}")])
        
        await callback_query.edit_message_text(
            f"🎬 **نتایج جستجو** ({len(results)} مورد)\n\n"
            f"👇 فیلم یا سریال مورد نظرت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    else:
        await callback_query.answer("❌ دستور ناشناخته!", show_alert=True)


# ========== پایان فایل ==========
# هندلرها در main.py ثبت می‌شوند
