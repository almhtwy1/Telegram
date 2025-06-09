import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN, logger
from handlers import start, help_command, handle_buttons, show_admin_panel, test_admin
from monitor import PostMonitor
from settings_manager import settings_manager
from category_filter import category_filter
from admin_handlers import admin_handlers
from user_manager import user_manager
from migration_helper import migrate_old_settings

async def main():
    """الدالة الرئيسية لتشغيل البوت"""
    logger.info("🚀 بدء تشغيل بوت خمسات...")
    
    # ترحيل الإعدادات القديمة إذا لزم الأمر
    migrate_old_settings()
    
    # إنشاء تطبيق البوت
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر الأساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", show_admin_panel))
    app.add_handler(CommandHandler("test", test_admin))
    app.add_handler(CommandHandler("pending", admin_handlers.show_pending_users))
    app.add_handler(CommandHandler("stats", admin_handlers.show_stats))
    app.add_handler(CommandHandler("cancel", lambda update, context: update.message.reply_text("❌ تم إلغاء العملية")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    # إضافة معالجات الاستدعاءات التفاعلية
    app.add_handler(CallbackQueryHandler(category_filter.handle_callback, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(admin_handlers.handle_admin_callback, pattern="^admin_"))
    
    # إنشاء نظام المراقبة
    monitor = PostMonitor()
    asyncio.create_task(monitor.monitor_loop(app))
    
    # عرض معلومات التشغيل
    stats = user_manager.get_stats()
    logger.info(f"👥 المستخدمين المعتمدين: {stats['approved']}")
    logger.info(f"⏳ طلبات الانتظار: {stats['pending']}")
    
    # عرض حالة المراقبة عند بدء التشغيل
    if settings_manager.is_monitoring_active():
        logger.info("🟢 البوت سيعمل بوضع المراقبة التلقائية (محفوظ من الجلسة السابقة)")
    else:
        logger.info("🔴 البوت يعمل بوضع يدوي - استخدم /start لتفعيل المراقبة")
    
    logger.info("✅ البوت جاهز للعمل!")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
