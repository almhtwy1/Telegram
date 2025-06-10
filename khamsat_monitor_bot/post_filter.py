from settings_manager import settings_manager
from config import logger

def filter_posts_by_category(posts, user_id=None):
    """تصفية المنشورات حسب الفئات المختارة لمستخدم محدد"""
    if not posts or user_id is None:
        return []
    
    selected_categories = settings_manager.get_selected_categories(user_id)
    
    # إذا لم يتم تحديد فئات، إرجاع جميع المنشورات
    if len(selected_categories) == 0:
        logger.debug(f"🏷️ المستخدم {user_id}: عرض جميع المنشورات ({len(posts)} منشور)")
        return posts
    
    # إذا تم تحديد "__none__"، لا تعرض أي منشور
    if "__none__" in selected_categories:
        logger.debug(f"🏷️ المستخدم {user_id}: تم إيقاف جميع الفئات - لا توجد منشورات للعرض")
        return []
    
    # تصفية المنشورات حسب الفئات المختارة
    filtered_posts = []
    for post in posts:
        post_categories = post.get('categories', [])
        
        # فحص إذا كان هناك تطابق مع الفئات المختارة
        has_match = any(category in selected_categories for category in post_categories)
        
        if has_match:
            filtered_posts.append(post)
    
    logger.debug(f"🏷️ المستخدم {user_id}: تصفية المنشورات: {len(filtered_posts)} من أصل {len(posts)} منشور")
    return filtered_posts
