from .connection import get_db_conn


def create_user_admin(username, email, password, role="user"):
    """
    Создаёт нового пользователя из админ-панели.
    Возвращает (user_id, error_message) - error_message будет None при успехе.
    """
    # Валидация
    if not username or not email or not password:
        return None, "Все поля обязательны для заполнения"
    
    if len(username) < 3:
        return None, "Имя пользователя должно быть не менее 3 символов"
    
    if len(password) < 4:
        return None, "Пароль должен быть не менее 4 символов"
    
    if "@" not in email or "." not in email:
        return None, "Некорректный формат email"
    
    DEFAULT_CATEGORIES = [
        ('Продукты', 'expense'), ('Транспорт', 'expense'),
        ('Развлечения', 'expense'), ('Комм. услуги', 'expense'),
        ('Покупки', 'expense'), ('Здоровье', 'expense'),
        ('Образование', 'expense'), ('Ресторан', 'expense'),
        ('Одежда', 'expense'), ('Связь', 'expense'),
        ('Спорт', 'expense'), ('Путешествия', 'expense'),
        ('Подарки', 'expense'), ('Красота', 'expense'),
        ('Автомобиль', 'expense'), ('Доходы', 'income'),
        ('Другое', 'expense')
    ]

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Проверяем существование пользователя с таким username
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return None, "Пользователь с таким именем уже существует"
                
                # Проверяем существование пользователя с таким email
                cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return None, "Пользователь с таким email уже существует"
                
                # Хешируем пароль (используем тот же алгоритм, что и в обычной регистрации)
                import hashlib
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Создаём пользователя
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, (username, email, password_hash, role))
                user_id = cur.fetchone()[0]

                # Создаём профиль пользователя
                cur.execute("""
                    INSERT INTO user_profiles (user_id, full_name, currency)
                    VALUES (%s, %s, 'KZT')
                """, (user_id, username))

                # Создаём основной счёт
                cur.execute("""
                    INSERT INTO accounts (user_id, account_name, account_type, balance)
                    VALUES (%s, 'Основной счет', 'cash', 0.00)
                """, (user_id,))

                # Создаём дефолтные категории
                cur.executemany("""
                    INSERT INTO categories (category_name, category_type, user_id)
                    VALUES (%s, %s, %s)
                """, [(name, ctype, user_id) for name, ctype in DEFAULT_CATEGORIES])

                conn.commit()
                
                print(f"Пользователь создан успешно: {username}, ID: {user_id}, роль: {role}")
                return user_id, None

    except Exception as e:
        print(f"Ошибка при создании пользователя админом: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Ошибка базы данных: {str(e)}"
    
    
def fetch_all_users():
    """Возвращает всех пользователей с их ролями"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, username, email, role FROM users ORDER BY user_id ASC")
                users = cur.fetchall()
                return [{"id": u[0], "username": u[1], "email": u[2], "role": u[3]} for u in users]
    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []

def get_user_role(username):
    """Возвращает роль пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Ошибка при получении роли: {e}")
        return None

def update_user(user_id, username=None, email=None, role=None):
    """Обновляет данные пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                if username:
                    cur.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))
                if email:
                    cur.execute("UPDATE users SET email=%s WHERE user_id=%s", (email, user_id))
                if role:
                    cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (role, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении пользователя: {e}")
        return False

def delete_user_by_id(user_id):
    """Удаляет пользователя и все связанные данные"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
                cur.execute("DELETE FROM categories WHERE user_id = %s", (user_id,))
                cur.execute("DELETE FROM accounts WHERE user_id = %s", (user_id,))
                cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
                cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return False


def get_current_user_id(username):
    """Получает ID пользователя по имени"""
    # ✅ ИСПРАВЛЕНИЕ: Преобразование в строку, чтобы предотвратить несовпадение типов в SQL
    if username is not None:
        username = str(username) 
        
    if not username:
        return None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # В PostgreSQL строковые параметры, переданные через %s, автоматически заключаются в кавычки
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Error fetching user ID: {e}")
        return None

def create_user_with_defaults(username, email, password_hash):
    """
    Создаёт нового пользователя с дефолтным профилем, основным счётом и категориями.
    Всё выполняется атомарно: либо создаётся полностью, либо откат при ошибке.
    """
    DEFAULT_CATEGORIES = [
        ('Продукты', 'expense'), ('Транспорт', 'expense'),
        ('Развлечения', 'expense'), ('Комм. услуги', 'expense'),
        ('Покупки', 'expense'), ('Здоровье', 'expense'),
        ('Образование', 'expense'), ('Ресторан', 'expense'),
        ('Одежда', 'expense'), ('Связь', 'expense'),
        ('Спорт', 'expense'), ('Путешествия', 'expense'),
        ('Подарки', 'expense'), ('Красота', 'expense'),
        ('Автомобиль', 'expense'), ('Доходы', 'income'),
        ('Другое', 'expense')
    ]

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Проверяем существование пользователя
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return None, "Пользователь с таким именем уже существует"

                # Создаём пользователя и сразу получаем ID
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (%s, %s, %s, 'user')
                    RETURNING user_id
                """, (username, email, password_hash))
                user_id = cur.fetchone()[0]

                # Создаём профиль и основной счёт одновременно
                cur.execute("""
                    INSERT INTO user_profiles (user_id, full_name, currency)
                    VALUES (%s, %s, 'KZT')
                """, (user_id, username))

                cur.execute("""
                    INSERT INTO accounts (user_id, account_name, account_type, balance)
                    VALUES (%s, 'Основной счет', 'cash', 0.00)
                """, (user_id,))

                # Вставка категорий одним запросом
                cur.executemany("""
                    INSERT INTO categories (category_name, category_type, user_id)
                    VALUES (%s, %s, %s)
                """, [(name, ctype, user_id) for name, ctype in DEFAULT_CATEGORIES])

            # Коммитим только если всё прошло успешно
            conn.commit()

        return {
            "user_id": user_id,
            "username": username,
            "email": email
        }, None

    except Exception as e:
        # В случае ошибки транзакция откатится автоматически благодаря контекстному менеджеру
        return None, str(e)



def verify_user_credentials(username, password_hash):
    """Проверяет учётные данные пользователя"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                result = cur.fetchone()
                if result and result[1] == password_hash:
                    return result[0], None
                return None, "Неверное имя пользователя или пароль"
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None, "Ошибка подключения к базе данных"

def ensure_default_data():
    """
    Функция оставлена для совместимости, но больше не создаёт 'local' пользователя.
    Каждый пользователь создаётся через регистрацию.
    """
    print("ensure_default_data: не требуется, пользователи создаются через регистрацию")
    return None