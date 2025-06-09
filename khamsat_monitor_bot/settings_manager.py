import json
import os
from config import logger

class SettingsManager:
    def __init__(self, settings_file="bot_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "monitoring_active": False,
            "last_sent_ids": []
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

# إنشاء مثيل مشترك للاستخدام في باقي الملفات
settings_manager = SettingsManager()
