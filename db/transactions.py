from datetime import datetime
from .users import get_current_user_id
from .connection import get_db_conn

def db_fetch_user_transactions(username):
    """Получает все транзакции конкретного пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.* FROM transactions t
                    JOIN users u ON t.user_id = u.user_id
                    WHERE u.username = %s
                    ORDER BY t.created_at DESC
                """, (username,))
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
    """Возвращает все транзакции всех пользователей для админ-панели"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        t.transaction_id,
                        t.user_id,
                        u.username,
                        c.category_name,  -- Получаем название категории из таблицы категорий
                        t.amount,
                        t.description,
                        t.transaction_type,
                        t.created_at
                    FROM transactions t
                    JOIN users u ON t.user_id = u.user_id
                    LEFT JOIN categories c ON t.category_id = c.category_id  -- JOIN с таблицей категорий
                    ORDER BY t.created_at DESC
                """)
                transactions = cur.fetchall()
                return [{
                    "id": t[0],
                    "user_id": t[1],
                    "username": t[2],
                    "category": t[3] if t[3] else "Без категории",  # Название категории
                    "amount": float(t[4]),
                    "description": t[5] or "",
                    "type": t[6],
                    "date": t[7].strftime("%d.%m.%Y %H:%M") if t[7] else ""
                } for t in transactions]
    except Exception as e:
        print(f"Ошибка при получении всех транзакций: {e}")
        return []

