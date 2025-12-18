from flet import *
from .constants import BG, FWG, PINK, FG, MOBILE_PADDING, MOBILE_ELEMENT_HEIGHT, MOBILE_BORDER_RADIUS, responsive_size
from db import db_clear_all_transactions, db_fetch_all_transactions, db_get_user_categories, get_current_user_id, get_user_role
from helpers import load_session, show_alert
from datetime import datetime
import os
import subprocess
import sys
import tempfile
import shutil
import time

# Если не установлен fpdf, установите через pip install fpdf
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False
    print("Для экспорта в PDF установите fpdf: pip install fpdf")

def create_settings_view(page, update_transactions_callback, update_categories_callback):
    """Создаёт адаптивный view для настроек для мобильных"""
    screen_width = page.window.width or 400
    screen_height = page.window.height or 800
    
    # Создаем FilePicker для экспорта PDF
    file_picker = FilePicker()
    page.overlay.append(file_picker)
    
    def check_admin_permission():
        """Проверяет, является ли текущий пользователь администратором"""
        current_username = load_session()
        if not current_username:
            return False
        
        try:
            role = get_user_role(current_username)
            return role == 'admin'
        except:
            return False
    
    def backup_database():
        """
        Создает резервную копию базы данных PostgreSQL, используя утилиту pg_dump.
        Только для администраторов.
        """
        # Проверяем права администратора
        if not check_admin_permission():
            show_alert(page, "❌ Доступ запрещен. Только администраторы могут создавать бэкапы.", bgcolor='red')
            return
        
        # Показываем индикатор загрузки
        page.splash = ProgressBar()
        page.update()
        
        try:
            # 1. Создаем папку для бэкапов, если нет
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # 2. Параметры подключения
            pg_host = os.getenv("PG_HOST", "localhost")
            pg_port = os.getenv("PG_PORT", "5432")
            pg_db = os.getenv("PG_DB", "finance_tracker")
            pg_user = os.getenv("PG_USER", "postgres")
            pg_password = os.getenv("PG_PASSWORD", "1234")

            # Устанавливаем пароль в переменную окружения, чтобы pg_dump мог подключиться
            os.environ["PGPASSWORD"] = pg_password

            # 3. Формируем имя файла с датой
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{backup_dir}/backup_{pg_db}_{timestamp}.sql"
            
            print(f"Начинаю создание бэкапа базы {pg_db}...")

            # 4. Команда запуска pg_dump
            command = [
                "pg_dump",
                "-h", pg_host,
                "-p", pg_port,
                "-U", pg_user,
                "-F", "p",          # Формат plain text (SQL скрипт)
                "-f", filename,     # Куда сохранить
                pg_db
            ]

            try:
                # Запускаем процесс
                result = subprocess.run(
                    command, 
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Успешное завершение
                show_alert(page, 
                    f"✅ Бэкап успешно создан!\nФайл: {filename}\nРазмер: {os.path.getsize(filename) / 1024:.1f} KB", 
                    bgcolor='green'
                )
                print(f"✅ Успешно! Бэкап сохранен в: {filename}")
                
                # Пытаемся открыть папку с бэкапами
                try:
                    if sys.platform == "win32":
                        os.startfile(backup_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", backup_dir])
                    else:
                        subprocess.run(["xdg-open", backup_dir])
                except:
                    pass
                    
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ Ошибка при создании бэкапа:\n{e.stderr}"
                show_alert(page, error_msg, bgcolor='red')
                print(f"❌ Ошибка при создании бэкапа: {e}")
                
            except FileNotFoundError:
                error_msg = "❌ pg_dump не найден!\nУстановите PostgreSQL и добавьте в PATH"
                show_alert(page, error_msg, bgcolor='red')
                print("❌ Утилита pg_dump не найдена")
                
        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка:\n{str(e)}"
            show_alert(page, error_msg, bgcolor='red')
            print(f"❌ Неожиданная ошибка: {e}")
            
        finally:
            # Убираем индикатор загрузки
            page.splash = None
            page.update()
    
    def clear_all_transactions():
        """Удаляет все транзакции"""
        current_username = load_session()
        if not current_username:
            show_alert(page, "Ошибка: Не удалось найти активного пользователя.", bgcolor='red')
            return

        if db_clear_all_transactions(current_username):
            update_transactions_callback()
            update_categories_callback()
            page.go("/")
            page.snack_bar = SnackBar(
                content=Text("Все транзакции удалены", 
                    color="white",
                    size=responsive_size(14)),
                bgcolor="green"
            )
            page.snack_bar.open = True
            page.update()
    
    def save_pdf_file(e: FilePickerResultEvent):
        """Сохранение PDF файла после выбора места"""
        print(f"FilePicker result: path={e.path}, files={e.files}")
        
        if e.path:
            try:
                # Получаем данные из временного файла
                temp_file = getattr(file_picker, '_temp_pdf_file', None)
                print(f"Temp file path: {temp_file}")
                
                if temp_file and os.path.exists(temp_file):
                    print(f"Copying PDF from {temp_file} to {e.path}")
                    
                    # Добавляем расширение .pdf если его нет
                    save_path = e.path
                    if not save_path.endswith('.pdf'):
                        save_path += '.pdf'
                    
                    # Копируем временный файл в выбранное место
                    shutil.copy(temp_file, save_path)
                    
                    # Удаляем временный файл
                    os.unlink(temp_file)
                    
                    # Показываем диалог успешного сохранения
                    show_success_dialog(save_path)
                    
                    print(f"PDF успешно сохранен в: {save_path}")
                    
                else:
                    error_msg = "❌ Ошибка: Временный файл не найден"
                    show_alert(page, error_msg, bgcolor='red')
                    print(error_msg)
            except Exception as ex:
                error_msg = f"❌ Ошибка при сохранении:\n{str(ex)}"
                show_alert(page, error_msg, bgcolor='red')
                print(f"Ошибка сохранения PDF: {ex}")
        else:
            show_alert(page, "Сохранение отменено", bgcolor='orange')
            print("Сохранение PDF отменено пользователем")
    
    # Подключаем обработчик для FilePicker
    file_picker.on_result = save_pdf_file
    
    def debug_transactions_structure():
        """Функция для отладки структуры транзакций"""
        current_username = load_session()
        if not current_username:
            return
        
        print("\n=== ДЕБАГ СТРУКТУРЫ ТРАНЗАКЦИЙ ===")
        
        # Способ 1
        try:
            trans1 = db_fetch_all_transactions(current_username)
            if trans1 and len(trans1) > 0:
                print(f"Способ 1 - первая транзакция: {trans1[0]}")
                print(f"Способ 1 - ключи: {list(trans1[0].keys())}")
        except Exception as e:
            print(f"Ошибка способа 1: {e}")
        
        # Способ 2
        try:
            from project import db_fetch_user_transactions
            trans2 = db_fetch_user_transactions(current_username)
            if trans2 and len(trans2) > 0:
                print(f"Способ 2 - первая транзакция: {trans2[0]}")
                print(f"Способ 2 - ключи: {list(trans2[0].keys())}")
        except Exception as e:
            print(f"Ошибка способа 2: {e}")
        
        print("=== КОНЕЦ ДЕБАГА ===\n")
    
    def generate_pdf_report():
        """Генерирует PDF отчет и возвращает путь к временному файлу"""
        print("=== Начало генерации PDF отчета ===")
        
        current_username = load_session()
        print(f"Текущий пользователь: {current_username}")
        
        if not current_username:
            show_alert(page, "Ошибка: Не удалось найти активного пользователя.", bgcolor='red')
            print("Ошибка: пользователь не найден")
            return None
        
        if not HAS_FPDF:
            show_alert(page, "❌ Модуль fpdf не установлен.", bgcolor='red')
            print("Ошибка: fpdf не установлен")
            return None
        
        # Получаем ID пользователя
        user_id = get_current_user_id(current_username)
        print(f"ID пользователя: {user_id}")
        
        if not user_id:
            show_alert(page, "❌ Не удалось найти ID пользователя.", bgcolor='red')
            print("Ошибка: ID пользователя не найден")
            return None
        
        # Получаем все транзакции для этого пользователя
        print("Получение транзакций...")
        
        # Пробуем получить транзакции разными способами
        transactions = []
        
        # Способ 1: Через db_fetch_all_transactions
        try:
            transactions = db_fetch_all_transactions(current_username)
            print(f"Способ 1 (db_fetch_all_transactions): найдено {len(transactions)} транзакций")
        except Exception as e:
            print(f"Ошибка способа 1: {e}")
        
        # Способ 2: Через project.db_fetch_user_transactions (импортируем)
        if not transactions:
            try:
                from project import db_fetch_user_transactions
                transactions = db_fetch_user_transactions(current_username)
                print(f"Способ 2 (project.db_fetch_user_transactions): найдено {len(transactions)} транзакций")
            except Exception as e:
                print(f"Ошибка способа 2: {e}")
        
        # Способ 3: Через run_app (импортируем из текущего контекста)
        if not transactions and 'db_fetch_user_transactions' in globals():
            try:
                transactions = db_fetch_user_transactions(current_username)
                print(f"Способ 3 (локальная функция): найдено {len(transactions)} транзакций")
            except Exception as e:
                print(f"Ошибка способа 3: {e}")
        
        # Если все равно нет транзакций
        if not transactions:
            print("Не удалось получить транзакции ни одним способом")
            transactions = []  # Устанавливаем пустой список
        
        # Проверяем структуру транзакций
        if transactions and len(transactions) > 0:
            print(f"Пример структуры транзакции: {transactions[0]}")
            print(f"Ключи в транзакции: {list(transactions[0].keys())}")
        
        # Получаем категории пользователя
        categories = db_get_user_categories(user_id)
        print(f"Найдено категорий: {len(categories) if categories else 0}")
        
        # Разрешаем создание PDF даже без транзакций, только с категориями
        if not transactions and not categories:
            show_alert(page, "Нет данных для экспорта.", bgcolor='orange')
            print("Нет данных для экспорта")
            return None
        
        try:
            print("Создание PDF документа...")
            
            # Создаем PDF документ
            pdf = FPDF()
            pdf.add_page()
            
            # Используем стандартный шрифт Arial
            pdf.set_font('Arial', '', 16)
            
            # Заголовок
            title = f"Financial Report: {current_username}"
            pdf.cell(0, 10, title, ln=True, align='C')
            pdf.ln(5)
            
            # Дата генерации
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
            pdf.ln(10)
            
            # Сводная статистика (только если есть транзакции)
            if transactions:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Summary Statistics", ln=True)
                pdf.set_font('Arial', '', 12)
                
                try:
                    total_income = 0
                    total_expense = 0
                    
                    for t in transactions:
                        amount = float(t.get('amount', 0))
                        # Определяем тип транзакции
                        transaction_type = t.get('type', t.get('transaction_type', 'expense')).lower()
                        
                        if transaction_type == 'income':
                            total_income += amount
                        else:
                            total_expense += amount
                    
                    balance = total_income - total_expense
                    
                    pdf.cell(0, 8, f"Total Income: {total_income:.2f} KZT", ln=True)
                    pdf.cell(0, 8, f"Total Expenses: {total_expense:.2f} KZT", ln=True)
                    pdf.cell(0, 8, f"Balance: {balance:.2f} KZT", ln=True)
                    pdf.ln(10)
                    
                    print(f"Статистика: доходы={total_income}, расходы={total_expense}, баланс={balance}")
                except Exception as stat_error:
                    print(f"Ошибка при расчете статистики: {stat_error}")
                    pdf.cell(0, 8, "Error calculating statistics", ln=True)
                    pdf.ln(10)
            else:
                # Если нет транзакций
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Summary Statistics", ln=True)
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 8, "No transaction data available", ln=True)
                pdf.ln(10)
            
            # Список категорий (только если есть категории)
            if categories:
                try:
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, "Categories", ln=True)
                    pdf.set_font('Arial', '', 10)
                    
                    for idx, category in enumerate(categories):
                        # Обрабатываем разные форматы категорий
                        if isinstance(category, dict):
                            category_name = category.get('name', 'No name')
                            category_type = category.get('category_type', 'expense')
                        elif isinstance(category, str):
                            category_name = category
                            category_type = 'expense'
                        elif isinstance(category, tuple) or isinstance(category, list):
                            try:
                                category_name = str(category[0]) if len(category) > 0 else 'No name'
                                category_type = str(category[1]) if len(category) > 1 else 'expense'
                            except:
                                category_name = str(category)
                                category_type = 'expense'
                        else:
                            category_name = str(category)
                            category_type = 'expense'
                        
                        # Транслитерация кириллицы
                        category_name_translit = transliterate(category_name)
                        category_text = f"{category_name_translit} ({category_type})"
                        
                        pdf.cell(0, 6, category_text, ln=True)
                    pdf.ln(10)
                except Exception as cat_error:
                    print(f"Ошибка при выводе категорий: {cat_error}")
                    import traceback
                    traceback.print_exc()
            
            # Детали транзакций (только если есть транзакции)
            if transactions:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Transaction Details", ln=True)
                pdf.set_font('Arial', 'B', 10)
                
                # Заголовки таблицы
                col_widths = [30, 40, 50, 30, 40]
                headers = ["Date", "Type", "Category", "Amount", "Description"]
                
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, border=1)
                pdf.ln()
                
                # Данные транзакций
                pdf.set_font('Arial', '', 9)
                
                try:
                    print(f"Обработка {len(transactions)} транзакций...")
                    
                    for idx, transaction in enumerate(transactions):
                        # Получаем данные из словаря с проверкой разных ключей
                        date_str = transaction.get('date', transaction.get('created_at', ''))
                        
                        # Определяем тип транзакции (пробуем разные ключи)
                        transaction_type = transaction.get('type', 
                                         transaction.get('transaction_type', 
                                         transaction.get('type_', 'expense'))).lower()
                        
                        # Получаем категорию
                        category_name = transaction.get('category', 
                                         transaction.get('category_name', 
                                         transaction.get('category', '')))
                        
                        amount = transaction.get('amount', 0)
                        description = transaction.get('description', '')
                        
                        # Преобразуем сумму в число
                        try:
                            amount_float = float(amount)
                        except:
                            amount_float = 0.0
                        
                        # Форматируем дату
                        date_display = "No date"
                        if date_str:
                            try:
                                if isinstance(date_str, str):
                                    # Пробуем разные форматы даты
                                    for fmt in ('%d.%m.%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
                                        try:
                                            date_obj = datetime.strptime(date_str, fmt)
                                            date_display = date_obj.strftime('%d.%m.%Y')
                                            break
                                        except:
                                            continue
                                else:
                                    date_display = str(date_str)[:10]
                            except:
                                date_display = str(date_str)
                        
                        # Транслитерация кириллицы
                        category_name_translit = transliterate(category_name) if category_name else "No category"
                        description_translit = transliterate(description) if description else ""
                        
                        # Обрезаем слишком длинные описания
                        if description_translit and len(description_translit) > 20:
                            description_translit = description_translit[:20] + "..."
                        
                        # Цвет для типа транзакции
                        color = (0, 100, 0) if transaction_type == 'income' else (200, 0, 0)
                        pdf.set_text_color(*color)
                        
                        # Определяем отображаемый тип
                        type_display = "Income" if transaction_type == 'income' else "Expense"
                        
                        # Данные строки
                        row_data = [
                            date_display,
                            type_display,
                            category_name_translit[:15],
                            f"{amount_float:.2f}",
                            description_translit
                        ]
                        
                        for i, data in enumerate(row_data):
                            pdf.cell(col_widths[i], 8, str(data), border=1)
                        pdf.ln()
                        
                        # Сброс цвета для следующей строки
                        pdf.set_text_color(0, 0, 0)
                        
                        if idx > 0 and idx % 10 == 0:
                            print(f"  Обработано {idx} транзакций...")
                            
                except Exception as trans_error:
                    print(f"Ошибка при обработке транзакций: {trans_error}")
                    import traceback
                    traceback.print_exc()
                    pdf.cell(0, 8, f"Error processing transaction data", ln=True)
            else:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Transaction Details", ln=True)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, "No transactions available", ln=True)
            
            pdf.ln(10)
            
            # Подвал
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 10, "Generated in Finance Tracker", ln=True, align='C')
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.pdf', 
                prefix=f'finance_report_{current_username}_'
            )
            
            print(f"Сохранение PDF в файл: {temp_file.name}")
            
            # Сохраняем PDF
            pdf.output(temp_file.name)
            
            # Проверяем, что файл создан
            if os.path.exists(temp_file.name):
                file_size = os.path.getsize(temp_file.name)
                print(f"PDF файл создан успешно! Размер: {file_size} байт")
            else:
                print("Ошибка: PDF файл не создан!")
                return None
            
            # Сохраняем путь к временному файлу
            file_picker._temp_pdf_file = temp_file.name
            
            print("=== Генерация PDF завершена успешно ===")
            
            return temp_file.name
            
        except Exception as e:
            show_alert(page, f"❌ Ошибка при создании отчета:\n{str(e)}", bgcolor='red')
            print(f"Критическая ошибка генерации PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def show_save_dialog(temp_file):
        """Универсальный диалог сохранения для всех устройств"""
        print(f"Создаю диалог сохранения для файла: {temp_file}")
        
        def save_to_documents_action(e):
            """Сохраняет в папку Documents"""
            print("Нажата кнопка 'Сохранить в Documents'")
            try:
                # Создаем папку для документов
                docs_dir = "Documents"
                if not os.path.exists(docs_dir):
                    os.makedirs(docs_dir)
                
                # Генерируем имя файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_username = load_session() or "user"
                filename = f"finance_report_{current_username}_{timestamp}.pdf"
                dest_path = os.path.join(docs_dir, filename)
                
                print(f"Сохраняю в: {dest_path}")
                
                # Копируем файл
                shutil.copy(temp_file, dest_path)
                
                # Удаляем временный файл
                os.unlink(temp_file)
                
                # Закрываем диалог
                page.dialog = None
                page.update()
                
                # Даем время на закрытие диалога
                time.sleep(0.1)
                
                # Показываем уведомление об успешном сохранении
                print("Показываю диалог успешного сохранения...")
                show_success_dialog(dest_path)
                
                print(f"PDF успешно сохранен в Documents: {dest_path}")
                
            except Exception as ex:
                print(f"Ошибка при сохранении: {ex}")
                show_alert(page, f"❌ Ошибка при сохранении:\n{str(ex)}", bgcolor='red')
        
        def open_file_picker(e):
            """Открывает диалог выбора файла"""
            print("Нажата кнопка 'Выбрать другое место'")
            try:
                # Для десктопа используем FilePicker
                filename = f"finance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                file_picker._temp_pdf_file = temp_file
                file_picker.save_file(
                    file_name=filename,
                    allowed_extensions=["pdf"]
                )
                
                # Закрываем текущий диалог
                page.dialog = None
                page.update()
                
                print("Открыт FilePicker")
                
            except Exception as ex:
                print(f"Ошибка при открытии файлового диалога: {ex}")
                show_alert(page, "❌ Не удалось открыть диалог выбора файла", bgcolor='red')
        
        def cancel_action(e):
            """Отмена сохранения"""
            print("Нажата кнопка 'Отмена'")
            try:
                # Удаляем временный файл
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print("Удален временный файл")
            except Exception as ex:
                print(f"Ошибка при удалении временного файла: {ex}")
            
            page.dialog = None
            page.update()
        
        # Определяем, мобильное ли устройство
        is_mobile = screen_width <= 480
        print(f"Экран: ширина={screen_width}, is_mobile={is_mobile}")
        
        # Текущий путь для сохранения
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_username = load_session() or "user"
        default_filename = f"finance_report_{current_username}_{timestamp}.pdf"
        
        # Путь для отображения
        if is_mobile:  # Мобильное устройство
            docs_dir = "Documents"
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir)
            default_path = os.path.join(docs_dir, default_filename)
        else:
            default_path = os.path.join(os.getcwd(), default_filename)
        
        print(f"Путь по умолчанию: {default_path}")
        
        # Создаем кнопки для диалога
        actions = []
        
        # Кнопка выбора пути (только для десктопа)
        if not is_mobile:
            actions.append(
                ElevatedButton(
                    "Выбрать другое место",
                    on_click=open_file_picker,
                    bgcolor=FG,
                    color=FWG,
                    height=40
                )
            )
        
        # Кнопка сохранения в Documents
        actions.append(
            ElevatedButton(
                "Сохранить в Documents",
                on_click=save_to_documents_action,
                bgcolor=PINK,
                color="white",
                height=40
            )
        )
        
        # Кнопка отмены
        actions.append(
            ElevatedButton(
                "Отмена",
                on_click=cancel_action,
                bgcolor=BG,
                color=FWG,
                height=40
            )
        )
        
        # Создаем диалог
        dialog = AlertDialog(
            modal=True,
            title=Text("Сохранение отчета", size=16, weight=FontWeight.BOLD),
            content=Column([
                Text("Отчет успешно сгенерирован!", size=14),
                Container(height=10),
                Text(f"Размер: {os.path.getsize(temp_file) / 1024:.1f} KB", 
                    size=12, color=FWG, opacity=0.7),
                Container(height=15),
                Text(f"Будет сохранен в:", size=14),
                Container(height=5),
                Text(default_path, size=12, color=FWG, opacity=0.8),
            ], tight=True),
            actions=actions,
            actions_alignment=MainAxisAlignment.CENTER
        )
        
        # Устанавливаем и показываем диалог
        page.dialog = dialog
        page.update()
        print("Диалог сохранения показан на экране")

    def show_success_dialog(file_path):
        """Показывает диалог об успешном сохранении"""
        print(f"Показываю диалог успеха для файла: {file_path}")
        
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)
        
        def open_folder(e):
            try:
                if sys.platform == "win32":
                    os.startfile(dir_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", dir_path])
                else:
                    subprocess.run(["xdg-open", dir_path])
                print(f"Открыта папка: {dir_path}")
            except Exception as ex:
                print(f"Не удалось открыть папку: {ex}")
            page.dialog = None
            page.update()
        
        def close_dialog(e):
            page.dialog = None
            page.update()
            print("Диалог успеха закрыт")
        
        success_dialog = AlertDialog(
            modal=True,
            title=Text("✅ Отчет сохранен", size=16, weight=FontWeight.BOLD),
            content=Column([
                Text("Отчет успешно сохранен!", size=14),
                Container(height=10),
                Text(f"Файл: {file_name}", size=12, color=FWG, opacity=0.7),
                Container(height=5),
                Text(f"Папка: {dir_path}", size=12, color=FWG, opacity=0.7),
            ], tight=True),
            actions=[
                ElevatedButton(
                    "Открыть папку",
                    on_click=open_folder,
                    bgcolor=PINK,
                    color="white",
                    height=40
                ),
                ElevatedButton(
                    "Закрыть",
                    on_click=close_dialog,
                    bgcolor=FG,
                    color=FWG,
                    height=40
                ),
            ],
            actions_alignment=MainAxisAlignment.CENTER
        )
        
        page.dialog = success_dialog
        page.update()
        print("Диалог успеха показан на экране")
    
    
    def transliterate(text):
        """Простая транслитерация кириллицы в латиницу"""
        if not text or not isinstance(text, str):
            return str(text) if text else ""
        
        # Словарь транслитерации
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        
        result = []
        for char in text:
            result.append(translit_dict.get(char, char))
        
        return ''.join(result)
    
    
    
    def export_data(e):
        """Обработчик экспорта данных"""
        print("Кнопка экспорта нажата")
        
        # Вызов отладки
        debug_transactions_structure()
        
        # Создаем диалог загрузки
        loading_dialog = AlertDialog(
            modal=True,
            title=Text("Пожалуйста, подождите"),
            content=Row([
                ProgressRing(width=30, height=30, stroke_width=3),
                Container(width=10),
                Text("Генерация отчета...", size=14)
            ], alignment=MainAxisAlignment.CENTER),
            open=True
        )
        
        # Устанавливаем диалог и обновляем страницу
        page.dialog = loading_dialog
        page.update()
        
        print("Показан диалог загрузки")
        
        # Запускаем экспорт
        def process_export():
            try:
                temp_file = generate_pdf_report()
                
                # Закрываем диалог загрузки
                page.dialog.open = False
                page.update()
                
                if temp_file and os.path.exists(temp_file):
                    print(f"PDF сгенерирован успешно: {temp_file}")
                    print(f"Размер файла: {os.path.getsize(temp_file)} байт")
                    
                    # Всегда используем FilePicker для выбора места сохранения
                    use_file_picker_for_save(temp_file)
                    
                elif temp_file:
                    print(f"Файл сгенерирован но не найден: {temp_file}")
                    show_alert(page, "❌ Ошибка: сгенерированный файл не найден", bgcolor='red')
                else:
                    print("Не удалось сгенерировать PDF")
                    
            except Exception as ex:
                # Закрываем диалог загрузки в случае ошибки
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                
                show_alert(page, f"❌ Ошибка при генерации отчета:\n{str(ex)}", bgcolor='red')
                print(f"Ошибка экспорта: {ex}")
        
        # Даем немного времени для отображения диалога загрузки
        import threading
        import time
        
        def run_with_delay():
            time.sleep(0.3)  # Даем время для отображения диалога загрузки
            process_export()
        
        threading.Thread(target=run_with_delay, daemon=True).start()

    def use_file_picker_for_save(temp_file):
        """Использует FilePicker для выбора места сохранения"""
        print(f"Использую FilePicker для сохранения файла: {temp_file}")
        
        # Сохраняем путь к временному файлу
        file_picker._temp_pdf_file = temp_file
        
        # Генерируем имя файла по умолчанию
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_username = load_session() or "user"
        filename = f"finance_report_{current_username}_{timestamp}.pdf"
        
        print(f"Предлагаемое имя файла: {filename}")
        
        # Показываем FilePicker для сохранения
        try:
            file_picker.save_file(
                file_name=filename,
                allowed_extensions=["pdf"],
                dialog_title="Сохранить отчет в PDF"
            )
            print("FilePicker показан")
        except Exception as ex:
            print(f"Ошибка при показе FilePicker: {ex}")
            # Если FilePicker не сработал, показываем простой диалог
            show_simple_save_dialog(temp_file)

    def show_simple_save_dialog(temp_file):
        """Простой диалог сохранения если FilePicker не работает"""
        print("Показываю простой диалог сохранения")
        
        def save_to_current_dir(e):
            """Сохраняет в текущую директорию"""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_username = load_session() or "user"
                filename = f"finance_report_{current_username}_{timestamp}.pdf"
                dest_path = os.path.join(os.getcwd(), filename)
                
                print(f"Сохраняю в: {dest_path}")
                
                # Копируем файл
                shutil.copy(temp_file, dest_path)
                
                # Удаляем временный файл
                os.unlink(temp_file)
                
                # Закрываем диалог
                page.dialog = None
                page.update()
                
                # Показываем уведомление об успешном сохранении
                show_alert(page, 
                        f"✅ Отчет сохранен в:\n{dest_path}\n\n"
                        f"Файл: {filename}\n"
                        f"Папка: {os.getcwd()}",
                        bgcolor='green')
                
                print(f"PDF успешно сохранен: {dest_path}")
                
            except Exception as ex:
                print(f"Ошибка при сохранении: {ex}")
                show_alert(page, f"❌ Ошибка при сохранении:\n{str(ex)}", bgcolor='red')
        
        def cancel_action(e):
            """Отмена сохранения"""
            try:
                # Удаляем временный файл
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print("Удален временный файл")
            except Exception as ex:
                print(f"Ошибка при удалении временного файла: {ex}")
            
            page.dialog = None
            page.update()
        
        # Создаем простой диалог
        dialog = AlertDialog(
            modal=True,
            title=Text("Сохранение отчета", size=16, weight=FontWeight.BOLD),
            content=Column([
                Text("Отчет успешно сгенерирован!", size=14),
                Container(height=10),
                Text(f"Размер: {os.path.getsize(temp_file) / 1024:.1f} KB", 
                    size=12, color=FWG, opacity=0.7),
                Container(height=15),
                Text("Нажмите 'Сохранить', чтобы сохранить отчет", size=14),
                Container(height=5),
            ], tight=True),
            actions=[
                ElevatedButton(
                    "Сохранить",
                    on_click=save_to_current_dir,
                    bgcolor=PINK,
                    color="white",
                    height=40
                ),
                ElevatedButton(
                    "Отмена",
                    on_click=cancel_action,
                    bgcolor=BG,
                    color=FWG,
                    height=40
                ),
            ],
            actions_alignment=MainAxisAlignment.CENTER
        )
        
        # Устанавливаем и показываем диалог
        page.dialog = dialog
        page.update()
        print("Простой диалог сохранения показан")
    
    
    
    # Проверяем, является ли пользователь администратором
    is_admin = check_admin_permission()

    return Container(
        width=screen_width,
        height=screen_height,
        bgcolor=BG,
        padding=padding.all(MOBILE_PADDING),
        content=Column(
            controls=[
                Row(
                    alignment="start",
                    controls=[
                        IconButton(
                            icon=Icons.ARROW_BACK,
                            icon_color=FWG,
                            icon_size=responsive_size(24),
                            on_click=lambda _: page.go("/")
                        ),
                        Text("Настройки", 
                            color=FWG, 
                            size=responsive_size(20), 
                            weight=FontWeight.BOLD,
                            expand=True)
                    ]
                ),
                Container(height=responsive_size(30)),
                
                # Раздел управления данными
                Container(
                    bgcolor=FG,
                    padding=padding.all(responsive_size(15)),
                    border_radius=MOBILE_BORDER_RADIUS,
                    content=Column(
                        controls=[
                            Text("Управление данными", 
                                color=FWG, 
                                size=responsive_size(16), 
                                weight=FontWeight.BOLD),
                            Container(height=responsive_size(15)),
                            
                            # Кнопка экспорта в PDF
                            ElevatedButton(
                                "Сохранить отчет в PDF",
                                width=screen_width - 2*MOBILE_PADDING,
                                height=MOBILE_ELEMENT_HEIGHT,
                                bgcolor="#4CAF50",  # Зеленый цвет
                                color="white",
                                on_click=export_data
                            ),
                            Container(height=responsive_size(10)),
                            Text("Создает PDF файл со всеми транзакциями", 
                                color=FWG, 
                                size=responsive_size(12), 
                                opacity=0.7),
                            Container(height=responsive_size(10)),
                            
                            # Кнопка создания бэкапа - показывается только для админов
                            Container(
                                content=Column([
                                    ElevatedButton(
                                        "Создать бэкап базы данных",
                                        width=screen_width - 2*MOBILE_PADDING,
                                        height=MOBILE_ELEMENT_HEIGHT,
                                        bgcolor="#2196F3",  # Синий для админов
                                        color="white",
                                        on_click=lambda e: backup_database()
                                    ),
                                    Container(height=responsive_size(10)),
                                    Text("Создает резервную копию всех данных", 
                                        color=FWG, 
                                        size=responsive_size(12), 
                                        opacity=0.7),
                                ])
                            ) if is_admin else Container(height=0),  # Полностью скрываем для не-админов
                            
                            Container(height=responsive_size(15) if is_admin else 0),
                            
                            # Кнопка очистки транзакций
                            ElevatedButton(
                                "Очистить все транзакции",
                                width=screen_width - 2*MOBILE_PADDING,
                                height=MOBILE_ELEMENT_HEIGHT,
                                bgcolor="red",
                                color="white",
                                on_click=lambda e: clear_all_transactions()
                            ),
                            Container(height=responsive_size(10)),
                            Text("Это действие нельзя отменить", 
                                color=FWG, 
                                size=responsive_size(12), 
                                opacity=0.7)
                        ]
                    )
                ),
                Container(height=responsive_size(30)),
                
                # Раздел о приложении
                Container(
                    bgcolor=FG,
                    padding=padding.all(responsive_size(15)),
                    border_radius=MOBILE_BORDER_RADIUS,
                    content=Column(
                        controls=[
                            Text("О приложении", 
                                color=FWG, 
                                size=responsive_size(16), 
                                weight=FontWeight.BOLD),
                            Container(height=responsive_size(15)),
                            Row(
                                controls=[
                                    Icon(Icons.ACCOUNT_BALANCE_WALLET, color=PINK, size=responsive_size(24)),
                                    Container(width=responsive_size(10)),
                                    Column(
                                        controls=[
                                            Text("Finance Tracker", 
                                                color=FWG, 
                                                size=responsive_size(16)),
                                            Text("Версия 1.0.0", 
                                                color=FWG, 
                                                size=responsive_size(12), 
                                                opacity=0.7),
                                        ]
                                    )
                                ]
                            ),
                            Container(height=responsive_size(15)),
                            Text("Приложение для учёта доходов и расходов", 
                                color=FWG, 
                                size=responsive_size(14), 
                                opacity=0.7),
                            Container(height=responsive_size(5)),
                            Text("Создано для эффективного управления личными финансами", 
                                color=FWG, 
                                size=responsive_size(12), 
                                opacity=0.7)
                        ]
                    )
                )
            ],
            scroll="auto"
        )
    )

__all__ = ['create_settings_view']