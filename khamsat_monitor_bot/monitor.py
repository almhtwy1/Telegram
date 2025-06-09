import asyncio
from config import ALLOWED_USER_ID, MONITORING_INTERVAL, logger
from scraper import fetch_posts
from formatter import format_new_posts_alert
from handlers import is_monitoring_active
from settings_manager import settings_manager
from post_filter import filter_posts_by_category

class PostMonitor:
    def __init__(self):
        # تحميل المعرفات المحفوظة من الإعدادات
        self.last_sent_ids = settings_manager.get_sent_ids()
    
    async def monitor_loop(self, application):
        """حلقة المراقبة التلقائية"""
        logger.info("🔄 بدء المراقبة التلقائية")
        
        while True:
            try:
                if is_monitoring_active():
                    await self._check_new_posts(application)
                
                await asyncio.sleep(MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ خطأ في المراقبة: {e}")
                await asyncio.sleep(15)
    
    async def _check_new_posts(self, application):
        """فحص المنشورات الجديدة"""
        recent_posts, _ = fetch_posts()
        new_posts = [p for p in recent_posts if p["id"] not in self.last_sent_ids]
        
        # تطبيق تصفية الفئات على المنشورات الجديدة
        filtered_new_posts = filter_posts_by_category(new_posts)
        
        if filtered_new_posts:
            logger.info(f"📢 {len(filtered_new_posts)} منشور جديد (بعد التصفية)")
            message = format_new_posts_alert(filtered_new_posts)
            
            if message:
                await application.bot.send_message(
                    chat_id=ALLOWED_USER_ID,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                
                # حفظ معرفات جميع المنشورات الجديدة (حتى المفلترة) لتجنب إعادة الإرسال
                for post in new_posts:
                    self.last_sent_ids.add(post["id"])
                    settings_manager.add_sent_id(post["id"])
                
                logger.info(f"✅ تم إرسال {len(filtered_new_posts)} منشور")
        else:
            # حفظ المعرفات حتى لو لم يتم إرسال شيء
            for post in new_posts:
                self.last_sent_ids.add(post["id"])
                settings_manager.add_sent_id(post["id"])
            
            if new_posts:
                logger.info(f"ℹ️ {len(new_posts)} منشور جديد لكن لا يطابق فئات أي مستخدم")
            else:
                logger.info("ℹ️ لا توجد منشورات جديدة")
