"""
🤖 Hermes Agent Bot — نسخه ساده‌شده
بات تلگرام هوشمند با ابزارهای واقعی
مثل Hermes Agent اصلی ولی سبک‌تر

ابزارها:
  → اجرای کد Python
  → جستجو در وب
  → خواندن/نوشتن فایل
  → حافظه بلندمدت
  → تاریخچه مکالمه
"""

import os
import json
import logging
import subprocess
import requests
import wikipedia
from datetime import datetime
from pathlib import Path
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

# ── لاگ ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── تنظیمات ─────────────────────────────────────────
API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_URL = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("AI_MODEL", "xiaomi/mimo-v2.5")
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    """تو Hermes Agent هستی، یک دستیار هوش مصنوعی هوشمند.
تو می‌تونی:
- کد Python اجرا کنی
- در وب جستجو کنی
- فایل بخونی و بنویسی
- حافظه داشته باشی
- تحلیل و خلاصه کنی
به فارسی جواب بده. مفید و دقیق باش."""
)
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4000"))
TIMEOUT = int(os.environ.get("API_TIMEOUT", "120"))

# ── مسیر ذخیره‌سازی ─────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MEMORY_FILE = DATA_DIR / "memory.json"
HISTORY_DIR = DATA_DIR / "history"


def ensure_dirs():
    HISTORY_DIR.mkdir(exist_ok=True)


# ── حافظه بلندمدت ────────────────────────────────────
def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"facts": [], "preferences": {}}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_memory(text):
    memory = load_memory()
    memory["facts"].append({
        "text": text,
        "time": datetime.now().isoformat()
    })
    # حداکثر ۱۰۰ حافظه
    if len(memory["facts"]) > 100:
        memory["facts"] = memory["facts"][-100:]
    save_memory(memory)
    return "✅ در حافظه ذخیره شد"


def get_memory():
    memory = load_memory()
    if not memory["facts"]:
        return "🧠 حافظه خالیه"
    lines = ["🧠 **حافظه بلندمدت:**\n"]
    for i, fact in enumerate(memory["facts"][-20:], 1):
        lines.append(f"{i}. {fact['text']}")
    return "\n".join(lines)


# ── تاریخچه مکالمه ──────────────────────────────────
chat_history = {}


def get_history(user_id):
    if user_id not in chat_history:
        chat_history[user_id] = []
    return chat_history[user_id]


def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 30:
        chat_history[user_id] = history[-30:]


# ── ابزارها ──────────────────────────────────────────
def tool_run_python(code):
    """اجرای کد Python"""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=30,
            cwd="/tmp"
        )
        output = result.stdout + result.stderr
        if len(output) > 3000:
            output = output[:3000] + "\n... [برش خورد]"
        return output or "✅ کد بدون خروجی اجرا شد"
    except subprocess.TimeoutExpired:
        return "⏰ زمان اجرا تموم شد (حداکثر ۳۰ ثانیه)"
    except Exception as e:
        return f"❌ خطا: {str(e)}"


def tool_search(query):
    """جستجو در ویکی‌پدیا"""
    try:
        wikipedia.set_lang("fa")
        results = wikipedia.search(query, results=3)
        if not results:
            wikipedia.set_lang("en")
            results = wikipedia.search(query, results=3)
        if not results:
            return "🔍 نتیجه‌ای پیدا نشد"
        summaries = []
        for title in results[:3]:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summaries.append(f"**{page.title}**\n{page.summary[:500]}...")
            except Exception:
                pass
        return "\n\n---\n\n".join(summaries) if summaries else "🔍 نتیجه‌ای پیدا نشد"
    except Exception as e:
        return f"❌ خطا در جستجو: {str(e)}"


def tool_write_file(filename, content):
    """نوشتن فایل"""
    try:
        filepath = DATA_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ فایل {filename} ذخیره شد ({len(content)} کاراکتر)"
    except Exception as e:
        return f"❌ خطا: {str(e)}"


def tool_read_file(filename):
    """خواندن فایل"""
    try:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            return f"❌ فایل {filename} پیدا نشد"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 3000:
            content = content[:3000] + "\n... [برش خورد]"
        return content
    except Exception as e:
        return f"❌ خطا: {str(e)}"


