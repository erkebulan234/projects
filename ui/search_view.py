from flet import *
from datetime import datetime
import re
from .constants import BG, FWG, PINK, FG, MOBILE_PADDING, MOBILE_ELEMENT_HEIGHT, MOBILE_BORDER_RADIUS, responsive_size
from db import db_fetch_all_transactions
from helpers import load_session

def create_search_view(page):
    
    screen_width = page.window.width or 400
    screen_height = page.window.height or 800
    current_username = load_session()
    
    start_date_value = None
    end_date_value = None
    
    min_amount_field = TextField(
        label="Мин. сумма", 
        hint_text="0.00", 
        keyboard_type=KeyboardType.NUMBER, 
        width=screen_width - 2*MOBILE_PADDING, 
        color=FWG, 
        border_color=PINK, 
        focused_border_color=PINK, 
        label_style=TextStyle(color=FWG, size=responsive_size(14)),
        text_size=responsive_size(14),
        height=MOBILE_ELEMENT_HEIGHT
    )
    
    max_amount_field = TextField(
        label="Макс. сумма", 
        hint_text="99999.99", 
        keyboard_type=KeyboardType.NUMBER, 
        width=screen_width - 2*MOBILE_PADDING, 
        color=FWG, 
        border_color=PINK, 
        focused_border_color=PINK, 
        label_style=TextStyle(color=FWG, size=responsive_size(14)),
        text_size=responsive_size(14),
        height=MOBILE_ELEMENT_HEIGHT
    )

    search_field = TextField(
        hint_text="Описание, категория (живой поиск)",
        color=FWG,
        border_color=PINK,
        focused_border_color=PINK,
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT,
        text_size=responsive_size(14)
    )
    
    search_results = Column(scroll="auto", spacing=responsive_size(10))
    search_results.controls.append(
        Text("Введите запрос или установите фильтры", 
            color=FWG, 
            opacity=0.8,
            size=responsive_size(14))
    )

    def highlight_match(text, keywords, default_color):
        
        pattern = '|'.join(re.escape(k) for k in keywords if k)
        if not pattern:
            return Text(text, color=default_color, weight=FontWeight.BOLD, size=responsive_size(13))
            
        spans = []
        last_end = 0
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.span()
            
            if start > last_end:
                spans.append(TextSpan(text[last_end:start]))
            
            spans.append(TextSpan(
                text[start:end], 
                style=TextStyle(
                    weight=FontWeight.BOLD, 
                    color=Colors.BLACK,
                    bgcolor=Colors.YELLOW_ACCENT_400
                )
            ))
            last_end = end
            
        if last_end < len(text):
            spans.append(TextSpan(text[last_end:]))
        
        if not spans:
            return Text(text, color=default_color, weight=FontWeight.BOLD, size=responsive_size(13))
            
        return Text(
            spans=spans,
            color=default_color,
            weight=FontWeight.BOLD, 
            size=responsive_size(13), 
            selectable=True
        )

    def date_picker_handler(e):
        nonlocal start_date_value, end_date_value
        
        if e.control.data == 'start_date':
            start_date_value = e.control.value
            start_date_button.content.controls[0].value = start_date_value.strftime("%d.%m.%Y")
        else:
            end_date_value = e.control.value
            end_date_button.content.controls[0].value = end_date_value.strftime("%d.%m.%Y")
        
        page.update()
        filter_and_display_results()

    start_date_picker = DatePicker(
        on_change=date_picker_handler,
        data='start_date',
        first_date=datetime(2023, 1, 1),
        last_date=datetime.now()
    )
    end_date_picker = DatePicker(
        on_change=date_picker_handler,
        data='end_date',
        first_date=datetime(2023, 1, 1),
        last_date=datetime.now()
    )
    
    if start_date_picker not in page.overlay: 
        page.overlay.append(start_date_picker)
    if end_date_picker not in page.overlay: 
        page.overlay.append(end_date_picker)

    start_date_button = Container(
        width=screen_width - 2*MOBILE_PADDING, 
        height=MOBILE_ELEMENT_HEIGHT, 
        bgcolor=FG, 
        border_radius=MOBILE_BORDER_RADIUS, 
        border=border.all(1, PINK), 
        padding=padding.all(responsive_size(12)), 
        content=Row(
            controls=[
                Text("Начальная дата", 
                    color=FWG, 
                    size=responsive_size(14))
            ]
        ),
        on_click=lambda e: (setattr(start_date_picker, "open", True), page.update())
    )
    
    end_date_button = Container(
        width=screen_width - 2*MOBILE_PADDING, 
        height=MOBILE_ELEMENT_HEIGHT, 
        bgcolor=FG, 
        border_radius=MOBILE_BORDER_RADIUS, 
        border=border.all(1, PINK), 
        padding=padding.all(responsive_size(12)), 
        content=Row(
            controls=[
                Text("Конечная дата", 
                    color=FWG, 
                    size=responsive_size(14))
            ]
        ),
        on_click=lambda e: (setattr(end_date_picker, "open", True), page.update()) 
    )

    def clear_filters(e=None):
        nonlocal start_date_value, end_date_value
        search_field.value = ""
        min_amount_field.value = ""
        max_amount_field.value = ""
        start_date_value = None
        end_date_value = None
        start_date_button.content.controls[0].value = "Начальная дата"
        end_date_button.content.controls[0].value = "Конечная дата"
        page.update()
        filter_and_display_results()

    min_amount_field.on_change = lambda e: filter_and_display_results()
    max_amount_field.on_change = lambda e: filter_and_display_results()
    search_field.on_change = lambda e: filter_and_display_results()

    def filter_and_display_results(e=None):
        if not current_username:
            search_results.controls.clear()
            search_results.controls.append(
                Text("Пожалуйста, авторизуйтесь для поиска", 
                    color=FWG,
                    size=responsive_size(14))
            )
            search_results.update()
            return
        
        query = (search_field.value or "").lower().strip()
        search_results.controls.clear()

        keywords = [k.strip() for k in query.split() if k.strip()]
        
        min_amount = None
        max_amount = None
        try:
            min_amount = float((min_amount_field.value or '0').replace(',', '.'))
            if min_amount < 0: min_amount = 0
        except: 
            min_amount = 0 
        
        try:
            max_amount = float((max_amount_field.value or '999999999').replace(',', '.'))
        except: 
            max_amount = 999999999
        all_records = db_fetch_all_transactions(current_username)
        found = []
        
        for trans in all_records:
            text_match = True
            if keywords:
                description_lower = trans["description"].lower()
                category_lower = trans["category"].lower()
                text_match = all(k in description_lower or k in category_lower for k in keywords)

            amount_match = True
            try:
                trans_amount = float(trans["amount"])
                if trans_amount < min_amount or trans_amount > max_amount:
                    amount_match = False
            except:
                amount_match = False

            date_match = True
            try:
                trans_date_obj = datetime.strptime(trans['date'].split(' ')[0], "%d.%m.%Y").date() 
                
                if start_date_value and trans_date_obj < start_date_value.date():
                    date_match = False
                
                if end_date_value and trans_date_obj > end_date_value.date():
                    date_match = False
                        
            except:
                date_match = False 

            if text_match and amount_match and date_match:
                found.append(trans)

        is_default_filter = (not query and min_amount == 0 and max_amount == 999999999 
                            and not start_date_value and not end_date_value)
        
        if is_default_filter and not all_records:
            search_results.controls.append(
                Text("Транзакций пока нет. Добавьте первую запись!", 
                    color=FWG,
                    size=responsive_size(14))
            )
        elif is_default_filter:
            search_results.controls.append(
                Text(f"Найдено {len(all_records)} транзакций. Введите запрос или установите фильтры", 
                     color=FWG,
                     size=responsive_size(14))
            )
        elif not found:
            search_results.controls.append(
                Text("Ничего не найдено по заданным критериям", 
                    color=FWG,
                    size=responsive_size(14))
            )
        else:
            search_results.controls.append(
                Text(f"Найдено {len(found)} транзакций", 
                    color=FWG,
                    size=responsive_size(14))
            )
            for trans in found:
                icon = Icons.ARROW_DOWNWARD if trans["type"] == "expense" else Icons.ARROW_UPWARD
                icon_color = "red" if trans["type"] == "expense" else "green"
                
                highlighted_description = highlight_match(trans["description"], keywords, FWG)
                highlighted_category_name = highlight_match(trans["category"], keywords, FWG)

                category_info = Row(
                    controls=[
                        highlighted_category_name,
                        Text(" • ", color=FWG, size=responsive_size(10), opacity=0.7),
                        Text(trans['date'], color=FWG, size=responsive_size(10), opacity=0.7)
                    ],
                    spacing=0
                )

                search_results.controls.append(
                    Container(
                        height=responsive_size(80),
                        bgcolor=BG,
                        border_radius=MOBILE_BORDER_RADIUS,
                        padding=padding.all(responsive_size(10)),
                        margin=margin.only(bottom=responsive_size(5)),
                        content=Column(
                            controls=[
                                Row(
                                    controls=[
                                        Icon(icon, color=icon_color, size=responsive_size(22)),
                                        Container(width=responsive_size(10)),
                                        Text(
                                            trans["description"][:30] + ("..." if len(trans["description"]) > 30 else ""),
                                            color=FWG,
                                            weight=FontWeight.BOLD,
                                            size=responsive_size(13),
                                            expand=True
                                        Text(f"₸{trans['amount']}", 
                                            color=PINK, 
                                            size=responsive_size(13), 
                                            weight=FontWeight.BOLD),
                                    ]
                                ),
                                Container(height=responsive_size(5)),
                                category_info
                            ]
                        )
                    )
                )

        search_results.update()

    return View(
        "/search",
        [
            Container(
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
                                    on_click=lambda e: page.go("/")
                                ),
                                Text("Расширенный Поиск", 
                                    size=responsive_size(18), 
                                    color=FWG, 
                                    weight=FontWeight.BOLD,
                                    expand=True)
                        Text("Фильтр по сумме", 
                            color=FWG, 
                            size=responsive_size(14), 
                            opacity=0.8),
                        Container(height=responsive_size(8)),
                        Column(
                            controls=[
                                min_amount_field,
                                Container(height=responsive_size(10)),
                                max_amount_field
                            ]
                        ),
                        Container(height=responsive_size(15)),
                        Text("Фильтр по дате", 
                            color=FWG, 
                            size=responsive_size(14), 
                            opacity=0.8),
                        Container(height=responsive_size(8)),
                        Column(
                            controls=[
                                start_date_button,
                                Container(height=responsive_size(10)),
                                end_date_button
                            ]
                        ),
                        Container(height=responsive_size(20)),
                        Container(
                            height=screen_height - responsive_size(450),
                            content=search_results
                        ),
                    ],
                    scroll="auto"
                )
            )
        ],
        bgcolor=BG
    )

__all__ = ['create_search_view']