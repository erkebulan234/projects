# project_fixed_with_json.py
from email import header
import sys
import os
import json
from datetime import datetime
from turtle import title
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QPoint
from PyQt5.QtWidgets import QGraphicsOpacityEffect

DATA_FILENAME = "data.json"



def createHeader(self, title, back_action="main"):
    header = QtWidgets.QWidget()
    header.setFixedHeight(92)
    header.setStyleSheet("background-color:white;")

    layout = QtWidgets.QHBoxLayout(header)
    layout.setContentsMargins(12,18,12,12)

    backBtn = QtWidgets.QPushButton("←")
    backBtn.setFixedSize(42,42)
    backBtn.clicked.connect(lambda: self.app.navigateTo(back_action))
    backBtn.setStyleSheet("font-size:22px; background:none; border:none; color:#007AFF;")
    layout.addWidget(backBtn)

    titleLabel = QtWidgets.QLabel(title)
    titleLabel.setAlignment(Qt.AlignCenter)
    titleLabel.setStyleSheet("font-size:18px; font-weight:600;")
    layout.addWidget(titleLabel, 1)

    return header


# -----------------------
# custom widgets (atributes.py style)
# -----------------------
class AnimatedButton(QtWidgets.QPushButton):
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
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(90)
        animation.setStartValue(self.geometry())
        new_geo = QRect(self.x()+2, self.y()+2, max(1, self.width()-4), max(1, self.height()-4))
        animation.setEndValue(new_geo)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def animate_release(self):
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(110)
        animation.setStartValue(self.geometry())
        new_geo = QRect(self.x()-2, self.y()-2, self.width()+4, self.height()+4)
        animation.setEndValue(new_geo)
        animation.setEasingCurve(QEasingCurve.OutBounce)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)


