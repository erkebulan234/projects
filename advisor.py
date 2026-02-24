"""
Модуль advisor.py - AI-советник по финансам с сохранением истории чата (БЕЗ СЕССИЙ)
"""
from datetime import datetime, timedelta
from db.statistics import db_get_expenses_summary, db_get_income_summary, db_get_transactions_period
from db import get_current_user_id, db_fetch_user_transactions, save_chat_message, get_chat_history, clear_chat_history
from helpers import load_session
import re

def get_savings_advice(total_expenses, total_income, top_categories):
    """Советы по экономии"""
    if total_expenses == 0:
        return "У вас пока нет расходов. Начните отслеживать свои траты, чтобы я мог дать персонализированные советы!"
    
    response = "**Советы по экономии:**\n\n"
    
    # 1. Анализ общих показателей
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    response += f"1. Ваши расходы: ₸{total_expenses:.2f}\n"
    if total_income > 0:
        response += f"   Доходы: ₸{total_income:.2f}\n"
        response += f"   Норма сбережений: {savings_rate:.1f}%\n"
    
    # 2. Анализ топ-категорий расходов
    if top_categories:
        response += "\n2. Самые затратные категории:\n"
        for i, (cat_name, amount, percentage) in enumerate(top_categories[:3], 1):
            response += f"   {i}. {cat_name}: ₸{amount:.2f} ({percentage:.1f}% от расходов)\n"
        
        # Конкретные советы для топ-категорий
        if top_categories:
            top_category = top_categories[0][0] if top_categories else ""
            if top_category == "Продукты":
                response += "\n   Советы по экономии на продуктах:\n"
                response += "   • Планируйте меню на неделю\n"
                response += "   • Составляйте список покупок\n"
                response += "   • Покупайте оптом\n"
                response += "   • Обращайте внимание на скидки\n"
            elif top_category == "Транспорт":
                response += "\n   Советы по экономии на транспорте:\n"
                response += "   • Используйте общественный транспорт\n"
                response += "   • Объединяйте поездки\n"
                response += "   • Рассмотрите каршеринг\n"
                response += "   • Следите за техобслуживанием авто\n"
    
    # 3. Общие рекомендации
    response += "\n3. Общие рекомендации:\n"
    response += "   • Откладывайте 10-20% дохода сразу\n"
    response += "   • Используйте правило 24 часов для импульсных покупок\n"
    response += "   • Отслеживайте все мелкие расходы\n"
    response += "   • Ставьте конкретные финансовые цели\n"
    
    return response

def get_budget_advice(total_income, total_expenses):
    """Советы по составлению бюджета"""
    if total_income == 0:
        return "Для составления бюджета сначала добавьте информацию о ваших доходах."
    
    response = "**Советы по составлению бюджета:**\n\n"
    
    # Классическое правило 50/30/20
    response += "1. **Правило 50/30/20** (рекомендация):\n"
    response += f"   • Необходимое (50%): ₸{total_income * 0.5:.2f}\n"
    response += f"   • Желания (30%): ₸{total_income * 0.3:.2f}\n"
    response += f"   • Накопления (20%): ₸{total_income * 0.2:.2f}\n"
    
    # Анализ текущей ситуации
    if total_expenses > 0:
        necessary_ratio = (total_expenses / total_income) * 100
        response += f"\n2. **Ваша текущая ситуация:**\n"
        response += f"   • Расходы составляют {necessary_ratio:.1f}% от доходов\n"
        
        if necessary_ratio > 80:
            response += "   ⚠️ Ваши расходы слишком высокие. Рекомендую сократить траты.\n"
        elif necessary_ratio > 60:
            response += "   ⚠️ Расходы на грани. Уделите внимание экономии.\n"
        else:
            response += "   ✅ Отличный показатель! У вас хороший баланс.\n"
    
    # Практические советы
    response += "\n3. **Практические шаги:**\n"
    response += "   • Ведите учёт всех доходов и расходов\n"
    response += "   • Создайте резервный фонд (3-6 месяцев расходов)\n"
    response += "   • Планируйте крупные покупки заранее\n"
    response += "   • Регулярно пересматривайте бюджет\n"
    
    return response

