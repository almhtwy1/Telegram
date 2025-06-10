import json
import os
from config import logger

class SettingsManager:
    def __init__(self, settings_file="bot_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "monitoring_active": False,
            "last_sent_ids": [],
            "user_categories": {}  # {user_id: [selected_categories]}
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"✅ تم تحميل الإعدادات: مراقبة={'مفعلة' if settings.get('monitoring_active') else 'معطلة'}")
                return settings
            else:
                logger.info("📁 إنشاء ملف إعدادات جديد")
                return self.default_settings.copy()
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """حفظ الإعدادات في الملف"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.debug("💾 تم حفظ الإعدادات")
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
    
    def set_monitoring_active(self, active):
        """تعديل حالة المراقبة"""
        self.settings["monitoring_active"] = active
        self.save_settings()
        logger.info(f"🔄 تم تعديل حالة المراقبة: {'مفعلة' if active else 'معطلة'}")
    
    def is_monitoring_active(self):
        """فحص حالة المراقبة"""
        return self.settings.get("monitoring_active", False)
    
    def add_sent_id(self, post_id):
        """إضافة معرف منشور مرسل"""
        if post_id not in self.settings["last_sent_ids"]:
            self.settings["last_sent_ids"].append(post_id)
            # الاحتفاظ بآخر 100 معرف فقط لتوفير المساحة
            if len(self.settings["last_sent_ids"]) > 100:
                self.settings["last_sent_ids"] = self.settings["last_sent_ids"][-100:]
            self.save_settings()
    
    def get_sent_ids(self):
        """الحصول على معرفات المنشورات المرسلة"""
        return set(self.settings.get("last_sent_ids", []))
    
    def clear_sent_ids(self):
        """مسح معرفات المنشورات المرسلة"""
        self.settings["last_sent_ids"] = []
        self.save_settings()
        logger.info("🗑️ تم مسح معرفات المنشورات المرسلة")
    
    def set_selected_categories(self, categories, user_id=None):
        """تحديد الفئات المختارة لمستخدم محدد"""
        if user_id is None:
            logger.warning("⚠️ لم يتم تحديد معرف المستخدم")
            return
        
        user_id_str = str(user_id)
        if "user_categories" not in self.settings:
            self.settings["user_categories"] = {}
        
        self.settings["user_categories"][user_id_str] = categories
        self.save_settings()
        
        if categories and "__none__" not in categories:
            logger.info(f"🏷️ تم تحديد الفئات للمستخدم {user_id}: {', '.join(categories)}")
        elif "__none__" in categories:
            logger.info(f"🏷️ تم إلغاء جميع الفئات للمستخدم {user_id}")
        else:
            logger.info(f"🏷️ تم تحديد جميع الفئات للمستخدم {user_id}")
    
    def get_selected_categories(self, user_id=None):
        """الحصول على الفئات المختارة لمستخدم محدد"""
        if user_id is None:
            return []
        
        user_id_str = str(user_id)
        user_categories = self.settings.get("user_categories", {})
        return user_categories.get(user_id_str, [])  # فارغة = كل الفئات
    
    def is_category_selected(self, category, user_id=None):
        """فحص إذا كانت الفئة مختارة لمستخدم محدد"""
        if user_id is None:
            return True
        
        selected = self.get_selected_categories(user_id)
        return len(selected) == 0 or category in selected  # فارغة = كل الفئات

# إنشاء مثيل مشترك للاستخدام في باقي الملفات
settings_manager = SettingsManager()
