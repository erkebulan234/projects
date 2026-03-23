from flet import AlertDialog, Text, TextButton, MainAxisAlignment

def create_alert_dialog():
    
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
    
    page.dialog.open = False
    page.update()


from flet import SnackBar, Text

def show_alert(page, message, bgcolor='red'):
    
    page.snack_bar = SnackBar(
        content=Text(message, color="white"),
        bgcolor=bgcolor
    )
    page.snack_bar.open = True
    page.update()

__all__ = ['show_alert', 'create_alert_dialog']