def tool_list_files():
    """لیست فایل‌ها"""
    try:
        files = list(DATA_DIR.rglob("*"))
        files = [f for f in files if f.is_file()]
        if not files:
            return "📁 هیچ فایلی ذخیره نشده"
        lines = ["📁 **فایل‌ها:**\n"]
        for f in files[:20]:
            size = f.stat().st_size
            lines.append(f"• `{f.relative_to(DATA_DIR)}` ({size} bytes)")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ خطا: {str(e)}"


# ── تعریف ابزارها برای API ───────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "اجرای کد Python. برای محاسبات، تحلیل، تولید محتوا و...",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "کد Python برای اجرا"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "جستجو در اینترنت (ویکی‌پدیا). برای پیدا کردن اطلاعات.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "عبارت جستجو"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "نوشتن محتوا در فایل",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "نام فایل"},
                    "content": {"type": "string", "description": "محتوای فایل"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "خواندن محتوای فایل",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "نام فایل"}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "لیست فایل‌های ذخیره شده",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "ذخیره یک اطلاعات در حافظه بلندمدت",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "متن برای ذخیره"}
                },
                "required": ["text"]
            }
        }
    },
]


# ── اجرای ابزار ──────────────────────────────────────
def execute_tool(name, args):
    """اجرای ابزار بر اساس نام"""
    if name == "run_python":
        return tool_run_python(args.get("code", ""))
    elif name == "search_web":
        return tool_search(args.get("query", ""))
    elif name == "write_file":
        return tool_write_file(args.get("filename", ""), args.get("content", ""))
    elif name == "read_file":
        return tool_read_file(args.get("filename", ""))
    elif name == "list_files":
        return tool_list_files()
    elif name == "save_memory":
        return add_memory(args.get("text", ""))
    return "❌ ابزار ناشناخته"


# ── پاکسازی پاسخ ─────────────────────────────────────
def clean_response(raw_text):
    if "data: [DONE]" in raw_text:
        raw_text = raw_text.replace("data: [DONE]", "")
    raw_text = raw_text.rstrip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw_text[start:end])
        except Exception:
            pass
    return None


