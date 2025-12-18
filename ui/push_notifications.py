
from flet import *
import asyncio
import threading
from datetime import datetime, timedelta
from db import (
    db_create_notification,
    db_fetch_notifications,
    db_mark_notification_read,
    db_mark_all_notifications_read,
    db_delete_notification,
    get_unread_count,
    get_current_user_id,
    create_transaction_notification,
    create_budget_warning_notification,
    create_weekly_report_notification,
    create_reminder_notification
)
from helpers import load_session
from .constants import BG, FWG, FG, PINK, responsive_size, MOBILE_PADDING, MOBILE_BORDER_RADIUS

class PushNotificationManager:
    """Менеджер push-уведомлений"""
    
    def __init__(self, page: Page):
        self.page = page
        self.notification_sounds = {
            'info': 'notification_simple',
            'warning': 'notification_warning',
            'alert': 'notification_alert',
            'success': 'notification_success'
        }
        self.notification_queue = []
        self.is_active = False
        self.current_notification = None
        
    def start(self):
        """Запускает менеджер уведомлений"""
        self.is_active = True
        self._check_notifications_loop()
        
    def stop(self):
        """Останавливает менеджер уведомлений"""
        self.is_active = False
        
    def _check_notifications_loop(self):
        """Фоновый цикл проверки уведомлений"""
        if not self.is_active:
            return
            
        # Проверяем новые уведомления
        current_username = load_session()
        if current_username:
            user_id = get_current_user_id(current_username)
            if user_id:
                unread_count = get_unread_count(user_id)
                # Можно добавить логику для проверки конкретных новых уведомлений
                
        # Запускаем следующий цикл через 30 секунд
        threading.Timer(30, self._check_notifications_loop).start()
        
    def show_push_notification(self, title, message, notification_type='info', action=None):
        """
        Показывает push-уведомление в виде всплывающего окна
        """
        def close_notification(e):
            if notification_container in self.page.overlay:
                self.page.overlay.remove(notification_container)
                self.page.update()
                self.current_notification = None
        
        def handle_action(e):
            if action and action.get('route'):
                self.page.go(action['route'])
            if action and action.get('callback'):
                action['callback']()
            close_notification(e)
        
        # Цвета для разных типов уведомлений
        colors = {
            'info': colors.BLUE,
            'warning': colors.ORANGE,
            'alert': colors.RED,
            'success': colors.GREEN,
            'transaction': colors.PURPLE,
            'budget': colors.AMBER,
            'reminder': colors.CYAN
        }
        
        bg_color = colors.get(notification_type, colors.BLUE)
        
        # Иконки для разных типов уведомлений
        icons = {
            'info': Icons.INFO_OUTLINE,
            'warning': Icons.WARNING_AMBER_ROUNDED,
            'alert': Icons.REPORT_PROBLEM_OUTLINED,
            'success': Icons.CHECK_CIRCLE_OUTLINE,
            'transaction': Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
            'budget': Icons.PIE_CHART_OUTLINE,
            'reminder': Icons.NOTIFICATIONS_ACTIVE_OUTLINED
        }
        
        icon = icons.get(notification_type, Icons.INFO_OUTLINE)
        
        # Создаем контейнер для уведомления
        notification_container = Container(
            width=350,
            height=100,
            bgcolor=bg_color,
            border_radius=15,
            padding=15,
            animate=Animation(300, AnimationCurve.EASE_OUT),
            opacity=0,
            top=20,
            right=20,
            border=border.all(1, colors.with_opacity(0.2, colors.WHITE)),
            shadow=BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=colors.with_opacity(0.3, colors.BLACK),
                offset=Offset(0, 4)
            ),
            data={"type": "notification"},  # Для идентификации
            content=Column(
                controls=[
                    # Заголовок и кнопка закрытия
                    Row(
                        controls=[
                            Icon(icon, color=colors.WHITE, size=20),
                            Text(
                                title,
                                color=colors.WHITE,
                                size=16,
                                weight=FontWeight.BOLD,
                                expand=True
                            ),
                            IconButton(
                                icon=Icons.CLOSE,
                                icon_color=colors.WHITE,
                                icon_size=20,
                                on_click=close_notification
                            )
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN
                    ),
                    # Сообщение
                    Container(
                        content=Text(
                            message,
                            color=colors.WHITE,
                            size=14,
                            max_lines=2,
                            overflow=TextOverflow.ELLIPSIS
                        ),
                        padding=padding.only(top=5, bottom=10)
                    ),
                    # Кнопка действия (если есть)
                    Row(
                        controls=[
                            TextButton(
                                "Просмотреть",
                                style=ButtonStyle(
                                    color=colors.WHITE,
                                    overlay_color=colors.with_opacity(0.1, colors.WHITE)
                                ),
                                on_click=handle_action
                            ) if action else Container()
                        ]
                    )
                ]
            )
        )
        
        # Добавляем в overlay
        self.page.overlay.append(notification_container)
        self.current_notification = notification_container
        
        # Анимация появления
        def animate_in():
            notification_container.opacity = 1
            self.page.update()
            
            # Автоматическое закрытие через 5 секунд
            def auto_close():
                if notification_container in self.page.overlay:
                    close_notification(None)
            
            threading.Timer(5, auto_close).start()
        
        # Немного задержки для анимации
        threading.Timer(0.1, animate_in).start()
        self.page.update()
        
    def show_toast_notification(self, message, bgcolor=None, duration=3000):
        """
        Показывает toast-уведомление (нижняя панель)
        """
        # Создаем контейнер для toast
        toast_container = Container(
            width=self.page.window.width - 40,
            height=50,
            bgcolor=bgcolor or Colors.GREEN,
            border_radius=10,
            padding=15,
            animate=Animation(300, AnimationCurve.EASE_OUT),
            opacity=0,
            bottom=20,
            left=20,
            right=20,
            alignment=alignment.center,
            content=Text(
                message,
                color=Colors.WHITE,
                size=14,
                text_align=TextAlign.CENTER
            )
        )
        
        # Добавляем в overlay
        self.page.overlay.append(toast_container)
        
        # Анимация появления
        def animate_toast():
            toast_container.opacity = 1
            self.page.update()
            
            # Исчезновение
            def animate_out():
                toast_container.opacity = 0
                self.page.update()
                
                # Удаление из overlay после анимации
                def remove_toast():
                    if toast_container in self.page.overlay:
                        self.page.overlay.remove(toast_container)
                        self.page.update()
                
                threading.Timer(0.3, remove_toast).start()
            
            threading.Timer(duration / 1000, animate_out).start()
        
        threading.Timer(0.1, animate_toast).start()
        self.page.update()

