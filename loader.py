# ui_loader.py
import sys
import json
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from project import FinanceApp  # если хочешь интегрировать с логикой

UI_FILE = "main.ui"

class UILoader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # access widgets
        self.stacked = self.findChild(QtWidgets.QStackedWidget, "stackedWidget")
        # bottom nav
        self.navHome = self.findChild(QtWidgets.QPushButton, "navHome")
        self.navStats = self.findChild(QtWidgets.QPushButton, "navStats")
        self.navSubscriptions = self.findChild(QtWidgets.QPushButton, "navSubscriptions")
        self.navReports = self.findChild(QtWidgets.QPushButton, "navReports")
        self.navSettings = self.findChild(QtWidgets.QPushButton, "navSettings")

        # top/home buttons
        self.btnExpenses = self.findChild(QtWidgets.QPushButton, "btnExpenses")
        self.btnStatistics = self.findChild(QtWidgets.QPushButton, "btnStatistics")
        self.btnSubscriptions = self.findChild(QtWidgets.QPushButton, "btnSubscriptions")
        self.btnBudget = self.findChild(QtWidgets.QPushButton, "btnBudget")

        # expenses controls
        self.btnRefresh = self.findChild(QtWidgets.QPushButton, "btnRefreshCategories")
        self.listCategories = self.findChild(QtWidgets.QListWidget, "listCategories")
        self.listRecent = self.findChild(QtWidgets.QListWidget, "listRecent")
        self.tableHistory = self.findChild(QtWidgets.QTableWidget, "tableHistory")
        self.tableCategories = self.findChild(QtWidgets.QTableWidget, "tableCategories")
        self.labelBudgetAmount = self.findChild(QtWidgets.QLabel, "labelBudgetAmount")

        # wire navigation (simple index switching)
        self.navHome.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.navStats.clicked.connect(lambda: self.stacked.setCurrentIndex(4))
        self.navSubscriptions.clicked.connect(lambda: self.stacked.setCurrentIndex(2))
        self.navReports.clicked.connect(lambda: self.stacked.setCurrentIndex(7))
        self.navSettings.clicked.connect(lambda: self.stacked.setCurrentIndex(8))

        # quick actions
        self.btnExpenses.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.btnStatistics.clicked.connect(lambda: self.stacked.setCurrentIndex(4))
        self.btnSubscriptions.clicked.connect(lambda: self.stacked.setCurrentIndex(2))
        self.btnBudget.clicked.connect(lambda: self.stacked.setCurrentIndex(3))

        # example: refresh button handler
        self.btnRefresh.clicked.connect(self.on_refresh)

        # populate placeholders
        self.listRecent.addItem("Пример: Ресторан — $45.00")
        self.listRecent.addItem("Пример: Такси — $12.50")
        self.populate_categories_table()
        self.populate_history_table()

    def on_refresh(self):
        # placeholder: in real integration call app.refresh_categories()
        self.listCategories.clear()
        self.listCategories.addItem("Еда — $842.50")
        self.listCategories.addItem("Транспорт — $650.00")
        QtWidgets.QMessageBox.information(self, "Обновлено", "Категории обновлены (демо).")

    def populate_categories_table(self):
        data = [
            ("🍔", "Еда", "$842.50", "$800"),
            ("🚗", "Транспорт", "$650.00", "$500"),
        ]
        self.tableCategories.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                item = QtWidgets.QTableWidgetItem(val)
                self.tableCategories.setItem(r, c, item)

    def populate_history_table(self):
        data = [
            ("2025-11-21 10:00", "Еда", "$45.00", "Обед"),
            ("2025-11-20 18:30", "Транспорт", "$12.50", "Такси"),
        ]
        self.tableHistory.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                item = QtWidgets.QTableWidgetItem(val)
                self.tableHistory.setItem(r, c, item)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = UILoader()
    win.show()
    sys.exit(app.exec_())
