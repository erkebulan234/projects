# Полный набор UI-экранов, перенесённых из старого db_auth.py
# Структура:
# - LoginView
# - RegisterView
# - HomeView
# - StatisticsView
# - NotificationsView
# - SearchView
# - SettingsView
# Все экраны используют модульную архитектуру db/* и helpers/*

from flet import *
from helpers.session import write_session, load_session, clear_session
from helpers.validators import is_valid_email
from db.users import get_user_id_by_username, create_local_user_if_missing
from db.transactions import fetch_transactions_for_user, insert_transaction_for_user
from db.notifications import fetch_notifications, mark_notification_read
from db.statistics import get_basic_statistics
from db.categories import get_or_create_category
from datetime import datetime

# -------------------------------
# LOGIN VIEW
# -------------------------------
class LoginView(Control):
    def build(self):
        self.username = TextField(label="Логин")
        self.password = TextField(label="Пароль", password=True)

        def do_login(e):
            u = self.username.value.strip()
            if not u:
                self.page.snack_bar = SnackBar(Text("Введите логин"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            user_id = get_user_id_by_username(u)
            if not user_id:
                self.page.dialog = AlertDialog(title=Text("Ошибка"), content=Text("Пользователь не найден"))
                self.page.dialog.open = True
                self.page.update()
                return

            write_session(u)
            self.page.go("/home")

        return Column([
            Text("Авторизация", size=26, weight=FontWeight.BOLD),
            self.username,
            self.password,
            ElevatedButton("Войти", on_click=do_login),
            TextButton("Создать аккаунт", on_click=lambda e: self.page.go("/register"))
        ], alignment=MainAxisAlignment.CENTER)


# -------------------------------
# REGISTER VIEW
# -------------------------------
class RegisterView(Control):
    def build(self):
        self.username = TextField(label="Логин")
        self.email = TextField(label="Email")
        self.password = TextField(label="Пароль", password=True)

        def do_register(e):
            u = self.username.value.strip()
            email = self.email.value.strip()
            if not u or not email:
                self.page.snack_bar = SnackBar(Text("Заполните поля"))
                self.page.snack_bar.open = True
                self.page.update()
                return
            if not is_valid_email(email):
                self.page.dialog = AlertDialog(title=Text("Ошибка"), content=Text("Некорректный email"))
                self.page.dialog.open = True
                self.page.update()
                return

            create_local_user_if_missing()  # упрощённо
            write_session(u)
            self.page.go("/home")

        return Column([
            Text("Регистрация", size=26, weight=FontWeight.BOLD),
            self.username,
            self.email,
            self.password,
            ElevatedButton("Создать", on_click=do_register),
            TextButton("Назад", on_click=lambda e: self.page.go("/login"))
        ])


# -------------------------------
# HOME VIEW
# -------------------------------
class HomeView(Control):
    def build(self):
        username = load_session() or "local"
        transactions = fetch_transactions_for_user(username, limit=20)

        items = Column(scroll="auto")
        for t in transactions:
            color = Colors.GREEN_600 if t["type"] == "income" else Colors.RED_600
            items.controls.append(Container(
                padding=12,
                bgcolor=color.with_opacity(0.08),
                border_radius=12,
                content=Column([
                    Text(f"{t['date']} - {t['category']}", weight=FontWeight.BOLD),
                    Text(t['description'] or "(нет описания)", size=12),
                    Text(f"{t['amount']} ₸", size=16)
                ])
            ))

        return Column([
            Text(f"Здравствуйте, {username}", size=22, weight=FontWeight.BOLD),
            Divider(),
            Text("Последние операции", size=18),
            items,
            Divider(),
            ElevatedButton("Добавить операцию", on_click=lambda e: self.page.go("/add")),
            ElevatedButton("Статистика", on_click=lambda e: self.page.go("/stats")),
            ElevatedButton("Уведомления", on_click=lambda e: self.page.go("/notifications")),
            ElevatedButton("Поиск", on_click=lambda e: self.page.go("/search")),
            ElevatedButton("Настройки", on_click=lambda e: self.page.go("/settings")),
        ])


# -------------------------------
# STATISTICS VIEW
# -------------------------------
class StatisticsView(Control):
    def build(self):
        username = load_session()
        stats = get_basic_statistics(username)
        return Column([
            Text("Статистика", size=26, weight=FontWeight.BOLD),
            Text(f"Доход: {stats['total_income']} ₸"),
            Text(f"Расход: {stats['total_expense']} ₸"),
            Text(f"Баланс: {stats['balance']} ₸", size=18, weight=FontWeight.BOLD),
            ElevatedButton("Назад", on_click=lambda e: self.page.go("/home"))
        ])


# -------------------------------
# NOTIFICATIONS VIEW
# -------------------------------
class NotificationsView(Control):
    def build(self):
        username = load_session()
        notifs = fetch_notifications(username)
        col = Column(scroll="auto")
        for n in notifs:
            col.controls.append(Row([
                Text(n['message'], expand=1),
                TextButton("✓", on_click=lambda e, id=n['notification_id']: self.mark(id))
            ]))

        return Column([
            Text("Уведомления", size=26, weight=FontWeight.BOLD),
            col,
            ElevatedButton("Назад", on_click=lambda e: self.page.go("/home"))
        ])

    def mark(self, notif_id):
        mark_notification_read(notif_id)
        self.page.go("/notifications")


# -------------------------------
# SEARCH VIEW
# -------------------------------
class SearchView(Control):
    def build(self):
        self.query = TextField(label="Поиск…")
        self.results = Column(scroll="auto")

        def do_search(e):
            username = load_session()
            items = fetch_transactions_for_user(username)
            q = self.query.value.lower().strip()
            self.results.controls.clear()

            for t in items:
                if q in t['description'].lower() or q in t['category'].lower():
                    self.results.controls.append(Text(f"{t['date']} — {t['amount']} ₸ [{t['category']}]"))

            self.update()

        return Column([
            Text("Поиск", size=26, weight=FontWeight.BOLD),
            self.query,
            ElevatedButton("Найти", on_click=do_search),
            self.results,
            ElevatedButton("Назад", on_click=lambda e: self.page.go("/home"))
        ])


# -------------------------------
# SETTINGS VIEW
# -------------------------------
class SettingsView(Control):
    def build(self):
        return Column([
            Text("Настройки", size=26, weight=FontWeight.BOLD),
            ElevatedButton("Выйти", on_click=self.logout),
            ElevatedButton("Назад", on_click=lambda e: self.page.go("/home"))
        ])

    def logout(self, e):
        clear_session()
        self.page.go("/login")
