from flet import *
from datetime import datetime as dt
import datetime as datetime_module
import threading
from helpers import load_session, clear_session
from ui.home_view import create_home_view
from project import db_fetch_user_transactions
from ui.push_notifications import PushNotificationManager, create_notification_bell

# Импорты из модулей
from db import (
    db_insert_transaction, 
    db_fetch_transactions_by_category,
    get_current_user_id,
    get_user_role,
    fetch_all_users,
    delete_user_by_id,
    update_user,
    update_transaction, 
    delete_transaction,
    db_fetch_all_transactions_for_admin,
    create_user_admin,
)
from db.savings_goals import (
    create_savings_goal,
    get_savings_goals,
    add_to_savings_goal,
    update_savings_goal,
    delete_savings_goal,
    get_savings_goal_progress
)
from helpers import clear_session, show_alert
from ui.login_view import create_login_view
from ui.register_view import create_register_view
from ui import (
    BG, FWG, FG, PINK,
    ALL_CATEGORIES,
    create_notifications_view,
    create_search_view,
    create_statistics_view,
    create_settings_view,
    responsive_size,
    MOBILE_PADDING,
    MOBILE_ELEMENT_HEIGHT,
    MOBILE_BORDER_RADIUS,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES
)
from advisor import ai_answer

def safe_username():
    s = load_session()
    if isinstance(s, dict):
        return s.get("username")
    return s

