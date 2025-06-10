from settings_manager import settings_manager
from config import logger

def filter_posts_by_category(posts):
    """تصفية المنشورات حسب الفئات المختارة"""
    if not posts:
        return []
    
    selected_categories = settings_manager.get_selected_categories()
    
    # إذا لم يتم تحديد فئات، إرجاع جميع المنشورات
    if len(selected_categories) == 0:
        logger.debug(f"🏷️ عرض جميع المنشورات ({len(posts)} منشور)")
        return posts
    
    # إذا تم تحديد "__none__"، لا تعرض أي منشور
    if "__none__" in selected_categories:
        logger.debug("🏷️ تم إيقاف جميع الفئات - لا توجد منشورات للعرض")
        return []
    
    # تصفية المنشورات حسب الفئات المختارة
    filtered_posts = []
    for post in posts:
        post_categories = post.get('categories', [])
        
        # فحص إذا كان هناك تطابق مع الفئات المختارة
        has_match = any(category in selected_categories for category in post_categories)
        
        if has_match:
            filtered_posts.append(post)
    
    logger.debug(f"🏷️ تصفية المنشورات: {len(filtered_posts)} من أصل {len(posts)} منشور")
    return filtered_posts
