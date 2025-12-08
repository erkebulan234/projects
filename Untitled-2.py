# ...existing code...
from flet import *
from datetime import datetime
import json
import os
from openai import OpenAI
import threading
import psycopg2
import psycopg2.extras
import subprocess
import time
from psycopg2 import sql
# ...existing code...

# --- PostgreSQL integration (added) ---
def get_db_conn():
	return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DB", "finance_tracker"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "")
    )

def ensure_db_schema():
    """
    Создает необходимые таблицы:
    - users (id PK)
    - accounts (id PK, user_id -> users) 1:Many users->accounts
    - categories (id PK)
    - transactions (id PK, account_id -> accounts, category_id -> categories) accounts->transactions 1:Many
    - transaction_tags (transaction_id, tag) many-many via lightweight tag table
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        created_at TIMESTAMP DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        currency TEXT NOT NULL DEFAULT 'KZT',
        created_at TIMESTAMP DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        color TEXT,
        created_at TIMESTAMP DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
        category_id INTEGER REFERENCES categories(id),
        amount NUMERIC(14,2) NOT NULL,
        description TEXT,
        type TEXT NOT NULL CHECK (type IN ('expense','income')),
        occurred_at TIMESTAMP NOT NULL,
+        created_at TIMESTAMP DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS transaction_tags (
        transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
        tag TEXT NOT NULL,
        PRIMARY KEY (transaction_id, tag)
    );
    """
    try:
       with get_db_conn() as conn:
           with conn.cursor() as cur:
                cur.execute(ddl)
                # индексы для производительности
                cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_occurred_at ON transactions(occurred_at);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);")
           conn.commit()
    except Exception as e:
        print("ensure_db_schema error:", e)

def db_insert_transaction(transaction):
    """Вставляет транзакцию в БД, создаёт категорию/аккаунт/пользователя при необходимости."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # category
                cur.execute("SELECT id FROM categories WHERE name=%s", (transaction['category'],))
                row = cur.fetchone()
                if row:
                    cat_id = row[0]
                else:
                    cur.execute("INSERT INTO categories(name) VALUES(%s) RETURNING id", (transaction['category'],))
                    cat_id = cur.fetchone()[0]
                # account (local default)
                cur.execute("SELECT id FROM accounts WHERE name=%s", ("Local",))
                row = cur.fetchone()
                if row:
                    account_id = row[0]
                else:
                    cur.execute("SELECT id FROM users WHERE username=%s", ("local",))
                    r = cur.fetchone()
                    if r:
                        user_id = r[0]
                    else:
                        cur.execute("INSERT INTO users(username) VALUES(%s) RETURNING id", ("local",))
                        user_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO accounts(user_id,name) VALUES(%s,%s) RETURNING id", (user_id, "Local"))
                    account_id = cur.fetchone()[0]
                occurred_at = datetime.strptime(transaction['date'], "%d.%m.%Y %H:%M")
                cur.execute("""
                    INSERT INTO transactions(account_id, category_id, amount, description, type, occurred_at)
                    VALUES(%s,%s,%s,%s,%s,%s) RETURNING id
                """, (account_id, cat_id, transaction['amount'], transaction['description'], transaction['type'], occurred_at))
                tid = cur.fetchone()[0]
                conn.commit()
                return tid
    except Exception as e:
        print("DB insert error:", e)
        return None

def db_fetch_all_transactions():
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                SELECT t.id, t.amount, t.description, c.name AS category, t.type,
                       to_char(t.occurred_at, 'DD.MM.YYYY HH24:MI') as date
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                ORDER BY t.occurred_at ASC
                """)
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
        print("DB fetch error:", e)
        return None

def get_monthly_expense(year, month):
    """Пример отчёта: расходы по категориям за месяц (используется JOIN и GROUP BY)."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                SELECT c.name AS category, SUM(t.amount) AS total
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'expense' AND EXTRACT(YEAR FROM t.occurred_at) = %s AND EXTRACT(MONTH FROM t.occurred_at) = %s
                GROUP BY c.name
                ORDER BY total DESC
                """, (year, month))
                return cur.fetchall()
    except Exception as e:
        print("monthly report error:", e)
        return []

def get_top_categories(limit=5):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                SELECT c.name, SUM(t.amount) AS total
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.type='expense'
                GROUP BY c.name
                ORDER BY total DESC
                LIMIT %s
                """, (limit,))
                return cur.fetchall()
    except Exception as e:
        print("top categories error:", e)
        return []

def backup_db(backup_path: str = None):
    """Создаёт дамп БД (требуется pg_dump). Возвращает путь к файлу."""
    backup_dir = os.path.join(os.getcwd(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = backup_path or os.path.join(backup_dir, f"finance_backup_{int(time.time())}.dump")
    cmd = [
        "pg_dump",
        "-h", os.getenv("PG_HOST", "localhost"),
        "-p", os.getenv("PG_PORT", "5432"),
        "-U", os.getenv("PG_USER", "postgres"),
        "-F", "c",
        "-b",
        "-f", backup_path,
        os.getenv("PG_DB", "finance_tracker")
    ]
    env = os.environ.copy()
    if os.getenv("PG_PASSWORD"):
        env["PGPASSWORD"] = os.getenv("PG_PASSWORD")
    try:
        subprocess.run(cmd, env=env, check=True)
        return backup_path
    except Exception as e:
        print("backup failed:", e)
        return None

def start_backup_scheduler(interval_hours=24):
    """Простейший планировщик бэкапов в отдельном потоке."""
    def loop():
        while True:
            path = backup_db()
            if path:
                print("Backup saved to", path)
            time.sleep(interval_hours * 3600)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
# --- end PostgreSQL integration ---
# ...existing code...