def main(page: Page):
    # === АДАПТИВНЫЕ НАСТРОЙКИ СТРАНИЦЫ ===
    page.padding = 0
    page.spacing = 0
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False
    page.window.min_width = 320
    page.window.min_height = 568
    page.font_family = "Roboto, Segoe UI, Arial, sans-serif"
    page.bgcolor = BG
    page.theme = Theme(
        text_theme=TextTheme(
            body_large=TextStyle(size=responsive_size(16)),
            body_medium=TextStyle(size=responsive_size(14)),
            body_small=TextStyle(size=responsive_size(12)),
            title_large=TextStyle(size=responsive_size(24), weight=FontWeight.BOLD),
            title_medium=TextStyle(size=responsive_size(20), weight=FontWeight.BOLD),
            title_small=TextStyle(size=responsive_size(16), weight=FontWeight.BOLD),
        )
    )


    # === АДАПТИВНЫЕ РАЗМЕРЫ ===
    screen_width = page.window.width or 400
    screen_height = page.window.height or 800
    
    # Контейнеры для меню и главной страницы
    main_page_container = Container()

    greeting_text = Text(
        f"Привет, {load_session() or 'Пользователь'}", 
        color=FWG, 
        size=responsive_size(20), 
        weight=FontWeight.BOLD
    )
    
    # Callbacks для обновления
    current_username = load_session()
    update_callbacks = {
        "load_session": load_session,
        "greeting_text": greeting_text,
        "db_fetch_transactions": db_fetch_user_transactions,
        "username": current_username,
        "screen_width": screen_width,
        "screen_height": screen_height,
        "mobile_padding": MOBILE_PADDING
    }

    # ✅ ИСПРАВЛЕНИЕ: Правильно распаковываем кортеж из create_home_view
    home_content, refresh_home_ui = create_home_view(page, update_callbacks)
    
    # ✅ ИСПРАВЛЕНИЕ: Сохраняем функцию обновления в callbacks
    update_callbacks['refresh_home_ui'] = refresh_home_ui

    notification_manager = PushNotificationManager(page)
    update_callbacks['notification_manager'] = notification_manager

    # Запускаем менеджер уведомлений
    def start_notification_manager():
        notification_manager.start()

    # Запускаем в отдельном потоке
    import threading
    threading.Thread(target=start_notification_manager, daemon=True).start()

    
    
    # === АНИМАЦИЯ МЕНЮ (АДАПТИВНАЯ) ===
    def shrink(_e=None):
        main_page_container.width = responsive_size(100)
        main_page_container.scale = Scale(0.85, alignment=alignment.center_right)
        main_page_container.border_radius = border_radius.only(
            top_left=MOBILE_BORDER_RADIUS,
            bottom_left=MOBILE_BORDER_RADIUS,
            top_right=0,
            bottom_right=25
        )
        main_page_container.z_index = 0
        page.update()

    def restore(_e=None):
        main_page_container.width = screen_width
        main_page_container.border_radius = border_radius.all(0)
        main_page_container.scale = Scale(1, alignment=alignment.center_right)
        page.update()

    update_callbacks['shrink'] = shrink
    update_callbacks['restore'] = restore

    # === АВАТАР ДЛЯ МЕНЮ (АДАПТИВНЫЙ) ===

    def create_admin_view(page: Page, callbacks):
        current_username = callbacks.get("username") or load_session()
        
        if not current_username or get_user_role(current_username) != "admin":
            return View(
                "/admin",
                [Text("Доступ запрещён. Только для администраторов.", color="red", size=responsive_size(16))],
                bgcolor=BG
            )

        # Главный контейнер с фиксированной высотой для скроллинга
        main_scroll_container = Container(
            height=screen_height - 100,  # Фиксированная высота для активации скроллинга
            content=Column(
                controls=[],
                scroll="auto",  # Включаем вертикальный скроллинг
                spacing=responsive_size(10),
                expand=True
            )
        )
        
        users_col = Column(scroll="auto", spacing=responsive_size(8))
        
        # Поля для редактирования существующего пользователя
        edit_username = TextField(
            hint_text="Username", 
            width=screen_width - 2*MOBILE_PADDING, 
            bgcolor=BG, 
            color=FWG, 
            border_color=PINK,
            label="Имя пользователя",
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            text_size=responsive_size(14)
        )
        edit_email = TextField(
            hint_text="Email", 
            width=screen_width - 2*MOBILE_PADDING, 
            bgcolor=BG, 
            color=FWG, 
            border_color=PINK,
            label="Email",
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            text_size=responsive_size(14)
        )
        edit_role = Dropdown(
            width=screen_width - 2*MOBILE_PADDING, 
            options=[
                dropdown.Option("user", "Пользователь"),
                dropdown.Option("admin", "Администратор")
            ], 
            bgcolor=BG, 
            color=FWG,
            label="Роль",
            text_size=responsive_size(14)
        )
        
        save_edit_btn = ElevatedButton(
            "Сохранить изменения", 
            bgcolor=PINK, 
            color="white",
            height=MOBILE_ELEMENT_HEIGHT
        )

        cancel_edit_btn = ElevatedButton(
            "Отмена",
            on_click=lambda e: clear_edit_fields(),
            bgcolor=BG,
            color=FWG,
            height=MOBILE_ELEMENT_HEIGHT
        )

        edit_target_id = None
        edit_target_username = None
        
        # Поля для добавления нового пользователя
        new_username = TextField(
            hint_text="Новое имя пользователя", 
            width=screen_width - 2*MOBILE_PADDING,
            bgcolor=BG, 
            color=FWG, 
            border_color=PINK,
            label="Имя пользователя",
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            text_size=responsive_size(14)
        )
        new_email = TextField(
            hint_text="example@mail.com", 
            width=screen_width - 2*MOBILE_PADDING, 
            bgcolor=BG, 
            color=FWG, 
            border_color=PINK,
            label="Email",
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            text_size=responsive_size(14)
        )
        new_password = TextField(
            hint_text="Пароль", 
            width=screen_width - 2*MOBILE_PADDING, 
            bgcolor=BG, 
            color=FWG, 
            border_color=PINK,
            label="Пароль",
            password=True,
            can_reveal_password=True,
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            text_size=responsive_size(14)
        )
        new_role = Dropdown(
            width=screen_width - 2*MOBILE_PADDING, 
            options=[
                dropdown.Option("user", "Пользователь"),
                dropdown.Option("admin", "Администратор")
            ], 
            bgcolor=BG, 
            color=FWG,
            label="Роль",
            value="user",
            text_size=responsive_size(14)
        )
        
        add_user_btn = ElevatedButton(
            "Добавить пользователя", 
            bgcolor="green", 
            color="white",
            width=screen_width - 2*MOBILE_PADDING,
            height=MOBILE_ELEMENT_HEIGHT
        )
        
        # Функция для диалога подтверждения
        def show_confirmation_dialog(message, on_confirm):
            """Показывает диалог подтверждения"""
            def confirm_action(e):
                page.close(dlg)
                on_confirm()
            
            def cancel_action(e):
                page.close(dlg)
            
            dlg = AlertDialog(
                title=Text("Подтверждение", size=responsive_size(16)),
                content=Text(message, size=responsive_size(14)),
                actions=[
                    TextButton("Да", on_click=confirm_action),
                    TextButton("Нет", on_click=cancel_action),
                ],
            )
            page.open(dlg)
        
        def refresh_users():
            """Обновляет список пользователей (показывает только обычных пользователей)"""
            users_col.controls.clear()
            all_users = fetch_all_users()
            
            # Фильтруем: показываем только обычных пользователей (не админов)
            regular_users = [u for u in all_users if u["role"] != "admin"]
            
            # Адаптивный заголовок таблицы
            header_row = Container(
                content=Column(
                    controls=[
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("ID", color=FWG, size=responsive_size(12), weight=FontWeight.BOLD, width=responsive_size(40)),
                                Text("Имя", color=FWG, size=responsive_size(12), weight=FontWeight.BOLD, width=responsive_size(80)),
                                Text("Email", color=FWG, size=responsive_size(12), weight=FontWeight.BOLD, width=responsive_size(100)),
                            ]
                        ),
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("Роль", color=FWG, size=responsive_size(12), weight=FontWeight.BOLD, width=responsive_size(80)),
                                Text("Действия", color=FWG, size=responsive_size(12), weight=FontWeight.BOLD, width=responsive_size(100)),
                            ]
                        )
                    ]
                ),
                bgcolor=FG,
                padding=responsive_size(10),
                border_radius=MOBILE_BORDER_RADIUS
            )
            users_col.controls.append(header_row)
            
            # Если нет обычных пользователей
            if not regular_users:
                users_col.controls.append(
                    Container(
                        content=Text("Нет обычных пользователей", color=FWG, size=responsive_size(14)),
                        padding=responsive_size(20),
                        alignment=alignment.center
                    )
                )
            
            # Добавляем пользователей с адаптивным дизайном
            for u in regular_users:
                user_row = Container(
                    content=Column(
                        controls=[
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Text(str(u['id']), color=FWG, size=responsive_size(11), width=responsive_size(40)),
                                    Text(u["username"][:10] + "..." if len(u["username"]) > 10 else u["username"], 
                                         color=FWG, size=responsive_size(11), width=responsive_size(80)),
                                    Text(u["email"][:12] + "..." if len(u["email"]) > 12 else u["email"], 
                                         color=FWG, size=responsive_size(11), width=responsive_size(100)),
                                ]
                            ),
                            Container(height=responsive_size(5)),
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Text(
                                        "Админ" if u["role"] == "admin" else "Польз.", 
                                        color=PINK if u["role"] == "admin" else FWG, 
                                        size=responsive_size(11), 
                                        width=responsive_size(80)
                                    ),
                                    Row(
                                        controls=[
                                            IconButton(
                                                icon=Icons.EDIT,
                                                icon_color=FWG,
                                                icon_size=responsive_size(16),
                                                on_click=lambda e, uid=u["id"]: edit_user(uid),
                                                tooltip="Редактировать"
                                            ),
                                            IconButton(
                                                icon=Icons.DELETE,
                                                icon_color="red",
                                                icon_size=responsive_size(16),
                                                on_click=lambda e, uid=u["id"], uname=u["username"]: 
                                                    confirm_delete_user(uid, uname),
                                                tooltip="Удалить"
                                            )
                                        ],
                                        spacing=responsive_size(5),
                                        width=responsive_size(100)
                                    )
                                ]
                            )
                        ]
                    ),
                    bgcolor=BG,
                    padding=responsive_size(10),
                    border=border.all(1, FG),
                    border_radius=MOBILE_BORDER_RADIUS,
                    margin=margin.only(bottom=responsive_size(8))
                )
                users_col.controls.append(user_row)
            
            # Адаптивная статистика
            total_users = len(all_users)
            admin_count = len([u for u in all_users if u["role"] == "admin"])
            regular_count = len(regular_users)
            
            stats_row = Container(
                content=Column(
                    controls=[
                        Text(f"Всего пользователей: {total_users}", color=FWG, size=responsive_size(12)),
                        Text(f"Администраторов: {admin_count}", color=PINK, size=responsive_size(12)),
                        Text(f"Обычных пользователей: {regular_count}", color=FWG, size=responsive_size(12))
                    ]
                ),
                bgcolor=FG,
                padding=responsive_size(10),
                border_radius=MOBILE_BORDER_RADIUS
            )
            users_col.controls.append(Container(height=responsive_size(10)))
            users_col.controls.append(stats_row)
            
            page.update()
        
        def edit_user(user_id):
            """Заполняет поля для редактирования пользователя"""
            nonlocal edit_target_id, edit_target_username
            user = next(u for u in fetch_all_users() if u["id"] == user_id)
            edit_target_id = user_id
            edit_target_username = user["username"]
            
            edit_username.value = user["username"]
            edit_email.value = user["email"]
            edit_role.value = user["role"]

            save_edit_btn.disabled = False

            page.update()

            show_alert(page, f"Заполнены данные пользователя {user['username']}. Прокрутите вниз для редактирования.", bgcolor="blue")



            page.update()
        
        def save_edit(_e):
            """Сохраняет изменения пользователя"""
            if edit_target_id is None:
                return
            
            # Валидация
            if not edit_username.value:
                show_alert(page, "Введите имя пользователя", bgcolor="red")
                return
            
            if not edit_email.value:
                show_alert(page, "Введите email", bgcolor="red")
                return
            
            if not edit_role.value:
                show_alert(page, "Выберите роль", bgcolor="red")
                return
            
            # Проверяем, не пытаемся ли сделать текущего админа обычным пользователем
            if edit_target_username == current_username and edit_role.value == "user":
                show_alert(page, "Вы не можете понизить свои собственные права!", bgcolor="red")
                return
            
            update_user(
                edit_target_id,
                username=edit_username.value,
                email=edit_email.value,
                role=edit_role.value
            )
            save_edit_btn.visible = False
            clear_edit_fields()
            show_alert(page, "Изменения сохранены!", bgcolor="green")
            refresh_users()
        
        def add_new_user(_e):
            """Добавляет нового пользователя через админ-панель"""
            print(f"\n=== DEBUG: Попытка создания пользователя ===")
            print(f"Username: {new_username.value}")
            print(f"Email: {new_email.value}")
            print(f"Password: {'*' * len(new_password.value) if new_password.value else 'None'}")
            print(f"Role: {new_role.value}")

            save_edit_btn.disabled = True
            clear_edit_fields()
            show_alert(page, "Изменения сохранены!", bgcolor="green")
            refresh_users()
            
            # Валидация
            if not new_username.value:
                show_alert(page, "Введите имя пользователя", bgcolor="red")
                return
            
            if not new_email.value:
                show_alert(page, "Введите email", bgcolor="red")
                return
            
            if not new_password.value:
                show_alert(page, "Введите пароль", bgcolor="red")
                return
            
            if not new_role.value:
                show_alert(page, "Выберите роль", bgcolor="red")
                return
            
            # Используем новую функцию create_user_admin
            print("Вызываем create_user_admin...")
            user_id, error_message = create_user_admin(
                username=new_username.value,
                email=new_email.value,
                password=new_password.value,
                role=new_role.value
            )
            
            print(f"Результат: user_id={user_id}, error={error_message}")
            
            if error_message:
                show_alert(page, f"Ошибка: {error_message}", bgcolor="red")
                print(f"Ошибка создания пользователя: {error_message}")
            else:
                show_alert(page, f"Пользователь '{new_username.value}' успешно создан! (ID: {user_id})", bgcolor="green")
                print(f"Пользователь успешно создан! ID: {user_id}")
                
                # Очищаем поля
                new_username.value = ""
                new_email.value = ""
                new_password.value = ""
                new_role.value = "user"
                
                # Обновляем список пользователей
                print("Обновляем список пользователей...")
                refresh_users()
                page.update()
        
        def confirm_delete_user(user_id, username):
            """Показывает подтверждение перед удалением пользователя"""
            def delete_action():
                # Проверяем, не пытаемся ли удалить самих себя
                if username == current_username:
                    show_alert(page, "Вы не можете удалить свой собственный аккаунт!", bgcolor="red")
                    return
                
                if delete_user_by_id(user_id):
                    show_alert(page, f"Пользователь '{username}' удалён!", bgcolor="green")
                    refresh_users()
                else:
                    show_alert(page, "Ошибка при удалении пользователя", bgcolor="red")
            
            show_confirmation_dialog(
                f"Вы уверены, что хотите удалить пользователя '{username}'?\nВсе его данные будут удалены безвозвратно.",
                delete_action
            )
        
        def clear_edit_fields():
            """Очищает поля редактирования"""
            nonlocal edit_target_id, edit_target_username
            edit_target_id = None
            edit_target_username = None
            
            edit_username.value = ""
            edit_email.value = ""
            edit_role.value = ""
            page.update()

            save_edit_btn.disabled = True
            page.update() 
        
        # Настройка обработчиков событий
        save_edit_btn.on_click = save_edit
        add_user_btn.on_click = add_new_user
        
        # Инициализация
        refresh_users()

        # Верхняя стрелка "назад"
        back_arrow = Container(
            border_radius=MOBILE_BORDER_RADIUS,
            padding=padding.all(responsive_size(10)),
            width=responsive_size(45),
            height=responsive_size(45),
            border=border.all(color=FWG, width=1),
            on_click=lambda e: page.go("/"),
            content=Icon(Icons.ARROW_BACK_IOS, color=FWG, size=responsive_size(20))
        )
        
        # Кнопка управления транзакциями
        transactions_btn = ElevatedButton(
            "Управление транзакциями",
            on_click=lambda e: page.go("/admin/transactions"),
            bgcolor=PINK,
            color="white",
            width=screen_width - 2*MOBILE_PADDING,
            height=MOBILE_ELEMENT_HEIGHT
        )
        
        # Заполняем главный скроллируемый контейнер
        main_scroll_container.content.controls = [
            # Заголовок и навигация
            Row(
                controls=[
                    back_arrow,
                    Text("Админ-панель", size=responsive_size(20), weight=FontWeight.BOLD, color=FWG)
                ],
                alignment="start"
            ),
            Container(height=responsive_size(20)),
            
            # Кнопка управления транзакциями
            Row([transactions_btn], alignment="center"),
            Container(height=responsive_size(20)),
            
            # Раздел добавления нового пользователя
            Container(
                bgcolor=FG,
                padding=responsive_size(15),
                border_radius=MOBILE_BORDER_RADIUS,
                content=Column(
                    controls=[
                        Text("Добавить нового пользователя:", 
                            size=responsive_size(16), weight=FontWeight.BOLD, color=FWG),
                        Container(height=responsive_size(10)),
                        new_username,
                        Container(height=responsive_size(8)),
                        new_email,
                        Container(height=responsive_size(8)),
                        new_password,
                        Container(height=responsive_size(8)),
                        new_role,
                        Container(height=responsive_size(15)),
                        Row([add_user_btn], alignment="center")
                    ]
                )
            ),
            Container(height=responsive_size(20)),
            
            # Раздел редактирования существующего пользователя
            Container(
                bgcolor=FG,
                padding=responsive_size(15),
                border_radius=MOBILE_BORDER_RADIUS,
                content=Column(
                    controls=[
                        Text("Редактирование пользователя:", 
                            size=responsive_size(16), weight=FontWeight.BOLD, color=FWG),
                        Container(height=responsive_size(10)),
                        edit_username,
                        Container(height=responsive_size(8)),
                        edit_email,
                        Container(height=responsive_size(8)),
                        edit_role,
                        Container(height=responsive_size(15)),
                        Row([save_edit_btn, cancel_edit_btn], alignment="center", spacing=responsive_size(10)) 
                    ]
                )
            ),
            Container(height=responsive_size(20)),
            
            # Информация
            Container(
                content=Text(
                    "В этом разделе отображаются только обычные пользователи.\n"
                    "Администраторы не отображаются в списке для безопасности.",
                    color=FWG,
                    size=responsive_size(12)
                ),
                bgcolor=FG,
                padding=responsive_size(10),
                border_radius=MOBILE_BORDER_RADIUS
            ),
            Container(height=responsive_size(20)),
            
            # Список пользователей в скроллируемом контейнере
            Container(
                content=Column(
                    controls=[
                        Text("Список пользователей:", 
                            size=responsive_size(16), weight=FontWeight.BOLD, color=FWG),
                        Container(height=responsive_size(10)),
                        Container(
                            content=users_col,
                            height=responsive_size(300),  # Фиксированная высота для внутреннего скроллинга
                            bgcolor=FG,
                            padding=responsive_size(10),
                            border_radius=MOBILE_BORDER_RADIUS
                        )
                    ]
                )
            ),
            Container(height=responsive_size(20))
        ]
        
        return View(
            "/admin",
            [
                Container(
                    bgcolor=BG,
                    padding=padding.all(MOBILE_PADDING),
                    content=main_scroll_container
                )
            ],
            bgcolor=BG
        )

    def create_admin_transactions_view(page: Page, callbacks, from_menu=False):
        """Панель управления транзакциями для администраторов"""
        current_username = callbacks.get("username") or load_session()
        
        # Проверка прав администратора
        if not current_username or get_user_role(current_username) != "admin":
            return View(
                "/admin/transactions",
                [Text("Доступ запрещён. Только для администраторов.", color="red", size=responsive_size(16))],
                bgcolor=BG
            )
        
        # Главный контейнер
        main_scroll_container = Container(
            height=screen_height - 100,
            content=Column(
                controls=[],
                scroll="auto",
                spacing=responsive_size(10),
                expand=True
            )
        )
        
        transactions_col = Column(scroll="auto", spacing=responsive_size(5))
        
        # Фильтры
        user_filter = Dropdown(
            width=screen_width - 2*MOBILE_PADDING,
            options=[dropdown.Option("Все")],
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        type_filter = Dropdown(
            width=screen_width - 2*MOBILE_PADDING,
            options=[
                dropdown.Option("Все"), 
                dropdown.Option("expense", "Расход"), 
                dropdown.Option("income", "Доход")
            ],
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        # Поля для редактирования
        edit_amount = TextField(
            width=screen_width - 2*MOBILE_PADDING,
            hint_text="Сумма",
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            keyboard_type=KeyboardType.NUMBER,
            prefix_text="₸ ",
            text_size=responsive_size(14)
        )
        
        edit_description = TextField(
            width=screen_width - 2*MOBILE_PADDING,
            hint_text="Описание",
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        edit_category = TextField(
            width=screen_width - 2*MOBILE_PADDING,
            hint_text="Категория",
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        edit_type = Dropdown(
            width=screen_width - 2*MOBILE_PADDING,
            options=[
                dropdown.Option("expense", "Расход"), 
                dropdown.Option("income", "Доход")
            ],
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        save_btn = ElevatedButton(
            "Сохранить",
            visible=True,
            disabled=True,
            bgcolor=PINK,
            color="white",
            height=MOBILE_ELEMENT_HEIGHT
        )
        
        cancel_btn = ElevatedButton(
            "Отмена",
            bgcolor=BG,
            color=FWG,
            height=MOBILE_ELEMENT_HEIGHT,
            on_click=lambda e: clear_edit_fields()
        )
        
        selected_transaction_id = None
        selected_user_id = None
        
        def refresh_users_filter():
            """Обновляет список пользователей в фильтре"""
            user_filter.options.clear()
            user_filter.options.append(dropdown.Option("Все"))
            
            users = fetch_all_users()
            for user in users:
                user_filter.options.append(dropdown.Option(user["username"]))
        
        def refresh_transactions():
            """Обновляет список транзакций"""
            transactions_col.controls.clear()
            
            # Получаем все транзакции
            all_transactions = db_fetch_all_transactions_for_admin()
            
            # Применяем фильтры
            filtered_transactions = all_transactions
            if user_filter.value and user_filter.value != "Все":
                filtered_transactions = [t for t in filtered_transactions if t["username"] == user_filter.value]
            
            if type_filter.value and type_filter.value != "Все":
                filtered_transactions = [t for t in filtered_transactions if t["type"] == type_filter.value]
            
            # Адаптивный заголовок таблицы
            header_row = Container(
                content=Column(
                    controls=[
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("ID", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(40)),
                                Text("Пользователь", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(80)),
                                Text("Сумма", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(80)),
                            ]
                        ),
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("Категория", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(80)),
                                Text("Тип", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(60)),
                                Text("Действия", color=FWG, size=responsive_size(11), weight=FontWeight.BOLD, width=responsive_size(100)),
                            ]
                        )
                    ]
                ),
                bgcolor=FG,
                padding=responsive_size(10),
                border_radius=MOBILE_BORDER_RADIUS
            )
            transactions_col.controls.append(header_row)
            
            # Добавляем транзакции с адаптивным дизайном
            for t in filtered_transactions:
                # Обрезаем длинные названия для отображения
                username_display = t["username"][:8] + "..." if len(t["username"]) > 8 else t["username"]
                category_display = t["category"][:8] + "..." if len(t["category"]) > 8 else t["category"]
                
                transaction_row = Container(
                    content=Column(
                        controls=[
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Text(str(t["id"]), color=FWG, size=responsive_size(11), width=responsive_size(40)),
                                    Text(username_display, color=FWG, size=responsive_size(11), width=responsive_size(80)),
                                    Text(f"₸{t['amount']:.2f}", 
                                        color=PINK if t["type"] == "expense" else "green", 
                                        size=responsive_size(11), width=responsive_size(80)),
                                ]
                            ),
                            Container(height=responsive_size(5)),
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Text(category_display, color=FWG, size=responsive_size(11), width=responsive_size(80)),
                                    Text("Расход" if t["type"] == "expense" else "Доход", 
                                        color=FWG, size=responsive_size(11), width=responsive_size(60)),
                                    Row(
                                        controls=[
                                            IconButton(
                                                icon=Icons.EDIT,
                                                icon_color=FWG,
                                                icon_size=responsive_size(16),
                                                on_click=lambda e, tr=t: edit_transaction(tr),
                                                tooltip="Редактировать"
                                            ),
                                            IconButton(
                                                icon=Icons.DELETE,
                                                icon_color="red",
                                                icon_size=responsive_size(16),
                                                on_click=lambda e, tr_id=t["id"]: delete_transaction_action(tr_id),
                                                tooltip="Удалить"
                                            )
                                        ],
                                        spacing=responsive_size(5),
                                        width=responsive_size(100)
                                    )
                                ]
                            )
                        ]
                    ),
                    bgcolor=BG,
                    padding=responsive_size(8),
                    border=border.all(1, FG),
                    border_radius=MOBILE_BORDER_RADIUS,
                    margin=margin.only(bottom=responsive_size(8))
                )
                transactions_col.controls.append(transaction_row)
            
            # Добавляем адаптивную статистику
            if filtered_transactions:
                total_expenses = sum(t["amount"] for t in filtered_transactions if t["type"] == "expense")
                total_income = sum(t["amount"] for t in filtered_transactions if t["type"] == "income")
                balance = total_income - total_expenses
                
                stats_row = Container(
                    content=Column(
                        controls=[
                            Text(f"Всего: {len(filtered_transactions)}", color=FWG, size=responsive_size(12)),
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Text(f"Расходы: ₸{total_expenses:.2f}", color=PINK, size=responsive_size(12)),
                                    Text(f"Доходы: ₸{total_income:.2f}", color="green", size=responsive_size(12)),
                                ]
                            ),
                            Text(f"Баланс: ₸{balance:.2f}", 
                                color="green" if balance >= 0 else PINK, 
                                size=responsive_size(12), weight=FontWeight.BOLD)
                        ]
                    ),
                    bgcolor=FG,
                    padding=responsive_size(10),
                    border_radius=MOBILE_BORDER_RADIUS
                )
                transactions_col.controls.append(Container(height=responsive_size(10)))
                transactions_col.controls.append(stats_row)
            
            page.update()
        
        def edit_transaction(transaction):
            """Заполняет поля для редактирования транзакции"""
            nonlocal selected_transaction_id, selected_user_id
            selected_transaction_id = transaction["id"]
            selected_user_id = transaction["user_id"]
            
            edit_amount.value = str(transaction["amount"])
            edit_description.value = transaction["description"]
            edit_category.value = transaction["category"]
            edit_type.value = transaction["type"]

            save_btn.disabled = False
            cancel_btn.disabled = False

            page.update()
        
        def save_edit(_e):
            """Сохраняет изменения транзакции"""
            if selected_transaction_id is None or selected_user_id is None:
                show_alert(page, "Ошибка: не выбрана транзакция", bgcolor="red")
                return
            
            try:
                # Валидация данных
                if not edit_amount.value:
                    show_alert(page, "Введите сумму", bgcolor="red")
                    return
                
                amount = float(edit_amount.value)
                if amount <= 0:
                    show_alert(page, "Сумма должна быть положительной", bgcolor="red")
                    return
                
                if not edit_category.value:
                    show_alert(page, "Введите категорию", bgcolor="red")
                    return
                
                if not edit_type.value:
                    show_alert(page, "Выберите тип транзакции", bgcolor="red")
                    return
                
                # Обновляем транзакцию
                success = update_transaction(
                    transaction_id=selected_transaction_id,
                    amount=amount,
                    description=edit_description.value,
                    category=edit_category.value,
                    type_=edit_type.value,
                    user_id=selected_user_id
                )
                
                if success:
                    show_alert(page, "Транзакция обновлена!", bgcolor="green")
                    clear_edit_fields()
                    refresh_transactions()
                else:
                    show_alert(page, "Ошибка при обновлении транзакции", bgcolor="red")
            except ValueError:
                show_alert(page, "Неверный формат суммы", bgcolor="red")
            except Exception as e:
                show_alert(page, f"Ошибка: {str(e)}", bgcolor="red")
        
        def delete_transaction_action(tr_id):
            """Удаляет транзакцию"""
            dlg = AlertDialog(
                title=Text("Подтверждение удаления", size=responsive_size(16)),
                content=Text("Вы уверены, что хотите удалить эту транзакцию?", size=responsive_size(14)),
                actions=[
                    TextButton("Да", on_click=lambda e: confirm_delete(tr_id, dlg)),
                    TextButton("Нет", on_click=lambda e: page.close(dlg)),
                ],
            )
            page.open(dlg)
        
        def confirm_delete(tr_id, dlg):
            """Подтверждение удаления"""
            page.close(dlg)
            if delete_transaction(tr_id):
                show_alert(page, "Транзакция удалена!", bgcolor="green")
                refresh_transactions()
            else:
                show_alert(page, "Ошибка при удалении", bgcolor="red")
        
        def clear_edit_fields():
            """Очищает поля редактирования"""
            nonlocal selected_transaction_id, selected_user_id
            selected_transaction_id = None
            selected_user_id = None
            
            edit_amount.value = ""
            edit_description.value = ""
            edit_category.value = ""
            edit_type.value = ""

            save_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
        
        # Настройка обработчиков событий
        save_btn.on_click = save_edit
        user_filter.on_change = lambda e: refresh_transactions()
        type_filter.on_change = lambda e: refresh_transactions()
        
        # Инициализация
        refresh_users_filter()
        refresh_transactions()
        
        # Определяем куда ведет стрелка "назад"
        back_destination = "/" 
        
        back_arrow = Container(
            border_radius=MOBILE_BORDER_RADIUS,
            padding=padding.all(responsive_size(10)),
            width=responsive_size(45),
            height=responsive_size(45),
            border=border.all(color=FWG, width=1),
            on_click=lambda e: page.go(back_destination),
            content=Icon(Icons.ARROW_BACK_IOS, color=FWG, size=responsive_size(20))
        )
        
        # Кнопка "назад к админ-панели" (только если пришли не из меню)
        if not from_menu:
            back_to_admin_btn = ElevatedButton(
                "В админ-панель",
                on_click=lambda e: page.go("/admin"),
                bgcolor=BG,
                color=FWG,
                width=screen_width - 2*MOBILE_PADDING,
                height=MOBILE_ELEMENT_HEIGHT
            )
        
        # Заполняем главный скроллируемый контейнер
        main_scroll_container.content.controls = [
            # Заголовок и навигация
            Row(
                controls=[
                    back_arrow,
                    Text("Управление транзакциями", 
                        size=responsive_size(20), 
                        weight=FontWeight.BOLD, 
                        color=FWG)
                ],
                alignment="start"
            ),
            Container(height=responsive_size(10)),
        ]
        
        # Добавляем кнопку "В админ-панель" только если пришли из админ-панели
        if not from_menu:
            main_scroll_container.content.controls.extend([
                Row([back_to_admin_btn], alignment="center"),
                Container(height=responsive_size(20)),
            ])
        else:
            main_scroll_container.content.controls.append(Container(height=responsive_size(20)))
        
        # Продолжаем заполнение остальными элементами
        main_scroll_container.content.controls.extend([
            # Фильтры
            Container(
                bgcolor=FG,
                padding=responsive_size(15),
                border_radius=MOBILE_BORDER_RADIUS,
                content=Column(
                    controls=[
                        Text("Фильтры:", size=responsive_size(16), weight=FontWeight.BOLD, color=FWG),
                        Container(height=responsive_size(10)),
                        Text("Фильтр по пользователю:", color=FWG, size=responsive_size(14)),
                        user_filter,
                        Container(height=responsive_size(10)),
                        Text("Фильтр по типу:", color=FWG, size=responsive_size(14)),
                        type_filter
                    ]
                )
            ),
            Container(height=responsive_size(20)),
            
            # Панель редактирования
            Container(
                bgcolor=FG,
                padding=responsive_size(15),
                border_radius=MOBILE_BORDER_RADIUS,
                content=Column(
                    controls=[
                        Text("Редактирование транзакции", 
                            size=responsive_size(16), 
                            weight=FontWeight.BOLD, 
                            color=FWG),
                        Container(height=responsive_size(10)),
                        edit_amount,
                        Container(height=responsive_size(8)),
                        edit_category,
                        Container(height=responsive_size(8)),
                        edit_type,
                        Container(height=responsive_size(8)),
                        edit_description,
                        Container(height=responsive_size(15)),
                        Row([save_btn, cancel_btn], alignment="center", spacing=responsive_size(10))
                    ]
                )
            ),
            Container(height=responsive_size(20)),
            
            # Список транзакций
            Container(
                bgcolor=FG,
                padding=responsive_size(15),
                border_radius=MOBILE_BORDER_RADIUS,
                content=Column(
                    controls=[
                        Text("Список транзакций:", 
                            size=responsive_size(16), 
                            weight=FontWeight.BOLD, 
                            color=FWG),
                        Container(height=responsive_size(10)),
                        Container(
                            content=transactions_col,
                            height=responsive_size(300),
                            bgcolor=BG,
                            padding=responsive_size(10),
                            border_radius=MOBILE_BORDER_RADIUS
                        )
                    ]
                )
            )
        ])
        
        return View(
            "/admin/transactions",
            [
                Container(
                    bgcolor=BG,
                    padding=padding.all(MOBILE_PADDING),
                    content=main_scroll_container
                )
            ],
            bgcolor=BG
        )
    
    def create_goals_view():
        """View для управления целями накоплений"""
        current_username = load_session()
        if not current_username:
            return Container(
                content=Text("Пожалуйста, авторизуйтесь", color="red", size=20),
                alignment=alignment.center,
                expand=True
            )
        
        user_id = get_current_user_id(current_username)
        
        # Контейнер для списка целей
        goals_list = Column(
            spacing=10,
            scroll="auto",
            expand=True
        )
        
        # Поля для создания/редактирования
        goal_name_field = TextField(
            hint_text="Название цели",
            label="Название",
            width=screen_width - 2*MOBILE_PADDING,
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        target_amount_field = TextField(
            hint_text="Целевая сумма",
            label="Целевая сумма (₸)",
            width=screen_width - 2*MOBILE_PADDING,
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            keyboard_type=KeyboardType.NUMBER,
            text_size=responsive_size(14)
        )
        
        deadline_field = TextField(
            hint_text="ДД.ММ.ГГГГ",
            label="Срок (необязательно)",
            width=screen_width - 2*MOBILE_PADDING,
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            text_size=responsive_size(14)
        )
        
        add_amount_field = TextField(
            hint_text="Сумма для добавления",
            label="Добавить сумму (₸)",
            width=screen_width - 2*MOBILE_PADDING,
            bgcolor=BG,
            color=FWG,
            border_color=PINK,
            keyboard_type=KeyboardType.NUMBER,
            text_size=responsive_size(14)
        )
        
        def refresh_goals():
            """Обновляет список целей"""
            goals_list.controls.clear()
            
            goals = get_savings_goals(user_id)
            
            if not goals:
                goals_list.controls.append(
                    Container(
                        padding=20,
                        content=Text(
                            "У вас пока нет целей накоплений.\nСоздайте первую цель!",
                            color=FWG,
                            size=16,
                            text_align="center"
                        ),
                        alignment=alignment.center
                    )
                )
            else:
                for goal in goals:
                    progress = float(goal['progress']) if goal['progress'] is not None else 0
                    remaining_days = ""
                    
                    if goal['deadline']:
                        try:
                            # ИСПРАВЛЕНИЕ: используем dt вместо datetime
                            if isinstance(goal['deadline'], str):
                                deadline = dt.strptime(goal['deadline'], '%Y-%m-%d')
                            else:
                                # Если это datetime.date или datetime.datetime
                                if isinstance(goal['deadline'], datetime_module.date):
                                    deadline = dt.combine(goal['deadline'], dt.min.time())
                                else:
                                    deadline = goal['deadline']
                            
                            remaining = (deadline - dt.now()).days
                            if remaining >= 0:
                                remaining_days = f"⏳ {remaining} дн."
                        except Exception as e:
                            print(f"Ошибка обработки даты: {e}")
                            pass
                    
                    goals_list.controls.append(
                        Container(
                            bgcolor=FG,
                            padding=15,
                            border_radius=MOBILE_BORDER_RADIUS,
                            margin=margin.only(bottom=10),
                            content=Column([
                                Row([
                                    Text(
                                        goal['goal_name'],
                                        size=16,
                                        weight=FontWeight.BOLD,
                                        color=FWG,
                                        expand=True
                                    ),
                                    Text(
                                        "✅" if goal['is_completed'] else "⏳",
                                        size=16
                                    )
                                ]),
                                
                                # Прогресс-бар
                                Container(
                                    content=Row([
                                        Container(
                                            # ИСПРАВЛЕНИЕ: progress теперь точно float
                                            width=(screen_width - 100) * (progress / 100),
                                            height=10,
                                            bgcolor=PINK,
                                            border_radius=5
                                        ),
                                        Container(
                                            expand=True,
                                            height=10,
                                            bgcolor=BG,
                                            border_radius=5
                                        )
                                    ]),
                                    margin=margin.only(top=5, bottom=5)
                                ),
                                
                                Row([
                                    Text(
                                        f"₸{float(goal['current_amount']):.2f} / ₸{float(goal['target_amount']):.2f}",
                                        size=14,
                                        color=FWG
                                    ),
                                    Text(
                                        f"{progress:.1f}%",
                                        size=14,
                                        color=PINK
                                    )
                                ]),
                                
                                Row([
                                    Text(
                                        remaining_days,
                                        size=12,
                                        color=FWG,
                                        expand=True
                                    ),
                                    Row([
                                        IconButton(
                                            icon=Icons.ADD,
                                            icon_color=FWG,
                                            icon_size=20,
                                            on_click=lambda e, g=goal: show_add_amount_dialog(g),
                                            tooltip="Добавить"
                                        ),
                                        IconButton(
                                            icon=Icons.EDIT,
                                            icon_color=FWG,
                                            icon_size=20,
                                            on_click=lambda e, g=goal: edit_goal_dialog(g),
                                            tooltip="Редактировать"
                                        ),
                                        IconButton(
                                            icon=Icons.DELETE,
                                            icon_color="red",
                                            icon_size=20,
                                            on_click=lambda e, g=goal: delete_goal_dialog(g),
                                            tooltip="Удалить"
                                        )
                                    ])
                                ])
                            ])
                        )
                    )
            
            # Статистика
            stats = get_savings_goal_progress(user_id)
            
            # ИСПРАВЛЕНИЕ: Преобразуем значения в float
            total_current = float(stats['total_current']) if stats['total_current'] is not None else 0
            total_target = float(stats['total_target']) if stats['total_target'] is not None else 0
            total_progress = float(stats['total_progress']) if stats['total_progress'] is not None else 0
            
            stats_text = f"""
        Всего целей: {stats['total_goals']}
        Выполнено: {stats['completed_goals']}
        Общий прогресс: {total_progress:.1f}%
        Накоплено: ₸{total_current:.2f} из ₸{total_target:.2f}
            """
            
            page.update()
        
        def create_goal_dialog(e=None):
            """Диалог создания цели"""
            goal_name_field.value = ""
            target_amount_field.value = ""
            deadline_field.value = ""
            
            def save_goal(e):
                if not goal_name_field.value:
                    show_alert(page, "Введите название цели", bgcolor="red")
                    return
                
                try:
                    target_amount = float(target_amount_field.value)
                    if target_amount <= 0:
                        show_alert(page, "Сумма должна быть больше 0", bgcolor="red")
                        return
                except:
                    show_alert(page, "Неверный формат суммы", bgcolor="red")
                    return
                
                deadline = None
                if deadline_field.value:
                    try:
                        deadline = dt.strptime(deadline_field.value, "%d.%m.%Y").strftime("%Y-%m-%d")
                    except:
                        show_alert(page, "Неверный формат даты. Используйте ДД.ММ.ГГГГ", bgcolor="red")
                        return
                
                goal_id = create_savings_goal(user_id, goal_name_field.value, target_amount, deadline)
                
                if goal_id:
                    show_alert(page, f"Цель '{goal_name_field.value}' создана!", bgcolor="green")
                    page.close(dialog)
                    refresh_goals()
                else:
                    show_alert(page, "Ошибка при создании цели", bgcolor="red")
            
            dialog = AlertDialog(
                modal=True,
                title=Text("Новая цель накопления", size=16),
                content=Column([
                    goal_name_field,
                    target_amount_field,
                    deadline_field
                ], tight=True),
                actions=[
                    TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                    # ИСПРАВЛЕНИЕ: используем style вместо bgcolor и color
                    TextButton(
                        "Создать", 
                        on_click=save_goal,
                        style=ButtonStyle(
                            color=Colors.WHITE,
                            bgcolor=PINK
                        )
                    )
                ]
            )
            page.open(dialog)
        
        def show_add_amount_dialog(goal):
            """Диалог добавления суммы к цели"""
            add_amount_field.value = ""
            
            def add_amount(e):
                try:
                    amount = float(add_amount_field.value)
                    if amount <= 0:
                        show_alert(page, "Сумма должна быть больше 0", bgcolor="red")
                        return
                    
                    # ИСПРАВЛЕНИЕ: используем 'goal_id' вместо 'id'
                    goal_id = int(goal['goal_id']) if isinstance(goal['goal_id'], (int, float)) else goal['goal_id']
                    
                    new_amount = add_to_savings_goal(goal_id, amount, user_id)
                    if new_amount is not None:
                        show_alert(page, f"Добавлено ₸{float(amount):.2f} к цели '{goal['goal_name']}'", bgcolor="green")
                        page.close(dialog)
                        refresh_goals()
                    else:
                        show_alert(page, "Ошибка при добавлении суммы", bgcolor="red")
                except ValueError:
                    show_alert(page, "Неверный формат суммы", bgcolor="red")
            
            dialog = AlertDialog(
                modal=True,
                title=Text(f"Добавить к цели: {goal['goal_name']}", size=16),
                content=add_amount_field,
                actions=[
                    TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                    TextButton(
                        "Добавить", 
                        on_click=add_amount,
                        style=ButtonStyle(
                            color=Colors.WHITE,
                            bgcolor=PINK
                        )
                    )
                ]
            )
            page.open(dialog)
        
        def edit_goal_dialog(goal):
            """Диалог редактирования цели"""
            goal_name_field.value = goal['goal_name']
            target_amount_field.value = str(goal['target_amount'])
            
            if goal['deadline']:
                try:
                    # ИСПРАВЛЕНИЕ: используем dt вместо datetime
                    if isinstance(goal['deadline'], str):
                        deadline_date = dt.strptime(goal['deadline'], '%Y-%m-%d').date()
                    elif hasattr(goal['deadline'], 'date'):  # для datetime.datetime или datetime.date
                        deadline_date = goal['deadline'].date() if hasattr(goal['deadline'], 'date') else goal['deadline']
                    else:
                        deadline_date = goal['deadline']
                    
                    deadline_field.value = deadline_date.strftime('%d.%m.%Y')
                except Exception as e:
                    print(f"Ошибка форматирования даты: {e}")
                    deadline_field.value = ""
            else:
                deadline_field.value = ""
            
            def save_edit(e):
                if not goal_name_field.value:
                    show_alert(page, "Введите название цели", bgcolor="red")
                    return
                
                try:
                    target_amount = float(target_amount_field.value)
                    if target_amount <= 0:
                        show_alert(page, "Сумма должна быть больше 0", bgcolor="red")
                        return
                except:
                    show_alert(page, "Неверный формат суммы", bgcolor="red")
                    return
                
                deadline = None
                if deadline_field.value:
                    try:
                        # ИСПРАВЛЕНИЕ: используем dt вместо datetime
                        deadline = dt.strptime(deadline_field.value, "%d.%m.%Y").strftime("%Y-%m-%d")
                    except:
                        show_alert(page, "Неверный формат даты. Используйте ДД.ММ.ГГГГ", bgcolor="red")
                        return
                
                success = update_savings_goal(
                    goal['goal_id'],
                    goal_name=goal_name_field.value,
                    target_amount=target_amount,
                    deadline=deadline,
                    user_id=user_id
                )
                
                if success:
                    show_alert(page, f"Цель '{goal_name_field.value}' обновлена!", bgcolor="green")
                    page.close(dialog)
                    refresh_goals()
                else:
                    show_alert(page, "Ошибка при обновлении цели", bgcolor="red")
            
            # ... остальной код без изменений
            
            dialog = AlertDialog(
                modal=True,
                title=Text("Редактировать цель", size=16),
                content=Column([
                    goal_name_field,
                    target_amount_field,
                    deadline_field
                ], tight=True),
                actions=[
                    TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                    TextButton(
                        "Сохранить", 
                        on_click=save_edit,
                        style=ButtonStyle(
                            color=Colors.WHITE,
                            bgcolor=PINK
                        )
                    )
                ]
            )
            page.open(dialog)
        
        def delete_goal_dialog(goal):
            """Диалог удаления цели"""
            def confirm_delete(e):
                # ИСПРАВЛЕНИЕ: используем 'goal_id' вместо 'id'
                success = delete_savings_goal(goal['goal_id'], user_id)  # <-- ИСПРАВЛЕНО ЗДЕСЬ
                if success:
                    show_alert(page, f"Цель '{goal['goal_name']}' удалена!", bgcolor="green")
                    page.close(dialog)
                    refresh_goals()
                else:
                    show_alert(page, "Ошибка при удалении цели", bgcolor="red")
            
            dialog = AlertDialog(
                modal=True,
                title=Text("Подтверждение удаления", size=16),
                content=Text(f"Вы уверены, что хотите удалить цель '{goal['goal_name']}'?"),
                actions=[
                    TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                    TextButton(
                        "Удалить", 
                        on_click=confirm_delete,
                        style=ButtonStyle(
                            color=Colors.WHITE,
                            bgcolor=Colors.RED
                        )
                    )
                ]
            )
            page.open(dialog)
        
        # Инициализация
        refresh_goals()
        
        # Основной контейнер
        return Container(
            width=screen_width,
            height=screen_height,
            bgcolor=BG,
            content=Column([
                # Заголовок
                Container(
                    bgcolor=FG,
                    padding=15,
                    content=Row([
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            on_click=lambda e: page.go("/")
                        ),
                        Text("Цели накоплений", 
                            size=18, 
                            weight=FontWeight.BOLD, 
                            color=FWG,
                            expand=True),
                        IconButton(
                            icon=Icons.ADD,
                            icon_color=PINK,
                            on_click=create_goal_dialog,
                            tooltip="Новая цель"
                        )
                    ])
                ),
                
                # Список целей
                Container(
                    content=goals_list,
                    padding=15,
                    expand=True
                )
            ])
        )

    # === СОЗДАНИЕ ТРАНЗАКЦИИ (АДАПТИВНАЯ) ===
    def create_transaction_view():
        amount_field = TextField(
            label="Сумма",
            hint_text="0.00",
            keyboard_type=KeyboardType.NUMBER,
            text_size=responsive_size(16),
            color=FWG,
            border_color=PINK,
            focused_border_color=PINK,
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            prefix_text="₸ ",
            width=screen_width - 2*MOBILE_PADDING,
            height=MOBILE_ELEMENT_HEIGHT
        )

        description_field = TextField(
            label="Описание",
            hint_text="Например: Покупка продуктов",
            color=FWG,
            border_color=PINK,
            focused_border_color=PINK,
            label_style=TextStyle(color=FWG, size=responsive_size(14)),
            width=screen_width - 2*MOBILE_PADDING,
            height=MOBILE_ELEMENT_HEIGHT
        )

        selected_category = Text("", visible=False)
        selected_type = Text("expense", visible=False)

        def select_category(category_name):
            selected_category.value = category_name
            category_button.content.value = f"Категория: {category_name}"
            page.views.pop()
            page.update()

        category_button = Container(
            width=screen_width - 2*MOBILE_PADDING,
            height=MOBILE_ELEMENT_HEIGHT,
            bgcolor=BG,
            border_radius=MOBILE_BORDER_RADIUS,
            border=border.all(1, PINK),
            padding=padding.symmetric(horizontal=MOBILE_PADDING, vertical=responsive_size(12)),
            content=Text("Выберите категорию", color=FWG, size=responsive_size(14)),
            on_click=lambda e: show_categories()
        )

        # Кнопки выбора типа транзакции (адаптивные)
        button_width = (screen_width - 4*MOBILE_PADDING - 10) / 2
        
        def select_expense(e):
            selected_type.value = "expense"
            expense_btn.bgcolor = PINK
            income_btn.bgcolor = BG
            page.update()

        def select_income(e):
            selected_type.value = "income"
            income_btn.bgcolor = PINK
            expense_btn.bgcolor = BG
            page.update()

        expense_btn = Container(
            width=button_width,
            height=MOBILE_ELEMENT_HEIGHT,
            bgcolor=PINK,
            border_radius=MOBILE_BORDER_RADIUS,
            border=border.all(1, PINK),
            padding=padding.all(responsive_size(12)),
            content=Row([
                Icon(Icons.ARROW_DOWNWARD, color=FWG, size=responsive_size(18)),
                Container(width=8),
                Text("Расход", color=FWG, size=responsive_size(12))
            ], alignment="center", spacing=8),
            on_click=select_expense
        )

        income_btn = Container(
            width=button_width,
            height=MOBILE_ELEMENT_HEIGHT,
            bgcolor=BG,
            border_radius=MOBILE_BORDER_RADIUS,
            border=border.all(1, PINK),
            padding=padding.all(responsive_size(12)),
            content=Row([
                Icon(Icons.ARROW_UPWARD, color=FWG, size=responsive_size(18)),
                Container(width=8),
                Text("Доход", color=FWG, size=responsive_size(12))
            ], alignment="center", spacing=8),
            on_click=select_income
        )

    # run_app.py - в функции create_transaction_view()
        def show_categories():
            category_buttons = []
            columns_count = 2  # На мобильных 2 колонки
            column_width = (screen_width - 3*MOBILE_PADDING) / columns_count
            
            # Определяем какие категории показывать в зависимости от выбранного типа
            current_categories = EXPENSE_CATEGORIES if selected_type.value == "expense" else INCOME_CATEGORIES
            
            for cat in current_categories:
                category_buttons.append(
                    Container(
                        width=column_width,
                        height=responsive_size(60),
                        content=Column([
                            Text(cat, 
                                color=FWG,
                                size=responsive_size(14), 
                                weight=FontWeight.BOLD, 
                                text_align="center"),
                        ], horizontal_alignment="center"),
                        padding=padding.all(responsive_size(12)),
                        bgcolor=FG,
                        border_radius=MOBILE_BORDER_RADIUS,
                        on_click=lambda e, c=cat: select_category(c)
                    )
                )
            
            # Создаем сетку категорий
            grid_items = []
            for i in range(0, len(category_buttons), columns_count):
                row_items = category_buttons[i:i+columns_count]
                grid_items.append(
                    Row(
                        controls=row_items,
                        spacing=MOBILE_PADDING,
                        wrap=True
                    )
                )
            
            # Создаем отдельную страницу для выбора категории
            categories_view = View(
                "/categories",
                [
                    Container(
                        bgcolor=BG,
                        width=screen_width,
                        height=screen_height,
                        padding=padding.all(MOBILE_PADDING),
                        content=Column(
                            [
                                Row([
                                    IconButton(
                                        icon=Icons.ARROW_BACK,
                                        icon_color=FWG,
                                        icon_size=responsive_size(24),
                                        on_click=lambda e: (page.views.pop(), page.update())  # ИСПРАВЛЕНО: Возвращаемся на страницу создания транзакции
                                    ),
                                    Text(f"Выберите категорию ({'расходов' if selected_type.value == 'expense' else 'доходов'})", 
                                        color=FWG, 
                                        size=responsive_size(18), 
                                        weight=FontWeight.BOLD)
                                ]),
                                Container(height=MOBILE_PADDING*2),
                                Container(
                                    content=Column(
                                        controls=grid_items,
                                        spacing=MOBILE_PADDING,
                                        height=screen_height - responsive_size(150),
                                        scroll="auto"  # ИСПРАВЛЕНО: Добавляем скроллинг
                                )
                                )
                            ],
                            spacing=0
                        )
                    )
                ],
                bgcolor=BG
            )
            
            page.views.append(categories_view)
            page.update()

        def save_transaction(_e=None):
            try:
                amount = float(amount_field.value)
                description = description_field.value or "Без описания"
                category = selected_category.value
                
                if not category:
                    show_alert(page, "Пожалуйста, выберите категорию", bgcolor="red")
                    return
                
                current_username = load_session()
                if not current_username:
                    show_alert(page, "Ошибка: Пользователь не авторизован", bgcolor="red")
                    page.go('/login')
                    return
                
                user_id = get_current_user_id(current_username)
                if user_id is None:
                    show_alert(page, "Ошибка: Не удалось найти ID пользователя", bgcolor="red")
                    return
                
                transaction = {
                    'category': category,
                    'amount': amount,
                    'description': description,
                    'type': selected_type.value,
                    'date': dt.now().strftime("%d.%m.%Y %H:%M")
                }

                transaction_id = db_insert_transaction(transaction, user_id)
                if 'notification_manager' in update_callbacks:
                    update_callbacks['notification_manager'].show_push_notification(
                        "Новая транзакция",
                        f"{'Расход' if selected_type.value == 'expense' else 'Доход'}: ₸{amount:.2f}",
                        'transaction',
                        {'route': '/'}
                    )
                
                # Создаем уведомление в базе данных
                from db import create_transaction_notification
                create_transaction_notification(
                    user_id, 
                    {'id': transaction_id, **transaction}
                )
                
                # Обновляем счетчик уведомлений если есть функция обновления
                if 'update_notification_bell' in update_callbacks:
                    update_callbacks['update_notification_bell']()
                
                show_alert(page, "Транзакция успешно добавлена!", bgcolor="green")
                
                if 'refresh_home_ui' in update_callbacks:
                    update_callbacks['refresh_home_ui']()
                
                page.go('/')
            except ValueError:
                show_alert(page, "Неверный формат суммы", bgcolor="red")

        return Container(
            bgcolor=BG,
            width=screen_width,
            height=screen_height,
            padding=padding.all(MOBILE_PADDING),
            content=Column(
                [
                    Row([
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=responsive_size(24),
                            on_click=lambda e: page.go('/')
                        ),
                        Text("Новая транзакция", 
                             color=FWG, 
                             size=responsive_size(18), 
                             weight=FontWeight.BOLD)
                    ]),
                    Container(height=MOBILE_PADDING*2),
                    Row([expense_btn, income_btn], 
                        alignment="spaceBetween",
                        spacing=10),
                    Container(height=MOBILE_PADDING*2),
                    amount_field,
                    Container(height=MOBILE_PADDING*2),
                    description_field,
                    Container(height=MOBILE_PADDING*2),
                    category_button,
                    Container(height=MOBILE_PADDING*3),
                    ElevatedButton(
                        "Сохранить транзакцию",
                        bgcolor=PINK,
                        color=FWG,
                        width=screen_width - 2*MOBILE_PADDING,
                        height=MOBILE_ELEMENT_HEIGHT,
                        on_click=save_transaction
                    )
                ],
                scroll="auto"
            )
        )

    # Замените функцию ai_view() в run_app.py на эту упрощенную версию

    def ai_view():
        """Упрощенный чат с AI-советником без сессий"""
        from db import get_current_user_id, get_chat_history, save_chat_message, delete_chat_message
        
        current_username = load_session()
        user_id = get_current_user_id(current_username) if current_username else None
        
        if not user_id:
            return Container(
                content=Text("Пожалуйста, авторизуйтесь", color="red", size=20),
                alignment=alignment.center,
                expand=True
            )
        
        # Контейнер сообщений
        messages_container = ListView(
            spacing=10,
            padding=padding.only(left=15, right=15, top=15, bottom=80),
            auto_scroll=True,
            expand=True
        )
        
        # Текстовое поле для ввода
        bottom_sheet_text = TextField(
            hint_text="Напишите сообщение...",
            multiline=True,
            min_lines=1,
            max_lines=4,
            filled=True,
            fill_color=FG,
            color=FWG,
            border_color=PINK,
            focused_border_color=PINK,
            text_size=14,
            expand=True
        )
        
        # Bottom sheet для ввода
        bottom_sheet_content = Container(
            width=screen_width,
            padding=padding.symmetric(horizontal=15, vertical=10),
            content=Column([
                Row([
                    Text("Новое сообщение", 
                        size=16, 
                        weight=FontWeight.BOLD, 
                        color=FWG,
                        expand=True),
                    IconButton(
                        icon=Icons.CLOSE,
                        icon_color=FWG,
                        on_click=lambda e: close_bottom_sheet()
                    )
                ]),
                Container(height=10),
                bottom_sheet_text,
                Container(height=10),
                Row([
                    ElevatedButton(
                        "Отмена",
                        on_click=lambda e: close_bottom_sheet(),
                        bgcolor=BG,
                        color=FWG
                    ),
                    Container(width=10),
                    ElevatedButton(
                        "Отправить",
                        on_click=lambda e: send_message_from_bottom_sheet(),
                        bgcolor=PINK,
                        color="white",
                        expand=True
                    )
                ])
            ])
        )
        
        bottom_sheet = BottomSheet(
            content=bottom_sheet_content,
            open=False,
            on_dismiss=lambda e: close_bottom_sheet()
        )
        
        # Кнопка открытия ввода
        open_input_button = Container(
            width=screen_width,
            height=50,
            bgcolor=FG,
            padding=padding.symmetric(horizontal=15, vertical=10),
            border_radius=border_radius.only(top_left=20, top_right=20),
            content=Row([
                Container(
                    content=Text(
                        "Нажмите, чтобы написать сообщение...",
                        color=FWG,
                        size=14,
                        opacity=0.7
                    ),
                    expand=True,
                    bgcolor=BG,
                    border_radius=10,
                    padding=padding.symmetric(horizontal=15, vertical=15),
                    on_click=lambda e: open_bottom_sheet()
                ),
                Container(
                    content=IconButton(
                        icon=Icons.SEND,
                        icon_color=PINK,
                        icon_size=24,
                        on_click=lambda e: open_bottom_sheet(),
                        tooltip="Написать сообщение"
                    ),
                    padding=padding.only(left=10)
                )
            ],
            vertical_alignment="center")
        )
        
        # Индикатор загрузки
        loading_indicator = ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            color=PINK,
            visible=False
        )
        
        def open_bottom_sheet():
            """Открывает bottom-sheet"""
            bottom_sheet.open = True
            bottom_sheet_text.focus()
            page.update()
        
        def close_bottom_sheet():
            """Закрывает bottom-sheet"""
            bottom_sheet.open = False
            page.update()
        
        def scroll_to_bottom(animate=True):
            """Прокручивает чат вниз"""
            if messages_container and len(messages_container.controls) > 0:
                try:
                    messages_container.scroll_to(
                        offset=-1,
                        duration=300 if animate else 0
                    )
                except:
                    pass
        
        def show_clear_all_dialog():
            """Диалог очистки чата"""
            dialog = AlertDialog(
                modal=True,
                title=Text("Очистить весь чат?", size=responsive_size(16)),
                content=Text(
                    "Все сообщения будут удалены безвозвратно.\n\nПродолжить?",
                    size=responsive_size(14)
                ),
                actions=[
                    TextButton("Отмена", 
                        on_click=lambda e: page.close(dialog)),
                    TextButton(
                        "Очистить все",
                        on_click=lambda e: confirm_clear_all(dialog),
                        style=ButtonStyle(color=Colors.RED)
                    ),
                ],
                actions_alignment=MainAxisAlignment.END,
            )
            page.open(dialog)
        
        def confirm_clear_all(dlg):
            """Подтверждение очистки"""
            page.close(dlg)
            
            from db import clear_chat_history
            deleted_count = clear_chat_history(user_id)
            if deleted_count > 0:
                load_chat_history()
                
                page.snack_bar = SnackBar(
                    Text(f"Удалено {deleted_count} сообщений", color="white"),
                    bgcolor="green"
                )
                page.snack_bar.open = True
                page.update()
        
        def create_message_bubble(message_data, is_user=True):
            """Создает пузырь сообщения"""
            message_id = message_data.get('id')
            text = message_data.get('text', '')
            
            bubble_color = PINK if is_user else FG
            alignment_pos = alignment.center_right if is_user else alignment.center_left
            
            message_container = Container(
                content=Row(
                    controls=[
                        Container(
                            content=Text(
                                text,
                                color=FWG,
                                size=14,
                                selectable=True
                            ),
                            padding=12,
                            bgcolor=bubble_color,
                            border_radius=15,
                            expand=True
                        ),
                        Container(
                            content=IconButton(
                                icon=Icons.DELETE_OUTLINE,
                                icon_color=Colors.RED_400,
                                icon_size=20,
                                on_click=lambda e: on_delete_message(e),
                                tooltip="Удалить сообщение",
                                padding=padding.all(5)
                            ),
                            visible=is_user,
                        ) if is_user else Container(width=0, height=0)
                    ],
                    spacing=5,
                    vertical_alignment="center"
                ),
                alignment=alignment_pos,
                margin=margin.only(
                    left=50 if not is_user else 0,
                    right=50 if is_user else 0,
                    bottom=10
                )
            )
            
            def on_delete_message(e):
                """Удаление сообщения"""
                dialog = AlertDialog(
                    modal=True,
                    title=Text("Подтверждение удаления", size=responsive_size(16)),
                    content=Text(
                        "Вы уверены, что хотите удалить это сообщение?",
                        size=responsive_size(14)
                    ),
                    actions=[
                        TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                        TextButton(
                            "Удалить",
                            on_click=lambda e: confirm_delete(message_id, dialog),
                            style=ButtonStyle(color=Colors.RED)
                        ),
                    ],
                    actions_alignment=MainAxisAlignment.END,
                )
                page.open(dialog)
            
            def confirm_delete(msg_id, dlg):
                """Подтверждение удаления"""
                page.close(dlg)
                
                if delete_chat_message(msg_id):
                    load_chat_history()
                    page.snack_bar = SnackBar(
                        content=Text("Сообщение удалено", color="white"),
                        bgcolor="green"
                    )
                    page.snack_bar.open = True
                    page.update()
            
            return message_container
        
        def load_chat_history(e=None):
            """Загружает историю сообщений"""
            if messages_container:
                messages_container.controls.clear()
            
            try:
                chat_history = get_chat_history(user_id, limit=50)
                
                if messages_container:
                    if not chat_history:
                        welcome_msg = "👋 Привет! Я ваш финансовый помощник.\n\nНажмите на поле ввода ниже, чтобы начать диалог."
                        messages_container.controls.append(
                            create_message_bubble(
                                {'id': None, 'text': welcome_msg},
                                False
                            )
                        )
                    else:
                        for msg in chat_history:
                            messages_container.controls.append(
                                create_message_bubble(
                                    msg,
                                    is_user=(msg['type'] == 'user')
                                )
                            )
                    
                    scroll_to_bottom(False)
                        
            except Exception as e:
                print(f"Ошибка загрузки истории: {e}")
        
        def send_message_from_bottom_sheet():
            """Отправляет сообщение"""
            user_message = bottom_sheet_text.value
            
            if not user_message or not user_message.strip():
                return
            
            user_message = user_message.strip()
            bottom_sheet_text.value = ""
            close_bottom_sheet()
            
            # Показываем сообщение пользователя
            if messages_container:
                msg_id = save_chat_message(user_id, None, user_message, 'user')
                
                messages_container.controls.append(
                    create_message_bubble(
                        {'id': msg_id, 'text': user_message},
                        True
                    )
                )
                
                scroll_to_bottom(True)
            
            # Показываем индикатор загрузки
            loading_indicator.visible = True
            page.update()
            
            # Обработка в отдельном потоке
            def process_response():
                try:
                    response = ai_answer(user_message, user_id)
                    response_id = save_chat_message(user_id, None, response, 'ai')
                    
                    if messages_container:
                        messages_container.controls.append(
                            create_message_bubble(
                                {'id': response_id, 'text': response},
                                False
                            )
                        )
                        
                        scroll_to_bottom(True)
                    
                except Exception as e:
                    print(f"Ошибка: {e}")
                finally:
                    loading_indicator.visible = False
                    page.update()
            
            import threading
            threading.Thread(target=process_response, daemon=True).start()
        
        # Загружаем историю при старте
        load_chat_history()
        
        # Основная область чата
        chat_area = Container(
            expand=True,
            content=Column([
                # Заголовок
                Container(
                    bgcolor=FG,
                    padding=15,
                    content=Row([
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            on_click=lambda e: page.go("/")
                        ),
                        Text("AI-Советник", size=18, weight=FontWeight.BOLD, color=FWG, expand=True),
                        IconButton(
                            icon=Icons.DELETE_SWEEP,
                            icon_color=FWG,
                            tooltip="Очистить чат",
                            on_click=lambda e: show_clear_all_dialog()
                        ),
                    ])
                ),
                
                # Сообщения
                Container(
                    content=messages_container,
                    expand=True,
                    bgcolor=BG
                ),
            ])
        )
        
        # Финальный контейнер
        main_container = Container(
            width=screen_width,
            height=screen_height,
            bgcolor=BG,
            content=Stack([
                # Основная область
                Container(
                    width=screen_width,
                    height=screen_height,
                    content=chat_area
                ),
                
                # Кнопка ввода (фиксированная внизу)
                Container(
                    content=open_input_button,
                    bottom=0,
                    left=0,
                    right=0
                ),
                
                # Bottom-sheet
                bottom_sheet
            ])
        )
        
        return main_container

    # === КАТЕГОРИЯ ТРАНЗАКЦИЙ (АДАПТИВНАЯ) ===
    def create_category_view(category_name):
        current_username = load_session()
        
        if not current_username:
            return Container(
                bgcolor=BG,
                width=screen_width,
                height=screen_height,
                padding=padding.all(MOBILE_PADDING),
                content=Column([
                    Row([
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=responsive_size(24),
                            on_click=lambda e: page.go('/')
                        ),
                        Text("Ошибка", color=FWG, size=responsive_size(18), weight=FontWeight.BOLD)
                    ]),
                    Container(height=100),
                    Text("Пожалуйста, авторизуйтесь", 
                         color=FWG, 
                         size=responsive_size(16), 
                         text_align="center")
                ])
            )
        
        filtered = db_fetch_transactions_by_category(category_name, current_username)
        
        category_transactions = Column(scroll="auto", spacing=responsive_size(10))
        for t in filtered:
            category_transactions.controls.append(
                Container(
                    content=Column([
                        Text(f"{t.get('description', 'Без описания')}", 
                             color=FWG, 
                             weight=FontWeight.BOLD, 
                             size=responsive_size(14)),
                        Text(f"₸{t.get('amount', 0)}", 
                             color=PINK, 
                             size=responsive_size(16)),
                        Text(f"{t.get('date', 'Неизвестно')}", 
                             color=FWG, 
                             size=responsive_size(12))
                    ]),
                    bgcolor=FG,
                    padding=padding.all(responsive_size(12)),
                    border_radius=MOBILE_BORDER_RADIUS
                )
            )
        
        return Container(
            bgcolor=BG,
            width=screen_width,
            height=screen_height,
            padding=padding.all(MOBILE_PADDING),
            content=Column(
                [
                    Row([
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=responsive_size(24),
                            on_click=lambda e: page.go('/')
                        ),
                        Text(category_name, 
                             color=FWG, 
                             size=responsive_size(18), 
                             weight=FontWeight.BOLD)
                    ]),
                    Container(height=MOBILE_PADDING),
                    Text(f"Всего транзакций: {len(filtered)}", 
                         color=FWG, 
                         size=responsive_size(14)),
                    Container(height=MOBILE_PADDING*2),
                    Container(
                        height=screen_height - 200,
                        content=category_transactions
                    )
                ],
                scroll="auto"
            )
        )

    # === ЛЕВОЕ МЕНЮ (АДАПТИВНОЕ) ===
    def menu_logout(e=None):
        clear_session()
        greeting_text.value = "Привет, пользователь"
        page.go('/login')
        page.update()

    def get_auth_menu_button():
        """Возвращает кнопку входа или выхода для меню"""
        if load_session():
            return Container(
                on_click=lambda e: (restore(e), menu_logout()),
                padding=padding.all(responsive_size(8)),
                content=Row(controls=[
                    Icon(Icons.LOGOUT, color=FWG, size=responsive_size(20)),
                    Container(width=10),
                    Text("Выход", 
                         size=responsive_size(16), 
                         weight=FontWeight.W_300, 
                         color=FWG)
                ])
            )
        else:
            return Container(
                on_click=lambda e: (restore(e), page.go("/login")),
                padding=padding.all(responsive_size(8)),
                content=Row(controls=[
                    Icon(Icons.LOGIN, color=FWG, size=responsive_size(20)),
                    Container(width=10),
                    Text("Вход", 
                         size=responsive_size(16), 
                         weight=FontWeight.W_300, 
                         color=FWG)
                ])
            )

    def create_left_menu():
        """Создаёт адаптивное левое меню со скроллингом"""
        current_username = load_session()
        user_role = None
        
        if current_username:
            user_role = get_user_role(current_username)
        
        # Создаем контейнер с фиксированной высотой для скроллинга
        scroll_container = Container(
            height=screen_height - MOBILE_PADDING*4,  # Оставляем место для верхних и нижних отступов
            content=Column(
                controls=[],
                scroll="auto",  # Включаем вертикальный скроллинг
                spacing=0
            )
        )
        
        # Добавляем элементы в скроллируемую колонку
        scroll_content = [
            # Верхняя стрелка
            Container(
                content=Row(
                    alignment="end",
                    controls=[Container(
                        border_radius=MOBILE_BORDER_RADIUS,
                        padding=padding.all(responsive_size(10)),
                        width=responsive_size(45),
                        height=responsive_size(45),
                        border=border.all(color='white', width=1),
                        on_click=lambda e: restore(e),
                        content=Icon(Icons.ARROW_FORWARD_IOS, 
                                    color=FWG, 
                                    size=responsive_size(20))
                    )]
                ),
                padding=padding.only(bottom=MOBILE_PADDING*2)
            ),
            
            # Аватар
            Container(
                alignment=alignment.center,
                padding=padding.only(bottom=MOBILE_PADDING)
            ),
            
            # Заголовок
            Container(
                content=Text("Меню", 
                        color=FWG, 
                        size=responsive_size(22), 
                        weight=FontWeight.BOLD,
                        text_align="center"),
                padding=padding.only(bottom=MOBILE_PADDING*2)
            ),
        ]
        
        # Основные элементы меню
        main_menu_items = [
            ("Главная", Icons.HOME, "/"),
            ("Статистика", Icons.PIE_CHART_OUTLINE, "/statistics"),
            ("Цели накоплений", Icons.FLAG_OUTLINED, "/goals"),
            ("Настройки", Icons.SETTINGS_OUTLINED, "/settings"),
            ("AI-Советник", Icons.SMART_TOY_OUTLINED, "/ai"),
        ]
        
        for item_text, item_icon, item_route in main_menu_items:
            scroll_content.append(
                Container(
                    on_click=lambda e, r=item_route: (restore(e), page.go(r)),
                    padding=padding.symmetric(vertical=responsive_size(8), horizontal=responsive_size(12)),
                    content=Row(controls=[
                        Icon(item_icon, color=FWG, size=responsive_size(20)),
                        Container(width=responsive_size(12)),
                        Text(item_text, 
                            size=responsive_size(16), 
                            weight=FontWeight.W_300, 
                            color=FWG)
                    ])
                )
            )
        
        # Админские элементы (если есть)
        if user_role == "admin":
            scroll_content.append(
                Container(
                    content=Divider(height=1, color=FG),
                    padding=padding.symmetric(vertical=MOBILE_PADDING*2)
                )
            )
            
            scroll_content.append(
                Container(
                    content=Text("Администратор", 
                            color=PINK, 
                            size=responsive_size(12),
                            weight=FontWeight.BOLD),
                    padding=padding.only(bottom=MOBILE_PADDING)
                )
            )
            
            admin_items = [
                ("Админ-панель", Icons.ADMIN_PANEL_SETTINGS, "/admin"),
                ("Транзакции", Icons.LIST_ALT, "/admin/transactions?from=menu"),
            ]
            
            for item_text, item_icon, item_route in admin_items:
                scroll_content.append(
                    Container(
                        on_click=lambda e, r=item_route: (restore(e), page.go(r)),
                        padding=padding.symmetric(vertical=responsive_size(8), horizontal=responsive_size(12)),
                        content=Row(controls=[
                            Icon(item_icon, color=PINK, size=responsive_size(20)),
                            Container(width=responsive_size(12)),
                            Text(item_text, 
                                size=responsive_size(16), 
                                weight=FontWeight.W_300, 
                                color=FWG)
                        ])
                    )
                )
        
        # Добавляем пространство перед кнопкой входа/выхода
        scroll_content.append(Container(height=MOBILE_PADDING*3))
        
        # Кнопка входа/выхода
        scroll_content.append(
            Container(
                content=get_auth_menu_button(),
                alignment=alignment.center,
                padding=padding.only(bottom=MOBILE_PADDING*2)
            )
        )
        
        # Версия приложения в самом низу
        scroll_content.append(
            Container(
                content=Text("Версия 1.0.0", 
                        size=responsive_size(11), 
                        weight=FontWeight.W_300, 
                        color=FWG,
                        text_align="center"),
                padding=padding.only(bottom=MOBILE_PADDING)
            )
        )
        
        # Добавляем все элементы в скроллируемый контейнер
        scroll_container.content.controls = scroll_content

        return Container(
            width=screen_width,
            height=screen_height,
            bgcolor=BG,
            border_radius=0,
            padding=padding.only(
                left=MOBILE_PADDING*2, 
                top=MOBILE_PADDING*2, 
                right=responsive_size(100),
                bottom=MOBILE_PADDING*2
            ),
            content=scroll_container
        )

    # Использование
    page_1 = create_left_menu()

    # === ГЛАВНОЕ СОДЕРЖИМОЕ (АДАПТИВНОЕ) ===
    main_page_container.content = Column(controls=[home_content], spacing=0)
    main_page_container.width = screen_width
    main_page_container.height = screen_height
    main_page_container.bgcolor = FG
    main_page_container.border_radius = 0
    main_page_container.animate = Animation(600, AnimationCurve.DECELERATE)
    main_page_container.animate_scale = Animation(400, curve='decelerate')
    main_page_container.padding = padding.only(
        top=MOBILE_PADDING*3, 
        right=MOBILE_PADDING, 
        left=MOBILE_PADDING, 
        bottom=MOBILE_PADDING
    )

    page_2 = Row(alignment="end", controls=[main_page_container])
    container = Container(
        width=screen_width, 
        height=screen_height, 
        bgcolor=BG, 
        border_radius=0, 
        content=Stack(controls=[page_1, page_2])
    )

    # === РОУТИНГ ===
    def route_change(route):
            page.views.clear()
            current_route = page.route
            current_username = safe_username()
            nonlocal update_callbacks

            if current_route == '/':
                if current_username:
                    user_id = get_current_user_id(current_username)

                    if user_id is not None:
                        greeting_text.value = f"Привет, {current_username}"
                        update_callbacks = {
                            "db_fetch_transactions": db_fetch_user_transactions,
                            "username": current_username,
                            "greeting_text": greeting_text,
                            "load_session": load_session,
                            "shrink": shrink,
                            "restore": restore,
                            "screen_width": screen_width,
                            "screen_height": screen_height,
                            "mobile_padding": MOBILE_PADDING
                        }
                        
                        home_content, refresh_home_ui = create_home_view(page, update_callbacks)
                        
                        update_callbacks['refresh_home_ui'] = refresh_home_ui
                        update_callbacks['transactions'] = refresh_home_ui 
                        update_callbacks['categories'] = refresh_home_ui
                        
                        main_page_container.content = Column(controls=[home_content], spacing=0)
                    else:
                        clear_session()
                        page.go('/login')
                        show_alert(page, "Ошибка: Не удалось найти ID пользователя. Пожалуйста, войдите снова.", bgcolor='red')
                else:
                    page.go('/login')
                
                if 'refresh_home_ui' in update_callbacks:
                    update_callbacks['refresh_home_ui']()

                page.views.append(View("/", [container], bgcolor=BG))
                
            elif current_route == '/login':
                page.views.append(create_login_view(page))
            elif current_route == '/register':
                page.views.append(create_register_view(page, greeting_text))
            elif current_route == '/create_transaction':
                page.views.append(View("/create_transaction", [create_transaction_view()], bgcolor=BG))
            elif current_route.startswith("/admin/transactions"):
                from_menu = "?from=menu" in current_route
                page.views.append(create_admin_transactions_view(page, update_callbacks, from_menu))
            elif current_route == '/statistics':
                page.views.append(View("/statistics", [create_statistics_view(page)], bgcolor=BG))
            elif current_route == '/goals':
                page.views.append(View("/goals", [create_goals_view()], bgcolor=BG))
            elif current_route == '/settings':
                page.views.append(View("/settings", [
                    create_settings_view(
                        page, 
                        update_callbacks.get('transactions', lambda: None),
                        update_callbacks.get('categories', lambda: None)
                    )
                ], bgcolor=BG))
            elif current_route == '/ai':
                page.views.append(View("/ai", [ai_view()], bgcolor=BG))
            elif current_route == "/admin":
                page.views.append(create_admin_view(page, update_callbacks))
            elif current_route == "/search":
                page.views.append(create_search_view(page))
            elif current_route == "/notifications":
                current_username = load_session()
                if current_username:
                    user_id = get_current_user_id(current_username)
                    if user_id is not None:
                        page.views.append(
                        View("/notifications", [create_notifications_view(page, user_id)], bgcolor=BG)
                    )
                    else:
                        page.go('/')
                        show_alert(page, "Ошибка: Не удалось найти ID пользователя.", bgcolor='red')
                else:
                    page.go('/login')
                    show_alert(page, "Пожалуйста, авторизуйтесь.", bgcolor='red')
                
            elif current_route.startswith('/category/'):
                category = current_route.replace('/category/', '')
                page.views.append(View(current_route, [create_category_view(category)], bgcolor=BG))

            # Обновляем меню
            nonlocal page_1
            page_1 = create_left_menu()
            container.content = Stack(controls=[page_1, page_2])
            page.update()

    page.on_route_change = route_change
    page.add(container)

    # Стартовая навигация
    if load_session():
        page.go('/')
    else:
        page.go('/login')
    page.update()

if __name__ == "__main__":
    app(target=main)