def get_savings_investment_advice(total_income, total_expenses):
    """Советы по накоплениям и инвестициям"""
    response = "💰 **Советы по накоплениям и инвестициям:**\n\n"
    
    # 1. Финансовая подушка безопасности
    response += "1. **Подушка безопасности:**\n"
    response += "   • Цель: 3-6 месяцев расходов\n"
    if total_expenses > 0:
        cushion_min = total_expenses * 3
        cushion_max = total_expenses * 6
        response += f"   • Для вас: ₸{cushion_min:.2f} - ₸{cushion_max:.2f}\n"
        response += "   • Храните в надёжном банке\n"
    
    # 2. Система накоплений
    response += "\n2. **Система накоплений:**\n"
    response += "   • Автоматизируйте переводы на сбережения\n"
    response += "   • 'Заплати сначала себе' - откладывайте сразу после получения дохода\n"
    response += "   • Разделяйте цели: краткосрочные, среднесрочные, долгосрочные\n"
    
    # 3. Инвестиционные советы
    response += "\n3. **Основы инвестиций:**\n"
    response += "   • Начинайте с малых сумм\n"
    response += "   • Диверсифицируйте портфель\n"
    response += "   • Инвестируйте в то, что понимаете\n"
    response += "   • Думайте долгосрочно\n"
    response += "   • Рассмотрите: акции, облигации, ETF, недвижимость (REIT)\n"
    
    # 4. Риски
    response += "\n4. **Управление рисками:**\n"
    response += "   • Не вкладывайте последние деньги\n"
    response += "   • Изучайте инструменты перед инвестированием\n"
    response += "   • Консультируйтесь с финансовыми советниками\n"
    
    return response

def get_expense_analysis(total_expenses, top_categories):
    """Анализ расходов"""
    if total_expenses == 0:
        return "У вас пока нет зарегистрированных расходов. Начните добавлять транзакции для анализа!"
    
    response = "**Анализ ваших расходов:**\n\n"
    response += f"**Общая сумма расходов:** ₸{total_expenses:.2f}\n\n"
    
    if top_categories:
        response += "**Распределение по категориям:**\n"
        for i, (cat_name, amount, percentage) in enumerate(top_categories, 1):
            emoji = "🛒" if "продукты" in cat_name.lower() else \
                   "🚗" if "транспорт" in cat_name.lower() else \
                   "🏠" if "жилье" in cat_name.lower() else \
                   "🍽️" if "кафе" in cat_name.lower() else \
                   "🎮" if "развлечения" in cat_name.lower() else \
                   "👕" if "одежда" in cat_name.lower() else "📊"
            
            response += f"{emoji} {cat_name}: ₸{amount:.2f} ({percentage:.1f}%)\n"
        
        # Выводы
        response += "\n**Выводы и рекомендации:**\n"
        if len(top_categories) > 0 and top_categories[0][2] > 40:
            response += f"• Категория '{top_categories[0][0]}' занимает слишком большую долю ({top_categories[0][2]:.1f}%)\n"
            response += "  Рекомендую найти способы сократить расходы в этой категории\n"
        
        if len(top_categories) > 5:
            small_categories = sum(amount for _, amount, _ in top_categories[5:])
            if small_categories > total_expenses * 0.15:
                response += "• У вас много мелких расходов в разных категориях\n"
                response += "  Рассмотрите возможность их объединения или сокращения\n"
    
    return response

