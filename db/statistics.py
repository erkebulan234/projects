from .connection import get_db_conn
from .users import get_current_user_id

def db_get_expenses_summary(username, period_days=30):
    """Получает сводку по расходам за период"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Получаем user_id
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return {"total_expenses": 0, "top_categories": []}
        
        user_id = user_result[0]
        
        # Исправленный SQL-запрос
        cursor.execute("""
            SELECT 
                c.category_name,
                COALESCE(SUM(ABS(t.amount)), 0) as total
            FROM categories c
            LEFT JOIN transactions t ON c.category_id = t.category_id
            WHERE t.user_id = %s 
            AND t.transaction_type = 'expense'
            AND t.transaction_date >= NOW() - INTERVAL '%s days'
            GROUP BY c.category_id, c.category_name
            ORDER BY total DESC
        """, (user_id, period_days))
        
        expenses_by_category = cursor.fetchall()
        
        # Рассчитываем общую сумму и проценты
        total_expenses = 0
        top_categories = []
        
        for category_name, amount in expenses_by_category:
            if amount and amount > 0:
                total_expenses += float(amount)
                top_categories.append((category_name, float(amount)))
        
        # Рассчитываем проценты и сортируем
        result_categories = []
        for category_name, amount in top_categories:
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            result_categories.append((category_name, amount, float(percentage)))
        
        # Сортируем по убыванию суммы
        result_categories.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "total_expenses": float(total_expenses),
            "top_categories": result_categories
        }
        
    except Exception as e:
        print(f"DB expenses summary error: {e}")
        return {"total_expenses": 0, "top_categories": []}
    finally:
        if conn:
            conn.close()

def db_get_statistics(username):
    """Получает статистику по транзакциям пользователя (версия с таблицей categories)"""
    user_id = get_current_user_id(username)
    
    if not user_id:
        return {
            "total_income": 0, 
            "total_expense": 0, 
            "balance": 0, 
            "expense_stats": [], 
            "income_stats": []
        }
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Общие суммы
                cur.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END), 0) as total_income,
                        COALESCE(SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END), 0) as total_expense
                    FROM transactions t
                    WHERE t.user_id = %s
                """, (user_id,))
                
                total_income, total_expense = cur.fetchone()
                balance = total_income - total_expense
                
                # Статистика по категориям расходов
                cur.execute("""
                    SELECT c.category_name, COALESCE(SUM(t.amount), 0) as total
                    FROM categories c
                    LEFT JOIN transactions t ON c.category_id = t.category_id 
                        AND t.transaction_type = 'expense' 
                        AND t.user_id = %s
                    WHERE c.user_id = %s
                    GROUP BY c.category_name
                    ORDER BY total DESC
                """, (user_id, user_id))
                
                expense_stats = cur.fetchall()
                
                # Статистика по категориям доходов
                cur.execute("""
                    SELECT c.category_name, COALESCE(SUM(t.amount), 0) as total
                    FROM categories c
                    LEFT JOIN transactions t ON c.category_id = t.category_id 
                        AND t.transaction_type = 'income' 
                        AND t.user_id = %s
                    WHERE c.user_id = %s
                    GROUP BY c.category_name
                    ORDER BY total DESC
                """, (user_id, user_id))
                
                income_stats = cur.fetchall()
                
                return {
                    "total_income": float(total_income),
                    "total_expense": float(total_expense),
                    "balance": float(balance),
                    "expense_stats": expense_stats,
                    "income_stats": income_stats
                }
                
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {
            "total_income": 0, 
            "total_expense": 0, 
            "balance": 0, 
            "expense_stats": [], 
            "income_stats": []
        }

# Добавьте эти функции в db/statistics.py

def db_get_income_summary(username, period_days=30):
    """Получает сводку по доходам за период"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Получаем user_id
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return {"total_income": 0, "top_categories": []}
        
        user_id = user_result[0]
        
        # Получаем доходы по категориям
        cursor.execute("""
            SELECT 
                c.category_name,
                COALESCE(SUM(t.amount), 0) as total
            FROM categories c
            LEFT JOIN transactions t ON c.category_id = t.category_id
            WHERE t.user_id = %s 
            AND t.amount > 0  
            AND t.transaction_date >= NOW() - INTERVAL '%s days'
            GROUP BY c.category_id, c.category_name
            HAVING COALESCE(SUM(t.amount), 0) > 0
            ORDER BY total DESC
        """, (user_id, period_days))
        
        income_by_category = cursor.fetchall()
        
        total_income = sum(float(row[1]) for row in income_by_category if row[1] is not None)
        
        top_categories = []
        for category_name, amount in income_by_category:
            if amount is not None and amount > 0:
                percentage = (float(amount) / total_income * 100) if total_income > 0 else 0
                top_categories.append((category_name, float(amount), float(percentage)))
        
        return {
            "total_income": float(total_income),
            "top_categories": top_categories
        }
        
    except Exception as e:
        print(f"Error getting income summary: {e}")
        return {"total_income": 0, "top_categories": []}
    finally:
        if conn:
            conn.close()

def db_get_transactions_period(username, start_date, end_date):
    """Получает транзакции за указанный период"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Получаем user_id
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return []
        
        user_id = user_result[0]
        
        # Получаем транзакции с названиями категорий
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.amount,
                c.category_name,
                t.description,
                t.transaction_date
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s 
            AND t.transaction_date BETWEEN %s AND %s
            ORDER BY t.transaction_date DESC
        """, (user_id, start_date, end_date))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'amount': float(row[1]) if row[1] is not None else 0.0,
                'category': row[2] if row[2] else "Без категории",
                'description': row[3] if row[3] else "Без описания",
                'date': row[4]
            })
        
        return transactions
        
    except Exception as e:
        print(f"Error getting transactions for period: {e}")
        return []
    finally:
        if conn:
            conn.close()

def db_get_category_stats(username):
    """Получает количество транзакций по категориям (версия с таблицей categories)"""
    user_id = get_current_user_id(username)
    
    if not user_id:
        return {}
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.category_name, COUNT(t.transaction_id) as count
                    FROM categories c
                    LEFT JOIN transactions t ON c.category_id = t.category_id 
                        AND t.user_id = %s
                    WHERE c.user_id = %s
                    GROUP BY c.category_name
                """, (user_id, user_id))
                
                rows = cur.fetchall()
                
                result = {}
                for row in rows:
                    result[row[0]] = row[1]
                
                return result
    except Exception as e:
        print(f"❌ DB category stats error: {e}")
        return {}