from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ALLOWED_USER_ID, logger
from scraper import fetch_posts
from formatter import format_posts_list
# استيراد مدير الإعدادات
from settings_manager import settings_manager
from category_filter import category_filter
from post_filter import filter_posts_by_category
# استيراد نظام التحكم في الوصول
from access_control import access_control
from user_manager import user_manager
from admin_handlers import admin_handlers

def get_keyboard(is_admin=False):
    """إنشاء لوحة المفاتيح"""
    basic_keyboard = [
        ["📋 عرض الطلبات الجديدة"],
        ["🚨 تفعيل الرصد التلقائي", "⛔️ إيقاف الرصد"],
        ["🏷️ اختيار الفئات", "🧭 عرض الأوامر"]
    ]
    
    if is_admin:
        # إضافة أزرار خاصة بالأدمن
        basic_keyboard.append(["👑 لوحة تحكم الأدمن"])
    
    return ReplyKeyboardMarkup(basic_keyboard, resize_keyboard=True)

def check_permission(update: Update):
    """فحص صلاحية المستخدم - الآن يدعم المستخدمين المعتمدين"""
    user_id = update.effective_user.id
    return user_manager.is_admin(user_id) or user_manager.is_approved(user_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت"""
    # فحص صلاحية الوصول أولاً
    if not await access_control.check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    is_admin = user_manager.is_admin(user_id)
    
    logger.info(f"🚀 تم بدء البوت - المستخدم: {update.effective_user.first_name}")
    
    # عرض حالة المراقبة الحالية
    monitoring_status = "🟢 مفعل" if settings_manager.is_monitoring_active() else "🔴 معطل"
    
    welcome_message = f"🔥 بوت مراقبة خمسات\n"
    welcome_message += f"📈 يعرض المواضيع الحديثة فقط (أقل من 3 دقائق)\n"
    welcome_message += f"📊 حالة الرصد التلقائي: {monitoring_status}\n"
    
    if is_admin:
        welcome_message += f"\n👑 مرحباً بك أيها الأدمن!"
    
    welcome_message += f"\n\nاختر أمرًا:"
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_keyboard(is_admin)
    )

async def show_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المنشورات"""
    if not check_permission(update):
        return
    
    user_id = update.effective_user.id
    logger.info(f"📋 طلب عرض المنشورات من المستخدم {user_id}")
    recent_posts, all_posts = fetch_posts()
    
    # تطبيق تصفية الفئات الشخصية
    filtered_posts = filter_posts_by_category(all_posts[:10], user_id)
    
    if not filtered_posts:
        await update.message.reply_text("⚠️ لا توجد مواضيع متاحة للفئات المختارة")
        return
    
    message = format_posts_list(filtered_posts, show_index=True)
    await update.message.reply_markdown(message, disable_web_page_preview=True)
    logger.info(f"✅ تم عرض {len(filtered_posts)} موضوع للمستخدم {user_id}")

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
    
    user_id = update.effective_user.id
    logger.info(f"🏷️ طلب عرض إعدادات الفئات من المستخدم {user_id}")
    
    # تحديد المستخدم الحالي في نظام الفئات
    category_filter.set_current_user(user_id)
    
    await update.message.reply_text(
        category_filter.get_status_text(),
        parse_mode="Markdown",
        reply_markup=category_filter.create_category_keyboard()
    )

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة تحكم الأدمن"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    await admin_handlers.show_admin_menu(update, context)
    """عرض المساعدة"""
    if not check_permission(update):
        return
    
    user_id = update.effective_user.id
    is_admin = user_manager.is_admin(user_id)
    
    # عرض الفئات المختارة للمستخدم
    selected = settings_manager.get_selected_categories(user_id)
    if len(selected) == 0:
        categories_status = "جميع الفئات"
    elif "__none__" in selected:
        categories_status = "لا توجد فئات"
    else:
        categories_status = f"{len(selected)} فئة مختارة"
    
    help_text = (
        "🧭 *الأوامر المتاحة:*\n\n"
        "📋 *عرض الطلبات الجديدة* - أول 10 مواضيع\n"
        "🚨 *تفعيل الرصد التلقائي* - مراقبة كل 30 ثانية\n"
        "⛔️ *إيقاف الرصد* - إيقاف المراقبة\n"
        "🏷️ *اختيار الفئات* - تخصيص فئاتك الشخصية\n"
        "🧭 *عرض الأوامر* - هذه الرسالة\n"
    )
    
    if is_admin:
        help_text += "\n👑 *أوامر الأدمن:*\n"
        help_text += "👑 *لوحة تحكم الأدمن* - إدارة المستخدمين\n"
        help_text += "/admin - فتح لوحة التحكم\n"
        help_text += "/pending - عرض طلبات الانتظار\n"
        help_text += "/stats - إحصائيات المستخدمين\n"
    
    help_text += f"\n📊 *فئاتك الحالية:* {categories_status}\n"
    help_text += "⚡️ يتم إرسال المواضيع الحديثة فقط (أقل من 3 دقائق)"
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    if not check_permission(update):
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    is_admin = user_manager.is_admin(user_id)
    
    # المعالجات الأساسية
    basic_handlers = {
        "📋 عرض الطلبات الجديدة": show_posts,
        "🚨 تفعيل الرصد التلقائي": start_monitoring,
        "⛔️ إيقاف الرصد": stop_monitoring,
        "🏷️ اختيار الفئات": select_categories,
        "🧭 عرض الأوامر": help_command
    }
    
    # معالجات خاصة بالأدمن
    admin_handlers_dict = {
        "👑 لوحة تحكم الأدمن": show_admin_panel
    }
    
    # دمج المعالجات حسب صلاحية المستخدم
    handlers = basic_handlers.copy()
    if is_admin:
        handlers.update(admin_handlers_dict)
    
    handler = handlers.get(text)
    if handler:
        await handler(update, context)
    else:
        # التحقق إذا كان النص يحتوي على معرف مستخدم أو مصطلح بحث للأدمن
        if is_admin:
            await admin_handlers.handle_admin_text_input(update, context)
        else:
            await update.message.reply_text("⚠️ أمر غير معروف. استخدم الأزرار.")

def is_monitoring_active():
    """فحص حالة المراقبة"""
    return settings_manager.is_monitoring_active()
