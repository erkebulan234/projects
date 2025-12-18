# db/categories.py

from .connection import get_db_conn
from .users import get_current_user_id

def db_get_category_stats(username):
    """Получает статистику по категориям (количество транзакций)"""
    user_id = get_current_user_id(username)
    if not user_id:
        return {}
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # ✅ ИСПРАВЛЕНИЕ: Используем user_id (%s) для фильтрации транзакций и категорий
                cur.execute("""
                SELECT c.category_name, COUNT(t.transaction_id) as count
                FROM categories c
                LEFT JOIN transactions t ON c.category_id = t.category_id AND t.user_id = %s
                WHERE c.user_id = %s
                GROUP BY c.category_name
                ORDER BY c.category_name
                """, (user_id, user_id)) # Передаем user_id дважды
                result = {}
                for row in cur.fetchall():
                    result[row[0]] = row[1]
                return result
    except Exception as e:
        print("DB category stats error:", e)
        return {}
    
def db_get_user_categories(user_id):
    """Возвращает все категории пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT category_name FROM categories 
                    WHERE user_id = %s 
                    ORDER BY category_name
                """, (user_id,))
                categories = cur.fetchall()
                return [cat[0] for cat in categories] if categories else []
    except Exception as e:
        print(f"Ошибка при получении категорий пользователя: {e}")
        return []