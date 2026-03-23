from flet import *
import threading
from .constants import BG, FWG, PINK, MOBILE_PADDING, MOBILE_ELEMENT_HEIGHT, MOBILE_BORDER_RADIUS, responsive_size
from helpers import show_alert, write_session
from project import verify_user

def create_login_view(page):
    
    screen_width = page.window.width or 400
    
    username_field = TextField(
        label="Имя пользователя", 
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT,
        label_style=TextStyle(color=FWG, size=responsive_size(14)),
        text_size=responsive_size(14)
    )
    
    password_field = TextField(
        label="Пароль", 
        password=True, 
        can_reveal_password=True, 
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT,
        label_style=TextStyle(color=FWG, size=responsive_size(14)),
        text_size=responsive_size(14)
    )
    
    login_btn = ElevatedButton(
        'Войти', 
        bgcolor=PINK, 
        color=BG,
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT
    )

    error_message = Text("", color=Colors.RED_ACCENT_400, size=responsive_size(14), visible=False)
    
    def verify_and_login(e):
        login_btn.disabled = True
        page.update()

        username = username_field.value.strip()
        password = password_field.value.strip()

        if not username or not password:
            error_message.value = "Пожалуйста, введите имя пользователя и пароль."
            error_message.visible = True
            login_btn.disabled = False
            page.update()
            return
        
        threading.Thread(target=perform_login, args=(username, password, page, login_btn, error_message)).start()

    def perform_login(username, password, page, btn, err_text_control):
        try:
            user_data, err = verify_user(username, password)
            if err:
                page.run_thread(lambda: setattr(err_text_control, 'value', err))
                page.run_thread(lambda: setattr(err_text_control, 'visible', True))
            elif user_data:
                write_session(username)
                page.run_thread(lambda: page.go('/'))
        except Exception as ex:
            print(f"Login failed due to DB error: {ex}")
            show_alert(
                page,
                "Ошибка подключения", 
                "Не удалось подключиться к серверу БД. Проверьте настройки сети и доступ к серверу.",
                bgcolor='red'
            )
        finally:
            page.run_thread(lambda: setattr(btn, 'disabled', False))
            page.run_thread(page.update)

    def go_register(e):
        page.go('/register')
        page.update()

    login_btn.on_click = verify_and_login

    return View(
        '/login', 
        [
            Container(
                width=screen_width,
                height=page.window.height or 800,
                bgcolor=BG, 
                padding=padding.all(MOBILE_PADDING),
                content=Column(
                    controls=[
                        Container(height=responsive_size(40)),
                        Text('Вход', 
                            color=FWG, 
                            size=responsive_size(24),
                            weight=FontWeight.BOLD,
                            text_align="center"),
                        Container(height=responsive_size(20)),
                        username_field,
                        Container(height=responsive_size(15)),
                        password_field,
                        Container(height=responsive_size(20)),

                        error_message,
                        Container(height=responsive_size(10), visible=error_message.visible),
                        Column(
                            controls=[
                                login_btn,
                                Container(height=responsive_size(15)),
                                ElevatedButton(
                                    'Регистрация', 
                                    on_click=go_register,
                                    width=screen_width - 2*MOBILE_PADDING,
                                    height=MOBILE_ELEMENT_HEIGHT
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    scroll="auto"
                )
            )
        ], 
        bgcolor=BG
    )

__all__ = ['create_login_view']