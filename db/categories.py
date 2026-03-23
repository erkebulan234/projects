
from .connection import get_db_conn
from .users import get_current_user_id

def db_get_category_stats(username):
    
    user_id = get_current_user_id(username)
    if not user_id:
        return {}
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (user_id, user_id))
        print("DB category stats error:", e)
        return {}
    
def db_get_user_categories(user_id):
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (user_id,))
                categories = cur.fetchall()
                return [cat[0] for cat in categories] if categories else []
    except Exception as e:
        print(f"Ошибка при получении категорий пользователя: {e}")
        return []