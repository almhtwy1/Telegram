import json
import os
from config import ALLOWED_USER_ID, logger

def migrate_old_settings():
    """ترحيل الإعدادات من النظام القديم إلى الجديد"""
    settings_file = "bot_settings.json"
    
    if not os.path.exists(settings_file):
        logger.info("📁 لا توجد إعدادات قديمة للترحيل")
        return
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            old_settings = json.load(f)
        
        # فحص إذا كانت الإعدادات بالنظام القديم
        if "selected_categories" in old_settings and "user_categories" not in old_settings:
            logger.info("🔄 بدء ترحيل الإعدادات من النظام القديم...")
            
            # نقل الفئات القديمة للأدمن
            old_categories = old_settings.get("selected_categories", [])
            new_user_categories = {
                str(ALLOWED_USER_ID): old_categories
            }
            
            # إنشاء البنية الجديدة
            new_settings = {
                "monitoring_active": old_settings.get("monitoring_active", False),
                "last_sent_ids": old_settings.get("last_sent_ids", []),
                "user_categories": new_user_categories
            }
            
            # حفظ الإعدادات الجديدة
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, ensure_ascii=False, indent=2)
            
            # حذف المفتاح القديم (لن نحتاجه بعد الآن)
            logger.info(f"✅ تم ترحيل فئات الأدمن: {old_categories}")
            logger.info("✅ تم ترحيل الإعدادات بنجاح!")
            
        else:
            logger.info("ℹ️ الإعدادات محدثة بالفعل")
            
    except Exception as e:
        logger.error(f"❌ خطأ في ترحيل الإعدادات: {e}")

if __name__ == "__main__":
    # تشغيل الترحيل مباشرة
    migrate_old_settings()
