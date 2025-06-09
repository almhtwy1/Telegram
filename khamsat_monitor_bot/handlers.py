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
from admin_state import set_admin_state, get_admin_state, clear_admin_state

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
        admin_row4 = ["🔔 إشعارات الأدمن"]  # زر جديد للتحكم في إشعارات الأدمن
        
        basic_keyboard.extend([admin_row1, admin_row2, admin_row3, admin_row4])
    
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

async def toggle_admin_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل حالة إشعارات الأدمن"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    current_status = settings_manager.is_admin_notifications_enabled()
    new_status = not current_status
    settings_manager.set_admin_notifications(new_status)
    
    if new_status:
        await update.message.reply_text(
            "🔔 **تم تفعيل إشعارات الأدمن**\n\n"
            "✅ ستصلك الآن إشعارات بالمواضيع الجديدة\n"
            "📋 تذكر اختيار فئاتك المفضلة في `🏷️ اختيار الفئات`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🔕 **تم إلغاء إشعارات الأدمن**\n\n"
            "❌ لن تصلك إشعارات تلقائية\n"
            "📋 يمكنك مراجعة المواضيع يدوياً بـ `📋 عرض الطلبات الجديدة`",
            parse_mode="Markdown"
        )

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
        "🧭 **الأوامر المتاحة:**\n\n"
        "📋 **عرض الطلبات الجديدة** - أول 10 مواضيع\n"
        "🚨 **تفعيل الرصد التلقائي** - مراقبة كل 30 ثانية\n"
        "⛔️ **إيقاف الرصد** - إيقاف المراقبة\n"
        "🏷️ **اختيار الفئات** - تخصيص فئاتك الشخصية\n"
    )
    
    if is_admin:
        notifications_status = "مفعلة" if settings_manager.is_admin_notifications_enabled() else "معطلة"
        help_text += (
            "\n👑 **أزرار الأدمن:**\n"
            "👥 **طلبات الانتظار** - عرض الطلبات الجديدة\n"
            "📊 **إحصائيات** - أرقام مفصلة\n"
            "📋 **قائمة المستخدمين** - المعتمدين\n"
            "🔍 **البحث** - العثور على مستخدم\n"
            "✅ **موافقة** - قبول مستخدم\n"
            "❌ **رفض** - رفض مستخدم\n"
            "🗑️ **حذف** - حذف مستخدم معتمد\n"
            f"🔔 **إشعارات الأدمن** - حالياً: {notifications_status}\n"
        )
    
    help_text += f"\n📊 **فئاتك الحالية:** {categories_status}\n"
    help_text += "⚡️ يتم إرسال المواضيع الحديثة فقط (أقل من 3 دقائق)"
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

# دوال الأدمن البسيطة
async def simple_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action):
    """معالج بسيط لأعمال الأدمن"""
    user_id = update.effective_user.id
    
    if action == "pending":
        await admin_handlers.show_pending_users(update, context)
    elif action == "stats":
        await admin_handlers.show_stats(update, context)
    elif action == "list":
        await list_users_command(update, context)
    elif action == "search":
        set_admin_state(user_id, "waiting_search")
        await update.message.reply_text(
            "🔍 **البحث عن مستخدم**\n\n"
            "أرسل اسم المستخدم أو جزء منه:",
            parse_mode="Markdown"
        )
    elif action == "approve":
        set_admin_state(user_id, "waiting_approve")
        await update.message.reply_text(
            "✅ **الموافقة على مستخدم**\n\n"
            "أرسل معرف المستخدم (ID):\n"
            "مثال: `123456789`",
            parse_mode="Markdown"
        )
    elif action == "reject":
        set_admin_state(user_id, "waiting_reject")
        await update.message.reply_text(
            "❌ **رفض مستخدم**\n\n"
            "أرسل معرف المستخدم (ID):\n"
            "مثال: `123456789`",
            parse_mode="Markdown"
        )
    elif action == "remove":
        set_admin_state(user_id, "waiting_remove")
        await update.message.reply_text(
            "🗑️ **حذف مستخدم**\n\n"
            "أرسل معرف المستخدم (ID):\n"
            "مثال: `123456789`\n\n"
            "⚠️ سيتم حذفه نهائياً!",
            parse_mode="Markdown"
        )

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج مدخلات الأدمن"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state_info = get_admin_state(user_id)
    
    if not state_info:
        return False  # ليس في حالة انتظار
    
    state = state_info.get("state")
    
    if state == "waiting_search":
        clear_admin_state(user_id)
        results = user_manager.search_user(text)
        
        if not results:
            await update.message.reply_text(f"🔍 لم يتم العثور على: `{text}`", parse_mode="Markdown")
            return True
        
        message = f"🔍 **نتائج البحث عن:** `{text}`\n\n"
        for result in results[:10]:
            user_info = result["info"]
            status_icon = {"معتمد": "✅", "انتظار": "⏳", "مرفوض": "❌"}.get(result["status"], "❓")
            
            message += f"{status_icon} **{user_info.get('first_name', 'غير معروف')}**\n"
            message += f"   📱 @{user_info.get('username', 'غير معروف')}\n"
            message += f"   🆔 `{result['user_id']}`\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        return True
        
    elif state == "waiting_approve":
        clear_admin_state(user_id)
        try:
            target_user_id = int(text)
            user_info = user_manager.approve_user(target_user_id)
            
            if user_info:
                await update.message.reply_text(f"✅ تم قبول: {user_info['first_name']}")
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="🎉 تم قبول طلبك! أرسل /start للبدء."
                    )
                except:
                    pass
            else:
                await update.message.reply_text("❌ المستخدم غير موجود في قائمة الانتظار")
        except ValueError:
            await update.message.reply_text("❌ يجب أن يكون رقماً")
        return True
        
    elif state == "waiting_reject":
        clear_admin_state(user_id)
        try:
            target_user_id = int(text)
            user_info = user_manager.reject_user(target_user_id)
            
            if user_info:
                await update.message.reply_text(f"❌ تم رفض: {user_info['first_name']}")
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="😔 تم رفض طلبك."
                    )
                except:
                    pass
            else:
                await update.message.reply_text("❌ المستخدم غير موجود في قائمة الانتظار")
        except ValueError:
            await update.message.reply_text("❌ يجب أن يكون رقماً")
        return True
        
    elif state == "waiting_remove":
        clear_admin_state(user_id)
        try:
            target_user_id = int(text)
            success, message = user_manager.remove_user(target_user_id)
            
            if success:
                await update.message.reply_text(f"✅ {message}")
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="🚫 تم إلغاء اشتراكك."
                    )
                except:
                    pass
            else:
                await update.message.reply_text(f"❌ {message}")
        except ValueError:
            await update.message.reply_text("❌ يجب أن يكون رقماً")
        return True
    
    return False

