from flet import *
from .constants import BG, FWG, PINK, FG, CAT_COLORS, MOBILE_PADDING, MOBILE_BORDER_RADIUS, responsive_size, EXPENSE_CATEGORIES, INCOME_CATEGORIES, INCOME_COLOR, EXPENSE_COLOR
from db import db_get_statistics
from helpers import load_session

def create_category_list(stats_list, title_color, colors_list, total_amount):
    """Создает список категорий с цветами"""
    category_list = Column(scroll="auto", spacing=responsive_size(8))
    color_index = 0
    
    if not stats_list:
        category_list.controls.append(
            Container(
                padding=responsive_size(20),
                content=Text("Нет данных по категориям", 
                    color=FWG, 
                    size=responsive_size(14), 
                    text_align="center")
            )
        )
        
        return Container(
            padding=padding.all(responsive_size(15)),
            bgcolor=FG,
            border_radius=MOBILE_BORDER_RADIUS,
            content=Column(
                controls=[
                    Text("Детализация по категориям", 
                        color=FWG, 
                        size=responsive_size(16), 
                        weight=FontWeight.BOLD),
                    Container(height=responsive_size(10)),
                    Container(
                        height=400,
                        content=category_list
                    )
                ]
            )
        )
    
    for cat, amount in stats_list:
        if total_amount > 0:
            percentage = (float(amount) / float(total_amount)) * 100
        else:
            percentage = 0
        
        category_list.controls.append(
            Container(
                padding=padding.all(responsive_size(12)),
                bgcolor=BG,
                border_radius=MOBILE_BORDER_RADIUS,
                content=Row(
                    controls=[
                        Container(
                            width=responsive_size(10), 
                            height=responsive_size(10), 
                            border_radius=responsive_size(5), 
                            bgcolor=colors_list[color_index % len(colors_list)]
                        ),
                        Container(width=responsive_size(10)),
                        Column(
                            controls=[
                                Text(cat, 
                                    color=FWG, 
                                    size=responsive_size(14), 
                                    weight=FontWeight.BOLD),
                                Text(f"{percentage:.1f}%", 
                                    color=FWG, 
                                    size=responsive_size(11), 
                                    opacity=0.7)
                            ],
                            expand=True
                        ),
                        Text(f"₸{float(amount):.2f}", 
                            color=title_color, 
                            size=responsive_size(14), 
                            weight=FontWeight.BOLD)
                    ]
                )
            )
        )
        color_index += 1
    
    return Container(
        padding=padding.all(responsive_size(15)),
        bgcolor=FG,
        border_radius=MOBILE_BORDER_RADIUS,
        content=Column(
            controls=[
                Text("Детализация по категориям", 
                    color=FWG, 
                    size=responsive_size(16), 
                    weight=FontWeight.BOLD),
                Container(height=responsive_size(10)),
                Container(
                    height=400,
                    content=category_list
                )
            ]
        )
    )

