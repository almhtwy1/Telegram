from telegram import Update
from telegram.ext import ContextTypes
from user_manager import user_manager
from config import logger

class AccessControl:
    
    @staticmethod
    async def check_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فحص صلاحية وصول المستخدم"""
        user = update.effective_user
        user_id = user.id
        
        # فحص إذا كان المستخدم أدمن
        if user_manager.is_admin(user_id):
            return True
        
        # فحص إذا كان المستخدم معتمد
        if user_manager.is_approved(user_id):
            return True
        
        # فحص إذا كان المستخدم مرفوض
        if user_manager.is_rejected(user_id):
            await update.message.reply_text(
                "😔 تم رفض طلب اشتراكك سابقاً.\n"
                "إذا كنت تعتقد أن هذا خطأ، يمكنك التواصل مع الإدارة."
            )
            return False
        
        # فحص إذا كان المستخدم في الانتظار
        if user_manager.is_pending(user_id):
            await update.message.reply_text(
                "⏳ طلب اشتراكك قيد المراجعة.\n"
                "سيتم إشعارك عند الموافقة على طلبك."
            )
            return False
        
        # مستخدم جديد - إضافة للانتظار
        username = user.username
        first_name = user.first_name
        
        if user_manager.add_pending_user(user_id, username, first_name):
            # إرسال إشعار للأدمن
            await AccessControl._notify_admin_new_user(context, user_id, username, first_name)
            
            await update.message.reply_text(
                "🔔 تم استلام طلب اشتراكك!\n\n"
                "⏳ طلبك قيد المراجعة من قبل الإدارة.\n"
                "سيتم إشعارك عند الموافقة على طلبك.\n\n"
                "شكراً لصبرك! 🙏"
            )
        else:
            await update.message.reply_text(
                "❌ حدث خطأ في معالجة طلبك.\n"
                "يرجى المحاولة مرة أخرى لاحقاً."
            )
        
        return False
    
    @staticmethod
    async def _notify_admin_new_user(context: ContextTypes.DEFAULT_TYPE, user_id, username, first_name):
        """إشعار الأدمن بمستخدم جديد"""
        try:
            admin_id = user_manager.admin_id
            message = (
                "🔔 *طلب اشتراك جديد!*\n\n"
                f"👤 *الاسم:* {first_name or 'غير محدد'}\n"
                f"📱 *المعرف:* @{username or 'غير محدد'}\n"
                f"🆔 *ID:* `{user_id}`\n\n"
                "استخدم /pending لعرض الطلبات المعلقة."
            )
            
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"📤 تم إرسال إشعار للأدمن عن المستخدم الجديد: {first_name}")
            
        except Exception as e:
            logger.error(f"❌ فشل إرسال إشعار الأدمن: {e}")

# إنشاء مثيل مشترك
access_control = AccessControl()
