from flet import AlertDialog, Text, TextButton, MainAxisAlignment

def create_alert_dialog():
    """Создаёт общий объект AlertDialog"""
    return AlertDialog(
        modal=True,
        title=Text("Заголовок"),
        content=Text("Текст сообщения"),
        actions=[
            TextButton("ОК", on_click=lambda e: close_alert(e.page)),
        ],
        actions_alignment=MainAxisAlignment.END,
    )

def close_alert(page):
    """Закрывает всплывающее окно"""
    page.dialog.open = False
    page.update()

"""
Модуль для показа уведомлений
"""
from flet import SnackBar, Text

def show_alert(page, message, bgcolor='red'):
    """Показывает всплывающее уведомление"""
    page.snack_bar = SnackBar(
        content=Text(message, color="white"),
        bgcolor=bgcolor
    )
    page.snack_bar.open = True
    page.update()

__all__ = ['show_alert', 'create_alert_dialog']