from flet import *
from .constants import BG, FWG, PINK, FG, MOBILE_PADDING, MOBILE_BORDER_RADIUS, responsive_size
from db import db_fetch_notifications, db_mark_notification_read, get_unread_count
from helpers import load_session

def create_notifications_button(page, user_id):
    
    unread_count = get_unread_count(user_id)
    
    return Container(
        padding=padding.all(responsive_size(8)),
        content=Stack(
            controls=[
                Icon(Icons.NOTIFICATIONS_OUTLINED, color=FWG, size=responsive_size(22)),
                Container(
                    width=responsive_size(16),
                    height=responsive_size(16),
                    border_radius=responsive_size(8),
                    bgcolor=Colors.RED_500 if unread_count > 0 else Colors.TRANSPARENT,
                    content=Text(
                        str(unread_count),
                        color=Colors.WHITE,
                        size=responsive_size(9),
                        weight=FontWeight.BOLD,
                        text_align=TextAlign.CENTER
                    ) if unread_count > 0 else Container(),
                    alignment=alignment.top_right,
                    right=0,
                    top=0
                )
            ]
        ),
        on_click=lambda e: page.go("/notifications"),
    )

def create_notifications_view(page, user_id):
    
    screen_width = page.window.width or 400
    screen_height = page.window.height or 800

    def on_notifications_click(e):
        notification_id = e.control.data
        db_mark_notification_read(notification_id)
        page.go('/notifications')
        page.update()

    def build_notification_list():
        notifications = db_fetch_notifications(user_id)
    
        if not notifications:
            return Column(
                controls=[
                    Container(height=responsive_size(50)),
                    Text("У вас нет новых уведомлений.", 
                        color=FWG, 
                        opacity=0.8, 
                        size=responsive_size(16), 
                        text_align=TextAlign.CENTER),
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=0
            )

        list_controls = []
        for notif in notifications:
            is_read = notif['is_read']
        
            if notif['type'] == 'warning':
                icon = Icons.WARNING_AMBER_ROUNDED
                color = Colors.YELLOW_ACCENT_700
            elif notif['type'] == 'alert':
                icon = Icons.REPORT_PROBLEM_OUTLINED
                color = Colors.RED_500
            else:
                icon = Icons.INFO_OUTLINE
                color = PINK
            
            opacity = 0.5 if is_read else 1.0
            time_str = notif['created_at'].strftime("%H:%M %d.%m.%Y") if notif['created_at'] else ""

            list_controls.append(
                Container(
                    data=notif['notification_id'],
                    on_click=on_notifications_click,
                    padding=padding.all(responsive_size(12)),
                    margin=margin.only(bottom=responsive_size(8)),
                    bgcolor=FG if not is_read else Colors.with_opacity(0.1, FG),
                    border_radius=MOBILE_BORDER_RADIUS,
                    opacity=opacity,
                    content=Column(
                        controls=[
                            Row(
                                controls=[
                                    Icon(icon, color=color, size=responsive_size(20)),
                                    Container(width=responsive_size(10)),
                                    Text(
                                        notif['message'], 
                                        color=FWG, 
                                        weight=FontWeight.W_500 if not is_read else FontWeight.NORMAL,
                                        size=responsive_size(13),
                                        max_lines=3,
                                        overflow=TextOverflow.ELLIPSIS,
                                        expand=True
            scroll="auto",
            expand=True,
            spacing=0
        )

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
                            on_click=lambda e: page.go("/")
                        ),
                        Text("Уведомления", 
                            size=responsive_size(20), 
                            color=FWG, 
                            weight=FontWeight.BOLD,
                            expand=True)
                    ]
                ),
                Container(height=responsive_size(15)),
                Container(
                    height=screen_height - responsive_size(150),
                    content=build_notification_list()
                )
            ],
            spacing=0
        )
    )

__all__ = ['create_notifications_view', 'create_notifications_button']