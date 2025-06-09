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
        # إضافة أزرار خاصة بالأدمن - مبسطة
        admin_row1 = ["👥 طلبات الانتظار", "📊 إحصائيات"]
        admin_row2 = ["📋 قائمة المستخدمين", "🔍 البحث"]
        admin_row3 = ["✅ موافقة", "❌ رفض", "🗑️ حذف"]
        
        basic_keyboard.extend([admin_row1, admin_row2, admin_row3])
    
    return ReplyKeyboardMarkup(basic_keyboard, resize_keyboard=True)

def check_permission(update: Update):
    """فحص صلاحية المستخدم - الآن يدعم المستخدمين المعتمدين"""
    user_id = update.effective_user.id
    return user_manager.is_admin(user_id) or user_manager.is_approved(user_id)

def is_monitoring_active():
    """فحص حالة المراقبة"""
    return settings_manager.is_monitoring_active()

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

async def test_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار صلاحيات الأدمن"""
    user_id = update.effective_user.id
    is_admin = user_manager.is_admin(user_id)
    is_approved = user_manager.is_approved(user_id)
    
    await update.message.reply_text(
        f"🔍 *اختبار الصلاحيات:*\n\n"
        f"🆔 معرفك: `{user_id}`\n"
        f"👑 أدمن: {'✅ نعم' if is_admin else '❌ لا'}\n"
        f"✅ معتمد: {'✅ نعم' if is_approved else '❌ لا'}\n\n"
        f"معرف الأدمن المحدد: `{user_manager.admin_id}`",
        parse_mode="Markdown"
    )

async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة أوامر الأدمن (بديل بسيط)"""
    user_id = update.effective_user.id
    
    if not user_manager.is_admin(user_id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    stats = user_manager.get_stats()
    
    menu_text = (
        "👑 *قائمة أوامر الأدمن*\n\n"
        f"📊 *الإحصائيات:*\n"
        f"✅ المعتمدين: {stats['approved']}\n"
        f"⏳ في الانتظار: {stats['pending']}\n"
        f"❌ المرفوضين: {stats['rejected']}\n\n"
        
        "🛠️ *الأوامر المتاحة:*\n"
        "/pending - عرض طلبات الانتظار\n"
        "/approve معرف_المستخدم - الموافقة على مستخدم\n"
        "/reject معرف_المستخدم - رفض مستخدم\n"
        "/remove معرف_المستخدم - حذف مستخدم\n"
        "/search نص_البحث - البحث عن مستخدم\n"
        "/list - قائمة المستخدمين المعتمدين\n"
        "/stats - الإحصائيات المفصلة\n\n"
        
        "💡 *مثال:* `/approve 123456789`"
    )
    
    await update.message.reply_text(menu_text, parse_mode="Markdown")

async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الموافقة على مستخدم"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    if not context.args:
        await update.message.reply_text("❌ استخدم: `/approve معرف_المستخدم`\nمثال: `/approve 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        user_info = user_manager.approve_user(user_id)
        
        if user_info:
            await update.message.reply_text(f"✅ تم قبول المستخدم: {user_info['first_name']}")
            
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 تم قبول طلب اشتراكك في البوت!\nيمكنك الآن استخدام جميع الميزات.\nأرسل /start للبدء."
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ المستخدم غير موجود في قائمة الانتظار")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")

async def reject_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفض مستخدم"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    if not context.args:
        await update.message.reply_text("❌ استخدم: `/reject معرف_المستخدم`\nمثال: `/reject 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        user_info = user_manager.reject_user(user_id)
        
        if user_info:
            await update.message.reply_text(f"❌ تم رفض المستخدم: {user_info['first_name']}")
            
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="😔 تم رفض طلب اشتراكك في البوت."
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ المستخدم غير موجود في قائمة الانتظار")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")

async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مستخدم"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    if not context.args:
        await update.message.reply_text("❌ استخدم: `/remove معرف_المستخدم`\nمثال: `/remove 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        success, message = user_manager.remove_user(user_id)
        
        if success:
            await update.message.reply_text(f"✅ {message}")
            
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚫 تم إلغاء اشتراكك في البوت من قبل الإدارة."
                )
            except:
                pass
        else:
            await update.message.reply_text(f"❌ {message}")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")

async def search_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث عن مستخدم"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    if not context.args:
        await update.message.reply_text("❌ استخدم: `/search نص_البحث`\nمثال: `/search أحمد`", parse_mode="Markdown")
        return
    
    search_term = " ".join(context.args)
    results = user_manager.search_user(search_term)
    
    if not results:
        await update.message.reply_text(f"🔍 لم يتم العثور على مستخدمين بالبحث: `{search_term}`", parse_mode="Markdown")
        return
    
    message = f"🔍 *نتائج البحث عن:* `{search_term}`\n\n"
    
    for result in results[:10]:
        user_info = result["info"]
        status_icon = {"معتمد": "✅", "انتظار": "⏳", "مرفوض": "❌"}.get(result["status"], "❓")
        
        message += f"{status_icon} *{user_info['first_name']}*\n"
        message += f"   📱 @{user_info['username']}\n"
        message += f"   🆔 `{result['user_id']}`\n"
        message += f"   📊 {result['status']}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة المستخدمين المعتمدين"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    approved_users = user_manager.get_approved_users()
    
    if not approved_users:
        await update.message.reply_text("📭 لا توجد مستخدمين معتمدين")
        return
    
    message = "✅ *المستخدمين المعتمدين:*\n\n"
    
    for i, user_id in enumerate(approved_users, 1):
        user_details = user_manager.get_user_details(user_id)
        user_info = user_details["info"]
        
        status_icon = "👑" if user_id == user_manager.admin_id else "👤"
        message += f"{status_icon} *{i}.* {user_info['first_name']}\n"
        message += f"   📱 @{user_info['username']}\n"
        message += f"   🆔 `{user_id}`\n\n"
        
        # تجنب الرسائل الطويلة جداً
        if len(message) > 3000:
            await update.message.reply_text(message, parse_mode="Markdown")
            message = ""
    
    if message:
        await update.message.reply_text(message, parse_mode="Markdown")
    """عرض لوحة تحكم الأدمن"""
    user_id = update.effective_user.id
    logger.info(f"👑 طلب فتح لوحة تحكم الأدمن من المستخدم {user_id}")
    
    if not user_manager.is_admin(user_id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    try:
        await admin_handlers.show_admin_menu(update, context)
        logger.info("✅ تم فتح لوحة تحكم الأدمن بنجاح")
    except Exception as e:
        logger.error(f"❌ خطأ في فتح لوحة تحكم الأدمن: {e}")
        await update.message.reply_text("❌ حدث خطأ في فتح لوحة التحكم")
    """عرض لوحة تحكم الأدمن"""
    user_id = update.effective_user.id
    logger.info(f"👑 طلب فتح لوحة تحكم الأدمن من المستخدم {user_id}")
    
    if not user_manager.is_admin(user_id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    try:
        await admin_handlers.show_admin_menu(update, context)
        logger.info("✅ تم فتح لوحة تحكم الأدمن بنجاح")
    except Exception as e:
        logger.error(f"❌ خطأ في فتح لوحة تحكم الأدمن: {e}")
        await update.message.reply_text("❌ حدث خطأ في فتح لوحة التحكم")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    logger.info(f"🔘 المستخدم {user_id} ضغط على: {text}")
    
    # معالجة الأزرار الأساسية
    if text == "📋 عرض الطلبات الجديدة":
        await show_posts(update, context)
    elif text == "🚨 تفعيل الرصد التلقائي":
        await start_monitoring(update, context)
    elif text == "⛔️ إيقاف الرصد":
        await stop_monitoring(update, context)
    elif text == "🏷️ اختيار الفئات":
        await select_categories(update, context)
    elif text == "🧭 عرض الأوامر":
        await help_command(update, context)
    elif text == "👑 لوحة تحكم الأدمن" and is_admin:
        logger.info(f"👑 الأدمن {user_id} يفتح لوحة التحكم")
        await admin_menu_command(update, context)
    else:
        # التحقق إذا كان النص يحتوي على معرف مستخدم أو مصطلح بحث للأدمن
        if is_admin and hasattr(context, 'user_data') and context.user_data.get('waiting_for'):
            await admin_handlers.handle_admin_text_input(update, context)
        else:
            await update.message.reply_text("⚠️ أمر غير معروف. استخدم الأزرار.")
