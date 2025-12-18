import json
import psycopg2.extras
from datetime import datetime
from .connection import get_db_conn

# Типы уведомлений
NOTIFICATION_TYPES = {
    'info': 'Информация',
    'warning': 'Предупреждение',
    'alert': 'Важное',
    'success': 'Успех',
    'transaction': 'Транзакция',
    'budget': 'Бюджет',
    'reminder': 'Напоминание'
}

def db_create_notification(user_id, message, type='info', data=None):
    """Сохраняет новое уведомление для пользователя"""
    if not user_id:
        return None
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Преобразуем данные в JSON если они есть
                data_json = psycopg2.extras.Json(data) if data else None
                
                cur.execute("""
                    INSERT INTO notifications 
                    (user_id, message, type, is_read, created_at) 
                    VALUES (%s, %s, %s, %s, FALSE, NOW())
                    RETURNING notification_id, created_at
                """, (user_id, message, type, data_json))
                
                result = cur.fetchone()
                conn.commit()
                return result
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def db_create_notifications_for_all_users(message, type='info', exclude_user_id=None):
    """Создает уведомление для всех пользователей"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Получаем всех пользователей
                cur.execute("SELECT id FROM users")
                users = cur.fetchall()
                
                # Создаем уведомления для каждого пользователя
                for user in users:
                    user_id = user[0]
                    if exclude_user_id and user_id == exclude_user_id:
                        continue
                    
                    cur.execute("""
                        INSERT INTO notifications 
                        (user_id, message, type, is_read, created_at) 
                        VALUES (%s, %s, %s, FALSE, NOW())
                    """, (user_id, message, type))
                
                conn.commit()
                return len(users)
    except Exception as e:
        print(f"Error creating notifications for all users: {e}")
        return 0

def db_fetch_notifications(user_id, limit=50, unread_only=False):
    """Извлекает уведомления для пользователя"""
    if not user_id:
        return []
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT * FROM notifications 
                    WHERE user_id = %s
                """
                params = [user_id]
                
                if unread_only:
                    query += " AND is_read = FALSE"
                
                query += " ORDER BY is_read ASC, created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                notifications = cur.fetchall()
                
                # Конвертируем дату в строку для удобства
                for notification in notifications:
                    if notification.get('created_at'):
                        notification['created_at_str'] = notification['created_at'].strftime("%H:%M %d.%m.%Y")
                        # Временно убираем относительное время
                        notification['created_at_relative'] = ""  # или используем created_at_str
                
                return notifications
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return []

def db_mark_notification_read(notification_id):
    """Помечает уведомление как прочитанное"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE notifications SET is_read = TRUE WHERE notification_id = %s",
                    (notification_id,)
                )
                conn.commit()
                return True
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return False

def db_mark_all_notifications_read(user_id):
    """Помечает все уведомления пользователя как прочитанные"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
                    (user_id,)
                )
                conn.commit()
                return cur.rowcount
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return 0

def db_delete_notification(notification_id):
    """Удаляет уведомление"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM notifications WHERE notification_id = %s",
                    (notification_id,)
                )
                conn.commit()
                return True
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False

def db_delete_all_read_notifications(user_id):
    """Удаляет все прочитанные уведомления пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM notifications WHERE user_id = %s AND is_read = TRUE",
                    (user_id,)
                )
                conn.commit()
                return cur.rowcount
    except Exception as e:
        print(f"Error deleting read notifications: {e}")
        return 0

def get_unread_count(user_id):
    """Возвращает количество непрочитанных уведомлений"""
    if not user_id:
        return 0
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                    (user_id,)
                )
                return cur.fetchone()[0]
    except Exception as e:
        print(f"Error fetching unread count: {e}")
        return 0

def get_relative_time(dt):
    """Возвращает относительное время (например, '5 минут назад')"""
    try:
        from datetime import datetime
        from datetime import timezone
        
        # Получаем текущее время
        now = datetime.now()
        
        # Если dt имеет часовой пояс (aware), делаем его naive
        if dt.tzinfo is not None:
            # Если now naive, а dt aware - делаем dt тоже naive
            if now.tzinfo is None:
                dt = dt.replace(tzinfo=None)
            else:
                # Если оба aware, приводим к одному часовому поясу
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                now = now.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Вычисляем разницу
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} год назад" if years == 1 else f"{years} лет назад"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} месяц назад" if months == 1 else f"{months} месяцев назад"
        elif diff.days > 0:
            return f"{diff.days} день назад" if diff.days == 1 else f"{diff.days} дней назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} час назад" if hours == 1 else f"{hours} часов назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} минуту назад" if minutes == 1 else f"{minutes} минут назад"
        else:
            return "только что"
    except Exception as e:
        print(f"Error in get_relative_time: {e}")
        return "недавно"

# Утилиты для создания специфических уведомлений
def create_transaction_notification(user_id, transaction):
    """
    Создает уведомление о новой транзакции
    Возвращает ID созданного уведомления или None в случае ошибки
    """
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Формируем сообщение
        transaction_type = "расход" if transaction.get('type') == 'expense' else "доход"
        message = f"Новый {transaction_type}: {transaction.get('description', 'Без описания')} на сумму ₸{transaction.get('amount', 0):.2f}"
        
        # Вставляем данные БЕЗ поля meta_data, так как его нет в таблице
        cursor.execute("""
            INSERT INTO notifications 
            (user_id, message, type, is_read, created_at) 
            VALUES (%s, %s, 'transaction', FALSE, NOW())
            RETURNING notification_id
        """, (user_id, message))
        
        notification_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Создано уведомление ID: {notification_id}")
        return notification_id
        
    except Exception as e:
        print(f"Ошибка при создании уведомления: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_budget_warning_notification(user_id, category, spent, limit):
    """Создает уведомление о превышении бюджета"""
    percentage = (spent / limit) * 100
    message = f"⚠️ Превышен бюджет по категории '{category}': ₸{spent:.2f} из ₸{limit:.2f} ({percentage:.0f}%)"
    return db_create_notification(user_id, message, 'warning')

def create_weekly_report_notification(user_id, stats):
    """Создает уведомление с недельным отчетом"""
    message = f"📊 Недельный отчет: доход ₸{stats.get('income', 0):.2f}, расход ₸{stats.get('expense', 0):.2f}, баланс ₸{stats.get('balance', 0):.2f}"
    return db_create_notification(user_id, message, 'info', stats)

def create_reminder_notification(user_id, reminder_text):
    """Создает уведомление-напоминание"""
    message = f"🔔 Напоминание: {reminder_text}"
    return db_create_notification(user_id, message, 'reminder')