from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from categories import CATEGORIES
from settings_manager import settings_manager
from config import logger

class CategoryFilter:
    def __init__(self):
        self.callback_prefix = "cat_"
        self.current_user_id = None  # معرف المستخدم الحالي
    
    def set_current_user(self, user_id):
        """تحديد المستخدم الحالي"""
        self.current_user_id = user_id
    
    def create_category_keyboard(self):
        """إنشاء لوحة مفاتيح الفئات"""
        if self.current_user_id is None:
            return None
        
        selected_categories = settings_manager.get_selected_categories(self.current_user_id)
        keyboard = []
        
        # إضافة أزرار الفئات (صفين في كل صف)
        categories_list = [cat for cat in CATEGORIES.keys() if cat != "أخرى"]  # استثناء "أخرى"
        categories_list.append("أخرى")  # إضافة "أخرى" في النهاية
        
        for i in range(0, len(categories_list), 2):
            row = []
            for j in range(2):
                if i + j < len(categories_list):
                    category = categories_list[i + j]
                    icon = CATEGORIES[category]["icon"]
                    
                    # تحديد إذا كانت الفئة مختارة
                    if "__none__" in selected_categories:
                        status = ""  # لا شيء مختار
                    elif len(selected_categories) == 0:
                        status = "✅"  # كل الفئات مختارة
                    elif category in selected_categories:
                        status = "✅"
                    else:
                        status = ""
                    
                    button_text = f"{status} {icon} {category}"
                    callback_data = f"{self.callback_prefix}{category}"
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            
            keyboard.append(row)
        
        # إضافة أزرار التحكم
        control_buttons = [
            InlineKeyboardButton("🔄 تحديد الكل", callback_data=f"{self.callback_prefix}select_all"),
            InlineKeyboardButton("❌ إلغاء الكل", callback_data=f"{self.callback_prefix}clear_all")
        ]
        keyboard.append(control_buttons)
        
        # زر الحفظ والإغلاق
        keyboard.append([InlineKeyboardButton("✅ حفظ وإغلاق", callback_data=f"{self.callback_prefix}save")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_status_text(self):
        """نص حالة الفئات المختارة"""
        if self.current_user_id is None:
            return "❌ خطأ في تحديد المستخدم"
        
        selected = settings_manager.get_selected_categories(self.current_user_id)
        
        if len(selected) == 0:
            return "🏷️ *إعدادات الفئات الشخصية*\n\n📊 الحالة الحالية: جميع الفئات مفعلة\n\n👆 اختر الفئات التي تريد متابعتها:"
        elif "__none__" in selected:
            return "🏷️ *إعدادات الفئات الشخصية*\n\n📊 الحالة الحالية: لا توجد فئات مختارة\n\n👆 اختر الفئات التي تريد متابعتها:"
        else:
            categories_text = []
            for category in selected:
                if category in CATEGORIES:  # تأكد من أن الفئة موجودة
                    icon = CATEGORIES[category]["icon"]
                    categories_text.append(f"{icon} {category}")
            
            categories_str = " | ".join(categories_text)
            return f"🏷️ *إعدادات الفئات الشخصية*\n\n📊 فئاتك المختارة:\n{categories_str}\n\n👆 اختر الفئات التي تريد متابعتها:"
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج استدعاءات الفئات"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        if not callback_data.startswith(self.callback_prefix):
            return
        
        user_id = query.from_user.id
        self.set_current_user(user_id)
        
        action = callback_data[len(self.callback_prefix):]
        selected_categories = settings_manager.get_selected_categories(user_id).copy()
        
        if action == "select_all":
            # تحديد جميع الفئات (قائمة فارغة = كل الفئات)
            settings_manager.set_selected_categories([], user_id)
            logger.info(f"🏷️ المستخدم {user_id} حدد جميع الفئات")
            
        elif action == "clear_all":
            # إلغاء جميع الفئات (قائمة تحتوي على فئة وهمية)
            settings_manager.set_selected_categories(["__none__"], user_id)
            logger.info(f"🏷️ المستخدم {user_id} ألغى جميع الفئات")
            
        elif action == "save":
            # حفظ وإغلاق
            await query.edit_message_text("✅ تم حفظ إعداداتك الشخصية بنجاح!")
            return
            
        elif action in CATEGORIES:
            # تبديل حالة فئة معينة
            if "__none__" in selected_categories:
                # إذا كانت في وضع "لا شيء"، ابدأ بفئة واحدة جديدة
                selected_categories = [action]
            elif len(selected_categories) == 0:
                # إذا كانت كل الفئات مختارة، ابدأ بقائمة جديدة واختر هذه الفئة فقط
                selected_categories = [action]
            else:
                # إذا كانت الفئة مختارة، احذفها، وإلا أضفها
                if action in selected_categories:
                    selected_categories.remove(action)
                    # إذا أصبحت القائمة فارغة، اجعلها "__none__"
                    if not selected_categories:
                        selected_categories = ["__none__"]
                else:
                    selected_categories.append(action)
            
            settings_manager.set_selected_categories(selected_categories, user_id)
        
        # تحديث الرسالة
        try:
            await query.edit_message_text(
                self.get_status_text(),
                parse_mode="Markdown",
                reply_markup=self.create_category_keyboard()
            )
        except Exception as e:
            logger.error(f"خطأ في تحديث رسالة الفئات للمستخدم {user_id}: {e}")

# إنشاء مثيل مشترك
category_filter = CategoryFilter()