def create_statistics_view(page):
    """Создаёт адаптивный view для статистики для мобильных"""
    screen_width = page.window.width or 400
    screen_height = page.window.height or 800
    
    current_username = load_session()
    
    if not current_username:
        return Container(
            width=screen_width,
            height=screen_height,
            bgcolor=BG,
            padding=padding.all(MOBILE_PADDING),
            content=Column(
                controls=[
                    Row(
                        alignment="start",
                        controls=[
                            IconButton(
                                icon=Icons.ARROW_BACK,
                                icon_color=FWG,
                                icon_size=responsive_size(24),
                                on_click=lambda _: page.go("/")
                            ),
                            Text("Статистика", 
                                color=FWG, 
                                size=responsive_size(20), 
                                weight=FontWeight.BOLD,
                                expand=True)
                        ]
                    ),
                    Container(height=responsive_size(100)),
                    Text("Пожалуйста, авторизуйтесь", 
                        color=FWG, 
                        size=responsive_size(16), 
                        text_align="center")
                ]
            )
        )
    
    stats = db_get_statistics(current_username)
    
    total_income = stats.get("total_income", 0)
    total_expense = stats.get("total_expense", 0)
    balance = stats.get("balance", 0)

    expense_stats = stats.get("expense_stats", [])
    income_stats = stats.get("income_stats", [])

    selected_tab = {"value": "expenses"}  # Используем словарь для изменяемости

    expense_stats_container = Container()
    income_stats_container = Container()
    
    # Кнопки переключения (создаем отдельно для обновления)
    expense_button = ElevatedButton(
        "Расходы",
        bgcolor=EXPENSE_COLOR,
        color=FWG,
        width=(screen_width - 6*MOBILE_PADDING) / 2
    )
    
    income_button = ElevatedButton(
        "Доходы",
        bgcolor=FG,
        color=FWG,
        width=(screen_width - 6*MOBILE_PADDING) / 2
    )

    def switch_to_expenses(e):
        selected_tab["value"] = "expenses"
        expense_button.bgcolor = EXPENSE_COLOR
        income_button.bgcolor = FG
        update_statistics_display()
        page.update()
    
    def switch_to_income(e):
        selected_tab["value"] = "income"
        expense_button.bgcolor = FG
        income_button.bgcolor = INCOME_COLOR
        update_statistics_display()
        page.update()
    
    expense_button.on_click = switch_to_expenses
    income_button.on_click = switch_to_income

    def create_pie_chart(stats_list, total_amount, is_expense=True):
        """Создает круговую диаграмму"""
        pie_sectors = []
        
        if not stats_list or total_amount == 0:
            return []
        
        color_index = 0
        colors = CAT_COLORS[:len(EXPENSE_CATEGORIES)] if is_expense else CAT_COLORS[len(EXPENSE_CATEGORIES):]
        
        for cat, amount in stats_list:
            if total_amount > 0:
                percentage = (float(amount) / float(total_amount)) * 100
            else:
                percentage = 0
            
            pie_sectors.append(
                PieChartSection(
                    value=float(amount),
                    color=colors[color_index % len(colors)],
                    title=f"₸{float(amount):.0f}",
                    title_style=TextStyle(
                        size=responsive_size(10), 
                        color=Colors.WHITE, 
                        weight=FontWeight.BOLD
                    )
                )
            )
            color_index += 1
        
        return pie_sectors
    
    

    def update_statistics_display():
        """Обновляет отображение статистики в зависимости от выбранной вкладки"""
        
        if selected_tab["value"] == "expenses":
            pie_sectors = create_pie_chart(expense_stats, total_expense, is_expense=True)
            
            expense_stats_container.content = Column(
                controls=[
                    Container(
                        padding=padding.all(responsive_size(15)),
                        bgcolor=FG,
                        border_radius=MOBILE_BORDER_RADIUS,
                        content=Column(
                            controls=[
                                Text("Распределение расходов", 
                                    color=FWG, 
                                    size=responsive_size(16), 
                                    weight=FontWeight.BOLD),
                                Container(height=responsive_size(10)),
                                Container(
                                    height=responsive_size(200),
                                    content=PieChart(
                                        sections=pie_sectors if pie_sectors else [
                                            PieChartSection(
                                                value=1,
                                                color=Colors.GREY_700,
                                                title="Нет данных",
                                                title_style=TextStyle(
                                                    size=responsive_size(12), 
                                                    color=Colors.WHITE
                                                )
                                            )
                                        ],
                                        sections_space=responsive_size(1),
                                        center_space_radius=responsive_size(30),
                                        expand=True
                                    ) if pie_sectors else Container(
                                        height=responsive_size(200),
                                        alignment=alignment.center,
                                        content=Text(
                                            "Нет данных для отображения", 
                                            color=FWG, 
                                            size=responsive_size(14),
                                            text_align="center"
                                        )
                                    )
                                )
                            ]
                        )
                    ),
                    Container(height=responsive_size(20)),
                    create_category_list(expense_stats, EXPENSE_COLOR, CAT_COLORS[:len(EXPENSE_CATEGORIES)], total_expense)
                ]
            )
            
            expense_stats_container.visible = True
            income_stats_container.visible = False
            
        else:
            pie_sectors = create_pie_chart(income_stats, total_income, is_expense=False)
            
            income_stats_container.content = Column(
                controls=[
                    Container(
                        padding=padding.all(responsive_size(15)),
                        bgcolor=FG,
                        border_radius=MOBILE_BORDER_RADIUS,
                        content=Column(
                            controls=[
                                Text("Распределение доходов", 
                                    color=FWG, 
                                    size=responsive_size(16), 
                                    weight=FontWeight.BOLD),
                                Container(height=responsive_size(10)),
                                Container(
                                    height=responsive_size(200),
                                    content=PieChart(
                                        sections=pie_sectors if pie_sectors else [
                                            PieChartSection(
                                                value=1,
                                                color=Colors.GREY_700,
                                                title="Нет данных",
                                                title_style=TextStyle(
                                                    size=responsive_size(12), 
                                                    color=Colors.WHITE
                                                )
                                            )
                                        ],
                                        sections_space=responsive_size(1),
                                        center_space_radius=responsive_size(30),
                                        expand=True
                                    ) if pie_sectors else Container(
                                        height=responsive_size(200),
                                        alignment=alignment.center,
                                        content=Text(
                                            "Нет данных для отображения", 
                                            color=FWG, 
                                            size=responsive_size(14),
                                            text_align="center"
                                        )
                                    )
                                )
                            ]
                        )
                    ),
                    Container(height=responsive_size(20)),
                    create_category_list(income_stats, INCOME_COLOR, CAT_COLORS[len(EXPENSE_CATEGORIES):], total_income)
                ]
            )
            
            expense_stats_container.visible = False
            income_stats_container.visible = True

    update_statistics_display()

    return Container(
        width=screen_width,
        height=screen_height,
        bgcolor=BG,
        padding=padding.all(MOBILE_PADDING),
        content=Column(
            controls=[
                Row(
                    alignment="start",
                    controls=[
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=responsive_size(24),
                            on_click=lambda _: page.go("/")
                        ),
                        Text("Статистика", 
                            color=FWG, 
                            size=responsive_size(20), 
                            weight=FontWeight.BOLD,
                            expand=True)
                    ]
                ),
                Container(height=responsive_size(20)),
                
                Container(
                    padding=padding.all(responsive_size(15)),
                    bgcolor=FG,
                    border_radius=MOBILE_BORDER_RADIUS,
                    content=Column(
                        controls=[
                            Text("Общий баланс", 
                                color=FWG, 
                                size=responsive_size(14)),
                            Text(f"₸{float(balance):.2f}", 
                                color=PINK, 
                                size=responsive_size(28), 
                                weight=FontWeight.BOLD),
                            Container(height=responsive_size(15)),
                            Row(
                                alignment="spaceBetween",
                                controls=[
                                    Column(
                                        controls=[
                                            Text("Доходы", color=FWG, size=responsive_size(12)),
                                            Text(f"₸{float(total_income):.2f}", 
                                                color=INCOME_COLOR, 
                                                size=responsive_size(16), 
                                                weight=FontWeight.BOLD)
                                        ]
                                    ),
                                    Column(
                                        controls=[
                                            Text("Расходы", color=FWG, size=responsive_size(12)),
                                            Text(f"₸{float(total_expense):.2f}", 
                                                color=EXPENSE_COLOR, 
                                                size=responsive_size(16), 
                                                weight=FontWeight.BOLD)
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ),
                Container(height=responsive_size(20)),
                
                Container(
                    padding=padding.all(responsive_size(10)),
                    bgcolor=BG,
                    border_radius=MOBILE_BORDER_RADIUS,
                    content=Row(
                        alignment="spaceBetween",
                        controls=[
                            expense_button,
                            income_button
                        ]
                    )
                ),
                Container(height=responsive_size(20)),
                
                expense_stats_container,
                income_stats_container
            ],
            scroll="auto"
        )
    )

__all__ = ['create_statistics_view']