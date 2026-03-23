from flet import *
BG = "#0B2A20"
FWG = "#F5F5DC"
FG = "#004D40"
PINK = "#D4AF37"
    "Еда", "Транспорт", "Развлечения", "Жилье", 
    "Здоровье", "Одежда", "Образование", "Подарки", 
    "Прочее"
]

INCOME_CATEGORIES = [
    "Зарплата", "Инвестиции", "Возврат", "Подарок",
    "Фриланс", "Премия", "Дивиденды", "Сбережения"
]

ALL_CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES
CAT_COLORS = [
    Colors.BLUE_400,
    
    if current_width is None:
        current_width = BASE_SCREEN_WIDTH
    scale_factor = current_width / BASE_SCREEN_WIDTH
    scaled_size = base_size * scale_factor
    min_size = base_size * 0.8
    
    return responsive_size(base_width, current_width)
def responsive_height(base_height, current_width=None):
    
    return responsive_size(base_height, current_width)
def adaptive_container(width=None, height=None, padding=None, margin=None):
    
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
def adaptive_text_style(size, weight=None, color=None):
    
    style_kwargs = {
        'size': responsive_size(size)
    }
    
    if weight is not None:
        style_kwargs['weight'] = weight
    
    if color is not None:
        style_kwargs['color'] = color
    
    return TextStyle(**style_kwargs)
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