def get_income_analysis(total_income, top_categories):
    """Анализ доходов"""
    if total_income == 0:
        return "У вас пока нет зарегистрированных доходов. Добавьте информацию о доходах для анализа!"
    
    response = "**Анализ ваших доходов:**\n\n"
    response += f"**Общая сумма доходов:** ₸{total_income:.2f}\n\n"
    
    if top_categories:
        response += "**Источники доходов:**\n"
        for i, (cat_name, amount, percentage) in enumerate(top_categories, 1):
            response += f"{i}. {cat_name}: ₸{amount:.2f} ({percentage:.1f}%)\n"
        
        response += "\n**Рекомендации:**\n"
        if len(top_categories) == 1:
            response += "• У вас один основной источник дохода\n"
            response += "  Рекомендую рассмотреть дополнительные источники дохода\n"
        elif len(top_categories) >= 3:
            response += "• Отличная диверсификация доходов!\n"
            response += "  Это снижает финансовые риски\n"
    
    response += "\n**Советы по увеличению доходов:**\n"
    response += "• Развивайте профессиональные навыки\n"
    response += "• Рассмотрите фриланс или подработку\n"
    response += "• Инвестируйте в образование\n"
    response += "• Ищите пассивные источники дохода\n"
    
    return response

def get_financial_health_advice(total_income, total_expenses):
    """Оценка финансового здоровья"""
    if total_income == 0:
        return "Для оценки финансового здоровья добавьте информацию о доходах и расходах."
    
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0
    
    response = "🏥 **Оценка финансового здоровья:**\n\n"
    
    response += "1. **Ключевые показатели:**\n"
    response += f"   • Доходы: ₸{total_income:.2f}\n"
    response += f"   • Расходы: ₸{total_expenses:.2f}\n"
    response += f"   • Сбережения: ₸{savings:.2f}\n"
    response += f"   • Норма сбережений: {savings_rate:.1f}%\n"
    
    response += "\n2. **Оценка:**\n"
    if savings_rate < 0:
        response += "   ⚠️ **Критическая ситуация:** расходы превышают доходы\n"
        response += "   Срочно сократите расходы или увеличьте доходы\n"
    elif savings_rate < 10:
        response += "   ⚠️ **Требует внимания:** низкая норма сбережений\n"
        response += "   Рекомендую увеличить сбережения до 20%\n"
    elif savings_rate < 20:
        response += "   ⚠️ **Удовлетворительно:** есть потенциал для улучшения\n"
    else:
        response += "   ✅ **Отлично:** хорошая норма сбережений\n"
    
    response += "\n3. **Рекомендации для улучшения:**\n"
    if savings_rate < 0:
        response += "   • Срочно сократите необязательные расходы\n"
        response += "   • Рассмотрите дополнительный доход\n"
        response += "   • Обратитесь за финансовой консультацией\n"
    elif savings_rate < 20:
        response += "   • Увеличьте норму сбережений на 5%\n"
        response += "   • Оптимизируйте крупные статьи расходов\n"
        response += "   • Создайте финансовый план\n"
    else:
        response += "   • Продолжайте в том же духе!\n"
        response += "   • Рассмотрите инвестиции\n"
        response += "   • Планируйте долгосрочные цели\n"
    
    return response

def get_help_message():
    """Сообщение со списком возможностей"""
    return """🤖 **Что я умею:**

**Команды чата:**
• /clear или "очистить чат" - очистить историю чата
• /history - показать историю сообщений
• /help - показать это сообщение

**Финансовый анализ:**
• "Проанализируй мои расходы"
• "Покажи мои доходы" 
• "Оцени моё финансовое здоровье"

**Бюджет и планирование:**
• "Помоги составить бюджет"
• "Советы по планированию бюджета"

**Экономия и оптимизация:**
• "Как мне экономить?"
• "Как сократить расходы на [категорию]?"

**Накопления и инвестиции:**
• "Как начать копить?"
• "Советы по инвестициям"
• "Создание финансовой подушки"

**Примеры вопросов:**
• "На что я трачу больше всего?"
• "Какой у меня должен быть бюджет?"
• "Как экономить на продуктах?"
• "Как создать подушку безопасности?"

**Задайте вопрос в свободной форме, и я постараюсь помочь!**"""

