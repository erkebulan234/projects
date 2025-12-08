from flet import *
from datetime import datetime
import json
import os
import psycopg2

# --- Настройки базы данных ---
DB_PARAMS = {
    "dbname": "finance_db",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

DATA_FILE = "transactions_data.json"

# --- Глобальные данные ---
transactions_data = []

# --- Загрузка JSON ---
def load_transactions():
    global transactions_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                transactions_data = json.load(f)
        except:
            transactions_data = []
    else:
        transactions_data = []
    return transactions_data

# --- Сохранение JSON ---
def save_transactions():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(transactions_data, f, ensure_ascii=False, indent=2)
    except:
        pass

# --- Работа с PostgreSQL ---
def create_table():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            amount NUMERIC(10,2),
            description TEXT,
            category TEXT,
            type TEXT,
            date TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_transaction_db(transaction):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (amount, description, category, type, date)
        VALUES (%s, %s, %s, %s, %s)
    """, (transaction['amount'], transaction['description'], transaction['category'], transaction['type'], datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def load_transactions_db():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT amount, description, category, type, date FROM transactions ORDER BY date DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"amount": str(row[0]), "description": row[1], "category": row[2], "type": row[3], "date": row[4].strftime("%d.%m.%Y %H:%M")}
        for row in rows
    ]

# --- Flet UI ---
def main(page: Page):
    global transactions_data
    page.title = "Finance Tracker"
    page.window.width = 400
    page.window.height = 800
    page.window_resizable = False
    page.scroll = "auto"

    # --- UI элементы ---
    amount_field = TextField(label="Сумма", width=200, hint_text="0.00")
    description_field = TextField(label="Описание", width=200, hint_text="Например: Покупка продуктов")
    category_button = Dropdown(
        options=[DropdownOption("Продукты"), DropdownOption("Транспорт"), DropdownOption("Развлечения"), DropdownOption("Доход")],
        value="Продукты"
    )
    transaction_type = Dropdown(
        options=[DropdownOption("Расход"), DropdownOption("Доход")],
        value="Расход"
    )
    transactions_column = Column(scroll="auto")

    # --- Функции обновления UI ---
    def update_transactions_list():
        transactions_column.controls.clear()
        last = list(reversed(transactions_data[-20:]))
        for t in last:
            transactions_column.controls.append(
                Row([
                    Text(t['date'], width=120),
                    Text(t['description'], width=150),
                    Text(f"{t['amount']}₸", width=80),
                    Text(t['category'], width=100),
                    Text(t['type'], width=80)
                ])
            )
        page.update()

    def update_categories():
        # Для демонстрации: можно обновлять список категорий динамически
        if transactions_data:
            cat = transactions_data[-1]["category"]
            category_button.value = cat
        page.update()

    # --- Сохранение новой транзакции ---
    def save_transaction(e):
        if not amount_field.value or not description_field.value:
            page.snack_bar = SnackBar(Text("Заполните все поля!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        try:
            amount_value = float(amount_field.value.replace(",", "."))
        except:
            page.snack_bar = SnackBar(Text("Некорректная сумма!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        transaction = {
            "amount": f"{amount_value:.2f}",
            "description": description_field.value,
            "category": category_button.value,
            "type": transaction_type.value,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        transactions_data.append(transaction)
        save_transactions()
        save_transaction_db(transaction)

        amount_field.value = ""
        description_field.value = ""
        update_transactions_list()
        update_categories()
        page.update()

    # --- Загрузка данных при старте ---
    load_transactions()
    create_table()
    transactions_data = load_transactions_db()
    update_transactions_list()

    # --- UI layout ---
    page.add(
        Column([
            amount_field,
            description_field,
            category_button,
            transaction_type,
            ElevatedButton("Сохранить транзакцию", on_click=save_transaction),
            Text("Последние транзакции:"),
            transactions_column
        ])
    )

if __name__ == "__main__":
    app(target=main)
