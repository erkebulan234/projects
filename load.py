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

CAT_COLORS = [
    Colors.RED_600, Colors.BLUE_600, Colors.GREEN_600,
    Colors.YELLOW_600, Colors.PURPLE_600, Colors.TEAL_600,
    Colors.ORANGE_600, Colors.BROWN_600, Colors.CYAN_600
]


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)
system_prompt = {
    "role": "system",
    "content": (
        "You are a helpful financial advisor bot integrated into a finance tracking application."
        "Provide users with advice on budgeting, saving, and managing their finances based on their transaction history."
        "Use a friendly and supportive tone."
        "Talk in Russian."
    )
}

DATA_FILE = "transactions_data.json"

transactions_data = []


def main(page: Page):
    # Цвета и константы 
    BG = "#0B2A20"
    FWG = "#F5F5DC"
    FG = "#004D40"
    PINK = "#D4AF37"

    # Настройка страницы
    page.padding = 0
    page.spacing = 0
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False

    # Загрузка / сохранение данных
    def load_transactions():
        global transactions_data
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    transactions_data = json.load(f)
            except Exception:
                transactions_data = []
        else:
            transactions_data = []
        return transactions_data

    def save_transactions():
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(transactions_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    load_transactions()

    # --- UI элементы и переменные ---
    menu_container = Container()
    main_page_container = Container()

    circle = Stack(
        controls=[
            Container(width=80, height=80, border_radius=40, bgcolor="white12"),
            Container(
                gradient=SweepGradient(
                    center=alignment.center,
                    start_angle=0.0,
                    end_angle=3,
                    stops=[0.5, 0.5],
                    colors=["#00000000", PINK],
                ),
                width=80,
                height=80,
                border_radius=40,
                content=Row(
                    alignment="center",
                    controls=[
                        Container(
                            padding=padding.all(5),
                            bgcolor=BG,
                            width=70,
                            height=70,
                            border_radius=35,
                            content=Container(
                                bgcolor=FG,
                                height=60,
                                width=60,
                                border_radius=30,
                                content=CircleAvatar(
                                    opacity=0.8,
                                    foreground_image_src="https://images.unsplash.com/photo-1545912452-8aea7e25a3d3?ixlib=rb-4.0.3&auto=format&fit=crop&w=687&q=80",
                                ),
                            ),
                        )
                    ],
                ),
            ),
        ]
    )

    def shrink(_e=None):
        main_page_container.width = 120
        main_page_container.scale = Scale(0.85, alignment=alignment.center_right)
        main_page_container.border_radius = border_radius.only(
            top_left=30, bottom_left=30, top_right=0, bottom_right=25
        )
        main_page_container.z_index = 0
        page.update()

    def restore(_e=None):
        main_page_container.width = 400
        main_page_container.border_radius = border_radius.all(0)
        main_page_container.scale = Scale(1, alignment=alignment.center_right)
        page.update()

    amount_field = TextField(
        label="Сумма",
        hint_text="0.00",
        keyboard_type=KeyboardType.NUMBER,
        text_size=20,
        color=FWG,
        border_color=PINK,
        focused_border_color=PINK,
        label_style=TextStyle(color=FWG),
        prefix_text="₸ ",
        width=300
    )

    description_field = TextField(
        label="Описание",
        hint_text="Например: Покупка продуктов",
        color=FWG,
        border_color=PINK,
        focused_border_color=PINK,
        label_style=TextStyle(color=FWG),
        width=300
    )

    selected_category = Text("", visible=False)

    all_categories = [
        'Продукты', 'Транспорт', 'Развлечения', 'Комм. услуги',
        'Покупки', 'Здоровье', 'Образование', 'Ресторан',
        'Одежда', 'Связь', 'Спорт', 'Путешествия',
        'Подарки', 'Красота', 'Автомобиль', 'Доходы', 'Другое'
    ]

    def select_category(category_name):
        selected_category.value = category_name
        category_button.content.value = f"Категория: {category_name}"
        if page.views:
            page.views.pop()
        page.update()

    # show_categories определена ниже, но lambda захватывает имя — это ок

    category_button = Container(
        width=300,
        height=50,
        bgcolor=BG,
        border_radius=10,
        border=border.all(1, PINK),
        padding=13,
        content=Text("Выберите категорию", color=FWG, size=16),
        on_click=lambda e: show_categories(e)
    )

    def show_categories(e):
        category_buttons = []
        for cat in all_categories:
            category_buttons.append(
                Container(
                    content=Text(cat, color=FWG, size=16),
                    padding=15,
                    bgcolor=FG,
                    border_radius=10,
                    margin=5,
                    on_click=lambda ev, c=cat: select_category(c)
                )
            )

        category_view = View(
            "/categories",
            [
                AppBar(
                    title=Text("Выберите категорию", color=FWG),
                    bgcolor=BG,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK,
                        icon_color=FWG,
                        on_click=lambda ev: (page.views.pop() if page.views else None) or page.update()
                    )
                ),
                Container(
                    expand=True,
                    bgcolor=BG,
                    padding=20,
                    content=Column(
                        controls=category_buttons,
                        scroll="auto"
                    )
                )
            ],
            bgcolor=BG
        )

        page.views.append(category_view)
        page.update()

    transaction_type = RadioGroup(
        content=Row([
            Radio(value="expense", label="Расход", fill_color=PINK),
            Radio(value="income", label="Доход", fill_color=PINK),
        ]),
        value="expense"
    )

    def save_transaction(e):
        if not amount_field.value or not description_field.value or category_button.content.value == "Выберите категорию":
            page.snack_bar = SnackBar(
                content=Text("Заполните все поля!", color="white"),
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        try:
            amount_value = float(amount_field.value.replace(',', '.'))
            if amount_value <= 0:
                raise ValueError()
        except Exception:
            page.snack_bar = SnackBar(
                content=Text("Введите корректную сумму (число больше 0)!", color="white"),
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        transaction = {
            "amount": f"{amount_value:.2f}",
            "description": description_field.value,
            "category": category_button.content.value.replace("Категория: ", ""),
            "type": transaction_type.value,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        transactions_data.append(transaction)
        save_transactions()

        amount_field.value = ""
        description_field.value = ""
        category_button.content.value = "Выберите категорию"
        selected_category.value = ""

        update_transactions_list()
        update_categories()

        page.go("/")
        page.snack_bar = SnackBar(
            content=Text("Транзакция добавлена!", color="white"),
            bgcolor="green"
        )
        page.snack_bar.open = True
        page.update()

    # --- Список транзакций ---
    transactions = Column(scroll="auto")

    def load_expenses():
        file_path = "transactions_data.json"
        if not os.path.exists(file_path):
            print("Файл не найден!")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # Если файл — список, просто вернём его
            if isinstance(data, list):
                expenses = data
            elif isinstance(data, dict):
                expenses = data.get("transactions", [])
            else:
                expenses = []

            print(f"Загружено транзакций: {len(expenses)}")
            return expenses

        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []




    def update_transactions_list():
        transactions.controls.clear()
        last = list(reversed(transactions_data[-20:]))
        for i, trans in enumerate(last):
            icon_name = Icons.ARROW_DOWNWARD if trans["type"] == "expense" else Icons.ARROW_UPWARD
            icon_color = "red" if trans["type"] == "expense" else "green"

            transactions.controls.append(
                Container(
                    height=80,
                    width=page.width - 40 if page.width else 360,
                    bgcolor=BG,
                    border_radius=15,
                    padding=15,
                    margin=5,
                    content=Row(
                        controls=[
                            Icon(icon_name, color=icon_color, size=30),
                            Container(width=10),
                            Column(
                                controls=[
                                    Text(trans["description"], color=FWG, weight=FontWeight.BOLD, size=14),
                                    Text(f"{trans['category']} • {trans['date']}", color=FWG, size=11, opacity=0.7),
                                ],
                                spacing=2,
                                expand=True
                            ),
                            Text(f"₸{trans['amount']}", color=FWG, size=16, weight=FontWeight.BOLD)
                        ],
                        alignment="center"
                    )
                )
            )
        page.update()

    # --- View создания транзакции ---
    create_transaction_view = Container(
        width=400,
        height=800,
        padding=20,
        content=Column(
            controls=[
                Row(
                    alignment="spaceBetween",
                    controls=[
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=28,
                            on_click=lambda _: page.go("/")
                        ),
                        Text(
                            "Новая транзакция",
                            color=FWG,
                            size=18,
                            weight=FontWeight.BOLD
                        ),
                        Container(width=40)
                    ]
                ),
                Container(height=30),
                amount_field,
                Container(height=20),
                description_field,
                Container(height=20),
                category_button,
                Container(height=20),
                Column(
                    controls=[
                        Text("Тип транзакции", color=FWG, size=16),
                        transaction_type
                    ]
                ),
                Container(height=40),
                ElevatedButton(
                    "Сохранить транзакцию",
                    width=300,
                    height=50,
                    bgcolor=PINK,
                    color=BG,
                    on_click=save_transaction
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            scroll="auto"
        )
    )

    # --- Категории ---
    categories_card = Row(scroll="auto", spacing=10)

    def get_category_count(category):
        return sum(1 for t in transactions_data if t['category'] == category)

    def show_category_transactions(category):
        def handler(e):
            page.go(f"/category/{category}")
        return handler

    def update_categories():
        categories_card.controls.clear()
        for i, category in enumerate(all_categories):
            count = get_category_count(category)

            categories_card.controls.append(
                Container(
                    border_radius=15,
                    bgcolor=BG,
                    height=100,
                    width=150,
                    padding=12,
                    on_click=show_category_transactions(category),
                    content=Column(
                        controls=[
                            Text(f"{count} транз.", color=FWG, size=11),
                            Container(height=3),
                            Text(category, color=FWG, weight=FontWeight.BOLD, size=13),
                        ]
                    )
                )
            )
        page.update()

    update_categories()

    first_page_contents = Container(
        content=Column(
            controls=[
                Row(
                    alignment="spaceBetween",
                    controls=[
                        IconButton(
                            icon=Icons.MENU,
                            icon_color=FWG,
                            icon_size=26,
                            on_click=lambda e: shrink(e)
                        ),
                        Row(
                            controls=[
                                IconButton(
                                    icon=Icons.SEARCH,
                                    icon_color=FWG,
                                    icon_size=22,
                                    on_click=lambda e: None
                                ),
                                IconButton(
                                    icon=Icons.NOTIFICATIONS_OUTLINED,
                                    icon_color=FWG,
                                    icon_size=22,
                                    on_click=lambda e: None
                                )
                            ],
                            spacing=0
                        )
                    ]
                ),
                Container(height=10),
                Text("Привет, Пользователь!", color=FWG, size=24, weight=FontWeight.BOLD),
                Container(height=10),
                Text("КАТЕГОРИИ", color=FWG, size=12, weight=FontWeight.W_500),
                Container(
                    padding=padding.only(top=10, bottom=15),
                    content=categories_card,
                    height=130
                ),
                Container(height=5),
                Text("ПОСЛЕДНИЕ ТРАНЗАКЦИИ", color=FWG, size=12, weight=FontWeight.W_500),
                Container(height=10),
                Container(
                    height=380,
                    content=Stack(
                        controls=[
                            Container(
                                content=transactions,
                                height=380
                            ),
                            Container(
                                alignment=alignment.bottom_right,
                                padding=padding.only(bottom=10, right=10),
                                content=FloatingActionButton(
                                    icon=Icons.ADD,
                                    bgcolor=PINK,
                                    on_click=lambda _: page.go("/create_transaction")
                                )
                            )
                        ]
                    )
                )
            ],
            spacing=0
        )
    )

    # --- Статистика / Настройки / Просмотр категории ---
    def create_statistics_view():
        total_income = sum(float(t['amount']) for t in transactions_data if t['type'] == 'income')
        total_expense = sum(float(t['amount']) for t in transactions_data if t['type'] == 'expense')
        balance = total_income - total_expense

        category_stats = []
        for cat in all_categories:
            cat_total = sum(float(t['amount']) for t in transactions_data if t['type'] == 'expense' and t['category'] == cat)
            if cat_total > 0:
                category_stats.append((cat, cat_total))

        category_stats.sort(key=lambda x: x[1], reverse=True)

        pie_sectors = []

        color_index = 0 

        for cat, amount in category_stats:
            percentage = (amount / total_expense) * 100 if total_expense else 0

            pie_sectors.append(
                PieChartSection(
                    value=amount,
                    color=CAT_COLORS[color_index % len(CAT_COLORS)],
                    title=f"₸{amount:.2f}\n({percentage:.1f}%)",
                    title_style=TextStyle(size=10, color=Colors.BLACK)
                )
            )
            color_index += 1

        stats_list = Column(scroll="auto")
        for cat, amount in category_stats:
            stats_list.controls.append(
                Container(
                    padding=15,
                    margin=margin.only(bottom=5),
                    bgcolor=BG,
                    border_radius=10,
                    content=Row(
                        controls=[
                            Container(width=10, height=10, border_radius=5, bgcolor=CAT_COLORS[color_index % len(CAT_COLORS)]),
                            Text(cat, color=FWG, size=16, weight=FontWeight.BOLD, expand=True),
                            Text(f"₸{amount:.2f}", color=PINK, size=16, weight=FontWeight.BOLD)
                        ]
                    )
                )
            )

        return Container(
            width=400,
            height=800,
            padding=20,
            content=Column(
                controls=[
                    Row(
                        alignment="spaceBetween",
                        controls=[
                            IconButton(
                                icon=Icons.ARROW_BACK,
                                icon_color=FWG,
                                icon_size=28,
                                on_click=lambda _: page.go("/")
                            ),
                            Text("Статистика", color=FWG, size=20, weight=FontWeight.BOLD),
                            Container(width=40)
                        ]
                    ),
                    Container(height=20),
                    Container(
                        padding=20,
                        bgcolor=FG,
                        border_radius=15,
                        content=Column(
                            controls=[
                                Text("Общий баланс", color=FWG, size=14),
                                Text(f"₸{balance:.2f}", color=PINK, size=32, weight=FontWeight.BOLD),
                                Container(height=10),
                                Row(
                                    alignment="spaceBetween",
                                    controls=[
                                        Column(
                                            controls=[
                                                Text("Доходы", color=FWG, size=12),
                                                Text(f"₸{total_income:.2f}", color="green", size=18, weight=FontWeight.BOLD)
                                            ]
                                        ),
                                        Column(
                                            controls=[
                                                Text("Расходы", color=FWG, size=12),
                                                Text(f"₸{total_expense:.2f}", color="red", size=18, weight=FontWeight.BOLD)
                                            ],
                                            horizontal_alignment=CrossAxisAlignment.END
                                        )
                                    ]
                                )
                            ]
                        )
                    ),
                    Container(height=20),
                    Text("По категориям", color=FWG, size=16, weight=FontWeight.BOLD),
                    Container(height=10),
                    Container(
                        height=200,
                        padding=10,
                        bgcolor=FG,
                        border_radius=15,
                        content=PieChart(
                            sections=pie_sectors,
                            sections_space=2,
                            center_space_radius=40,
                            expand=True
                        )
                    ),
                    Container(height=20),
                    Text("Детализация доходов", color=FWG, weight=FontWeight.BOLD),
                    Container(height=10),
                    Container(
                        height=200,
                        content=stats_list
                    )
                ],
                scroll="auto"
            )
        )
    
    def ai_answer(question):
        expenses = load_expenses()
        expense_summary = "Расходы не найдены"

        if expenses: 
            total_expenses = sum(
                float(item.get("amount", 0))
                for item in expenses
                if item.get("type") == "expense"
            )

            top_categories = {}
            for t in expenses:
                if t.get("type") == "expense":
                    cat = t.get("category", "Прочее")
                    top_categories[cat] = top_categories.get(cat, 0) + float(t.get("amount", 0))

            sorted_category = sorted(top_categories.items(), key=lambda x: x[1], reverse=True)
            top_cats_str = ", ".join(f"{cat}: {amt}" for cat, amt in sorted_category[:3])
            expense_summary = f"Всего расходов: {total_expenses}. Топ категории трат: {top_cats_str}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты финансовый советчик. "
                            "Отвечай кратко, дружелюбно и полезно. "
                            "Используй данные о расходах, чтобы давать советы. "
                            "Всегда говори по-русски."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Расходы пользователя: {expense_summary}. Вопрос: {question}"
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка API: {e}")  # Логируем для себя
            return "Прости, возникла ошибка при обращении к AI."

    def ai_view(page):
        chat_column = Column(spacing=10, expand=True, scroll="auto")

        def add_message(text, is_user):
            chat_column.controls.append(
                Row(
                    alignment="end" if is_user else "start",
                    controls=[
                        Container(
                            content=Text(
                                text,
                                size=16,
                                color=FWG,
                                no_wrap=False,
                                # Можно добавить line_height, чтобы текст выглядел аккуратнее
                            ),
                            padding=10,
                            margin=margin.only(left=40 if is_user else 0, right=40 if not is_user else 0),
                            bgcolor=FG,
                            border_radius=10,
                            width=250,       # Ограничиваем ширину сообщений
                            clip_behavior=ClipBehavior.HARD_EDGE  # чтобы текст не вылезал
                        )
                    ]
                )
            )
            page.update()
            chat_column.scroll = "end"


        def send_message(e):
            text = user_input.value.strip()
            if text == "":
                return

            add_message(text, is_user=True)
            user_input.value = ""
            page.update()

            # Запускаем AI в отдельном потоке, чтобы не блокировать UI
            def worker():
                bot_reply = ai_answer(text)
                add_message(bot_reply, is_user=False)

            threading.Thread(target=worker).start()

        user_input = TextField(
            label="Задайте вопрос по финансам",
            hint_text="Например: Как мне сэкономить больше денег?",
            color=FWG,
            border_color=PINK,
            focused_border_color=PINK,
            label_style=TextStyle(color=FWG),
            width=300,
            on_submit=send_message
        )

        return Container(
            width=400,
            height=800,
            padding=20,
            content=Column(
                controls=[
                    Row(
                        alignment="spaceBetween",
                        controls=[
                            IconButton(icon=Icons.ARROW_BACK, icon_color=FWG, icon_size=28, on_click=lambda _: page.go("/")),
                            Text("AI-Советник", color=FWG, size=20, weight=FontWeight.BOLD),
                            Container(width=40)
                        ]
                    ),
                    chat_column,
                    Row(
                        controls=[
                            user_input,
                            IconButton(icon=Icons.SEND, icon_color=PINK, icon_size=28, on_click=send_message)
                        ]
                    )
                ]
            )
        )


    def create_settings_view():
        return Container(
            width=400,
            height=800,
            padding=20,
            content=Column(
                controls=[
                    Row(
                        alignment="spaceBetween",
                        controls=[
                            IconButton(
                                icon=Icons.ARROW_BACK,
                                icon_color=FWG,
                                icon_size=28,
                                on_click=lambda _: page.go("/")
                            ),
                            Text("Настройки", color=FWG, size=20, weight=FontWeight.BOLD),
                            Container(width=40)
                        ]
                    ),
                    Container(height=30),
                    Text("Управление данными", color=FWG, size=16, weight=FontWeight.BOLD),
                    Container(height=10),
                    ElevatedButton(
                        "Очистить все транзакции",
                        width=300,
                        bgcolor="red",
                        color="white",
                        on_click=lambda e: clear_all_transactions()
                    ),
                    Container(height=30),
                    Text("О приложении", color=FWG, size=16, weight=FontWeight.BOLD),
                    Container(height=10),
                    Text("Finance Tracker", color=FWG, size=14),
                    Text("Версия 1.0.0", color=FWG, size=12, opacity=0.7),
                    Container(height=10),
                    Text("Приложение для учета доходов и расходов", color=FWG, size=12, opacity=0.7)
                ],
                scroll="auto"
            )
        )

    def clear_all_transactions():
        global transactions_data
        transactions_data.clear()
        save_transactions()
        update_transactions_list()
        update_categories()
        page.go("/")
        page.snack_bar = SnackBar(
            content=Text("Все транзакции удалены", color="white"),
            bgcolor="green"
        )
        page.snack_bar.open = True
        page.update()

    # --- Левое меню ---
    page_1 = Container(
        width=400,
        height=800,
        bgcolor=BG,
        border_radius=0,
        padding=padding.only(left=30, top=50, right=150),
        content=Column(
            controls=[
                Row(
                    alignment="end",
                    controls=[
                        Container(
                            border_radius=15,
                            padding=padding.only(top=5, left=12, right=8, bottom=5),
                            width=45,
                            height=45,
                            border=border.all(color='white', width=1),
                            on_click=lambda e: restore(e),
                            content=Icon(Icons.ARROW_FORWARD_IOS, color=FWG, size=20)
                        )
                    ]
                ),
                Container(height=20),
                circle,
                Container(height=10),
                Text("Меню", color=FWG, size=26, weight=FontWeight.BOLD),
                Container(height=20),
                Container(on_click=lambda e:(restore(e), page.go("/")), content=Row(controls=[Icon(Icons.HOME, color=FWG, size=22), Container(width=10), Text("Главная", size=16, weight=FontWeight.W_300, color=FWG)])),
                Container(height=15),
                Container(on_click=lambda e:(restore(e), page.go("/statistics")), content=Row(controls=[Icon(Icons.PIE_CHART_OUTLINE, color=FWG, size=22), Container(width=10), Text("Статистика", size=16, weight=FontWeight.W_300, color=FWG)])),
                Container(height=15),
                Container(on_click=lambda e: (restore(e), page.go("/settings")), content=Row(controls=[Icon(Icons.SETTINGS_OUTLINED, color=FWG, size=22), Container(width=10), Text("Настройки", size=16, weight=FontWeight.W_300, color=FWG)])),
                Container(height=15),
                Container(on_click=lambda e: (restore(e), page.go("/ai")), content=Row(controls=[Icon(Icons.SMART_TOY_OUTLINED, color=FWG, size=22), Container(width=10), Text("AI-Советник", size=16, weight=FontWeight.W_300, color=FWG)])),
                Container(height=60),
                Icon(Icons.LOGOUT, color=FWG, size=26),
                Text("Выход", size=15, weight=FontWeight.W_300, color=FWG),
                Container(height=20),
                Text("Версия 1.0.0", size=11, weight=FontWeight.W_300, color=FWG)
            ]
        )
    )

    # --- Правое (главное) содержимое ---
    main_page_container.content = Column(controls=[first_page_contents], spacing=0)
    main_page_container.width = 400
    main_page_container.height = 800
    main_page_container.bgcolor = FG
    main_page_container.border_radius = 0
    main_page_container.animate = Animation(600, AnimationCurve.DECELERATE)
    main_page_container.animate_scale = Animation(400, curve='decelerate')
    main_page_container.padding = padding.only(top=50, right=20, left=20, bottom=5)

    page_2 = Row(alignment="end", controls=[main_page_container])

    container = Container(width=400, height=800, bgcolor=BG, border_radius=0, content=Stack(controls=[page_1, page_2]))

    def create_category_view(category):
        category_transactions = Column(scroll="auto")
        filtered = [t for t in transactions_data if t['category'] == category]
        for trans in reversed(filtered):
            icon_name = Icons.ARROW_DOWNWARD if trans["type"] == "expense" else Icons.ARROW_UPWARD
            icon_color = "red" if trans["type"] == "expense" else "green"
            category_transactions.controls.append(
                Container(
                    height=80,
                    width=360,
                    bgcolor=BG,
                    border_radius=15,
                    padding=15,
                    margin=5,
                    content=Row(
                        controls=[
                            Icon(icon_name, color=icon_color, size=30),
                            Container(width=10),
                            Column(
                                controls=[
                                    Text(trans["description"], color=FWG, weight=FontWeight.BOLD, size=14),
                                    Text(f"{trans['date']}", color=FWG, size=11, opacity=0.7),
                                ],
                                spacing=2,
                                expand=True
                            ),
                            Text(f"₸{trans['amount']}", color=FWG, size=16, weight=FontWeight.BOLD)
                        ],
                        alignment="center"
                    )
                )
            )

        return Container(
            width=400,
            height=800,
            padding=20,
            content=Column(
                controls=[
                    Row(
                        alignment="spaceBetween",
                        controls=[
                            IconButton(icon=Icons.ARROW_BACK, icon_color=FWG, icon_size=28, on_click=lambda _: page.go("/")),
                            Text(category, color=FWG, size=20, weight=FontWeight.BOLD),
                            Container(width=40)
                        ]
                    ),
                    Container(height=10),
                    Text(f"Всего транзакций: {len(filtered)}", color=FWG, size=14),
                    Container(height=20),
                    Container(height=650, content=category_transactions)
                ],
                scroll="auto"
            )
        )

    pages = {
        '/': View("/", [container], bgcolor=BG),
        '/create_transaction': View("/create_transaction", [create_transaction_view], bgcolor=BG),
    }

    def route_change(route):
        page.views.clear()
        current_route = page.route

        if current_route == '/':
            update_transactions_list()
            update_categories()
            page.views.append(pages['/'])
        elif current_route == '/create_transaction':
            page.views.append(pages['/create_transaction'])
        elif current_route == '/statistics':
            page.views.append(View("/statistics", [create_statistics_view()], bgcolor=BG))
        elif current_route == '/settings':
            page.views.append(View("/settings", [create_settings_view()], bgcolor=BG))
        elif current_route == '/ai':
            page.views.append(View("/ai", [ai_view(page)], bgcolor=BG))
        elif current_route.startswith('/category/'):
            category = current_route.replace('/category/', '')
            page.views.append(View(current_route, [create_category_view(category)], bgcolor=BG))

        page.update()

    page.bgcolor = BG
    page.on_route_change = route_change
    page.add(container)

    update_transactions_list()
    page.update()


if __name__ == "__main__":
    app(target=main)