# ── فراخوانی مدل با ابزارها ──────────────────────────
def call_model(messages, use_tools=True):
    """فراخوانی مدل با پشتیبانی ابزار"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
    }

    if use_tools:
        payload["tools"] = TOOLS
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(
            f"{API_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=TIMEOUT,
        )
        response.encoding = "utf-8"

        if response.status_code == 200:
            data = clean_response(response.text)
            if data and "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]
            else:
                return {"content": "⚠️ پاسخ نامعتبر"}
        elif response.status_code == 429:
            return {"content": "⚠️ درخواست زیاد! لطفاً صبر کنید."}
        elif response.status_code == 401:
            return {"content": "⚠️ کلید API نامعتبر!"}
        elif response.status_code == 402:
            return {"content": "⚠️ اعتبار تمام شده!"}
        else:
            return {"content": f"⚠️ خطا: {response.status_code}"}

    except requests.Timeout:
        return {"content": "⏰ زمان پاسخ‌دهی تموم شد"}
    except Exception as e:
        return {"content": f"⚠️ خطا: {str(e)}"}


# ── چت اصلی با ابزارها ──────────────────────────────
def chat_with_tools(user_msg, user_id):
    """چت با پشتیبانی ابزار (مثل Hermes Agent)"""
    history = get_history(user_id)
    memory = load_memory()

    # ساخت پیام‌ها
    system = SYSTEM_PROMPT
    if memory["facts"]:
        memory_text = "\n".join([f"- {f['text']}" for f in memory["facts"][-10:]])
        system += f"\n\nحافظه بلندمدت:\n{memory_text}"

    messages = [{"role": "system", "content": system}]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_msg})

    # حلقه ابزار (حداکثر ۵ دور)
    for round_num in range(5):
        response = call_model(messages, use_tools=True)

        # اگه محتوا داشت → تموم شد
        if response.get("content") and not response.get("tool_calls"):
            return response["content"]

        # اگه tool call داشت → اجرا کن
        if response.get("tool_calls"):
            # اضافه کردن پاسخ مدل به پیام‌ها
            messages.append(response)

            for tool_call in response["tool_calls"]:
                func = tool_call["function"]
                tool_name = func["name"]
                tool_args = json.loads(func["arguments"])

                logger.info(f"🔧 ابزار: {tool_name}({tool_args})")
                result = execute_tool(tool_name, tool_args)
                logger.info(f"📤 نتیجه: {result[:100]}...")

                # اضافه کردن نتیجه ابزار
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })
        else:
            break

    # اگه بعد از ۵ دور هنوز tool call داشت
    return "⚠️ پردازش طولانی شد. لطفاً ساده‌تر بپرسید."


# ── بررسی متغیرها ────────────────────────────────────
def check_env():
    if not API_KEY:
        logger.error("❌ OPENAI_API_KEY تنظیم نشده!")
        return False
    logger.info(f"✅ API: {API_URL}")
    logger.info(f"✅ Model: {MODEL}")
    return True


# ── دستورات ───────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""🤖 **سلام! من Hermes Agent هستم!**

من یک دستیار هوش مصنوعی هوشمندم که می‌تونم:

🔧 **ابزارها:**
• اجرای کد Python
• جستجو در اینترنت
• خواندن/نوشتن فایل
• حافظه بلندمدت

📝 **دستورات:**
/start - شروع
/help - راهنما
/model - نمایش مدل
/memory - حافظه
/clear - پاک کردن تاریخچه
/files - لیست فایل‌ها

⚡ مدل: `{MODEL}`
🌐 API: `{API_URL.split('/')[2]}`"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📖 **راهنمای Hermes Agent:**

💬 **نحوه استفاده:**
فقط پیام بفرست! من خودم ابزار مناسب رو انتخاب میکنم.

🔧 **مثال‌ها:**
• "محاسبه ۲+۲" → اجرای کد
• " gonorrhoea چیه" → جستجو
• "یه فایل بنویس" → نوشتن فایل
• "اسم من مهدیه" → ذخیره در حافظه

📝 **دستورات:**
/start - شروع
/help - راهنما
/model - نمایش مدل
/memory - نمایش حافظه
/clear - پاک کردن تاریخچه
/files - لیست فایل‌ها"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def model_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""🤖 **مدل فعلی:**
`{MODEL}`

🌐 **API:**
`{API_URL}`

🔧 **ابزارها:** ۶ ابزار فعال
🧠 **حافظه:** {'✅ فعال' if MEMORY_FILE.exists() else '🟢 خالی'}"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_memory()
    await update.message.reply_text(text, parse_mode="Markdown")


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_history[user_id] = []
    await update.message.reply_text("✅ تاریخچه پاک شد!")


async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = tool_list_files()
    await update.message.reply_text(text, parse_mode="Markdown")


# ── چت اصلی ──────────────────────────────────────────
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_id = update.effective_user.id

    # ذخیره پیام کاربر
    add_to_history(user_id, "user", user_msg)

    # نمایش در حال پردازش
    processing = await update.message.reply_text("⏳ در حال پردازش...")

    # اجرای چت با ابزارها
    bot_reply = chat_with_tools(user_msg, user_id)

    # ذخیره پاسخ
    add_to_history(user_id, "assistant", bot_reply)

    # حذف پیام در حال پردازش و ارسال جواب
    await processing.delete()

    # ارسال با حداکثر طول تلگرام
    if len(bot_reply) > 4000:
        for i in range(0, len(bot_reply), 4000):
            await update.message.reply_text(bot_reply[i:i+4000])
    else:
        await update.message.reply_text(bot_reply)


# ── اجرای اصلی ───────────────────────────────────────
def main():
    ensure_dirs()

    logger.info("=" * 50)
    logger.info("🤖 Hermes Agent Bot شروع شد!")
    logger.info(f"🧠 مدل: {MODEL}")
    logger.info(f"🌐 API: {API_URL}")
    logger.info(f"🔧 ابزارها: ۶ ابزار فعال")
    logger.info("=" * 50)

    if not check_env():
        return

    app = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("model", model_cmd))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start", "شروع"),
            BotCommand("help", "راهنما"),
            BotCommand("model", "مدل فعلی"),
            BotCommand("memory", "حافظه"),
            BotCommand("clear", "پاک کردن تاریخچه"),
            BotCommand("files", "لیست فایل‌ها"),
        ])

    app.post_init = post_init

    logger.info("✅ Hermes Agent آماده!")
    app.run_polling()


if __name__ == "__main__":
    main()
