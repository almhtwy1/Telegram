# حالات الأدمن لتذكر آخر عملية
admin_states = {}

def set_admin_state(user_id, state, data=None):
    """تحديد حالة الأدمن"""
    admin_states[user_id] = {
        "state": state,
        "data": data
    }

def get_admin_state(user_id):
    """الحصول على حالة الأدمن"""
    return admin_states.get(user_id, {})

def clear_admin_state(user_id):
    """مسح حالة الأدمن"""
    admin_states.pop(user_id, None)