class CircularProgressBar(QtWidgets.QWidget):
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
        width = self.width(); height = self.height(); side = min(width, height)
        painter.translate(width / 2, height / 2)
        pen = QtGui.QPen(); pen.setWidth(15); pen.setColor(QtGui.QColor("#E5E5E7")); pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        rect = QRect(-side // 2 + 15, -side // 2 + 15, side - 30, side - 30)
        painter.drawArc(rect, 90 * 16, -360 * 16)
        gradient = QtGui.QConicalGradient(0, 0, 90)
        gradient.setColorAt(0, QtGui.QColor("#667EEA"))
        gradient.setColorAt(1, QtGui.QColor("#764BA2"))
        pen.setBrush(gradient)
        pen.setColor(QtGui.QColor("#667EEA"))
        painter.setPen(pen)
        angle = int(360 * self.value / self.max_value)
        painter.drawArc(rect, 90 * 16, -angle * 16)
        painter.setPen(QtGui.QColor("#1D1D1F"))
        font = painter.font(); font.setPointSize(24); font.setBold(True); painter.setFont(font)
        text = f"{int(self.value)}%"
        painter.drawText(rect, Qt.AlignCenter, text)


class ToggleSwitch(QtWidgets.QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(60, 34)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self); painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor("#34C759") if self.isChecked() else QtGui.QColor("#E5E5E7")
        painter.setBrush(color); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() // 2, self.height() // 2)
        x = self.width() - self.height() + 2 if self.isChecked() else 2
        painter.setBrush(QtGui.QColor("white"))
        circle_size = self.height() - 4
        painter.drawEllipse(x, 2, circle_size, circle_size)


class AmountInput(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("0.00")
        self.textChanged.connect(self.format_amount)

    def format_amount(self, text):
        cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
        if '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) > 2:
                cleaned = parts[0] + '.' + parts[1]
            elif len(parts[1]) > 2:
                cleaned = parts[0] + '.' + parts[1][:2]
        if cleaned:
            try:
                if '.' in cleaned:
                    integer, decimal = cleaned.split('.')
                    formatted = f"{int(integer):,}"
                    if decimal:
                        formatted += f".{decimal}"
                else:
                    formatted = f"{int(cleaned):,}"
                if self.text() != formatted:
                    cursor_pos = self.cursorPosition()
                    self.setText(formatted)
                    self.setCursorPosition(min(cursor_pos, len(formatted)))
            except:
                pass


class ExpenseCategorySelector(QtWidgets.QWidget):
    categorySelected = pyqtSignal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_category = None
        layout = QtWidgets.QGridLayout(self); layout.setSpacing(12)
        self.buttons = []
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
            self.buttons.append(btn)
            col += 1
            if col > 3:
                col = 0; row += 1

    def create_category_button(self, icon, name, color):
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(80, 90)
        btn.setProperty("category_name", name)
        btn.setProperty("category_color", color)
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked, b=btn: self.select_category(b))
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: white; border: 2px solid #E5E5E7; border-radius: 15px; }}
            QPushButton:hover {{ border: 2px solid {color}; background-color: {color}10; }}
            QPushButton:checked {{ border: 3px solid {color}; background-color: {color}20; }}
        """)
        layout = QtWidgets.QVBoxLayout(btn); layout.setSpacing(5); layout.setContentsMargins(0,0,0,0)
        iconLabel = QtWidgets.QLabel(icon); iconLabel.setAlignment(Qt.AlignCenter); iconLabel.setStyleSheet("font-size:28px; border: none;")
        nameLabel = QtWidgets.QLabel(name); nameLabel.setAlignment(Qt.AlignCenter); nameLabel.setStyleSheet("font-size:11px; color:#1D1D1F; border: none;"); nameLabel.setWordWrap(True)
        layout.addWidget(iconLabel); layout.addWidget(nameLabel)
        return btn

    def select_category(self, btn):
        for child in self.findChildren(QtWidgets.QPushButton):
            if child != btn:
                child.setChecked(False)
        btn.setChecked(True)
        name = btn.property("category_name"); color = btn.property("category_color")
        self.selected_category = name
        self.categorySelected.emit(name, color)

# -----------------------
# SlidingStackedWidget for animated transitions
# -----------------------
class SlidingStackedWidget(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def slideToIndex(self, index):
        if index == self.currentIndex():
            return
        current_widget = self.currentWidget(); next_widget = self.widget(index)
        if not current_widget or not next_widget:
            self.setCurrentIndex(index)
            return
        direction = 1 if index > self.currentIndex() else -1
        offset_x = self.width() * direction
        next_widget.setGeometry(offset_x, 0, self.width(), self.height()); next_widget.show()
        anim_current = QPropertyAnimation(current_widget, b"pos", self)
        anim_current.setDuration(280)
        anim_current.setStartValue(QPoint(0, 0))
        anim_current.setEndValue(QPoint(-offset_x, 0))
        anim_current.setEasingCurve(QEasingCurve.OutCubic)
        anim_next = QPropertyAnimation(next_widget, b"pos", self)
        anim_next.setDuration(280)
        anim_next.setStartValue(QPoint(offset_x, 0))
        anim_next.setEndValue(QPoint(0, 0))
        anim_next.setEasingCurve(QEasingCurve.OutCubic)
        anim_current.start(); anim_next.start()
        anim_next.finished.connect(lambda: self.setCurrentIndex(index))


# -----------------------
# Main application
# -----------------------
class FinanceApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Финансовый Трекер")
        self.setFixedSize(400, 700)

        # data
        self.expenses = []
        self.budget = 2550.0
        self.categories = {}  # will be loaded or defaulted

        # load saved data (if exists)
        self.load_data()

        # lazy screens store
        self.screens = {}  # name -> widget instance (created lazily)
        self.screen_order = ["main", "expenses", "subscriptions", "add_expense",
                             "statistics", "profile", "budget", "reports", "settings",
                             "history", "categories", "income", "goals"]

        self.stackedWidget = SlidingStackedWidget()
        self.setCentralWidget(self.stackedWidget)

        # create only main screen eagerly
        main = MainScreen(self)
        self.screens["main"] = main
        self.stackedWidget.addWidget(main)
        self.current_index_map = {"main": 0}  # mapping screen_name -> index in stacked widget

        # apply base style
        self.setStyleSheet("QMainWindow { background-color: #F5F5F7; }")

    # ----- persistence -----
    def load_data(self):
        if os.path.exists(DATA_FILENAME):
            try:
                with open(DATA_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.categories = data.get("categories", {})
                self.expenses = data.get("expenses", [])
                self.budget = float(data.get("budget", self.budget))
            except Exception as e:
                print("Ошибка загрузки data.json:", e)
                self.set_default_data()
        else:
            self.set_default_data()
            self.save_data()  # create file with defaults

    def set_default_data(self):
        # default categories
        self.categories = {
            "Еда": {"spent": 842.50, "budget": 800, "color": "#FF6B6B", "icon": "🍔"},
            "Транспорт": {"spent": 650.00, "budget": 500, "color": "#4ECDC4", "icon": "🚗"},
            "Дом": {"spent": 520.30, "budget": 600, "color": "#95E1D3", "icon": "🏠"},
            "Развлечения": {"spent": 380.00, "budget": 300, "color": "#F38181", "icon": "🎮"},
        }
        self.expenses = []
        self.budget = 2550.0

    def save_data(self):
        try:
            data = {"categories": self.categories, "expenses": self.expenses, "budget": self.budget}
            with open(DATA_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Ошибка сохранения data.json:", e)



    # ----- navigation + lazy creation -----
    def navigateTo(self, screen_name):
        # if exists in map -> slide to it directly
        if screen_name in self.current_index_map:
            idx = self.current_index_map[screen_name]
            self.stackedWidget.slideToIndex(idx)
            return

        # otherwise, create lazily, append to stackedWidget and map
        widget = None
        if screen_name == "expenses":
            widget = ExpensesScreen(self)
        elif screen_name == "subscriptions":
            widget = SubscriptionsScreen(self)
        elif screen_name == "add_expense":
            widget = AddExpenseScreen(self)
        elif screen_name == "statistics":
            widget = StatisticsScreen(self)
        elif screen_name == "profile":
            widget = ProfileScreen(self)
        elif screen_name == "budget":
            widget = BudgetScreen(self)
        elif screen_name == "reports":
            widget = ReportsScreen(self)
        elif screen_name == "settings":
            widget = SettingsScreen(self)
        elif screen_name == "history":
            widget = HistoryScreen(self)
        elif screen_name == "categories":
            widget = CategoriesScreen(self)
        elif screen_name == "income":
            widget = IncomeScreen(self)
        elif screen_name == "goals":
            widget = GoalsScreen(self)
        else:
            print("Unknown screen:", screen_name)
            return

        # register and show
        if widget is not None:
            self.screens[screen_name] = widget
            self.stackedWidget.addWidget(widget)
            new_index = self.stackedWidget.count() - 1
            self.current_index_map[screen_name] = new_index
            self.stackedWidget.slideToIndex(new_index)

    # ----- data operations -----
    def addExpense(self, amount, category, description="", date=None):
        try:
            amt = float(str(amount).replace(",", "").replace(" ", ""))
        except:
            try:
                amt = float(amount.replace(",", "."))
            except:
                amt = 0.0
        if date is None:
            date = datetime.now().isoformat()
        expense = {"amount": amt, "category": category, "description": description, "date": date}
        self.expenses.insert(0, expense)  # newest first
        # update categories
        if category:
            if category not in self.categories:
                # create with defaults
                self.categories[category] = {"spent": amt, "budget": 0.0, "color": "#CCCCCC", "icon": "❓"}
            else:
                self.categories[category]["spent"] = round(self.categories[category].get("spent", 0.0) + amt, 2)
        self.save_data()

def refresh_categories(self):
    # Step 1 — сбросить траты
    for k in self.categories.keys():
        self.categories[k]["spent"] = 0.0

    # Step 2 — пересчитать траты по всем расходам
    for exp in self.expenses:
        cat = exp["category"]
        amt = float(exp["amount"])

        if cat not in self.categories:
            self.categories[cat] = {
                "spent": amt,
                "budget": 0,
                "color": "#CCCCCC",
                "icon": "❓"
            }
        else:
            self.categories[cat]["spent"] += amt

    # Step 3 — сохранить
    self.save_data()

# -----------------------
# Screens (UI)
# -----------------------
class MainScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        header = QtWidgets.QWidget(); header.setFixedHeight(100)
        header.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #667EEA, stop:1 #764BA2);")
        headerLayout = QtWidgets.QVBoxLayout(header); headerLayout.setContentsMargins(20,40,20,20)
        titleLabel = QtWidgets.QLabel("Финансовый Трекер 💰"); titleLabel.setStyleSheet("font-size:24px; font-weight:700; color:white;")
        headerLayout.addWidget(titleLabel)
        scrollArea = QtWidgets.QScrollArea(); scrollArea.setWidgetResizable(True); scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F7; }")
        scrollContent = QtWidgets.QWidget(); scrollLayout = QtWidgets.QVBoxLayout(scrollContent); scrollLayout.setContentsMargins(20,20,20,20); scrollLayout.setSpacing(15)
        actionsLabel = QtWidgets.QLabel("Быстрые действия"); actionsLabel.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F;"); scrollLayout.addWidget(actionsLabel)
        actionsLayout = QtWidgets.QGridLayout(); actionsLayout.setSpacing(15)
        self.addActionCard("💸", "Затраты", "Просмотр расходов", "expenses", actionsLayout, 0, 0)
        self.addActionCard("📊", "Статистика", "Анализ трат", "statistics", actionsLayout, 0, 1)
        self.addActionCard("📋", "Подписки", "Управление", "subscriptions", actionsLayout, 1, 0)
        self.addActionCard("💰", "Бюджет", "Планирование", "budget", actionsLayout, 1, 1)
        scrollLayout.addLayout(actionsLayout)
        addExpenseBtn = QtWidgets.QPushButton("+ Добавить расход"); addExpenseBtn.setFixedHeight(60)
        addExpenseBtn.clicked.connect(lambda: self.app.navigateTo("add_expense"))
        addExpenseBtn.setStyleSheet("QPushButton{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #11998E, stop:1 #38EF7D); border:none; border-radius:15px; font-size:18px; font-weight:600; color:white;} QPushButton:hover{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0D7A72, stop:1 #2DBF64); }")
        scrollLayout.addWidget(addExpenseBtn)
        recentLabel = QtWidgets.QLabel("Последние транзакции"); recentLabel.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F; margin-top:10px;"); scrollLayout.addWidget(recentLabel)

        # show up to 6 recent transactions
        for e in self.app.expenses[:6]:
            amt = float(e.get("amount", 0.0))
            sign = "-" if amt < 0 else ""
            pretty = f"{sign}${abs(amt):.2f}"
            self.addTransaction(e.get("category", "—"), e.get("description", ""), pretty, e.get("date", ""), scrollLayout)

        scrollLayout.addStretch()
        scrollArea.setWidget(scrollContent)
        layout.addWidget(header); layout.addWidget(scrollArea)
        self.addBottomNav(layout)

    def addActionCard(self, icon, title, subtitle, action, layout, row, col):
        card = QtWidgets.QPushButton(); card.setFixedSize(170,120); card.clicked.connect(lambda checked=False, a=action: self.app.navigateTo(a))
        card.setStyleSheet("QPushButton{ background-color:white; border-radius:20px; text-align:left; padding:20px;} QPushButton:hover{ background-color:#F0F8FF; border:2px solid #007AFF; }")
        cardLayout = QtWidgets.QVBoxLayout(card); cardLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        iconLabel = QtWidgets.QLabel(icon); iconLabel.setStyleSheet("font-size:36px;"); titleLabel = QtWidgets.QLabel(title); titleLabel.setStyleSheet("font-size:16px; font-weight:600; color:#1D1D1F;")
        subtitleLabel = QtWidgets.QLabel(subtitle); subtitleLabel.setStyleSheet("font-size:12px; color:#86868B;")
        cardLayout.addWidget(iconLabel); cardLayout.addWidget(titleLabel); cardLayout.addWidget(subtitleLabel)
        layout.addWidget(card, row, col)

    def addTransaction(self, icon, title, amount, time, layout):
        card = QtWidgets.QWidget(); card.setFixedHeight(70); card.setStyleSheet("QWidget{ background-color:white; border-radius:15px; }")
        cardLayout = QtWidgets.QHBoxLayout(card); cardLayout.setContentsMargins(15,10,15,10)
        iconLabel = QtWidgets.QLabel("💸"); iconLabel.setFixedSize(40,40); iconLabel.setAlignment(Qt.AlignCenter); iconLabel.setStyleSheet("font-size:18px; background-color:#F5F5F7; border-radius:10px;")
        infoLayout = QtWidgets.QVBoxLayout(); titleLabel = QtWidgets.QLabel(icon + " " + title); titleLabel.setStyleSheet("font-size:15px; font-weight:500; color:#1D1D1F;")
        timeLabel = QtWidgets.QLabel(time); timeLabel.setStyleSheet("font-size:12px; color:#86868B;")
        infoLayout.addWidget(titleLabel); infoLayout.addWidget(timeLabel)
        amountLabel = QtWidgets.QLabel(amount); amountLabel.setStyleSheet("font-size:16px; font-weight:600; color:#FF3B30;"); amountLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cardLayout.addWidget(iconLabel); cardLayout.addSpacing(10); cardLayout.addLayout(infoLayout, 1); cardLayout.addWidget(amountLabel)
        layout.addWidget(card)

    def addBottomNav(self, layout):
        nav = QtWidgets.QWidget(); nav.setFixedHeight(80); nav.setStyleSheet("background-color:white;"); navLayout = QtWidgets.QHBoxLayout(nav); navLayout.setContentsMargins(6,10,6,10)
        buttons = [
            ("🏠", "Главная", "main"),
            ("📊", "Статистика", "statistics"),
            ("💳", "Счета", "subscriptions"),
            ("📑", "Отчёты", "reports"),
            ("⚙️", "Настройки", "settings"),
        ]
        for icon, text, action in buttons:
            btn = QtWidgets.QPushButton(); btn.setFixedSize(68, 60)
            btn.clicked.connect(lambda checked=False, a=action: self.app.navigateTo(a))
            btnLayout = QtWidgets.QVBoxLayout(btn); btnLayout.setSpacing(2); btnLayout.setContentsMargins(0,0,0,0)
            iconLabel = QtWidgets.QLabel(icon); iconLabel.setAlignment(Qt.AlignCenter); iconLabel.setStyleSheet("font-size:20px;")
            textLabel = QtWidgets.QLabel(text); textLabel.setAlignment(Qt.AlignCenter); textLabel.setStyleSheet("font-size:10px; color:#86868B;")
            btnLayout.addWidget(iconLabel); btnLayout.addWidget(textLabel)
            btn.setStyleSheet("QPushButton{ background-color:transparent; border:none; }")
            navLayout.addWidget(btn)
        layout.addWidget(nav)


class ExpensesScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.container_layout = None
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        header = self.createHeader("Затраты", True, True); layout.addWidget(header)

        # controls row with refresh
        ctrl = QtWidgets.QWidget(); ctrlL = QtWidgets.QHBoxLayout(ctrl); ctrlL.setContentsMargins(16,8,16,8)
        refresh_btn = QtWidgets.QPushButton("🔄 Обновить категории"); refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.on_refresh_clicked)
        ctrlL.addWidget(refresh_btn)
        ctrlL.addStretch()
        layout.addWidget(ctrl)

        scrollArea = QtWidgets.QScrollArea(); scrollArea.setWidgetResizable(True); scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F5F5F7; }")
        scrollContent = QtWidgets.QWidget()
        self.container_layout = QtWidgets.QVBoxLayout(scrollContent); self.container_layout.setContentsMargins(20,20,20,20)
        totalCard = QtWidgets.QWidget(); totalCard.setFixedHeight(120); totalCard.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #FF6B6B, stop:1 #F38181); border-radius:20px;")
        totalLayout = QtWidgets.QVBoxLayout(totalCard); totalLayout.setContentsMargins(25,20,25,20)
        totalLabel = QtWidgets.QLabel("Всего потрачено"); totalLabel.setStyleSheet("font-size:14px; color: rgba(255,255,255,0.9);")
        totalAmount = QtWidgets.QLabel(f"${sum(e.get('amount', 0.0) for e in self.app.expenses):.2f}"); totalAmount.setStyleSheet("font-size:36px; font-weight:700; color:white;")
        totalLayout.addWidget(totalLabel); totalLayout.addWidget(totalAmount)
        self.container_layout.addWidget(totalCard); self.container_layout.addSpacing(12)
        expensesLabel = QtWidgets.QLabel("По категориям"); expensesLabel.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F;"); self.container_layout.addWidget(expensesLabel)

        # category list
        self.build_category_list()

        self.container_layout.addStretch()
        scrollArea.setWidget(scrollContent)
        layout.addWidget(scrollArea)

    def build_category_list(self):
        # clear existing category item widgets (except first two widgets in layout which are totalCard and label)
        # but simpler: remove all widgets after the "По категориям" label and then re-add
        while self.container_layout.count() > 3:
            item = self.container_layout.takeAt(3)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        for category, data in self.app.categories.items():
            self.addExpenseItem(category, data, self.container_layout)

    def addExpenseItem(self, category, data, layout):
        card = QtWidgets.QWidget(); card.setFixedHeight(80); card.setStyleSheet("background-color:white; border-radius:15px;")
        cardLayout = QtWidgets.QHBoxLayout(card); cardLayout.setContentsMargins(12,12,12,12)
        icon = QtWidgets.QLabel(data.get("icon", "❓")); icon.setFixedSize(50,50); icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"background-color: {data.get('color','#CCCCCC')}20; border-radius:12px; font-size:22px;")
        name = QtWidgets.QLabel(category); name.setStyleSheet("font-size:16px; font-weight:500; color:#1D1D1F;")
        amount = QtWidgets.QLabel(f"${data.get('spent', 0.0):.2f}"); amount.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F;")
        cardLayout.addWidget(icon); cardLayout.addSpacing(12); cardLayout.addWidget(name, 1); cardLayout.addWidget(amount)
        layout.addWidget(card)

    def createHeader(self, title, back=True, add=False):
        header = QtWidgets.QWidget(); header.setFixedHeight(92); header.setStyleSheet("background-color:white;")
        headerLayout = QtWidgets.QHBoxLayout(header); headerLayout.setContentsMargins(12,18,12,12)
        if back:
            backBtn = QtWidgets.QPushButton("<"); backBtn.setFixedSize(42,42); backBtn.clicked.connect(lambda: self.app.navigateTo("main"))
            backBtn.setStyleSheet("QPushButton{ background-color:transparent; border:none; font-size:22px; color:#007AFF; }"); headerLayout.addWidget(backBtn)
        titleLabel = QtWidgets.QLabel(title); titleLabel.setAlignment(Qt.AlignCenter); titleLabel.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F;"); headerLayout.addWidget(titleLabel, 1)
        if add:
            addBtn = QtWidgets.QPushButton("+"); addBtn.setFixedSize(42,42); addBtn.clicked.connect(lambda: self.app.navigateTo("add_expense"))
            addBtn.setStyleSheet("QPushButton{ background-color:transparent; border:none; font-size:22px; color:#007AFF; }"); headerLayout.addWidget(addBtn)
        return header

    def on_refresh_clicked(self):
        self.app.refresh_categories()
        self.build_category_list()
        QtWidgets.QMessageBox.information(self, "Обновлено", "Категории и суммы обновлены.")


class AddExpenseScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.selected_category = None
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        header = self.createHeader("Новый расход", True); layout.addWidget(header)
        formLayout = QtWidgets.QVBoxLayout(); formLayout.setContentsMargins(20,20,20,20); formLayout.setSpacing(12)
        self.amountInput = AmountInput(); self.amountInput.setPlaceholderText("Сумма (например 12.50)"); self.amountInput.setFixedHeight(46)
        self.selector = ExpenseCategorySelector(); self.selector.categorySelected.connect(self.on_category_selected)
        self.descInput = QtWidgets.QLineEdit(); self.descInput.setPlaceholderText("Описание"); self.descInput.setFixedHeight(40)
        saveBtn = QtWidgets.QPushButton("Сохранить"); saveBtn.setFixedHeight(50)
        saveBtn.clicked.connect(self.on_save_clicked)
        saveBtn.setStyleSheet("QPushButton{ background-color:#007AFF; border:none; border-radius:12px; font-size:16px; font-weight:600; color:white; }")
        formLayout.addWidget(self.amountInput); formLayout.addWidget(self.selector); formLayout.addWidget(self.descInput); formLayout.addWidget(saveBtn)
        formLayout.addStretch()
        layout.addLayout(formLayout)

    def createHeader(self, title, back=True):
        header = QtWidgets.QWidget(); header.setFixedHeight(88); header.setStyleSheet("background-color:white;")
        headerLayout = QtWidgets.QHBoxLayout(header); headerLayout.setContentsMargins(12,18,12,12)
        if back:
            backBtn = QtWidgets.QPushButton("←"); backBtn.setFixedSize(42,42); backBtn.clicked.connect(lambda: self.app.navigateTo("main"))
            backBtn.setStyleSheet("QPushButton{ background-color:transparent; border:none; font-size:22px; color:#007AFF; }"); headerLayout.addWidget(backBtn)
        titleLabel = QtWidgets.QLabel(title); titleLabel.setAlignment(Qt.AlignCenter); titleLabel.setStyleSheet("font-size:18px; font-weight:600; color:#1D1D1F;"); headerLayout.addWidget(titleLabel, 1)
        return header

    def on_category_selected(self, name, color):
        self.selected_category = name

    def on_save_clicked(self):
        text = self.amountInput.text().replace(",", "").replace(" ", "")
        if not text:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите сумму.")
            return
        if self.selector.selected_category is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите категорию.")
            return
        # parse float
        try:
            amt = float(text)
        except:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Неверный формат суммы.")
            return
        desc = self.descInput.text() or ""
        self.app.addExpense(amt, self.selector.selected_category, desc, datetime.now().isoformat())
        QtWidgets.QMessageBox.information(self, "Успешно", f"Расход ${amt:.2f} добавлен.")
        # navigate back to expenses and refresh it if exists
        if "expenses" in self.app.screens:
            # rebuild expenses screen UI to reflect new data
            screen = self.app.screens["expenses"]
            screen.build_category_list()
        self.app.navigateTo("expenses")

class SubscriptionsScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Подписки"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel("Экран подписок — пример."))

class StatisticsScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Статистика"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        cp = CircularProgressBar(); cp.setValue(64); cp.setFixedSize(220,220)
        box = QtWidgets.QWidget(); bl = QtWidgets.QVBoxLayout(box); bl.setAlignment(Qt.AlignCenter); bl.addWidget(cp)
        layout.addWidget(box)

    def createHeader(self, title, back_action="main"):
        header = QtWidgets.QWidget()
        header.setFixedHeight(92)
        header.setStyleSheet("background-color:white;")

        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(12,18,12,12)

        backBtn = QtWidgets.QPushButton("←")
        backBtn.setFixedSize(42,42)
        backBtn.clicked.connect(lambda: self.app.navigateTo(back_action))
        backBtn.setStyleSheet("font-size:22px; background:none; border:none; color:#007AFF;")
        layout.addWidget(backBtn)

        titleLabel = QtWidgets.QLabel(title)
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setStyleSheet("font-size:18px; font-weight:600;")
        layout.addWidget(titleLabel, 1)
        layout.addWidget(self.createHeader("Статистика", "main"))
        return header



class ProfileScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QWidget(); header.setFixedHeight(160)
        header.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #667EEA, stop:1 #764BA2);")
        headerLayout = QtWidgets.QVBoxLayout(header); headerLayout.setAlignment(Qt.AlignCenter)
        avatar = QtWidgets.QLabel("👤"); avatar.setStyleSheet("font-size:48px; color:white;"); avatar.setAlignment(Qt.AlignCenter)
        name = QtWidgets.QLabel("Иван Иванов"); name.setStyleSheet("font-size:20px; font-weight:700; color:white;"); name.setAlignment(Qt.AlignCenter)
        headerLayout.addWidget(avatar); headerLayout.addWidget(name)
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel("Детальная информация профиля — пример."))
        b = QtWidgets.QPushButton("← Назад"); b.clicked.connect(lambda: self.app.navigateTo("main")); layout.addWidget(b)

class BudgetScreen(QtWidgets.QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.createHeader("Бюджет"))

        inputLabel = QtWidgets.QLabel("Введите новый бюджет:")
        inputLabel.setStyleSheet("font-size:14px;")
        layout.addWidget(inputLabel)

        self.budgetInput = QtWidgets.QLineEdit()
        self.budgetInput.setText(str(self.app.budget))
        self.budgetInput.setFixedHeight(40)
        layout.addWidget(self.budgetInput)

        saveBtn = QtWidgets.QPushButton("Сохранить бюджет")
        saveBtn.setFixedHeight(45)
        saveBtn.clicked.connect(self.saveBudget)
        saveBtn.setStyleSheet("font-size:16px; background:#007AFF; color:white; border-radius:10px;")
        layout.addWidget(saveBtn)

        layout.addStretch()

    def saveBudget(self):
        try:
            new_budget = float(self.budgetInput.text())
            self.app.budget = new_budget
            self.app.save_data()
            QtWidgets.QMessageBox.information(self, "OK", "Бюджет сохранён.")
        except:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите корректное число.")

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Бюджет"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel(f"Текущий бюджет: ${self.app.budget:.2f}"))

class ReportsScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Отчёты"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel("Генерация отчётов — пример."))

# New extra screens
class HistoryScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("История операций"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        for e in self.app.expenses:
            layout.addWidget(QtWidgets.QLabel(f"{e.get('date','')[:19]} — {e.get('category','')} — ${e.get('amount',0.0):.2f} — {e.get('description','')}"))

class CategoriesScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Категории"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        for k, v in self.app.categories.items():
            layout.addWidget(QtWidgets.QLabel(f"{v.get('icon','')} {k} — spent: ${v.get('spent',0.0):.2f} — budget: ${v.get('budget',0.0):.2f}"))

class IncomeScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Доходы"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel("Экран доходов — пример."))

class GoalsScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Цели"); header.setStyleSheet("font-size:22px; font-weight:700; padding:18px;")
        layout.addWidget(header)
        layout.addWidget(QtWidgets.QLabel("Экран целей — пример."))

class SettingsScreen(QtWidgets.QWidget):
    def __init__(self, app: FinanceApp):
        super().__init__()
        self.app = app
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setContentsMargins(16,16,16,16)
        header = QtWidgets.QLabel("Настройки"); header.setStyleSheet("font-size:22px; font-weight:700;")
        layout.addWidget(header)
        themeRow = QtWidgets.QHBoxLayout()
        themeRow.addWidget(QtWidgets.QLabel("Тёмная тема"))
        toggle = ToggleSwitch(); themeRow.addWidget(toggle); themeRow.addStretch()
        layout.addLayout(themeRow)
        currencyRow = QtWidgets.QHBoxLayout(); currencyRow.addWidget(QtWidgets.QLabel("Валюта:")); currencyCombo = QtWidgets.QComboBox(); currencyCombo.addItems(["USD", "KZT", "EUR"]); currencyRow.addWidget(currencyCombo); currencyRow.addStretch()
        layout.addLayout(currencyRow)
        saveBtn = QtWidgets.QPushButton("Сохранить настройки"); saveBtn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Сохранено", "Настройки сохранены"))
        layout.addWidget(saveBtn)
        layout.addStretch()

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app_qt = QtWidgets.QApplication(sys.argv)
    font = QtGui.QFont("Segoe UI", 10)
    app_qt.setFont(font)
    window = FinanceApp()
    window.show()
    sys.exit(app_qt.exec_())
