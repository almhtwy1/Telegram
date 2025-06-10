import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.error import NetworkError, TelegramError

from config import BOT_TOKEN, logger
from handlers import start, help_command, handle_buttons
from monitor import PostMonitor
from settings_manager import settings_manager

async def error_handler(update, context):
    """معالج الأخطاء العام"""
    error = context.error
    if isinstance(error, NetworkError):
        logger.warning(f"⚠️ خطأ شبكة مؤقت: {error}")
        # لا نحتاج لفعل أي شيء، البوت سيعيد المحاولة تلقائياً
        return
    else:
        logger.error(f"❌ خطأ غير متوقع: {error}")

async def main():
    """الدالة الرئيسية لتشغيل البوت"""
    logger.info("🚀 بدء تشغيل بوت خمسات...")
    
    # إنشاء تطبيق البوت
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)
    
    # إنشاء نظام المراقبة
    monitor = PostMonitor()
    asyncio.create_task(monitor.monitor_loop(app))
    
    # عرض حالة المراقبة عند بدء التشغيل
    if settings_manager.is_monitoring_active():
        logger.info("🟢 البوت سيعمل بوضع المراقبة التلقائية (محفوظ من الجلسة السابقة)")
    else:
        logger.info("🔴 البوت يعمل بوضع يدوي - استخدم /start لتفعيل المراقبة")
    
    logger.info("✅ البوت جاهز!")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
