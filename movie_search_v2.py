import json
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


# ========== توابع کمکی ==========

# تفاوت اصلی با نسخه قبلی:
# قدیمی: movie["title"], movie["info"] (لیست رشته), downloads[i]["text"/"url"]
# جدید:  movie["title_en"/"title_fa"], فیلدهای مستقیم, downloads[i]["version"/"quality"/"url"/"folder"]

def get_type_emoji(type_str: str) -> str:
    return {
        "movie": "🎬",
        "series": "📺",   # جدید: "series" نه "tvSeries"
        "tvSeries": "📺",
        "tvMiniSeries": "🎞",
        "tvMovie": "🎥",
    }.get(type_str, "🎬")


def get_type_label(type_str: str) -> str:
    return {
        "movie": "فیلم",
        "series": "سریال",   # جدید
        "tvSeries": "سریال",
        "tvMiniSeries": "مینی‌سریال",
        "tvMovie": "فیلم TV",
    }.get(type_str, "فیلم")


def search_movies(query: str, limit: int = 8) -> list:
    """جستجو در دیتابیس - جستجو در هر دو عنوان انگلیسی و فارسی"""
    movies = load_movies()
    query_lower = query.lower().strip()

    exact_matches = []
    partial_matches = []

    for i, movie in enumerate(movies):
        # جدید: title_en و title_fa به جای title
        title_en = movie.get("title_en", "").lower()
        title_fa = movie.get("title_fa", "").lower()

        if title_en == query_lower or title_fa == query_lower:
            exact_matches.append((i, movie))
        elif query_lower in title_en or query_lower in title_fa:
            partial_matches.append((i, movie))

    results = exact_matches + partial_matches
    return results[:limit]


def get_downloads_by_version(movie: dict) -> dict:
    """
    دسته‌بندی لینک‌های دانلود به SoftSub و Dubbed

    ساختار جدید downloads:
      فیلم:   {"type":"movie", "version":"SoftSub", "quality":"1080p.BluRay", "size":"2.7 GB", "url":"https://..."}
      سریال:  {"type":"series", "version":"SoftSub", "quality":"1080p.BluRay", "season":1, "episodes":12, "folder":"https://..."}
    """
    downloads = movie.get("downloads", [])
    softsub = []
    dubbed = []

    for d in downloads:
        version = d.get("version", "")

        if version == "SoftSub":
            if d.get("type") == "series":
                softsub.append({
                    "text": f"{d.get('quality','')} ({d.get('episodes','')} قسمت)",
                    "url": d.get("folder", ""),
                    "season": d.get("season"),
                    "quality": d.get("quality", ""),
                    "episodes": d.get("episodes", ""),
                })
            else:
                softsub.append({
                    "text": f"{d.get('quality','')} - {d.get('size','')}",
                    "url": d.get("url", ""),
                    "season": None,
                    "quality": d.get("quality", ""),
                    "size": d.get("size", ""),
                })

        elif version == "Dubbed":
            if d.get("type") == "series":
                dubbed.append({
                    "text": f"{d.get('quality','')} ({d.get('episodes','')} قسمت)",
                    "url": d.get("folder", ""),
                    "season": d.get("season"),
                    "quality": d.get("quality", ""),
                    "episodes": d.get("episodes", ""),
                })
            else:
                dubbed.append({
                    "text": f"{d.get('quality','')} - {d.get('size','')}",
                    "url": d.get("url", ""),
                    "season": None,
                    "quality": d.get("quality", ""),
                    "size": d.get("size", ""),
                })

    return {"softsub": softsub, "dubbed": dubbed}


def get_seasons(downloads_list: list) -> list:
    """لیست فصل‌های موجود"""
    seasons = sorted(set(d["season"] for d in downloads_list if d.get("season") is not None))
    return seasons


# ========== موقت‌سازی داده‌های callback ==========

_search_sessions = {}


# ========== دستور /movie ==========

