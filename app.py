# app.py
import sys
import os
import json
from datetime import datetime
from functools import partial

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox

# matplotlib for charts
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

UI_FILE = "main.ui"
DATA_FILE = "data.json"

# -------------------------
# Simple persistence
# -------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Ошибка загрузки data.json:", e)
    # defaults
    return {
        "budget": 2550.0,
        "categories": {
            "Еда": {"spent": 842.50, "budget": 800, "color": "#FF6B6B", "icon": "🍔"},
            "Транспорт": {"spent": 650.00, "budget": 500, "color": "#4ECDC4", "icon": "🚗"},
            "Дом": {"spent": 520.30, "budget": 600, "color": "#95E1D3", "icon": "🏠"},
            "Развлечения": {"spent": 380.00, "budget": 300, "color": "#F38181", "icon": "🎮"},
        },
        "expenses": [],
        "subscriptions": [],
        "theme": "light"
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Ошибка сохранения data.json:", e)

# -------------------------
# Fullscreen modal for category choice
# -------------------------
class CategoryPickerDialog(QDialog):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.selected = None
        self.resize(parent.width(), parent.height())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40,40,40,40)
        title = QLabel("Выберите категорию")
        title.setStyleSheet("font-size:20px; font-weight:700; color:white;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        buttons_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(buttons_widget)
        grid.setSpacing(12)
        row = col = 0
        for k, v in categories.items():
            b = QPushButton(f"{v.get('icon','❓')}  {k}")
            b.setFixedHeight(56)
            b.setStyleSheet("font-size:16px; border-radius:10px;")
            b.clicked.connect(partial(self.choose, k))
            grid.addWidget(b, row, col)
            col += 1
            if col > 2:
                col = 0; row += 1
        layout.addWidget(buttons_widget)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel, alignment=Qt.AlignCenter)
        # dark background
        self.setStyleSheet("QDialog{ background: rgba(0,0,0,0.75);} QPushButton{ background:white; }")

    def choose(self, name):
        self.selected = name
        self.accept()

# -------------------------
# Add Expense full-screen dialog
# -------------------------
class AddExpenseDialog(QDialog):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Добавить расход")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(parent.width(), parent.height())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24,24,24,24)
        header = QLabel("Добавить расход")
        header.setStyleSheet("font-size:20px; font-weight:700;")
        layout.addWidget(header)
        self.amount_input = QtWidgets.QLineEdit(); self.amount_input.setPlaceholderText("Сумма, например 12.50")
        layout.addWidget(self.amount_input)
        self.desc_input = QtWidgets.QLineEdit(); self.desc_input.setPlaceholderText("Описание")
        layout.addWidget(self.desc_input)
        self.cat_btn = QPushButton("Выбрать категорию")
        self.cat_label = QLabel("Категория: —")
        self.cat_name = None
        self.cat_btn.clicked.connect(self.pick_category)
        layout.addWidget(self.cat_btn); layout.addWidget(self.cat_label)
        self.date_input = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addWidget(self.date_input)
        btn_save = QPushButton("Сохранить"); btn_save.clicked.connect(self.on_save)
        btn_cancel = QPushButton("Отмена"); btn_cancel.clicked.connect(self.reject)
        row = QtWidgets.QHBoxLayout(); row.addWidget(btn_cancel); row.addWidget(btn_save)
        layout.addLayout(row)
        self.setStyleSheet("""
            QDialog{ background: white; }
            QLineEdit, QDateTimeEdit{ padding:10px; font-size:16px; border-radius:8px; border:1px solid #ddd; }
            QPushButton{ padding:10px; font-size:16px; border-radius:8px; }
        """)

    def pick_category(self):
        dlg = CategoryPickerDialog(self, self.data["categories"])
        if dlg.exec_():
            self.cat_name = dlg.selected
            self.cat_label.setText(f"Категория: {self.cat_name}")

    def on_save(self):
        text = self.amount_input.text().strip().replace(",", ".")
        try:
            amt = float(text)
        except:
            QMessageBox.warning(self, "Ошибка", "Неверная сумма")
            return
        if not self.cat_name:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию")
            return
        desc = self.desc_input.text().strip()
        date = self.date_input.dateTime().toString("yyyy-MM-dd HH:mm")
        expense = {"amount": amt, "category": self.cat_name, "description": desc, "date": date}
        # persist to data
        self.data["expenses"].insert(0, expense)
        # update category spent
        cat = self.data["categories"].get(self.cat_name)
        if cat:
            cat["spent"] = round(cat.get("spent", 0.0) + amt, 2)
        else:
            self.data["categories"][self.cat_name] = {"spent": amt, "budget": 0.0, "color": "#CCCCCC", "icon": "❓"}
        save_data(self.data)
        self.accept()

