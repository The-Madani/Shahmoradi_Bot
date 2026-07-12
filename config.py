# ========== تنظیمات اولیه ==========

# لیست ادمین‌ها
ADMINS = [0123456789, 0123456789]

# کلید API گوگل جمینی
GEMINI_API_KEY = ""

# آیدی مدیر اصلی برای دریافت نوتیفیکیشن
MAIN_ADMIN_ID = 0123456789 

# لینک گروه
GROUP_LINK = "https://t.me/example"

# فایل‌های JSON برای ذخیره داده‌ها
POINTS_FILE = "user_points.json"
LEVELS_FILE = "user_levels.json"
BETS_FILE = "active_bets.json"

# ========== تنظیمات سیستم شرط‌بندی ==========
BET_CONFIG = {
    "min_bet": 10,              # حداقل مقدار شرط
    "max_bet": 10000,            # حداکثر مقدار شرط
    "bet_timeout": 60,          # زمان انقضای شرط (ثانیه)
    "multipliers": {
        "even_odd": 2,          # ضریب زوج/فرد
        "exact": 6,             # ضریب حدس عدد دقیق
        "range_low": 3,         # ضریب محدوده 1-3
        "range_high": 3         # ضریب محدوده 4-6
    }
}

# ========== تنظیمات سیستم جعبه ==========
BOX_CONFIG = {
    "message_threshold": 50,    # تعداد پیام برای ظاهر شدن جعبه
    "min_reward": 5,           # حداقل جایزه
    "max_reward": 50,          # حداکثر جایزه
    "operations": ["+", "-", "*", "/"],  # عملیات‌های ریاضی
    "number_range": (1, 50),   # محدوده اعداد برای سوالات
    "sticker_id": "CAACAgQAAyEFAASyTOk5AAMFaN_-Do141GgmCVjw5OIQJgKL1koAAo8YAAJc5gFT_ajtuyWZet8eBA"
}

# ========== تنظیمات سیستم لول ==========
LEVEL_CONFIG = {
    "level_1": {"min_points": 0, "max_points": 99, "title": "🔰 نوب", "badge": "🔰"},
    "level_2": {"min_points": 100, "max_points": 249, "title": "🔗 نوپا", "badge": "🔗"},
    "level_3": {"min_points": 250, "max_points": 499, "title": "⭐ ستاره", "badge": "⭐"},
    "level_4": {"min_points": 500, "max_points": 999, "title": "🔥 حرفه‌ای", "badge": "🔥"},
    "level_5": {"min_points": 1000, "max_points": 1999, "title": "💎 الماسی", "badge": "💎"},
    "level_6": {"min_points": 2000, "max_points": 4999, "title": "👑 پادشاه", "badge": "👑"},
    "level_7": {"min_points": 5000, "max_points": 9999, "title": "🌟 افسانه‌ای", "badge": "🌟"},
    "level_8": {"min_points": 10000, "max_points": float('inf'), "title": "🏆 خدا", "badge": "🏆"}
}
