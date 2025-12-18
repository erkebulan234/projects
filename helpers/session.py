
import json
import os
from flet import SnackBar, Text

SESSION_FILE = "session.json"

SESSION_FILE = "session.json"

def load_session():
    """Загружает имя пользователя из сессии"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("username")
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    return None

def write_session(username):
    """Сохраняет имя пользователя в сессию"""
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({"username": username}, f, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing session: {e}")
        return False

def clear_session():
    """Очищает сессию (удаляет файл)"""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        return True
    except Exception as e:
        print(f"Error clearing session: {e}")
        return False


def show_alert(page, message, bgcolor="red"):
    """Универсальный alert с поддержкой цвета"""
    page.snack_bar = SnackBar(
        content=Text(message, color="white"),
        bgcolor=bgcolor
    )
    page.snack_bar.open = True

    try:
        page.update()
    except:
        pass


__all__ = ['load_session', 'write_session', 'clear_session']