def db_insert_transaction(transaction, user_id):
    """Вставляет транзакцию в БД"""
    if not user_id:
        print("db_insert_transaction error: user_id is missing")
        return None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_id FROM accounts 
                    WHERE user_id=%s AND account_name='Основной счет'
                """, (user_id,))
                account_row = cur.fetchone()
                if not account_row:
                    print(f"Аккаунт 'Основной счет' для user_id {user_id} не найден. Создаю...")
                    cur.execute("""
                        INSERT INTO accounts (user_id, account_name, account_type, balance)
                        VALUES (%s, 'Основной счет', 'cash', 0.00)
                        RETURNING account_id
                    """, (user_id,))
                    account_id = cur.fetchone()[0]
                else:
                    account_id = account_row[0]
                
                cur.execute("""
                    SELECT category_id FROM categories 
                    WHERE category_name=%s AND user_id=%s
                """, (transaction['category'], user_id))
                cat_row = cur.fetchone()
                
                if not cat_row:
                    category_type = 'expense' if transaction['type'] == 'expense' else 'income'
                    cur.execute("""
                        INSERT INTO categories (category_name, category_type, user_id)
                        VALUES (%s, %s, %s)
                        RETURNING category_id
                    """, (transaction['category'], category_type, user_id))
                    category_id = cur.fetchone()[0]
                else:
                    category_id = cat_row[0]
                
                transaction_date = datetime.strptime(transaction['date'], "%d.%m.%Y %H:%M")
                
                cur.execute("""
                    INSERT INTO transactions (
                        user_id, account_id, category_id, 
                        amount, transaction_type, description, transaction_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING transaction_id
                """, (user_id, account_id, category_id, 
                      float(transaction['amount']), transaction['type'], 
                      transaction['description'], transaction_date))
                
                tid = cur.fetchone()[0]
                
                if transaction['type'] == 'income':
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance + %s 
                        WHERE account_id = %s
                    """, (float(transaction['amount']), account_id))
                else:
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance - %s 
                        WHERE account_id = %s
                    """, (float(transaction['amount']), account_id))
                
                conn.commit()
                return tid
    except Exception as e:
        print("DB insert error:", e)
        return None



def db_fetch_all_transactions(username):
    """Возвращает ВСЕ транзакции текущего пользователя"""
    user_id = get_current_user_id(username)
    if not user_id:
        return []
    try:
        with get_db_conn() as conn:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                SELECT t.transaction_id as id, t.amount, t.description, 
                       c.category_name AS category, t.transaction_type as type,
                       to_char(t.transaction_date, 'DD.MM.YYYY HH24:MI') as date
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = %s
                ORDER BY t.transaction_date DESC
                """, (user_id,))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    result.append({
                        "id": r["id"],
                        "amount": r["amount"],  # Возвращаем Decimal, а не строку
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
    """Редактирует транзакцию (исправленная версия)"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Получаем текущий user_id транзакции, если не передан
                if user_id is None:
                    cur.execute("""
                        SELECT user_id FROM transactions 
                        WHERE transaction_id = %s
                    """, (transaction_id,))
                    result = cur.fetchone()
                    if result:
                        user_id = result[0]
                    else:
                        return False
                
                # Обрабатываем категорию
                category_id = None
                if category is not None:
                    # Ищем существующую категорию - ИСПРАВЛЕНО ИМЯ СТОЛБЦА!
                    cur.execute("""
                        SELECT category_id FROM categories 
                        WHERE category_name = %s AND user_id = %s
                        LIMIT 1
                    """, (category, user_id))
                    category_result = cur.fetchone()
                    
                    if category_result:
                        category_id = category_result[0]
                    else:
                        # Создаем новую категорию
                        category_type = type_ if type_ else 'expense'
                        cur.execute("""
                            INSERT INTO categories (category_name, category_type, user_id)
                            VALUES (%s, %s, %s)
                            RETURNING category_id
                        """, (category, category_type, user_id))
                        category_result = cur.fetchone()
                        if category_result:
                            category_id = category_result[0]
                        else:
                            print(f"❌ Не удалось создать категорию '{category}'")
                            return False
                
                # Собираем обновляемые поля
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
                
                # Если есть что обновлять
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
    """Версия с подробным логированием для отладки"""
    print(f"\n=== DEBUG: Обновление транзакции {transaction_id} ===")
    print(f"Переданные параметры: {kwargs}")
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Логируем текущее состояние транзакции
                cur.execute("""
                    SELECT transaction_id, user_id, amount, description, 
                           transaction_type, category_id
                    FROM transactions 
                    WHERE transaction_id = %s
                """, (transaction_id,))
                current = cur.fetchone()
                print(f"Текущее состояние: {current}")
                
                # Логируем категорию, если указана
                if 'category' in kwargs and kwargs.get('category'):
                    cur.execute("""
                        SELECT category_id FROM categories 
                        WHERE category_name = %s AND user_id = %s
                    """, (kwargs['category'], kwargs.get('user_id') or (current[1] if current else None)))
                    cat_result = cur.fetchone()
                    print(f"Найдена категория: {cat_result}")
                
                # Выполняем обновление
                return update_transaction(transaction_id, **kwargs)
                
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_user_transaction(transaction_id, username=None, user_id=None):
    """
    Удаляет транзакцию пользователя с проверкой прав
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Если передан username, получаем user_id
                if username and not user_id:
                    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                    user_row = cur.fetchone()
                    if user_row:
                        user_id = user_row[0]
                
                # Получаем информацию о транзакции и проверяем права
                if user_id:
                    cur.execute("""
                        SELECT t.user_id, t.account_id, t.amount, t.transaction_type,
                               a.balance as current_balance
                        FROM transactions t
                        JOIN accounts a ON t.account_id = a.account_id
                        WHERE t.transaction_id = %s AND t.user_id = %s
                        FOR UPDATE
                    """, (transaction_id, user_id))
                else:
                    # Для админов - без проверки user_id
                    cur.execute("""
                        SELECT t.user_id, t.account_id, t.amount, t.transaction_type,
                               a.balance as current_balance
                        FROM transactions t
                        JOIN accounts a ON t.account_id = a.account_id
                        WHERE t.transaction_id = %s
                        FOR UPDATE
                    """, (transaction_id,))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False, "Транзакция не найдена"
                
                trans_user_id, account_id, amount, trans_type, current_balance = transaction_info
                
                # Проверяем права (если user_id передан, проверяем что это владелец)
                if user_id and trans_user_id != user_id:
                    return False, "Нет прав на удаление этой транзакции"
                
                print(f"🗑️ Удаление транзакции {transaction_id}:")
                print(f"   Пользователь: {trans_user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                
                # Обновляем баланс счета
                if trans_type == 'income':
                    new_balance = current_balance - amount
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance - %s 
                        WHERE account_id = %s
                    """, (amount, account_id))
                else:  # expense
                    new_balance = current_balance + amount
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance + %s 
                        WHERE account_id = %s
                    """, (amount, account_id))
                
                # Удаляем саму транзакцию
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
    """Удаляет транзакцию с обновлением баланса"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # 1. Получаем информацию о транзакции перед удалением
                cur.execute("""
                    SELECT t.user_id, t.account_id, t.amount, t.transaction_type,
                           a.balance as current_balance
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.account_id
                    WHERE t.transaction_id = %s
                    FOR UPDATE
                """, (transaction_id,))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False
                
                user_id, account_id, amount, trans_type, current_balance = transaction_info
                
                print(f"🗑️ Удаление транзакции {transaction_id}:")
                print(f"   Пользователь: {user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                
                # 2. Обновляем баланс счета
                if trans_type == 'income':
                    # Если удаляем доход - вычитаем из баланса
                    new_balance = current_balance - amount
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance - %s 
                        WHERE account_id = %s
                    """, (amount, account_id))
                else:  # expense
                    # Если удаляем расход - добавляем к балансу
                    new_balance = current_balance + amount
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance + %s 
                        WHERE account_id = %s
                    """, (amount, account_id))
                
                # 3. Удаляем саму транзакцию
                cur.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
                
                # 4. Логируем действие
                cur.execute("""
                    INSERT INTO transaction_logs 
                    (transaction_id, action, amount, transaction_type, 
                     old_balance, new_balance, user_id)
                    VALUES (%s, 'delete', %s, %s, %s, %s, %s)
                """, (transaction_id, amount, trans_type, current_balance, new_balance, user_id))
                
                conn.commit()
                
                print(f"   Новый баланс счета {account_id}: {new_balance}")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка при удалении транзакции {transaction_id}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def db_delete_transaction(transaction_id, username):
    """Удаляет транзакцию с обновлением баланса для конкретного пользователя"""
    user_id = get_current_user_id(username)
    if not user_id:
        print(f"❌ Пользователь {username} не найден")
        return False
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # 1. Получаем информацию о транзакции перед удалением
                # Проверяем, что транзакция принадлежит пользователю
                cur.execute("""
                    SELECT t.user_id, t.account_id, t.amount, t.transaction_type,
                           a.balance as current_balance
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.account_id
                    WHERE t.transaction_id = %s AND t.user_id = %s
                    FOR UPDATE
                """, (transaction_id, user_id))
                
                transaction_info = cur.fetchone()
                
                if not transaction_info:
                    return False
                
                trans_user_id, account_id, amount, trans_type, current_balance = transaction_info
                
                print(f"🗑️ Удаление транзакции {transaction_id} для пользователя {username}:")
                print(f"   Пользователь: {trans_user_id}, Счет: {account_id}")
                print(f"   Сумма: {amount}, Тип: {trans_type}")
                print(f"   Текущий баланс: {current_balance}")
                
                # 2. Обновляем баланс счета
                if trans_type == 'income':
                    # Если удаляем доход - вычитаем из баланса
                    new_balance = float(current_balance) - float(amount)
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance - %s 
                        WHERE account_id = %s AND user_id = %s
                    """, (amount, account_id, user_id))
                else:  # expense
                    # Если удаляем расход - добавляем к балансу
                    new_balance = float(current_balance) + float(amount)
                    cur.execute("""
                        UPDATE accounts 
                        SET balance = balance + %s 
                        WHERE account_id = %s AND user_id = %s
                    """, (amount, account_id, user_id))
                
                # 3. Удаляем саму транзакцию
                cur.execute("""
                    DELETE FROM transactions 
                    WHERE transaction_id = %s AND user_id = %s
                """, (transaction_id, user_id))
                
                # 4. Логируем действие
                cur.execute("""
                    INSERT INTO transaction_logs 
                    (transaction_id, action, amount, transaction_type, 
                     old_balance, new_balance, user_id)
                    VALUES (%s, 'delete', %s, %s, %s, %s, %s)
                """, (transaction_id, amount, trans_type, current_balance, new_balance, user_id))
                
                conn.commit()

                return True
                
    except Exception as e:
        print(f"❌ Ошибка при удалении транзакции {transaction_id}: {e}")
        import traceback
        traceback.print_exc()
        return False    

def db_fetch_transactions_by_category(category, username):
    """Получает транзакции по категории"""
    user_id = get_current_user_id(username)
    if not user_id:
        return []
    try:
        with get_db_conn() as conn:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # ИСПРАВЛЕНО: используем user_id вместо 'local'
                cur.execute("""
                SELECT t.transaction_id as id, t.amount, t.description, 
                       c.category_name AS category, t.transaction_type as type,
                       to_char(t.transaction_date, 'DD.MM.YYYY HH24:MI') as date
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.category_id
                WHERE c.category_name = %s AND t.user_id = %s
                ORDER BY t.transaction_date DESC
                """, (category, user_id))
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
    """Удаляет все транзакции текущего пользователя"""
    user_id = get_current_user_id(username)
    if not user_id:
        return False
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # ИСПРАВЛЕНО: используем user_id вместо 'local'
                cur.execute("DELETE FROM transactions WHERE user_id=%s", (user_id,))
                cur.execute("UPDATE accounts SET balance=0 WHERE user_id=%s", (user_id,))
                conn.commit()
                return True
    except Exception as e:
        print("DB clear transactions error:", e)
        return False