def get_general_advice(total_income, total_expenses, question):
    """Общий совет на неизвестный вопрос"""
    if total_income == 0 and total_expenses == 0:
        return "Привет! Я ваш финансовый помощник. Начните добавлять доходы и расходы в приложение, чтобы получать персонализированные советы.\n\nНапишите:\n• 'Как начать вести учёт?'\n• 'С чего начать планирование бюджета?'\n• 'Базовые советы по финансам'"

    if "как" in question and "начать" in question:
        return "**Как начать управлять финансами:**\n\n1. **Начните с учёта** - добавляйте все доходы и расходы\n2. **Анализируйте** - смотрите, куда уходят деньги\n3. **Ставьте цели** - определите, зачем вам экономить\n4. **Создайте бюджет** - используйте правило 50/30/20\n5. **Автоматизируйте** - настройте автоматические накопления\n\nХотите подробнее о каком-то из пунктов?"

    elif "совет" in question or "рекомендац" in question:
        return "**Топ-5 финансовых советов:**\n\n1. **Ведите учёт** - знайте свои финансы\n2. **Живите по средствам** - расходы ≤ доходы\n3. **Создайте подушку** - 3-6 месяцев расходов\n4. **Инвестируйте в себя** - образование и здоровье\n5. **Планируйте на будущее** - пенсия, крупные покупки\n\nКакой совет вас интересует больше?"

    else:
        return f"Я ваш финансовый помощник. На основе ваших данных могу дать советы по:\n• Экономии (вы тратите ₸{total_expenses:.2f})\n• Бюджету (доходы: ₸{total_income:.2f})\n• Накоплениям\n• Инвестициям\n\nЗадайте конкретный вопрос!"

def ai_answer(user_question, user_id=None):
    """
    Генерирует ответ AI-советника и сохраняет историю (БЕЗ СЕССИЙ)
    """
    try:
        current_username = load_session()
        
        if not current_username:
            return "Пожалуйста, авторизуйтесь для получения персонализированных советов."
        
        if not user_id:
            user_id = get_current_user_id(current_username)
            if not user_id:
                return "Ошибка: не удалось получить данные пользователя."
        
        # Сохраняем вопрос пользователя (БЕЗ session_id)
        save_chat_message(user_id, None, user_question, 'user')
        
        # Обработка специальных команд
        question_lower = user_question.lower().strip()
        
        if question_lower in ["/clear", "очистить", "очистить чат", "/clean"]:
            cleared = clear_chat_history(user_id)
            response = f"✅ История чата очищена. Удалено сообщений: {cleared}"
            save_chat_message(user_id, None, response, 'ai')
            return response
        
        elif question_lower in ["/history", "история", "показать историю"]:
            history = get_chat_history(user_id, limit=20)
            if not history:
                response = "История чата пуста."
            else:
                response = "📜 **История чата:**\n\n"
                for msg in history[-10:]:
                    sender = "Вы" if msg['type'] == 'user' else "AI"
                    time = msg['created_at'].strftime("%H:%M") if hasattr(msg['created_at'], 'strftime') else str(msg['created_at'])
                    response += f"[{time}] {sender}: {msg['text'][:80]}{'...' if len(msg['text']) > 80 else ''}\n"
            save_chat_message(user_id, None, response, 'ai')
            return response
        
        elif question_lower == "/help":
            response = get_help_message()
            save_chat_message(user_id, None, response, 'ai')
            return response
        
        # Генерируем ответ на основе вопроса
        response = generate_ai_response(user_question, current_username, user_id)
        
        # Сохраняем ответ AI
        save_chat_message(user_id, None, response, 'ai')
        
        return response
        
    except Exception as e:
        print(f"Ошибка в AI-советнике: {e}")
        import traceback
        traceback.print_exc()
        error_msg = "Извините, произошла техническая ошибка. Попробуйте задать вопрос позже."
        if user_id:
            save_chat_message(user_id, None, error_msg, 'ai')
        return error_msg


