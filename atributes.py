from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt5.QtWidgets import QGraphicsOpacityEffect


class AnimatedButton(QtWidgets.QPushButton):
    """Кнопка с анимацией нажатия"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._pressed = False
        
    def mousePressEvent(self, event):
        self._pressed = True
        self.animate_press()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self._pressed:
            self.animate_release()
        self._pressed = False
        super().mouseReleaseEvent(event)
        
    def animate_press(self):
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(100)
        animation.setStartValue(self.geometry())
        
        new_geo = self.geometry()
        new_geo.setWidth(self.width() - 4)
        new_geo.setHeight(self.height() - 4)
        new_geo.moveCenter(self.geometry().center())
        
        animation.setEndValue(new_geo)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        
    def animate_release(self):
        animation = QPropertyAnimation(self, b"geometry")
        animation.setDuration(100)
        animation.setStartValue(self.geometry())
        
        new_geo = self.geometry()
        new_geo.setWidth(self.width() + 4)
        new_geo.setHeight(self.height() + 4)
        new_geo.moveCenter(self.geometry().center())
        
        animation.setEndValue(new_geo)
        animation.setEasingCurve(QEasingCurve.OutBounce)
        animation.start()


class CircularProgressBar(QtWidgets.QWidget):
    """Круговой прогресс-бар"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 100
        self.setMinimumSize(150, 150)
        
    def setValue(self, value):
        self.value = value
        self.update()
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Размеры
        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Центр
        painter.translate(width / 2, height / 2)
        
        # Фон круга
        pen = QtGui.QPen()
        pen.setWidth(15)
        pen.setColor(QtGui.QColor("#E5E5E7"))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        rect = QRect(-side // 2 + 15, -side // 2 + 15, 
                     side - 30, side - 30)
        painter.drawArc(rect, 90 * 16, -360 * 16)
        
        # Прогресс
        gradient = QtGui.QConicalGradient(0, 0, 90)
        gradient.setColorAt(0, QtGui.QColor("#667EEA"))
        gradient.setColorAt(1, QtGui.QColor("#764BA2"))
        
        pen.setBrush(gradient)
        pen.setColor(QtGui.QColor("#667EEA"))
        painter.setPen(pen)
        
        angle = int(360 * self.value / self.max_value)
        painter.drawArc(rect, 90 * 16, -angle * 16)
        
        # Текст в центре
        painter.setPen(QtGui.QColor("#1D1D1F"))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        
        text = f"{int(self.value)}%"
        painter.drawText(rect, Qt.AlignCenter, text)


class GradientCard(QtWidgets.QWidget):
    """Карточка с градиентным фоном"""
    
    def __init__(self, color1="#667EEA", color2="#764BA2", parent=None):
        super().__init__(parent)
        self.color1 = color1
        self.color2 = color2
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Градиент
        gradient = QtGui.QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QtGui.QColor(self.color1))
        gradient.setColorAt(1, QtGui.QColor(self.color2))
        
        # Рисуем округлый прямоугольник
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)


class CategoryIcon(QtWidgets.QLabel):
    """Иконка категории с фоном"""
    
    def __init__(self, emoji, color="#667EEA", size=50, parent=None):
        super().__init__(emoji, parent)
        self.bg_color = color
        self.icon_size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}20;
                border-radius: {size // 4}px;
                font-size: {size // 2}px;
            }}
        """)


class SlidingStackedWidget(QtWidgets.QStackedWidget):
    """StackedWidget с анимацией слайда"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def slideToIndex(self, index):
        """Переключение на индекс с анимацией"""
        if index == self.currentIndex():
            return
            
        current_widget = self.currentWidget()
        next_widget = self.widget(index)
        
        if not current_widget or not next_widget:
            return
        
        # Определяем направление
        direction = 1 if index > self.currentIndex() else -1
        
        # Позиционируем виджеты
        offset_x = self.width() * direction
        next_widget.setGeometry(offset_x, 0, self.width(), self.height())
        next_widget.show()
        
        # Анимация текущего виджета
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(300)
        anim_current.setStartValue(QtCore.QPoint(0, 0))
        anim_current.setEndValue(QtCore.QPoint(-offset_x, 0))
        anim_current.setEasingCurve(QEasingCurve.OutCubic)
        
        # Анимация следующего виджета
        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(300)
        anim_next.setStartValue(QtCore.QPoint(offset_x, 0))
        anim_next.setEndValue(QtCore.QPoint(0, 0))
        anim_next.setEasingCurve(QEasingCurve.OutCubic)
        
        # Запускаем анимации
        anim_current.start()
        anim_next.start()
        
        # Меняем индекс после анимации
        anim_next.finished.connect(lambda: self.setCurrentIndex(index))


