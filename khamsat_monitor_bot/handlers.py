from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ALLOWED_USER_ID, logger
from scraper import fetch_posts
from formatter import format_posts_list
# استيراد مدير الإعدادات
from settings_manager import settings_manager
from category_filter import category_filter

def get_keyboard():
    """إنشاء لوحة المفاتيح"""
    return ReplyKeyboardMarkup([
        ["📋 عرض الطلبات الجديدة"],
        ["🚨 تفعيل الرصد التلقائي", "⛔️ إيقاف الرصد"],
        ["🏷️ اختيار الفئات", "🧭 عرض الأوامر"]
    ], resize_keyboard=True)

def check_permission(update: Update):
    """فحص صلاحية المستخدم"""
    return update.effective_user.id == ALLOWED_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت"""
    if not check_permission(update):
        await update.message.reply_text("🚫 لا تملك صلاحية استخدام هذا البوت.")
        return

    logger.info("🚀 تم بدء البوت")
    
    # عرض حالة المراقبة الحالية
    monitoring_status = "🟢 مفعل" if settings_manager.is_monitoring_active() else "🔴 معطل"
    
    await update.message.reply_text(
        f"🔥 بوت مراقبة خمسات\n"
        f"📈 يعرض المواضيع الحديثة فقط (أقل من 3 دقائق)\n"
        f"📊 حالة الرصد التلقائي: {monitoring_status}\n\n"
        f"اختر أمرًا:",
        reply_markup=get_keyboard()
    )

async def show_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المنشورات"""
    if not check_permission(update):
        return
    
    logger.info("📋 طلب عرض المنشورات")
    recent_posts, all_posts = fetch_posts()
    
    posts_to_show = all_posts[:10] if all_posts else []
    if not posts_to_show:
        await update.message.reply_text("⚠️ لا توجد مواضيع متاحة")
        return
    
    message = format_posts_list(posts_to_show, show_index=True)
    await update.message.reply_markdown(message, disable_web_page_preview=True)
    logger.info(f"✅ تم عرض {len(posts_to_show)} موضوع")

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تفعيل المراقبة"""
    if not check_permission(update):
        return
    
    settings_manager.set_monitoring_active(True)
    logger.info("🚨 تم تفعيل الرصد التلقائي")
    await update.message.reply_text("✅ تم تفعيل الرصد التلقائي")

async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف المراقبة"""
    if not check_permission(update):
        return
    
    settings_manager.set_monitoring_active(False)
    logger.info("⛔️ تم إيقاف الرصد التلقائي")
    await update.message.reply_text("⛔️ تم إيقاف الرصد")

async def select_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة اختيار الفئات"""
    if not check_permission(update):
        return
    
    logger.info("🏷️ طلب عرض إعدادات الفئات")
    await update.message.reply_text(
        category_filter.get_status_text(),
        parse_mode="Markdown",
        reply_markup=category_filter.create_category_keyboard()
    )
    """عرض المساعدة"""
    if not check_permission(update):
        return
    
    await update.message.reply_text(
        "🧭 *الأوامر المتاحة:*\n\n"
        "📋 *عرض الطلبات الجديدة* - أول 10 مواضيع\n"
        "🚨 *تفعيل الرصد التلقائي* - مراقبة كل 30 ثانية\n"
        "⛔️ *إيقاف الرصد* - إيقاف المراقبة\n"
        "🧭 *عرض الأوامر* - هذه الرسالة\n\n"
        "⚡️ يتم إرسال المواضيع الحديثة فقط (أقل من 3 دقائق)",
        parse_mode="Markdown"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    if not check_permission(update):
        return
    
    text = update.message.text
    handlers = {
        "📋 عرض الطلبات الجديدة": show_posts,
        "🚨 تفعيل الرصد التلقائي": start_monitoring,
        "⛔️ إيقاف الرصد": stop_monitoring,
        "🏷️ اختيار الفئات": select_categories,
        "🧭 عرض الأوامر": help_command
    }
    
    handler = handlers.get(text)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text("⚠️ أمر غير معروف. استخدم الأزرار.")

def is_monitoring_active():
    """فحص حالة المراقبة"""
    return settings_manager.is_monitoring_active()
