from .connection import get_db_conn
from .users import get_current_user_id

def db_get_expenses_summary(username, period_days=30):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return {"total_expenses": 0, "top_categories": []}
        
        user_id = user_result[0]
        cursor.execute(, (user_id, period_days))
        
        expenses_by_category = cursor.fetchall()
        total_expenses = 0
        top_categories = []
        
        for category_name, amount in expenses_by_category:
            if amount and amount > 0:
                total_expenses += float(amount)
                top_categories.append((category_name, float(amount)))
        result_categories = []
        for category_name, amount in top_categories:
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            result_categories.append((category_name, amount, float(percentage)))
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
                cur.execute(, (user_id,))
                
                total_income, total_expense = cur.fetchone()
                balance = total_income - total_expense
                cur.execute(, (user_id, user_id))
                
                expense_stats = cur.fetchall()
                cur.execute(, (user_id, user_id))
                
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

def db_get_income_summary(username, period_days=30):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return {"total_income": 0, "top_categories": []}
        
        user_id = user_result[0]
        cursor.execute(, (user_id, period_days))
        
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
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return []
        
        user_id = user_result[0]
        cursor.execute(, (user_id, start_date, end_date))
        
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
    
    user_id = get_current_user_id(username)
    
    if not user_id:
        return {}
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (user_id, user_id))
                
                rows = cur.fetchall()
                
                result = {}
                for row in rows:
                    result[row[0]] = row[1]
                
                return result
    except Exception as e:
        print(f"❌ DB category stats error: {e}")
        return {}