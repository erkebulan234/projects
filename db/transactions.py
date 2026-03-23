from datetime import datetime
from .users import get_current_user_id
from .connection import get_db_conn

def db_fetch_user_transactions(username):
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (username,))
                transactions = cur.fetchall()
                return [{
                    "id": t[0],
                    "user_id": t[1],
                    "category": t[2],
                    "amount": float(t[3]),
                    "description": t[4] or "",
                    "type": t[5],
                    "date": t[6].strftime("%d.%m.%Y %H:%M") if t[6] else ""
                } for t in transactions]
    except Exception as e:
        print(f"Ошибка при получении транзакций пользователя: {e}")
        return []


def db_fetch_all_transactions_for_admin():
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute()
                transactions = cur.fetchall()
                return [{
                    "id": t[0],
                    "user_id": t[1],
                    "username": t[2],
                    "category": t[3] if t[3] else "Без категории",
                    "amount": float(t[4]),
                    "description": t[5] or "",
                    "type": t[6],
                    "date": t[7].strftime("%d.%m.%Y %H:%M") if t[7] else ""
                } for t in transactions]
    except Exception as e:
        print(f"Ошибка при получении всех транзакций: {e}")
        return []

def db_insert_transaction(transaction, user_id):
    
    if not user_id:
        print("db_insert_transaction error: user_id is missing")
        return None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (user_id,))
                account_row = cur.fetchone()
                if not account_row:
                    print(f"Аккаунт 'Основной счет' для user_id {user_id} не найден. Создаю...")
                    cur.execute(, (user_id,))
                    account_id = cur.fetchone()[0]
                else:
                    account_id = account_row[0]
                
                cur.execute(, (transaction['category'], user_id))
                cat_row = cur.fetchone()
                
                if not cat_row:
                    category_type = 'expense' if transaction['type'] == 'expense' else 'income'
                    cur.execute(, (transaction['category'], category_type, user_id))
                    category_id = cur.fetchone()[0]
                else:
                    category_id = cat_row[0]
                
                transaction_date = datetime.strptime(transaction['date'], "%d.%m.%Y %H:%M")
                
                cur.execute(, (user_id, account_id, category_id, 
                      float(transaction['amount']), transaction['type'], 
                      transaction['description'], transaction_date))
                
                tid = cur.fetchone()[0]
                
                if transaction['type'] == 'income':
                    cur.execute(, (float(transaction['amount']), account_id))
                else:
                    cur.execute(, (float(transaction['amount']), account_id))
                
                conn.commit()
                return tid
    except Exception as e:
        print("DB insert error:", e)
        return None



def db_fetch_all_transactions(username):
    
    user_id = get_current_user_id(username)
    if not user_id:
        return []
    try:
        with get_db_conn() as conn:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(, (user_id,))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    result.append({
                        "id": r["id"],
                        "amount": r["amount"],
                        "description": r["description"] or "",
                        "category": r["category"] or "Другое",
                        "type": r["type"],
                        "date": r["date"]
                    })
                return result
    except Exception as e:
        print("DB fetch error:", e)
        return []

