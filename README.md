# 🤖 Hermes Agent Bot

بات تلگرام هوشمند مثل Hermes Agent

## ✅ ویژگی‌ها

🔧 **ابزارها:**
- اجرای کد Python
- جستجو در اینترنت (ویکی‌پدیا)
- خواندن/نوشتن فایل
- حافظه بلندمدت
- تاریخچه مکالمه

💰 **پشتیبانی از:**
- Rewind.ai
- OpenRouter
- 9Router
- CometAPI
- OpenCode Zen
- هر OpenAI-compatible API

## 📋 متغیرهای محیطی

| متغیر | توضیح | پیش‌فرض |
|-------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | توکن بات | - |
| `OPENAI_API_KEY` | کلید API | - |
| `OPENAI_BASE_URL` | آدرس API | openrouter.ai |
| `AI_MODEL` | نام مدل | xiaomi/mimo-v2.5 |

## 🚀 Deploy

```
۱. GitHub repo بساز
۲. فایل‌ها رو push کن
۳. Railway → New Project → GitHub
۴. Environment Variables رو اضافه کن
۵. Deploy بزن
```

## 📝 دستورات

```
/start - شروع
/help - راهنما
/model - مدل فعلی
/memory - حافظه
/clear - پاک کردن تاریخچه
/files - لیست فایل‌ها
```

## 💡 مثال‌ها

```
"محاسبه ۲+۲" → اجرای کد Python
"gonorrhoea چیه" → جستجو
"یه فایل بنویس" → نوشتن فایل
"اسم من مهدیه" → ذخیره در حافظه
```

## 📄 License

MIT
