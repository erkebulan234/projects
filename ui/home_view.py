from flet import *
from .constants import BG, FWG, PINK, EXPENSE_CATEGORIES, INCOME_CATEGORIES, responsive_size, MOBILE_PADDING,  MOBILE_BORDER_RADIUS, INCOME_COLOR, EXPENSE_COLOR
from db import db_get_category_stats, db_delete_transaction
from helpers import  show_alert

def create_home_view(page: Page, callbacks):
    """Создаёт адаптивный главный view приложения для мобильных"""
    fetch_transactions = callbacks.get("db_fetch_transactions")
    username = callbacks.get("username")
    load_session_func = callbacks.get("load_session")
    greeting_text = callbacks.get("greeting_text")
    screen_width = callbacks.get("screen_width", 400)
    screen_height = callbacks.get("screen_height", 800)
    
    # Адаптивные размеры
    mobile_padding = MOBILE_PADDING
    category_card_width = (screen_width - 3*mobile_padding) / 2
    
    # Создаем контейнер для ВСЕХ категорий
    all_categories_card = Row(
        scroll="auto", 
        spacing=responsive_size(10),
        height=responsive_size(140)
    )
    
    # Список транзакций - создаем контейнер который будем обновлять
    transactions_container = Container(
        height=screen_height - responsive_size(450),
        expand=True
    )
    
    def create_swipeable_transaction_card(trans):
        """Создает карточку транзакции с кнопкой удаления"""
        trans_id = trans["id"]
        trans_desc = trans.get("description", "Без описания")

        def on_delete_click(e):
            """Обработчик клика на кнопку удаления"""
            
            # Создаем диалог сначала, чтобы иметь к нему доступ в функциях
            dialog = None
            
            def confirm_delete(e):
                """Подтверждение удаления"""
                print(f"✅ Подтверждено удаление транзакции {trans_id}")
                # Закрываем диалог
                page.close(dialog)
                
                # Удаляем транзакцию
                if db_delete_transaction(trans_id, username):
                    
                    # ВАЖНО: Обновляем UI принудительно
                    update_transactions_list()
                    update_categories()
                    page.update()
                else:
                    print(f"❌ Ошибка при удалении транзакции из БД")
                    show_alert(page, "Ошибка при удалении транзакции", bgcolor="red")
            
            def cancel_delete(e):
                """Отмена удаления"""
                print(f"❌ Отменено удаление транзакции {trans_id}")
                page.close(dialog)
            
            # Создаем и показываем диалог
            try:
                dialog = AlertDialog(
                    modal=True,
                    title=Text("Подтверждение удаления", size=responsive_size(16)),
                    content=Text(
                        f"Вы уверены, что хотите удалить транзакцию:\n\"{trans_desc}\"?", 
                        size=responsive_size(14)
                    ),
                    actions=[
                        TextButton("Отмена", on_click=cancel_delete),
                        TextButton(
                            "Удалить", 
                            on_click=confirm_delete, 
                            style=ButtonStyle(color=Colors.RED)
                        ),
                    ],
                    actions_alignment=MainAxisAlignment.END,
                )
                
                page.open(dialog)
                
            except Exception as ex:
                print(f"❌ Ошибка при создании диалога: {ex}")
                import traceback
                traceback.print_exc()

        # Создаем карточку с кнопкой удаления
        card_content = Container(
            height=responsive_size(70),
            bgcolor=BG,
            border_radius=MOBILE_BORDER_RADIUS,
            padding=padding.all(responsive_size(12)),
            margin=margin.only(bottom=responsive_size(8)),
            content=Row(
                controls=[
                    Icon(
                        Icons.ARROW_DOWNWARD if trans["type"] == "expense" else Icons.ARROW_UPWARD,
                        color=EXPENSE_COLOR if trans["type"] == "expense" else INCOME_COLOR,
                    ),
                    Container(width=10),
                    Column(
                        expand=True,
                        controls=[
                            Text(trans_desc, color=FWG, weight=FontWeight.BOLD, size=responsive_size(14)),
                            Text(trans["category"], size=responsive_size(11), opacity=0.7, color=FWG),
                        ],
                    ),
                    Text(f"₸{trans['amount']}", color=PINK, size=responsive_size(14)),
                    Container(width=5),
                    IconButton(
                        icon=Icons.DELETE_OUTLINE,
                        icon_color=Colors.RED_400,
                        icon_size=responsive_size(20),
                        on_click=on_delete_click,
                        tooltip="Удалить",
                        padding=padding.all(5)
                    )
                ]
            )
        )
        
        return card_content
    
    def update_transactions_list():
        """Обновляет список транзакций на главной"""
        
        # Создаем новый Column каждый раз
        new_transactions = Column(
            spacing=responsive_size(8),
            scroll=ScrollMode.AUTO,
            auto_scroll=False,
        )

        if not username:
            new_transactions.controls.append(
                Container(
                    padding=padding.all(responsive_size(20)),
                    content=Text("Нет транзакций для отображения", 
                                color=FWG, 
                                size=responsive_size(14), 
                                text_align="center")
                )
            )
        else:
            transactions_data = fetch_transactions(username)
            
            if not transactions_data:
                new_transactions.controls.append(
                    Container(
                        padding=padding.all(responsive_size(20)),
                        content=Text("Добавьте первую транзакцию", 
                                    color=FWG, 
                                    size=responsive_size(14), 
                                    text_align="center")
                    )
                )
            else:
                # Создаем карточки транзакций
                for trans in transactions_data[:8]:
                    try:
                        card = create_swipeable_transaction_card(trans)
                        new_transactions.controls.append(card)
                    except Exception as e:
                        print(f"❌ ERROR при создании карточки транзакции: {e}")
                        new_transactions.controls.append(
                            Container(
                                height=responsive_size(70),
                                bgcolor=BG,
                                border_radius=MOBILE_BORDER_RADIUS,
                                padding=padding.all(responsive_size(12)),
                                margin=margin.only(bottom=responsive_size(8)),
                                content=Text(f"Ошибка отображения транзакции", color=FWG)
                            )
                        )
        
        # Обновляем контейнер с новым содержимым
        transactions_container.content = new_transactions

    def show_category_transactions(category):
        def handler(e):
            page.go(f"/category/{category}")
        return handler
    
    def update_categories():
        """Обновляет список всех категорий"""
        current_username = load_session_func()
        if not current_username:
            category_stats = {}
        else:
            category_stats = db_get_category_stats(current_username) 
            
        all_categories_card.controls.clear()
        
        all_categories = EXPENSE_CATEGORIES + INCOME_CATEGORIES
        
        for category in all_categories:
            count = category_stats.get(category, 0)
            
            if category in EXPENSE_CATEGORIES:
                category_color = EXPENSE_COLOR
            else:
                category_color = INCOME_COLOR
            
            all_categories_card.controls.append(
                Container(
                    border_radius=MOBILE_BORDER_RADIUS,
                    bgcolor=BG,
                    height=responsive_size(100),
                    width=category_card_width,
                    padding=padding.all(responsive_size(10)),
                    on_click=show_category_transactions(category),
                    content=Column(
                        controls=[
                            Text(f"{count} транз.", color=FWG, size=responsive_size(10)),
                            Container(height=responsive_size(3)),
                            Text(category, 
                                color=category_color,
                                weight=FontWeight.BOLD, 
                                size=responsive_size(12),
                                text_align="center")
                        ],
                        horizontal_alignment="center"
                    )
                )
            )

    def refresh_home_ui():
        """Обновляет список транзакций и статистику категорий на главной"""
        update_categories()
        update_transactions_list()
        
        if greeting_text and load_session_func:
            current_username = load_session_func()
            greeting_text.value = f"Привет, {current_username or 'Пользователь'}" 
        
        page.update()
        return True
    
    # Сохраняем коллбеки для обновления
    callbacks['transactions'] = update_transactions_list
    callbacks['categories'] = update_categories
    callbacks['refresh_home_ui'] = refresh_home_ui
    
    # Начальное обновление
    refresh_home_ui()
    
    # Создаем FloatingActionButton
    fab = FloatingActionButton(
        icon=Icons.ADD,
        bgcolor=PINK,
        on_click=lambda _: page.go("/create_transaction"),
        width=responsive_size(56),
        height=responsive_size(56),
        shape=CircleBorder(),
        right=responsive_size(20),
        bottom=responsive_size(80)
    )
    
    home_content_container = Stack(
        controls=[
            Container(
                content=Column(
                    controls=[
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                IconButton(
                                    icon=Icons.MENU,
                                    icon_color=FWG,
                                    icon_size=responsive_size(26),
                                    on_click=lambda e: callbacks.get('shrink', lambda x: None)(e)
                                ),
                                Row(
                                    controls=[
                                        IconButton(
                                            icon=Icons.SEARCH,
                                            icon_color=FWG,
                                            icon_size=responsive_size(22),
                                            on_click=lambda e: page.go("/search")
                                        ),
                                        IconButton(
                                            icon=Icons.NOTIFICATIONS_OUTLINED,
                                            icon_color=FWG,
                                            icon_size=responsive_size(22),
                                            on_click=lambda e: page.go("/notifications")
                                        )
                                    ],
                                    spacing=responsive_size(5)
                                )
                            ]
                        ),
                        Container(height=responsive_size(10)),
                        
                        greeting_text if greeting_text else Text("Привет, Пользователь", 
                            color=FWG, 
                            size=responsive_size(20), 
                            weight=FontWeight.BOLD),
                        Container(height=responsive_size(15)),
                        
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("ВСЕ КАТЕГОРИИ", 
                                    color=FWG,
                                    size=responsive_size(12), 
                                    weight=FontWeight.W_500),
                                IconButton(
                                    icon=Icons.EXPAND_MORE,
                                    icon_color=FWG,
                                    icon_size=responsive_size(18),
                                    on_click=lambda e: page.go("/statistics")
                                )
                            ]
                        ),
                        Container(height=responsive_size(8)),
                        Container(
                            content=all_categories_card,
                            height=responsive_size(140)
                        ),
                        Container(height=responsive_size(20)),
                        
                        Row(
                            alignment="spaceBetween",
                            controls=[
                                Text("ПОСЛЕДНИЕ ТРАНЗАКЦИИ", 
                                    color=FWG, 
                                    size=responsive_size(12), 
                                    weight=FontWeight.W_500),
                                IconButton(
                                    icon=Icons.MORE_VERT,
                                    icon_color=FWG,
                                    icon_size=responsive_size(18),
                                    on_click=lambda e: page.go("/search")
                                )
                            ]
                        ),
                        Container(height=responsive_size(10)),
                        
                        # Используем контейнер транзакций напрямую
                        transactions_container,
                        
                        Container(height=responsive_size(40))
                    ],
                    spacing=0,
                    expand=True
                ),
                expand=True
            ),
            
            fab
        ],
        expand=True
    )
    return home_content_container, refresh_home_ui

__all__ = ['create_home_view']