class NotificationBanner(QtWidgets.QWidget):
    """Баннер уведомлений"""
    
    def __init__(self, message, type="info", parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        
        # Цвета по типам
        colors = {
            "success": "#34C759",
            "error": "#FF3B30",
            "warning": "#FF9500",
            "info": "#007AFF"
        }
        
        bg_color = colors.get(type, colors["info"])
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 15px;
            }}
        """)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Иконка
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        
        icon = QtWidgets.QLabel(icons.get(type, "ℹ"))
        icon.setStyleSheet("font-size: 24px; color: white;")
        
        # Текст
        text = QtWidgets.QLabel(message)
        text.setStyleSheet("""
            font-size: 15px;
            color: white;
            font-weight: 500;
        """)
        
        layout.addWidget(icon)
        layout.addSpacing(10)
        layout.addWidget(text, 1)
        
        # Автоматическое скрытие
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.deleteLater)
        
        # Запускаем таймер на скрытие
        QtCore.QTimer.singleShot(3000, self.fade_out)
        
    def fade_out(self):
        self.fade_animation.start()


class AmountInput(QtWidgets.QLineEdit):
    """Поле ввода суммы с автоматическим форматированием"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("$0.00")
        self.textChanged.connect(self.format_amount)
        
    def format_amount(self, text):
        # Удаляем все кроме цифр и точки
        cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
        
        # Ограничиваем до 2 знаков после запятой
        if '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) > 2:
                cleaned = parts[0] + '.' + parts[1]
            elif len(parts[1]) > 2:
                cleaned = parts[0] + '.' + parts[1][:2]
        
        # Форматируем с запятыми
        if cleaned:
            try:
                if '.' in cleaned:
                    integer, decimal = cleaned.split('.')
                    formatted = f"{int(integer):,}"
                    if decimal:
                        formatted += f".{decimal}"
                else:
                    formatted = f"{int(cleaned):,}"
                
                # Обновляем только если изменилось
                if self.text() != formatted:
                    cursor_pos = self.cursorPosition()
                    self.setText(formatted)
                    self.setCursorPosition(min(cursor_pos, len(formatted)))
            except:
                pass


class ToggleSwitch(QtWidgets.QCheckBox):
    """iOS стиль переключатель"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 34)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Фон
        if self.isChecked():
            color = QtGui.QColor("#34C759")
        else:
            color = QtGui.QColor("#E5E5E7")
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 
                               self.height() // 2, self.height() // 2)
        
        # Кружок
        if self.isChecked():
            x = self.width() - self.height() + 2
        else:
            x = 2
        
        painter.setBrush(QtGui.QColor("white"))
        circle_size = self.height() - 4
        painter.drawEllipse(x, 2, circle_size, circle_size)


class ExpenseCategorySelector(QtWidgets.QWidget):
    """Селектор категории расходов"""
    
    categorySelected = QtCore.pyqtSignal(str, str)  # name, color
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_category = None
        
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(15)
        
        categories = [
            ("🍔", "Еда", "#FF6B6B"),
            ("🚗", "Транспорт", "#4ECDC4"),
            ("🏠", "Дом", "#95E1D3"),
            ("🎮", "Развлечения", "#F38181"),
            ("💳", "Счета", "#AA96DA"),
            ("🛍️", "Покупки", "#FCBAD3"),
            ("✈️", "Путешествия", "#A8E6CF"),
            ("💊", "Здоровье", "#FFD3B6"),
        ]
        
        row, col = 0, 0
        for icon, name, color in categories:
            btn = self.create_category_button(icon, name, color)
            layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def create_category_button(self, icon, name, color):
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(80, 90)
        btn.setProperty("category_name", name)
        btn.setProperty("category_color", color)
        btn.clicked.connect(lambda: self.select_category(btn))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 2px solid #E5E5E7;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                border: 2px solid {color};
                background-color: {color}10;
            }}
            QPushButton:checked {{
                border: 3px solid {color};
                background-color: {color}20;
            }}
        """)
        
        btn.setCheckable(True)
        
        layout = QtWidgets.QVBoxLayout(btn)
        layout.setSpacing(5)
        
        iconLabel = QtWidgets.QLabel(icon)
        iconLabel.setAlignment(Qt.AlignCenter)
        iconLabel.setStyleSheet("font-size: 28px; border: none;")
        
        nameLabel = QtWidgets.QLabel(name)
        nameLabel.setAlignment(Qt.AlignCenter)
        nameLabel.setStyleSheet("font-size: 11px; color: #1D1D1F; border: none;")
        nameLabel.setWordWrap(True)
        
        layout.addWidget(iconLabel)
        layout.addWidget(nameLabel)
        
        return btn
    
    def select_category(self, btn):
        # Снимаем выделение со всех кнопок
        for child in self.findChildren(QtWidgets.QPushButton):
            if child != btn:
                child.setChecked(False)
        
        btn.setChecked(True)
        name = btn.property("category_name")
        color = btn.property("category_color")
        self.categorySelected.emit(name, color)


# Пример использования
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Custom Widgets Demo")
    window.setFixedSize(400, 700)
    
    central = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(central)
    layout.setSpacing(20)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Демонстрация виджетов
    animated_btn = AnimatedButton("Нажми меня!")
    animated_btn.setFixedHeight(50)
    animated_btn.setStyleSheet("""
        QPushButton {
            background-color: #007AFF;
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            font-weight: 600;
        }
    """)
    layout.addWidget(animated_btn)
    
    # Круговой прогресс
    progress = CircularProgressBar()
    progress.setValue(75)
    layout.addWidget(progress)
    
    # Переключатель
    switch = ToggleSwitch()
    layout.addWidget(switch)
    
    # Поле ввода суммы
    amount = AmountInput()
    amount.setFixedHeight(50)
    amount.setStyleSheet("""
        QLineEdit {
            border: 2px solid #E5E5E7;
            border-radius: 12px;
            padding: 10px;
            font-size: 18px;
            font-weight: 600;
        }
    """)
    layout.addWidget(amount)
    
    layout.addStretch()
    
    window.setCentralWidget(central)
    window.show()
    
    sys.exit(app.exec_())