def generate_ai_response(user_question, username, user_id):
    """
    Генерирует ответ на основе вопроса
    """
    try:
        from db.statistics import db_get_expenses_summary, db_get_income_summary
        
        expenses_summary = db_get_expenses_summary(username)
        income_summary = db_get_income_summary(username)
        
        # Получаем историю для контекста
        chat_history = get_chat_history(user_id, limit=5)
        
        total_expenses = expenses_summary.get("total_expenses", 0)
        total_income = income_summary.get("total_income", 0)
        top_expense_categories = expenses_summary.get("top_categories", [])
        top_income_categories = income_summary.get("top_categories", [])
        
        question_lower = user_question.lower().strip()
        
        # Проверяем благодарность
        if any(word in question_lower for word in ["спасибо", "благодарю", "отлично", "хорошо"]):
            return "Пожалуйста! Рад был помочь 😊\n\nЕсли у вас есть ещё вопросы по финансам - обращайтесь!"
        
        # Проверяем приветствие
        if any(word in question_lower for word in ["привет", "здравствуй", "добрый день", "доброе утро"]):
            greeting = f"Привет! Я ваш финансовый помощник. "
            if total_expenses > 0 or total_income > 0:
                greeting += "Вижу у вас уже есть финансовые данные. Могу помочь с анализом расходов, составлением бюджета, советами по экономии и накоплениям."
            else:
                greeting += "У вас пока нет финансовых данных. Начните добавлять доходы и расходы, чтобы получать персонализированные советы."
            greeting += "\n\nЧто вас интересует?"
            return greeting
        
        if any(word in question_lower for word in ["экономить", "сэкономить", "тратить меньше", "сократить расходы", "сберечь"]):
            return get_savings_advice(total_expenses, total_income, top_expense_categories)
        
        elif any(word in question_lower for word in ["бюджет", "бюджетирование", "планирование", "план", "правило 50/30/20"]):
            return get_budget_advice(total_income, total_expenses)
        
        elif any(word in question_lower for word in ["накопления", "накопить", "инвестиции", "сбережения", "подушка безопасности", "копить"]):
            return get_savings_investment_advice(total_income, total_expenses)
        
        elif any(word in question_lower for word in ["расходы", "траты", "куда уходят деньги", "анализ расходов", "на что трачу"]):
            return get_expense_analysis(total_expenses, top_expense_categories)
        
        elif any(word in question_lower for word in ["доходы", "заработок", "прибыль", "анализ доходов", "сколько зарабатываю"]):
            return get_income_analysis(total_income, top_income_categories)
        
        elif any(word in question_lower for word in ["финансовое здоровье", "финансовое состояние", "стабильность", "финансовый статус"]):
            return get_financial_health_advice(total_income, total_expenses)
        
        elif "как начать" in question_lower or "с чего начать" in question_lower:
            return "**Как начать управлять финансами:**\n\n1. **Начните с учёта** - добавляйте все доходы и расходы\n2. **Анализируйте** - смотрите, куда уходят деньги\n3. **Ставьте цели** - определите, зачем вам экономить\n4. **Создайте бюджет** - используйте правило 50/30/20\n5. **Автоматизируйте** - настройте автоматические накопления\n\nХотите подробнее о каком-то из пунктов?"
        
        elif "совет" in question_lower or "рекомендац" in question_lower or "подскажи" in question_lower:
            return "**Топ-5 финансовых советов:**\n\n1. **Ведите учёт** - знайте свои финансы\n2. **Живите по средствам** - расходы ≤ доходы\n3. **Создайте подушку** - 3-6 месяцев расходов\n4. **Инвестируйте в себя** - образование и здоровье\n5. **Планируйте на будущее** - пенсия, крупные покупки\n\nКакой совет вас интересует больше?"
        
        else:
            recent_topics = []
            for msg in chat_history[-3:]:
                if msg['type'] == 'user':
                    recent_topics.append(msg['text'].lower())
            
            if any(any(word in topic for word in ["экономи", "сэкономить", "тратить"]) for topic in recent_topics):
                return f"Продолжая тему экономии:\n\n{get_savings_advice(total_expenses, total_income, top_expense_categories)}"
            elif any(any(word in topic for word in ["бюджет", "план", "планирование"]) for topic in recent_topics):
                return f"Возвращаясь к теме бюджета:\n\n{get_budget_advice(total_income, total_expenses)}"
            else:
                return get_general_advice(total_income, total_expenses, question_lower)
                
    except Exception as e:
        print(f"Ошибка генерации ответа: {e}")
        import traceback
        traceback.print_exc()
        return "Извините, не могу обработать ваш запрос. Попробуйте задать вопрос по-другому."