def update_transaction(transaction_id, amount=None, description=None, category=None, type_=None, user_id=None):
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                if user_id is None:
                    cur.execute(, (transaction_id,))
                    result = cur.fetchone()
                    if result:
                        user_id = result[0]
                    else:
                        return False
                category_id = None
                if category is not None:
                    cur.execute(, (category, user_id))
                    category_result = cur.fetchone()
                    
                    if category_result:
                        category_id = category_result[0]
                    else:
                        category_type = type_ if type_ else 'expense'
                        cur.execute(, (category, category_type, user_id))
                        category_result = cur.fetchone()
                        if category_result:
                            category_id = category_result[0]
                        else:
                            print(f"❌ Не удалось создать категорию '{category}'")
                            return False
                updates = []
                params = []
                
                if amount is not None:
                    updates.append("amount = %s")
                    params.append(float(amount))
                
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                
                if type_ is not None:
                    updates.append("transaction_type = %s")
                    params.append(type_)
                
                if category_id is not None:
                    updates.append("category_id = %s")
                    params.append(category_id)
                if updates:
                    query = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = %s AND user_id = %s"
                    params.extend([transaction_id, user_id])
                    
                    cur.execute(query, tuple(params))
                    conn.commit()
                    
                    if cur.rowcount > 0:
                        return True
                    else:
                        print(f"❌ Не удалось обновить транзакцию {transaction_id}")
                        return False
                
                print(f"⚠️ Нет полей для обновления транзакции {transaction_id}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при обновлении транзакции: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_update_transaction(transaction_id, **kwargs):
    
    print(f"\n=== DEBUG: Обновление транзакции {transaction_id} ===")
    print(f"Переданные параметры: {kwargs}")
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (transaction_id,))
                current = cur.fetchone()
                print(f"Текущее состояние: {current}")
                if 'category' in kwargs and kwargs.get('category'):
                    cur.execute(, (kwargs['category'], kwargs.get('user_id') or (current[1] if current else None)))
                    cat_result = cur.fetchone()
                    print(f"Найдена категория: {cat_result}")
                return update_transaction(transaction_id, **kwargs)
                
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_user_transaction(transaction_id, username=None, user_id=None):
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                if username and not user_id:
                    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                    user_row = cur.fetchone()
                    if user_row:
                        user_id = user_row[0]
                if user_id:
                    cur.execute(, (transaction_id, user_id))
                else:
                    cur.execute(, (transaction_id,))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False, "Транзакция не найдена"
                
                trans_user_id, account_id, amount, trans_type, current_balance = transaction_info
                if user_id and trans_user_id != user_id:
                    return False, "Нет прав на удаление этой транзакции"
                
                print(f"🗑️ Удаление транзакции {transaction_id}:")
                print(f"   Пользователь: {trans_user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                if trans_type == 'income':
                    new_balance = current_balance - amount
                    cur.execute(, (amount, account_id))
                else:
                    cur.execute(, (amount, account_id))
                cur.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
                
                conn.commit()
                
                print(f"   Новый баланс счета {account_id}: {new_balance}")
                return True, "Транзакция удалена"
                
    except Exception as e:
        print(f"❌ Ошибка при удалении транзакции {transaction_id}: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Ошибка: {str(e)}"

def delete_transaction(transaction_id):
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (transaction_id,))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False
                
                user_id, account_id, amount, trans_type, current_balance = transaction_info
                
                print(f"🗑️ Удаление транзакции {transaction_id}:")
                print(f"   Пользователь: {user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                if trans_type == 'income':
                    new_balance = current_balance - amount
                    cur.execute(, (amount, account_id))
                else:
                    cur.execute(, (amount, account_id))
                cur.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
                cur.execute(, (transaction_id, amount, trans_type, current_balance, new_balance, user_id))
                
                conn.commit()
                
                print(f"   Новый баланс счета {account_id}: {new_balance}")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка при удалении транзакции {transaction_id}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def db_delete_transaction(transaction_id, username):
    
    user_id = get_current_user_id(username)
    if not user_id:
        print(f"❌ Пользователь {username} не найден")
        return False
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(, (transaction_id, user_id))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False
                
                trans_user_id, account_id, amount, trans_type, current_balance = transaction_info
                
                print(f"🗑️ Удаление транзакции {transaction_id} для пользователя {username}:")
                print(f"   Пользователь: {trans_user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                if trans_type == 'income':
                    new_balance = float(current_balance) - float(amount)
                    cur.execute(, (amount, account_id, user_id))
                else:
                    cur.execute(, (amount, account_id, user_id))
                cur.execute(, (transaction_id, user_id))
                cur.execute(, (transaction_id, amount, trans_type, current_balance, new_balance, user_id))
                
                conn.commit()

                return True
                
    except Exception as e:
        print(f"❌ Ошибка при удалении транзакции {transaction_id}: {e}")
        import traceback
        traceback.print_exc()
        return False    

def db_fetch_transactions_by_category(category, username):
    
    user_id = get_current_user_id(username)
    if not user_id:
        return []
    try:
        with get_db_conn() as conn:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(, (category, user_id))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    result.append({
                        "id": r["id"],
                        "amount": f"{float(r['amount']):.2f}",
                        "description": r["description"] or "",
                        "category": r["category"] or "Другое",
                        "type": r["type"],
                        "date": r["date"]
                    })
                return result
    except Exception as e:
        print("DB fetch by category error:", e)
        return []

def db_clear_all_transactions(username):
    
    user_id = get_current_user_id(username)
    if not user_id:
        return False
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM transactions WHERE user_id=%s", (user_id,))
                cur.execute("UPDATE accounts SET balance=0 WHERE user_id=%s", (user_id,))
                conn.commit()
                return True
    except Exception as e:
        print("DB clear transactions error:", e)
        return False