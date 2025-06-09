from categories import CATEGORIES

def format_post(post, index=None):
    """تنسيق المنشور للعرض"""
    categories = post['categories']
    primary_category = categories[0] if categories else "أخرى"
    primary_icon = CATEGORIES[primary_category]["icon"]
    
    # تنسيق التصنيفات
    if len(categories) > 1:
        categories_with_icons = []
        for category in categories:
            icon = CATEGORIES[category]["icon"]
            categories_with_icons.append(f"{icon} {category}")
        
        categories_text = " | ".join(categories_with_icons)
        prefix = f"*{categories_text} {index}*\n" if index else f"*{categories_text}:*\n"
    else:
        prefix = f"{primary_icon} *{primary_category} {index}*\n" if index else f"{primary_icon} *{primary_category}:*\n"
    
    return (
        f"{prefix}"
        f"*العنوان:* [{post['title']}]({post['link']})\n"
        f"*الناشر:* {post['username']}\n"
        f"*تاريخ النشر:* {post['time_text']}\n"
        f"{'-'*40}"
    )

def format_posts_list(posts, show_index=True):
    """تنسيق قائمة المنشورات"""
    if not posts:
        return "⚠️ لا توجد مواضيع متاحة"
    
    if show_index:
        return "\n\n".join(format_post(p, i+1) for i, p in enumerate(posts))
    else:
        return "\n\n".join(format_post(p) for p in posts)

def format_new_posts_alert(posts):
    """تنسيق تنبيه المنشورات الجديدة"""
    if not posts:
        return None
    
    message = format_posts_list(reversed(posts), show_index=False)
    return f"🔔 *مواضيع جديدة:*\n\n{message}"