def create_notification_bell(page, user_id, on_click=None):
    """
    Создает иконку колокольчика с индикатором непрочитанных уведомлений
    """
    unread_count = get_unread_count(user_id)
    
    # Функция для обновления счетчика
    def update_bell():
        nonlocal unread_count
        unread_count = get_unread_count(user_id)
        if unread_count > 0:
            badge_container.content.controls[1].content = Text(
                str(min(unread_count, 99)),
                color=Colors.WHITE,
                size=9,
                weight=FontWeight.BOLD,
                text_align=TextAlign.CENTER
            )
            badge_container.content.controls[1].bgcolor = Colors.RED_500
        else:
            badge_container.content.controls[1].content = Container()
            badge_container.content.controls[1].bgcolor = Colors.TRANSPARENT
        page.update()
    
    # Создаем badge
    badge_container = Container(
        content=Stack(
            controls=[
                IconButton(
                    icon=Icons.NOTIFICATIONS_OUTLINED,
                    icon_color=FWG,
                    icon_size=24,
                    on_click=on_click or (lambda e: page.go("/notifications")),
                    tooltip="Уведомления",
                    style=ButtonStyle(
                        shape=RoundedRectangleBorder(radius=20),
                        overlay_color=Colors.with_opacity(0.1, FWG)
                    )
                ),
                Container(
                    width=18,
                    height=18,
                    border_radius=9,
                    bgcolor=Colors.RED_500 if unread_count > 0 else Colors.TRANSPARENT,
                    content=Text(
                        str(min(unread_count, 99)) if unread_count > 0 else "",
                        color=Colors.WHITE,
                        size=9,
                        weight=FontWeight.BOLD,
                        text_align=TextAlign.CENTER
                    ) if unread_count > 0 else Container(),
                    alignment=alignment.top_right,
                    right=0,
                    top=0
                )
            ]
        )
    )
    
    return badge_container, update_bell

# Утилиты для работы с уведомлениями
def check_and_notify_budget_exceeded(user_id, transactions):
    """
    Проверяет превышение бюджета и создает уведомления
    """
    # Здесь должна быть логика проверки бюджета
    # Например, проверка категорий и лимитов
    # Временная реализация - проверяем большие расходы
    for transaction in transactions:
        if transaction['type'] == 'expense' and transaction['amount'] > 10000:
            create_budget_warning_notification(
                user_id, 
                transaction['category'], 
                transaction['amount'], 
                10000
            )
    pass

def create_scheduled_notifications(user_id):
    """
    Создает запланированные уведомления (ежедневные, еженедельные отчеты)
    """
    # Получаем последнее уведомление такого типа
    # Создаем новое если нужно
    # Временная реализация - создаем тестовое уведомление
    db_create_notification(
        user_id,
        "📅 Ежедневный отчет: проверьте свои расходы за сегодня",
        'reminder'
    )

__all__ = [
    'PushNotificationManager',
    'create_notification_bell',
    'check_and_notify_budget_exceeded',
    'create_scheduled_notifications'
]