# دوال الأوامر القديمة (للتوافق مع الكود القديم)
async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة أوامر الأدمن (بديل بسيط)"""
    await help_command(update, context)

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة المستخدمين المعتمدين"""
    if not user_manager.is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
        return
    
    approved_users = user_manager.get_approved_users()
    
    if not approved_users:
        await update.message.reply_text("📭 لا توجد مستخدمين معتمدين")
        return
    
    message = "✅ **المستخدمين المعتمدين:**\n\n"
    
    for i, user_id in enumerate(approved_users, 1):
        # البحث عن معلومات المستخدم
        user_info = user_manager._find_user_info(user_id)
        
        if user_info:
            status_icon = "👑" if user_id == user_manager.admin_id else "👤"
            message += f"{status_icon} **{i}.** {user_info['first_name']}\n"
            message += f"   📱 @{user_info['username']}\n"
            message += f"   🆔 `{user_id}`\n\n"
        else:
            # إذا لم تتوفر معلومات المستخدم
            status_icon = "👑" if user_id == user_manager.admin_id else "👤"
            message += f"{status_icon} **{i}.** مستخدم {user_id}\n"
            message += f"   🆔 `{user_id}`\n\n"
        
        # تجنب الرسائل الطويلة جداً
        if len(message) > 3000:
            await update.message.reply_text(message, parse_mode="Markdown")
            message = ""
    
    if message:
        await update.message.reply_text(message, parse_mode="Markdown")

# دوال فارغة للتوافق
async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def reject_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def search_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    if not check_permission(update):
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    is_admin = user_manager.is_admin(user_id)
    
    logger.info(f"🔘 المستخدم {user_id} ضغط على: {text}")
    
    # أولاً، فحص إذا كان المستخدم في حالة انتظار إدخال
    if is_admin and await handle_admin_input(update, context):
        return
    
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
        
    # أزرار الأدمن البسيطة
    elif is_admin and text == "👥 طلبات الانتظار":
        await simple_admin_action(update, context, "pending")
    elif is_admin and text == "📊 إحصائيات":
        await simple_admin_action(update, context, "stats")
    elif is_admin and text == "📋 قائمة المستخدمين":
        await simple_admin_action(update, context, "list")
    elif is_admin and text == "🔍 البحث":
        await simple_admin_action(update, context, "search")
    elif is_admin and text == "✅ موافقة":
        await simple_admin_action(update, context, "approve")
    elif is_admin and text == "❌ رفض":
        await simple_admin_action(update, context, "reject")
    elif is_admin and text == "🗑️ حذف":
        await simple_admin_action(update, context, "remove")
    elif is_admin and text == "🔔 إشعارات الأدمن":
        await toggle_admin_notifications(update, context)
    else:
        await update.message.reply_text("⚠️ أمر غير معروف. استخدم الأزرار.")