async def movie_command(client, message: Message):
    """/movie [نام فیلم] - جستجوی فیلم"""
    query = message.text[7:].strip()

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
        idx, movie = results[0]
        _search_sessions[message.from_user.id] = {
            "results": results,
            "selected_movie_idx": 0
        }
        await show_movie_detail(client, message, movie, message.from_user.id, reply=True)
    else:
        _search_sessions[message.from_user.id] = {"results": results}

        buttons = []
        for i, (idx, movie) in enumerate(results):
            media_type = movie.get("type", "movie")
            emoji = get_type_emoji(media_type)
            # جدید: imdb_rating به جای parse از info
            rate = movie.get("imdb_rating", "")
            rate_str = f"⭐{rate}" if rate else ""
            # جدید: title_en به جای title
            title = movie.get("title_en", "")
            label = f"{emoji} {title} {rate_str}"
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
    """نمایش اطلاعات فیلم"""
    # جدید: خواندن مستقیم از فیلدها به جای parse از info
    media_type = movie.get("type", "movie")
    emoji = get_type_emoji(media_type)
    type_label = get_type_label(media_type)

    title_en = movie.get("title_en", "")
    title_fa = movie.get("title_fa", "")
    year = movie.get("year", "")
    rating = movie.get("imdb_rating", "")
    votes = movie.get("imdb_votes", "")
    imdb_id = movie.get("imdb_id", "")

    downloads = get_downloads_by_version(movie)
    has_softsub = len(downloads["softsub"]) > 0
    has_dubbed = len(downloads["dubbed"]) > 0

    # ساخت متن
    text = f"{emoji} **{title_en}**"
    if title_fa:
        text += f" | {title_fa}"
    text += "\n━━━━━━━━━━━━━━━━━\n"

    if rating:
        votes_str = f" ({votes:,} رای)" if isinstance(votes, int) else f" ({votes} رای)" if votes else ""
        text += f"⭐ **امتیاز IMDb:** {rating}{votes_str}\n"

    text += f"📅 **سال:** {year}\n"
    text += f"📂 **نوع:** {type_label}\n"

    if imdb_id:
        text += f"🔗 **IMDb:** `{imdb_id}`\n"

    text += "\n📥 **لینک‌های دانلود موجود:**\n"
    if has_softsub:
        text += "✅ زیرنویس (SoftSub)\n"
    if has_dubbed:
        text += "✅ دوبله فارسی (Dubbed)\n"

    # دکمه‌ها
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
    """نمایش لینک‌های دانلود"""
    media_type = movie.get("type", "movie")
    downloads = get_downloads_by_version(movie)
    title_en = movie.get("title_en", "")

    links = downloads[sub_type]
    type_label = "زیرنویس" if sub_type == "softsub" else "دوبله فارسی"
    type_emoji = "🎬" if sub_type == "softsub" else "🗣"

    # جدید: نوع "series" به جای "tvSeries"/"tvMiniSeries"
    is_series = media_type in ("series", "tvSeries", "tvMiniSeries")

    if is_series:
        seasons = get_seasons(links)

        if season is None and seasons:
            # انتخاب فصل
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
                f"{type_emoji} **{title_en}** - {type_label}\n\n"
                f"📅 فصل مورد نظرت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        # نمایش لینک‌های یک فصل
        season_links = [l for l in links if l.get("season") == season]

        text = f"{type_emoji} **{title_en}**\n"
        text += f"📅 فصل {season} - {type_label}\n"
        text += "━━━━━━━━━━━━━━━━━\n\n"

        if season_links:
            text += "📥 **لینک‌های دانلود:**\n\n"
            for link in season_links:
                episodes = link.get("episodes", "")
                ep_str = f" | {episodes} قسمت" if episodes else ""
                # جدید: folder به جای url برای سریال‌ها
                text += f"[⬇️ {link['text']}]({link['url']}){ep_str}\n"
        else:
            text += "❌ لینکی برای این فصل موجود نیست."

        buttons = [
            [InlineKeyboardButton("🔙 انتخاب فصل دیگه", callback_data=f"mv_type_{sub_type}_{user_id}")],
            [InlineKeyboardButton("🏠 برگشت به فیلم", callback_data=f"mv_detail_{user_id}")]
        ]

    else:
        # فیلم - مستقیم لینک‌ها
        text = f"{type_emoji} **{title_en}**\n"
        text += f"{type_label}\n"
        text += "━━━━━━━━━━━━━━━━━\n\n"

        if links:
            text += "📥 **لینک‌های دانلود:**\n\n"
            for link in links:
                # جدید: quality و size جدا هستن
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
        sub_type = parts[2]
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
        sub_type = parts[2]
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
            media_type = movie.get("type", "movie")
            emoji = get_type_emoji(media_type)
            rate = movie.get("imdb_rating", "")
            rate_str = f"⭐{rate}" if rate else ""
            title = movie.get("title_en", "")
            label = f"{emoji} {title} {rate_str}"
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
