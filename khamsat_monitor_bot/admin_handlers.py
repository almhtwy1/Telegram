from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from user_manager import user_manager
from config import logger

class AdminHandlers:
    def __init__(self):
        self.callback_prefix = "admin_"
    
    async def show_pending_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المستخدمين في الانتظار"""
        if not user_manager.is_admin(update.effective_user.id):
            return
        
        pending_users = user_manager.get_pending_users()
        
        if not pending_users:
            await update.message.reply_text("✅ لا توجد طلبات انتظار")
            return
        
        message = "⏳ *طلبات الاشتراك في الانتظار:*\n\n"
        
        for user_id, info in pending_users.items():
            username = info.get('username', 'غير محدد')
            first_name = info.get('first_name', 'غير محدد')
            timestamp = info.get('timestamp', 'غير محدد')
            
            message += f"👤 *الاسم:* {first_name}\n"
            message += f"📱 *المعرف:* @{username}\n"
            message += f"🆔 *ID:* `{user_id}`\n"
            message += f"⏰ *التاريخ:* {timestamp}\n"
            
            # أزرار الموافقة والرفض
            keyboard = [
                [
                    InlineKeyboardButton("✅ موافقة", callback_data=f"{self.callback_prefix}approve_{user_id}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"{self.callback_prefix}reject_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            message = ""  # إعادة تعيين للمستخدم التالي
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المستخدمين"""
        if not user_manager.is_admin(update.effective_user.id):
            return
        
        stats = user_manager.get_stats()
        
        message = (
            "📊 *إحصائيات المستخدمين:*\n\n"
            f"✅ المعتمدين: {stats['approved']}\n"
            f"⏳ في الانتظار: {stats['pending']}\n"
            f"❌ المرفوضين: {stats['rejected']}\n\n"
            f"📈 إجمالي الطلبات: {stats['approved'] + stats['pending'] + stats['rejected']}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج استدعاءات الأدمن"""
        query = update.callback_query
        await query.answer()
        
        if not user_manager.is_admin(query.from_user.id):
            await query.edit_message_text("🚫 غير مصرح لك بهذا الإجراء")
            return
        
        callback_data = query.data
        if not callback_data.startswith(self.callback_prefix):
            return
        
        action_data = callback_data[len(self.callback_prefix):]
        
        if action_data.startswith("approve_"):
            user_id = int(action_data.split("_")[1])
            user_info = user_manager.approve_user(user_id)
            
            if user_info:
                await query.edit_message_text(
                    f"✅ تم قبول المستخدم: {user_info['first_name']}\n"
                    f"سيتم إرسال إشعار له بالموافقة."
                )
                
                # إرسال إشعار للمستخدم
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 تم قبول طلب اشتراكك في البوت!\n"
                             "يمكنك الآن استخدام جميع الميزات.\n"
                             "أرسل /start للبدء."
                    )
                    logger.info(f"📤 تم إرسال إشعار الموافقة للمستخدم {user_id}")
                except Exception as e:
                    logger.error(f"❌ فشل إرسال إشعار الموافقة: {e}")
            else:
                await query.edit_message_text("❌ خطأ في الموافقة على المستخدم")
        
        elif action_data.startswith("reject_"):
            user_id = int(action_data.split("_")[1])
            user_info = user_manager.reject_user(user_id)
            
            if user_info:
                await query.edit_message_text(
                    f"❌ تم رفض المستخدم: {user_info['first_name']}\n"
                    f"سيتم إرسال إشعار له بالرفض."
                )
                
                # إرسال إشعار للمستخدم
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="😔 تم رفض طلب اشتراكك في البوت.\n"
                             "إذا كنت تعتقد أن هذا خطأ، يمكنك إرسال /start مرة أخرى."
                    )
                    logger.info(f"📤 تم إرسال إشعار الرفض للمستخدم {user_id}")
                except Exception as e:
                    logger.error(f"❌ فشل إرسال إشعار الرفض: {e}")
            else:
                await query.edit_message_text("❌ خطأ في رفض المستخدم")

# إنشاء مثيل مشترك
admin_handlers = AdminHandlers()
