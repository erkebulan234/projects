from .connection import get_db_conn

def save_chat_message(user_id, session_id, message_text, message_type):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print(f"DEBUG DB: Сохраняю сообщение для user_id={user_id}, type={message_type}")
        cursor.execute(, (user_id, message_text, message_type))
        
        message_id = cursor.fetchone()[0]
        print(f"DEBUG DB: Сообщение сохранено с chat_id={message_id}")
        
        conn.commit()
        return message_id
        
    except Exception as e:
        print(f"Ошибка сохранения сообщения чата: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()

def get_chat_history(user_id, limit=50):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print(f"DEBUG DB: Получаю историю для user_id={user_id}, limit={limit}")
        
        cursor.execute(, (user_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'text': row[1],
                'type': row[2],
                'created_at': row[3]
            })
        
        print(f"DEBUG DB: Найдено {len(messages)} сообщений")
        messages.reverse()
        return messages
        
    except Exception as e:
        print(f"Ошибка получения истории чата: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def clear_chat_history(user_id):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print(f"DEBUG DB: Очищаю чат для user_id={user_id}")
        cursor.execute("DELETE FROM chat_history WHERE user_id = %s", (user_id,))
        
        deleted_count = cursor.rowcount
        print(f"DEBUG DB: Удалено {deleted_count} сообщений")
        
        conn.commit()
        return deleted_count
        
    except Exception as e:
        print(f"Ошибка очистки истории чата: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if conn:
            conn.close()

def delete_chat_message(message_id):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print(f"DEBUG DB: Удаляю сообщение chat_id={message_id}")
        
        cursor.execute("DELETE FROM chat_history WHERE chat_id = %s", (message_id,))
        
        deleted_count = cursor.rowcount
        print(f"DEBUG DB: Удалено {deleted_count} сообщений")
        
        conn.commit()
        return deleted_count > 0
        
    except Exception as e:
        print(f"Ошибка удаления сообщения чата: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()