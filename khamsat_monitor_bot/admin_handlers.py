from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from user_manager import user_manager
from config import logger

class AdminHandlers:
    def __init__(self):
        self.callback_prefix = "admin_"
    
    async def show_admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة الأدمن الرئيسية"""
        if not user_manager.is_admin(update.effective_user.id):
            await update.message.reply_text("🚫 هذا الأمر خاص بالأدمن فقط")
            return
        
        stats = user_manager.get_stats()
        
        keyboard = [
            [
                InlineKeyboardButton("👥 طلبات الانتظار", callback_data=f"{self.callback_prefix}pending"),
                InlineKeyboardButton("📊 الإحصائيات", callback_data=f"{self.callback_prefix}stats")
            ],
            [
                InlineKeyboardButton("👤 البحث عن مستخدم", callback_data=f"{self.callback_prefix}search"),
                InlineKeyboardButton("📋 قائمة المعتمدين", callback_data=f"{self.callback_prefix}list_approved")
            ],
            [
                InlineKeyboardButton("🗑️ حذف مستخدم", callback_data=f"{self.callback_prefix}remove_user"),
                InlineKeyboardButton("🔄 إعادة تعيين مستخدم", callback_data=f"{self.callback_prefix}reset_user")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "👑 *لوحة تحكم الأدمن*\n\n"
            f"📊 *الإحصائيات السريعة:*\n"
            f"✅ المعتمدين: {stats['approved']}\n"
            f"⏳ في الانتظار: {stats['pending']}\n"
            f"❌ المرفوضين: {stats['rejected']}\n\n"
            "اختر العملية المطلوبة:"
        )
        
    async def list_approved_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة المستخدمين المعتمدين"""
        if not user_manager.is_admin(update.effective_user.id):
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
        
        # إضافة أزرار للإجراءات السريعة
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف مستخدم", callback_data=f"{self.callback_prefix}remove_user")],
            [InlineKeyboardButton("🔙 العودة للقائمة", callback_data=f"{self.callback_prefix}menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    
    async def handle_remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج حذف المستخدم"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "🗑️ *حذف مستخدم*\n\n"
                "أرسل معرف المستخدم (ID) الذي تريد حذفه:\n"
                "مثال: `123456789`\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🗑️ *حذف مستخدم*\n\n"
                "أرسل معرف المستخدم (ID) الذي تريد حذفه:\n"
                "مثال: `123456789`\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        
        # هنا يمكن إضافة حالة انتظار للرد
        context.user_data['waiting_for'] = 'remove_user_id'
    
    async def handle_reset_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج إعادة تعيين المستخدم"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "🔄 *إعادة تعيين مستخدم*\n\n"
                "أرسل معرف المستخدم (ID) الذي تريد إعادة تعيينه:\n"
                "مثال: `123456789`\n\n"
                "ملاحظة: سيتم حذفه من جميع القوائم ويمكنه التقديم مرة أخرى\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔄 *إعادة تعيين مستخدم*\n\n"
                "أرسل معرف المستخدم (ID) الذي تريد إعادة تعيينه:\n"
                "مثال: `123456789`\n\n"
                "ملاحظة: سيتم حذفه من جميع القوائم ويمكنه التقديم مرة أخرى\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        
        context.user_data['waiting_for'] = 'reset_user_id'
    
    async def handle_search_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج البحث عن المستخدم"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "👤 *البحث عن مستخدم*\n\n"
                "أرسل اسم المستخدم أو جزء من الاسم للبحث:\n"
                "مثال: `أحمد` أو `ahmed`\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "👤 *البحث عن مستخدم*\n\n"
                "أرسل اسم المستخدم أو جزء من الاسم للبحث:\n"
                "مثال: `أحمد` أو `ahmed`\n\n"
                "أو أرسل /cancel للإلغاء",
                parse_mode="Markdown"
            )
        
        context.user_data['waiting_for'] = 'search_term'
    
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
        
        if action_data == "menu":
            # العودة للقائمة الرئيسية
            await self.show_admin_menu(update, context)
            
        elif action_data == "pending":
            await self.show_pending_users(update, context)
            
        elif action_data == "stats":
            await self.show_stats(update, context)
            
        elif action_data == "list_approved":
            await self.list_approved_users(update, context)
            
        elif action_data == "remove_user":
            await self.handle_remove_user(update, context)
            
        elif action_data == "reset_user":
            await self.handle_reset_user(update, context)
            
        elif action_data == "search":
            await self.handle_search_user(update, context)
            
        elif action_data.startswith("approve_"):
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
    
    async def handle_admin_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج النصوص للأدمن (معرفات المستخدمين، البحث، إلخ)"""
        if not user_manager.is_admin(update.effective_user.id):
            return
        
        waiting_for = context.user_data.get('waiting_for')
        text = update.message.text.strip()
        
        if text == "/cancel":
            context.user_data.pop('waiting_for', None)
            await update.message.reply_text("❌ تم إلغاء العملية")
            return
        
        if waiting_for == 'remove_user_id':
            try:
                user_id = int(text)
                success, message = user_manager.remove_user(user_id)
                
                if success:
                    await update.message.reply_text(f"✅ {message}")
                    # إرسال إشعار للمستخدم المحذوف
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="🚫 تم إلغاء اشتراكك في البوت من قبل الإدارة.\n"
                                 "لن تتمكن من استخدام البوت بعد الآن."
                        )
                    except:
                        pass  # قد يكون المستخدم قد حظر البوت
                else:
                    await update.message.reply_text(f"❌ {message}")
                    
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً\nمثال: 123456789")
                return
            
            context.user_data.pop('waiting_for', None)
            
        elif waiting_for == 'reset_user_id':
            try:
                user_id = int(text)
                success, message = user_manager.reset_user(user_id)
                
                if success:
                    await update.message.reply_text(f"✅ {message}")
                else:
                    await update.message.reply_text(f"❌ {message}")
                    
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً\nمثال: 123456789")
                return
            
            context.user_data.pop('waiting_for', None)
            
        elif waiting_for == 'search_term':
            results = user_manager.search_user(text)
            
            if not results:
                await update.message.reply_text(f"🔍 لم يتم العثور على مستخدمين بالبحث: `{text}`", parse_mode="Markdown")
            else:
                message = f"🔍 *نتائج البحث عن:* `{text}`\n\n"
                
                for result in results[:10]:  # أول 10 نتائج
                    user_info = result["info"]
                    status_icon = {"معتمد": "✅", "انتظار": "⏳", "مرفوض": "❌"}.get(result["status"], "❓")
                    
                    message += f"{status_icon} *{user_info['first_name']}*\n"
                    message += f"   📱 @{user_info['username']}\n"
                    message += f"   🆔 `{result['user_id']}`\n"
                    message += f"   📊 الحالة: {result['status']}\n\n"
                
                if len(results) > 10:
                    message += f"... وجدت {len(results) - 10} نتيجة أخرى"
                
                await update.message.reply_text(message, parse_mode="Markdown")
            
            context.user_data.pop('waiting_for', None)

# إنشاء مثيل مشترك
admin_handlers = AdminHandlers()
