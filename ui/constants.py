from flet import *

# Цвета
BG = "#0B2A20"  # Темный фон
FWG = "#F5F5DC"  # Светлый текст (Flet White Gray)
FG = "#004D40"  # Средний фон (Flet Gray)
PINK = "#D4AF37"  # Акцентный цвет

# Категории транзакций
EXPENSE_CATEGORIES = [
    "Еда", "Транспорт", "Развлечения", "Жилье", 
    "Здоровье", "Одежда", "Образование", "Подарки", 
    "Прочее"
]

INCOME_CATEGORIES = [
    "Зарплата", "Инвестиции", "Возврат", "Подарок",
    "Фриланс", "Премия", "Дивиденды", "Сбережения"
]

ALL_CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES

# Цвета для категорий в статистике
CAT_COLORS = [
    Colors.BLUE_400,      # Еда
    Colors.GREEN_400,     # Транспорт
    Colors.ORANGE_400,    # Развлечения
    Colors.RED_400,       # Жилье
    Colors.PURPLE_400,    # Здоровье
    Colors.PINK_400,      # Одежда
    Colors.TEAL_400,      # Образование
    Colors.AMBER_400,     # Подарки
    Colors.CYAN_400,      # Прочее
    Colors.INDIGO_400,    # Зарплата
    Colors.LIGHT_BLUE_400,# Инвестиции
    Colors.LIME_400,      # Возврат
    Colors.DEEP_ORANGE_400,# Подарок
    Colors.DEEP_PURPLE_400,# Фриланс
    Colors.BROWN_400,     # Премия
    Colors.GREY_400       # Дивиденды
]


INCOME_COLOR = Colors.GREEN_400
EXPENSE_COLOR = Colors.RED_400

# ============ АДАПТИВНЫЕ КОНСТАНТЫ ДЛЯ МОБИЛЬНЫХ ============

# Базовый размер экрана для расчетов
BASE_SCREEN_WIDTH = 360  # Стандартная ширина мобильного телефона
BASE_SCREEN_HEIGHT = 800  # Стандартная высота мобильного телефона

# Функция для адаптивных размеров
def responsive_size(base_size, current_width=None):
    """
    Рассчитывает адаптивный размер на основе базовой ширины экрана.
    
    Args:
        base_size: Базовый размер для ширины 360px
        current_width: Текущая ширина экрана (если None, используется BASE_SCREEN_WIDTH)
    
    Returns:
        Адаптивный размер
    """
    if current_width is None:
        current_width = BASE_SCREEN_WIDTH
    
    # Рассчитываем коэффициент масштабирования
    scale_factor = current_width / BASE_SCREEN_WIDTH
    
    # Применяем масштабирование с ограничениями
    scaled_size = base_size * scale_factor
    
    # Ограничиваем минимальный и максимальный размер
    min_size = base_size * 0.8  # Не меньше 80% от базового
    max_size = base_size * 1.2  # Не больше 120% от базового
    
    return max(min_size, min(scaled_size, max_size))

# Адаптивные константы (рассчитаны для BASE_SCREEN_WIDTH = 360)
MOBILE_PADDING = responsive_size(16)
MOBILE_MARGIN = responsive_size(8)
MOBILE_BORDER_RADIUS = responsive_size(12)
MOBILE_ELEMENT_HEIGHT = responsive_size(48)
MOBILE_SMALL_ELEMENT_HEIGHT = responsive_size(36)
MOBILE_FONT_SIZE = responsive_size(14)
MOBILE_TITLE_SIZE = responsive_size(18)
MOBILE_HEADER_SIZE = responsive_size(24)
MOBILE_ICON_SIZE = responsive_size(24)

# Функция для расчета ширины элемента
def responsive_width(base_width, current_width=None):
    """Рассчитывает адаптивную ширину элемента"""
    return responsive_size(base_width, current_width)

# Функция для расчета высоты элемента
def responsive_height(base_height, current_width=None):
    """Рассчитывает адаптивную высоту элемента"""
    return responsive_size(base_height, current_width)

# Функция для создания адаптивного контейнера
def adaptive_container(width=None, height=None, padding=None, margin=None):
    """
    Создает адаптивный контейнер с автоматическим расчетом размеров.
    
    Args:
        width: Базовая ширина
        height: Базовая высота
        padding: Отступы (может быть числом или кортежем)
        margin: Внешние отступы
    
    Returns:
        Контейнер с адаптивными свойствами
    """
    container_kwargs = {}
    
    if width is not None:
        container_kwargs['width'] = responsive_size(width)
    
    if height is not None:
        container_kwargs['height'] = responsive_size(height)
    
    if padding is not None:
        if isinstance(padding, (int, float)):
            container_kwargs['padding'] = responsive_size(padding)
        elif isinstance(padding, (tuple, list)) and len(padding) == 4:
            container_kwargs['padding'] = padding.only(
                top=responsive_size(padding[0]),
                right=responsive_size(padding[1]),
                bottom=responsive_size(padding[2]),
                left=responsive_size(padding[3])
            )
        else:
            container_kwargs['padding'] = padding
    
    if margin is not None:
        if isinstance(margin, (int, float)):
            container_kwargs['margin'] = responsive_size(margin)
        else:
            container_kwargs['margin'] = margin
    
    return Container(**container_kwargs)

# Адаптивные стили текста
def adaptive_text_style(size, weight=None, color=None):
    """Создает адаптивный стиль текста"""
    style_kwargs = {
        'size': responsive_size(size)
    }
    
    if weight is not None:
        style_kwargs['weight'] = weight
    
    if color is not None:
        style_kwargs['color'] = color
    
    return TextStyle(**style_kwargs)

# Экспортируем все необходимые константы
__all__ = [
    'BG', 'FWG', 'FG', 'PINK',
    'ALL_CATEGORIES', 'CAT_COLORS',
    'responsive_size', 'responsive_width', 'responsive_height',
    'MOBILE_PADDING', 'MOBILE_MARGIN', 'MOBILE_BORDER_RADIUS',
    'MOBILE_ELEMENT_HEIGHT', 'MOBILE_SMALL_ELEMENT_HEIGHT',
    'MOBILE_FONT_SIZE', 'MOBILE_TITLE_SIZE', 'MOBILE_HEADER_SIZE',
    'MOBILE_ICON_SIZE', 'BASE_SCREEN_WIDTH', 'BASE_SCREEN_HEIGHT',
    'adaptive_container', 'adaptive_text_style'
]