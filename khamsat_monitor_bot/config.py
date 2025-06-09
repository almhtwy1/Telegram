import os
import logging
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = 267112556

# إعدادات المراقبة
MONITORING_INTERVAL = 30  # ثانية
MAX_POST_AGE_MINUTES = 3  # دقائق

# إعداد التسجيل
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(), 
            logging.FileHandler('khamsat_bot.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
