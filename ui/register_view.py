from flet import *
import threading
from .constants import BG, FWG, PINK, MOBILE_PADDING, MOBILE_ELEMENT_HEIGHT, MOBILE_BORDER_RADIUS, responsive_size
from helpers import show_alert, is_valid_email, write_session
from project import create_user

def create_register_view(page, greeting_text=None):
    """Создаёт адаптивный view для регистрации для мобильных"""
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
    
    email_field = TextField(
        label="Электронная почта", 
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT,
        label_style=TextStyle(color=FWG, size=responsive_size(14)),
        text_size=responsive_size(14)
    )
    
    register_btn = ElevatedButton(
        'Создать аккаунт', 
        bgcolor=PINK, 
        color=BG,
        width=screen_width - 2*MOBILE_PADDING,
        height=MOBILE_ELEMENT_HEIGHT
    )

    error_message = Text("", color=Colors.RED_ACCENT_400, size=responsive_size(14), visible=False) 

    def register_new_user(e):
        register_btn.disabled = True
        error_message.value = ""
        error_message.visible = False
        page.update()
        
        username = username_field.value.strip()
        email = email_field.value.strip()
        password = password_field.value.strip()
        
        if not username or not email or not password:
            error_message.value = "Пожалуйста, заполните все поля."
            error_message.visible = True
            register_btn.disabled = False
            page.update()
            return

        if not is_valid_email(email):
            error_message.value = "Пожалуйста, введите действительный адрес электронной почты."
            error_message.visible = True
            register_btn.disabled = False
            page.update()
            return

        threading.Thread(target=perform_registration, 
                        args=(username, email, password, page, register_btn, error_message, greeting_text)).start()

    def perform_registration(username, email, password, page, btn, err_text_control, greeting):
        try:
            user_data, err = create_user(username, email, password)

            if err:
                page.run_thread(lambda: setattr(err_text_control, 'value', err))
                page.run_thread(lambda: setattr(err_text_control, 'visible', True))
            
            elif user_data:
                write_session(username)
                if greeting:
                    page.run_thread(lambda: setattr(greeting, 'value', f"Привет, {username}"))
                page.run_thread(lambda: page.go('/'))
                
        except Exception as ex:
            print(f"Registration error: {ex}")
            show_alert(page, "Ошибка", "Произошла ошибка при регистрации.", bgcolor='red')
        finally:
            page.run_thread(lambda: setattr(btn, 'disabled', False))
            page.run_thread(page.update)

    def go_back_to_login(e):
        page.go('/login')
        page.update()

    register_btn.on_click = register_new_user

    return View(
        '/register', 
        [
            Container(
                width=screen_width,
                height=page.window.height or 800,
                bgcolor=BG, 
                padding=padding.all(MOBILE_PADDING),
                content=Column(
                    controls=[
                        Row(
                            alignment='start',
                            controls=[
                                IconButton(
                                    icon=Icons.ARROW_BACK, 
                                    icon_color=FWG,
                                    icon_size=responsive_size(24),
                                    on_click=go_back_to_login
                                )
                            ]
                        ),
                        Container(height=responsive_size(10)),
                        Text('Регистрация', 
                            color=FWG, 
                            size=responsive_size(24),
                            weight=FontWeight.BOLD,
                            text_align="center"),
                        Container(height=responsive_size(20)),
                        username_field,
                        Container(height=responsive_size(15)),
                        email_field,
                        Container(height=responsive_size(15)),
                        password_field,
                        Container(height=responsive_size(20)),
                        
                        error_message, 
                        Container(height=responsive_size(10), visible=error_message.visible),
                        
                        register_btn
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    scroll="auto"
                )
            )
        ], 
        bgcolor=BG
    )

__all__ = ['create_register_view']