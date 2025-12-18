
"""
Модуль db - работа с базой данных PostgreSQL
"""



from .connection import get_db_conn
from .users import ensure_default_data, get_current_user_id, create_user_with_defaults, fetch_all_users, get_user_role, update_user, delete_user_by_id, create_user_admin
from .transactions import (
    db_insert_transaction,
    db_fetch_all_transactions,
    db_fetch_transactions_by_category,
    db_clear_all_transactions,
    update_transaction,
    delete_transaction,
    db_fetch_all_transactions_for_admin,
    db_fetch_user_transactions,
    debug_update_transaction,
    delete_user_transaction,
    db_delete_transaction
)
from .ai_advisor import save_chat_message, get_chat_history, clear_chat_history, save_chat_message, delete_chat_message
# =========================================================
# ✅ ИСПРАВЛЕНИЕ: Добавлен импорт из categories.py
from .categories import db_get_category_stats, db_get_user_categories
# =========================================================
from .statistics import db_get_statistics, db_get_expenses_summary, db_get_income_summary,db_get_transactions_period # Здесь была дублирующаяся db_get_statistics, я ее удалил

# Обновленный импорт уведомлений с новыми функциями
from .notifications import (
    db_create_notification,
    db_create_notifications_for_all_users,
    db_fetch_notifications,
    db_mark_notification_read,
    db_mark_all_notifications_read,
    db_delete_notification,
    db_delete_all_read_notifications,
    get_unread_count,
    get_relative_time,
    # Утилиты для создания специфических уведомлений
    create_transaction_notification,
    create_budget_warning_notification,
    create_weekly_report_notification,
    create_reminder_notification,
    NOTIFICATION_TYPES
)

from .savings_goals import (
    create_savings_goal,
    get_savings_goals,
    get_savings_goal_by_id,
    add_to_savings_goal,
    update_savings_goal,
    delete_savings_goal,
    get_savings_goal_progress
)

__all__ = [
    'get_db_conn',
    'ensure_default_data',
    'get_current_user_id',
    'create_user_with_defaults',
    'db_insert_transaction',
    'db_fetch_all_transactions',
    'db_fetch_transactions_by_category',
    'db_clear_all_transactions',
    'db_get_category_stats', # Это имя теперь будет доступно после импорта выше
    'db_get_expenses_summary',
    'db_get_statistics',
    # Основные функции уведомлений
    'db_create_notification',
    'db_create_notifications_for_all_users',
    'db_fetch_notifications',
    'db_mark_notification_read',
    'db_mark_all_notifications_read',
    'db_delete_notification',
    'db_delete_all_read_notifications',
    'get_unread_count',
    'get_relative_time',
    # Утилиты для уведомлений
    'create_transaction_notification',
    'create_budget_warning_notification',
    'create_weekly_report_notification',
    'create_reminder_notification',
    'NOTIFICATION_TYPES',
    # Пользователи и транзакции
    'fetch_all_users',
    'get_user_role',
    'update_user',
    'delete_user_by_id',
    'update_transaction',
    'delete_transaction',
    'db_fetch_all_transactions_for_admin',
    'db_fetch_user_transactions',
    'db_get_user_categories',
    'debug_update_transaction',
    'create_user_admin',
    'db_get_income_summary',
    'db_get_transactions_period',
    'clear_chat_history',
    'get_chat_history',
    'save_chat_message',
    'delete_user_transaction',
    'db_delete_transaction',
    'activate_chat_session',
    'delete_chat_message',
    'create_savings_goal',
    'get_savings_goals',
    'get_savings_goal_by_id',
    'add_to_savings_goal',
    'update_savings_goal',
    'delete_savings_goal',
    'get_savings_goal_progress'
]