# -------------------------
# Subscriptions dialog (simple add)
# -------------------------
class AddSubscriptionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Добавить подписку")
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.name_in = QtWidgets.QLineEdit(); self.name_in.setPlaceholderText("Название")
        self.amount_in = QtWidgets.QLineEdit(); self.amount_in.setPlaceholderText("Ежемесячно")
        layout.addWidget(QLabel("Название")); layout.addWidget(self.name_in)
        layout.addWidget(QLabel("Сумма в месяц")); layout.addWidget(self.amount_in)
        btn_ok = QPushButton("Добавить"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена"); btn_cancel.clicked.connect(self.reject)
        row = QtWidgets.QHBoxLayout(); row.addWidget(btn_cancel); row.addWidget(btn_ok); layout.addLayout(row)

# -------------------------
# Matplotlib canvas helper
# -------------------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)

# -------------------------
# Main UI controller
# -------------------------
class UIController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # load UI
        if not os.path.exists(UI_FILE):
            raise FileNotFoundError(f"{UI_FILE} not found in current folder.")
        uic.loadUi(UI_FILE, self)

        # load data
        self.data = load_data()

        # find important widgets by objectName (those exist in main.ui from canvas)
        self.stacked = self.findChild(QtWidgets.QStackedWidget, "stackedWidget")
        self.listCategories = self.findChild(QtWidgets.QListWidget, "listCategories")
        self.listRecent = self.findChild(QtWidgets.QListWidget, "listRecent")
        self.tableCategories = self.findChild(QtWidgets.QTableWidget, "tableCategories")
        self.tableHistory = self.findChild(QtWidgets.QTableWidget, "tableHistory")
        self.labelBudgetAmount = self.findChild(QtWidgets.QLabel, "labelBudgetAmount")
        # buttons
        self.btnAddTop = self.findChild(QtWidgets.QPushButton, "btnAddExpenseTop")
        self.btnRefresh = self.findChild(QtWidgets.QPushButton, "btnRefreshCategories")
        # bottom nav
        self.navHome = self.findChild(QtWidgets.QPushButton, "navHome")
        self.navStats = self.findChild(QtWidgets.QPushButton, "navStats")
        self.navSubscriptions = self.findChild(QtWidgets.QPushButton, "navSubscriptions")
        self.navReports = self.findChild(QtWidgets.QPushButton, "navReports")
        self.navSettings = self.findChild(QtWidgets.QPushButton, "navSettings")
        # quick actions
        self.btnExpenses = self.findChild(QtWidgets.QPushButton, "btnExpenses")
        self.btnStatistics = self.findChild(QtWidgets.QPushButton, "btnStatistics")
        self.btnSubscriptionsTop = self.findChild(QtWidgets.QPushButton, "btnSubscriptions")
        self.btnBudget = self.findChild(QtWidgets.QPushButton, "btnBudget")

        # connect navigation
        self.setup_navigation()
        # handlers
        if self.btnAddTop:
            self.btnAddTop.clicked.connect(self.open_add_expense)
        if self.btnRefresh:
            self.btnRefresh.clicked.connect(self.on_refresh_categories)

        # add programmatic pages if needed: charts, subscriptions, add-expense page (we open dialogs for add)
        self.ensure_chart_page()
        self.ensure_subscriptions_page()
        self.apply_theme(self.data.get("theme","light"))

        # initial refresh UI
        self.refresh_all_ui()

    def setup_navigation(self):
        # nav buttons switch pages by index based on main.ui creation order
        name_to_index = {
            "home": 0,
            "expenses": 1,
            "categories": 2,
            "budget": 3,
            "history": 4,
            "profile": 5
        }
        # bottom nav mapping (if exists in UI)
        if self.navHome: self.navHome.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["home"]))
        if self.navStats: self.navStats.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["history"]))
        if self.navSubscriptions: self.navSubscriptions.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["categories"]))
        if self.navReports: self.navReports.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["history"]))
        if self.navSettings: self.navSettings.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["profile"]))

        if self.btnExpenses: self.btnExpenses.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["expenses"]))
        if self.btnStatistics: self.btnStatistics.clicked.connect(lambda: self.open_charts_page())
        if self.btnSubscriptionsTop: self.btnSubscriptionsTop.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["categories"]))
        if self.btnBudget: self.btnBudget.clicked.connect(lambda: self.stacked.setCurrentIndex(name_to_index["budget"]))

    # -------------------------
    # Programmatic pages
    # -------------------------
    def ensure_chart_page(self):
        # create a charts page and append to stacked if not exists
        if not hasattr(self, "charts_index"):
            charts_page = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(charts_page)
            header = QLabel("Статистика"); header.setStyleSheet("font-size:20px; font-weight:700; padding:8px;")
            layout.addWidget(header)
            # pie chart canvas
            self.pie_canvas = MplCanvas(self, width=4, height=3, dpi=100)
            layout.addWidget(self.pie_canvas)
            # bar chart canvas
            self.bar_canvas = MplCanvas(self, width=4, height=3, dpi=100)
            layout.addWidget(self.bar_canvas)
            idx = self.stacked.addWidget(charts_page)
            self.charts_index = idx

    def open_charts_page(self):
        self.update_charts()
        self.stacked.setCurrentIndex(self.charts_index)

    def ensure_subscriptions_page(self):
        if not hasattr(self, "subs_index"):
            subs_page = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(subs_page)
            header = QLabel("Подписки"); header.setStyleSheet("font-size:20px; font-weight:700; padding:8px;")
            layout.addWidget(header)
            self.subs_list = QtWidgets.QListWidget()
            layout.addWidget(self.subs_list)
            btn_add = QPushButton("Добавить подписку")
            btn_add.clicked.connect(self.open_add_subscription)
            layout.addWidget(btn_add)
            idx = self.stacked.addWidget(subs_page)
            self.subs_index = idx

    def open_add_subscription(self):
        dlg = AddSubscriptionDialog(self)
        if dlg.exec_():
            name = dlg.name_in.text().strip()
            try:
                amount = float(dlg.amount_in.text().strip().replace(",", "."))
            except:
                QMessageBox.warning(self, "Ошибка", "Неверная сумма")
                return
            self.data.setdefault("subscriptions", []).append({"name": name, "amount": amount})
            save_data(self.data)
            self.refresh_subscriptions()

    # -------------------------
    # UI refreshers
    # -------------------------
    def refresh_all_ui(self):
        self.refresh_categories_table()
        self.refresh_history()
        self.refresh_subscriptions()
        self.refresh_budget()
        self.refresh_recent_list()

    def refresh_recent_list(self):
        if not self.listRecent:
            return
        self.listRecent.clear()
        for exp in self.data.get("expenses", [])[:10]:
            self.listRecent.addItem(f"{exp.get('category','—')} — ${float(exp.get('amount',0)):.2f} — {exp.get('description','')}")

    def refresh_categories_table(self):
        if not self.tableCategories or not self.listCategories:
            return
        self.listCategories.clear()
        cats = self.data.get("categories", {})
        self.tableCategories.setRowCount(0)
        for name, info in cats.items():
            self.listCategories.addItem(f"{info.get('icon','❓')} {name} — ${info.get('spent',0.0):.2f}")
            r = self.tableCategories.rowCount()
            self.tableCategories.insertRow(r)
            self.tableCategories.setItem(r, 0, QtWidgets.QTableWidgetItem(info.get("icon","")))
            self.tableCategories.setItem(r, 1, QtWidgets.QTableWidgetItem(name))
            self.tableCategories.setItem(r, 2, QtWidgets.QTableWidgetItem(f"${info.get('spent',0.0):.2f}"))
            self.tableCategories.setItem(r, 3, QtWidgets.QTableWidgetItem(str(info.get('budget',0.0))))

    def refresh_history(self):
        if not self.tableHistory:
            return
        self.tableHistory.setRowCount(0)
        for e in self.data.get("expenses", []):
            r = self.tableHistory.rowCount()
            self.tableHistory.insertRow(r)
            self.tableHistory.setItem(r, 0, QtWidgets.QTableWidgetItem(str(e.get("date",""))))
            self.tableHistory.setItem(r, 1, QtWidgets.QTableWidgetItem(e.get("category","")))
            self.tableHistory.setItem(r, 2, QtWidgets.QTableWidgetItem(f"${float(e.get('amount',0)):.2f}"))
            self.tableHistory.setItem(r, 3, QtWidgets.QTableWidgetItem(e.get("description","")))

    def refresh_subscriptions(self):
        if not hasattr(self, "subs_list"):
            return
        self.subs_list.clear()
        total = 0.0
        for s in self.data.get("subscriptions", []):
            self.subs_list.addItem(f"{s.get('name')} — ${float(s.get('amount',0)):.2f}/mo")
            total += float(s.get('amount',0))
        # optionally show aggregate
        self.subs_list.addItem(f"--- Всего: ${total:.2f}/mo ---")

    def refresh_budget(self):
        if not self.labelBudgetAmount:
            return
        self.labelBudgetAmount.setText(f"${float(self.data.get('budget',0.0)):.2f}")

    # -------------------------
    # Charts
    # -------------------------
    def update_charts(self):
        # pie chart by categories spent
        cats = self.data.get("categories", {})
        labels = []
        sizes = []
        for k,v in cats.items():
            labels.append(k)
            sizes.append(max(0.0, float(v.get("spent", 0.0))))
        # update pie
        self.pie_canvas.ax.clear()
        if sum(sizes) > 0:
            self.pie_canvas.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            self.pie_canvas.ax.set_title("Расходы по категориям")
        else:
            self.pie_canvas.ax.text(0.5,0.5,"Нет данных для графика", ha='center')
        self.pie_canvas.draw()

        # bar chart: last 7 expenses amounts
        exps = self.data.get("expenses", [])[:7]
        exps = exps[::-1]  # older -> newer in left->right
        names = [e.get("category","") for e in exps]
        vals = [float(e.get("amount",0.0)) for e in exps]
        self.bar_canvas.ax.clear()
        if vals:
            self.bar_canvas.ax.bar(range(len(vals)), vals)
            self.bar_canvas.ax.set_xticks(range(len(vals)))
            self.bar_canvas.ax.set_xticklabels(names, rotation=45, ha='right')
            self.bar_canvas.ax.set_title("Последние расходы")
        else:
            self.bar_canvas.ax.text(0.5,0.5,"Нет данных", ha='center')
        self.bar_canvas.draw()

    # -------------------------
    # Actions
    # -------------------------
    def open_add_expense(self):
        dlg = AddExpenseDialog(self, self.data)
        if dlg.exec_():
            # saved into data by dialog
            save_data(self.data)
            self.refresh_all_ui()
            QMessageBox.information(self, "Успех", "Расход добавлен.")

    def on_refresh_categories(self):
        # recalc from expenses (recompute spent)
        for k in self.data.get("categories", {}):
            self.data["categories"][k]["spent"] = 0.0
        for e in self.data.get("expenses", []):
            cat = e.get("category")
            amt = float(e.get("amount",0.0))
            if cat:
                if cat not in self.data["categories"]:
                    self.data["categories"][cat] = {"spent": amt, "budget": 0.0, "color": "#CCCCCC", "icon": "❓"}
                else:
                    self.data["categories"][cat]["spent"] = round(self.data["categories"][cat].get("spent",0.0) + amt, 2)
        save_data(self.data)
        self.refresh_categories_table()
        QMessageBox.information(self, "Обновлено", "Категории пересчитаны.")

    # -------------------------
    # Theme (dark mode)
    # -------------------------
    def apply_theme(self, mode):
        if mode == "dark":
            self.setStyleSheet("""
                QWidget { background: #111216; color: #E6E6E6; }
                QTableWidget, QListWidget { background: #17181A; }
                QPushButton { background: #2A2B2D; color: #E6E6E6; border-radius:8px; padding:8px; }
            """)
            self.data["theme"] = "dark"
        else:
            self.setStyleSheet("")  # default
            self.data["theme"] = "light"
        save_data(self.data)

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = UIController()
    window.show()
    sys.exit(app.exec_())
