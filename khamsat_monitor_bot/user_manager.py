import json
import os
from config import ALLOWED_USER_ID, logger

class UserManager:
    def __init__(self, users_file="bot_users.json"):
        self.users_file = users_file
        self.admin_id = ALLOWED_USER_ID
        self.default_data = {
            "approved_users": [ALLOWED_USER_ID],  # الأدمن معتمد افتراضياً
            "pending_users": {},  # {user_id: {"username": "", "first_name": "", "timestamp": ""}}
            "rejected_users": []
        }
        self.users_data = self.load_users()
    
    def load_users(self):
        """تحميل بيانات المستخدمين"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"✅ تم تحميل بيانات المستخدمين: {len(data.get('approved_users', []))} معتمد")
                return data
            else:
                logger.info("📁 إنشاء ملف مستخدمين جديد")
                return self.default_data.copy()
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل بيانات المستخدمين: {e}")
            return self.default_data.copy()
    
    def save_users(self):
        """حفظ بيانات المستخدمين"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, ensure_ascii=False, indent=2)
            logger.debug("💾 تم حفظ بيانات المستخدمين")
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ بيانات المستخدمين: {e}")
    
    def is_admin(self, user_id):
        """فحص إذا كان المستخدم أدمن"""
        return user_id == self.admin_id
    
    def is_approved(self, user_id):
        """فحص إذا كان المستخدم معتمد"""
        return user_id in self.users_data.get("approved_users", [])
    
    def is_pending(self, user_id):
        """فحص إذا كان المستخدم في انتظار الموافقة"""
        return str(user_id) in self.users_data.get("pending_users", {})
    
    def is_rejected(self, user_id):
        """فحص إذا كان المستخدم مرفوض"""
        return user_id in self.users_data.get("rejected_users", [])
    
    def add_pending_user(self, user_id, username, first_name):
        """إضافة مستخدم للانتظار"""
        from datetime import datetime
        
        if self.is_approved(user_id) or self.is_pending(user_id):
            return False
        
        # إزالة من قائمة المرفوضين إذا كان موجود
        if user_id in self.users_data.get("rejected_users", []):
            self.users_data["rejected_users"].remove(user_id)
        
        self.users_data["pending_users"][str(user_id)] = {
            "username": username or "غير محدد",
            "first_name": first_name or "غير محدد",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_users()
        logger.info(f"⏳ تم إضافة مستخدم للانتظار: {first_name} (@{username})")
        return True
    
    def approve_user(self, user_id):
        """الموافقة على مستخدم"""
        user_id_str = str(user_id)
        if user_id_str in self.users_data.get("pending_users", {}):
            user_info = self.users_data["pending_users"][user_id_str]
            
            # نقل المستخدم إلى قائمة المعتمدين
            if user_id not in self.users_data["approved_users"]:
                self.users_data["approved_users"].append(user_id)
            
            # حذف من قائمة الانتظار
            del self.users_data["pending_users"][user_id_str]
            
            self.save_users()
            logger.info(f"✅ تم اعتماد المستخدم: {user_info['first_name']}")
            return user_info
        return None
    
    def reject_user(self, user_id):
        """رفض مستخدم"""
        user_id_str = str(user_id)
        if user_id_str in self.users_data.get("pending_users", {}):
            user_info = self.users_data["pending_users"][user_id_str]
            
            # نقل المستخدم إلى قائمة المرفوضين
            if user_id not in self.users_data["rejected_users"]:
                self.users_data["rejected_users"].append(user_id)
            
            # حذف من قائمة الانتظار
            del self.users_data["pending_users"][user_id_str]
            
            self.save_users()
            logger.info(f"❌ تم رفض المستخدم: {user_info['first_name']}")
            return user_info
        return None
    
    def get_pending_users(self):
        """الحصول على قائمة المستخدمين في الانتظار"""
        return self.users_data.get("pending_users", {})
    
    def get_approved_users(self):
        """الحصول على قائمة المستخدمين المعتمدين"""
        return self.users_data.get("approved_users", [])
    
    def remove_user(self, user_id):
        """حذف مستخدم معتمد"""
        if user_id == self.admin_id:
            return False, "لا يمكن حذف الأدمن"
        
        if user_id in self.users_data.get("approved_users", []):
            self.users_data["approved_users"].remove(user_id)
            
            # إضافة للمرفوضين لمنع العودة
            if user_id not in self.users_data.get("rejected_users", []):
                self.users_data["rejected_users"].append(user_id)
            
            self.save_users()
            logger.info(f"🗑️ تم حذف المستخدم {user_id}")
            return True, "تم حذف المستخدم بنجاح"
        
        return False, "المستخدم غير موجود في قائمة المعتمدين"
    
    def search_user(self, search_term):
        """البحث عن مستخدم بالاسم أو المعرف"""
        results = []
        
        # البحث في المستخدمين المعتمدين
        for user_id in self.users_data.get("approved_users", []):
            # محاولة العثور على معلومات المستخدم من الطلبات السابقة
            user_info = self._find_user_info(user_id)
            if user_info and self._matches_search(user_info, search_term):
                results.append({
                    "user_id": user_id,
                    "status": "معتمد",
                    "info": user_info
                })
        
        # البحث في طلبات الانتظار
        for user_id_str, info in self.users_data.get("pending_users", {}).items():
            if self._matches_search(info, search_term):
                results.append({
                    "user_id": int(user_id_str),
                    "status": "انتظار",
                    "info": info
                })
        
        return results
    
    def _find_user_info(self, user_id):
        """البحث عن معلومات المستخدم في السجلات"""
        # البحث في طلبات الانتظار الحالية
        user_id_str = str(user_id)
        if user_id_str in self.users_data.get("pending_users", {}):
            return self.users_data["pending_users"][user_id_str]
        
        # إذا كان الأدمن
        if user_id == self.admin_id:
            return {
                "first_name": "الأدمن",
                "username": "admin",
                "timestamp": "منذ البداية"
            }
        
        return None
    
    def _matches_search(self, user_info, search_term):
        """فحص إذا كانت معلومات المستخدم تطابق البحث"""
        search_term = search_term.lower()
        first_name = user_info.get("first_name", "").lower()
        username = user_info.get("username", "").lower()
        
        return search_term in first_name or search_term in username
    
    def get_user_details(self, user_id):
        """الحصول على تفاصيل مستخدم محدد"""
        user_info = self._find_user_info(user_id)
        
        if user_id in self.users_data.get("approved_users", []):
            status = "معتمد"
        elif str(user_id) in self.users_data.get("pending_users", {}):
            status = "انتظار"
        elif user_id in self.users_data.get("rejected_users", []):
            status = "مرفوض"
        else:
            status = "غير موجود"
        
        return {
            "user_id": user_id,
            "status": status,
            "info": user_info or {"first_name": "غير متوفر", "username": "غير متوفر"}
        }
    
    def reset_user(self, user_id):
        """إعادة تعيين حالة المستخدم (السماح له بالتقديم مرة أخرى)"""
        if user_id == self.admin_id:
            return False, "لا يمكن إعادة تعيين الأدمن"
        
        changed = False
        
        # حذف من المعتمدين
        if user_id in self.users_data.get("approved_users", []):
            self.users_data["approved_users"].remove(user_id)
            changed = True
        
        # حذف من المرفوضين
        if user_id in self.users_data.get("rejected_users", []):
            self.users_data["rejected_users"].remove(user_id)
            changed = True
        
        # حذف من الانتظار
        user_id_str = str(user_id)
        if user_id_str in self.users_data.get("pending_users", {}):
            del self.users_data["pending_users"][user_id_str]
            changed = True
        
        if changed:
            self.save_users()
            logger.info(f"🔄 تم إعادة تعيين المستخدم {user_id}")
            return True, "تم إعادة تعيين المستخدم - يمكنه التقديم مرة أخرى"
        
        return False, "المستخدم غير موجود في أي قائمة"
    
    def get_user_details(self, user_id):
        """الحصول على تفاصيل مستخدم محدد"""
        user_info = self._find_user_info(user_id)
        
        if user_id in self.users_data.get("approved_users", []):
            status = "معتمد"
        elif str(user_id) in self.users_data.get("pending_users", {}):
            status = "انتظار"
        elif user_id in self.users_data.get("rejected_users", []):
            status = "مرفوض"
        else:
            status = "غير موجود"
        
        return {
            "user_id": user_id,
            "status": status,
            "info": user_info or {"first_name": "غير متوفر", "username": "غير متوفر"}
        }
    
    def get_stats(self):
        """إحصائيات المستخدمين"""
        return {
            "approved": len(self.users_data.get("approved_users", [])),
            "pending": len(self.users_data.get("pending_users", {})),
            "rejected": len(self.users_data.get("rejected_users", []))
        }

# إنشاء مثيل مشترك
user_manager = UserManager()
