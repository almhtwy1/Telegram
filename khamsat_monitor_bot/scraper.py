import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from categories import classify_post, CATEGORIES
from config import logger, MAX_POST_AGE_MINUTES

def is_recent_post(timestamp_str, max_minutes=MAX_POST_AGE_MINUTES):
    """فحص إذا كان المنشور حديث"""
    try:
        timestamp_str = timestamp_str.replace(" GMT", "").strip()
        post_time = datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        minutes_diff = (current_time - post_time).total_seconds() / 60
        return minutes_diff <= max_minutes
    except Exception as e:
        logger.debug(f"خطأ في تحليل الوقت: {e}")
        return False

def fetch_posts():
    """جلب المنشورات من خمسات"""
    try:
        logger.info("🔍 جاري جلب المنشورات...")
        
        response = requests.get(
            "https://khamsat.com/community/requests", 
            headers={"User-Agent": "Mozilla/5.0"}, 
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"❌ خطأ في الاستجابة: {response.status_code}")
            return [], []

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.select("tr.forum_post")
        recent_posts = []
        all_posts = []

        for post in posts[:10]:  # أول 10 مواضيع
            post_data = extract_post_data(post)
            if post_data:
                all_posts.append(post_data)
                
                # فحص إذا كان حديث
                if post_data['timestamp'] and is_recent_post(post_data['timestamp']):
                    recent_posts.append(post_data)
                    logger.info(f"✅ منشور حديث: {post_data['title'][:30]}...")

        logger.info(f"✅ {len(recent_posts)} منشور حديث من أصل {len(all_posts)}")
        return recent_posts, all_posts
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المنشورات: {e}")
        return [], []

def extract_post_data(post):
    """استخراج بيانات المنشور"""
    try:
        title_tag = post.select_one("h3.details-head a")
        if not title_tag:
            return None
            
        title = title_tag.get_text(strip=True)
        link = f"https://khamsat.com{title_tag['href']}"
        
        username = post.select_one("a.user")
        username = username.get_text(strip=True) if username else "غير معروف"
        
        # استخراج الوقت
        time_element = post.select_one("li.d-lg-inline-block span[dir='ltr']")
        if time_element:
            time_text = time_element.get_text(strip=True)
            timestamp = time_element.get('title', '')
        else:
            time_text = "منذ دقائق قليلة"
            timestamp = ""
        
        categories = classify_post(title)
        primary_category = categories[0] if categories else "أخرى"
        primary_icon = CATEGORIES[primary_category]["icon"]
        
        return {
            "id": post.get("id", ""),
            "title": title,
            "link": link,
            "username": username,
            "time_text": time_text,
            "timestamp": timestamp,
            "categories": categories,
            "primary_category": primary_category,
            "primary_icon": primary_icon
        }
    except Exception as e:
        logger.error(f"خطأ في استخراج بيانات المنشور: {e}")
        return None
