import psycopg2
from datetime import datetime
from db.connection import get_db_conn

def create_savings_goal(user_id, goal_name, target_amount, deadline=None):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        target_amount = float(target_amount)
        
        cursor.execute(, (user_id, goal_name, target_amount, deadline))
        
        goal_id = cursor.fetchone()[0]
        conn.commit()
        return goal_id
    except Exception as e:
        print(f"Ошибка при создании цели: {e}")
        return None
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def get_savings_goals(user_id):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute(, (user_id,))
        
        goals = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            goal = dict(zip(columns, row))
            current_amount = float(goal['current_amount']) if goal['current_amount'] is not None else 0.0
            target_amount = float(goal['target_amount']) if goal['target_amount'] is not None else 0.0
            if target_amount > 0:
                progress = (current_amount / target_amount * 100)
            else:
                progress = 0.0
            goal['current_amount'] = current_amount
            goal['target_amount'] = target_amount
            goal['progress'] = float(progress)
            goal['remaining'] = target_amount - current_amount
            if goal['deadline'] and hasattr(goal['deadline'], 'strftime'):
                goal['deadline'] = goal['deadline'].strftime('%Y-%m-%d')
            
            goals.append(goal)
        
        return goals
    except Exception as e:
        print(f"Ошибка при получении целей: {e}")
        return []
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def get_savings_goal_by_id(goal_id, user_id=None):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute(, (goal_id, user_id))
        else:
            cursor.execute(, (goal_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"Ошибка при получении цели: {e}")
        return None
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def add_to_savings_goal(goal_id, amount, user_id=None):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        if user_id:
            cursor.execute(, (goal_id, user_id))
        else:
            cursor.execute(, (goal_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        current_amount, target_amount = result
        new_amount = float(current_amount) + float(amount)
        if new_amount > float(target_amount):
            amount_to_add = float(target_amount) - float(current_amount)
            if amount_to_add <= 0:
                return current_amount
            print(f"Внимание: добавлено только {amount_to_add:.2f} из {amount:.2f} (ограничение цели)")
        if user_id:
            cursor.execute(, (amount, goal_id, user_id))
        else:
            cursor.execute(, (amount, goal_id))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            current_amount, target_amount = result
            if float(current_amount) >= float(target_amount):
                cursor.execute(, (goal_id,))
                conn.commit()
            
            return current_amount
        return None
    except Exception as e:
        print(f"Ошибка при добавлении к цели: {e}")
        conn.rollback()
        return None
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def update_savings_goal(goal_id, goal_name=None, target_amount=None, deadline=None, user_id=None):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if goal_name:
            updates.append("goal_name = %s")
            params.append(goal_name)
        
        if target_amount is not None:
            updates.append("target_amount = %s")
            params.append(target_amount)
        
        if deadline:
            updates.append("deadline = %s")
            params.append(deadline)
        
        if not updates:
            return False
        if user_id:
            updates.append("user_id = %s")
            params.append(user_id)
            where_condition = "WHERE goal_id = %s AND user_id = %s"
            params.append(goal_id)
            params.append(user_id)
        else:
            where_condition = "WHERE goal_id = %s"
            params.append(goal_id)
        
        query = f"UPDATE savings_goals SET {', '.join(updates)} {where_condition}"
        cursor.execute(query, params)
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при обновлении цели: {e}")
        conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def delete_savings_goal(goal_id, user_id=None):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute(, (goal_id, user_id))
        else:
            cursor.execute(, (goal_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при удалении цели: {e}")
        conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def get_savings_goal_progress(user_id):
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute(, (user_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            stats = dict(zip(columns, row))
            total_target = float(stats['total_target'])
            total_current = float(stats['total_current'])
            total_goals = int(stats['total_goals'])
            completed_goals = int(stats['completed_goals'])
            
            if total_target > 0:
                total_progress = (total_current / total_target * 100)
            else:
                total_progress = 0.0
            
            return {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'total_target': total_target,
                'total_current': total_current,
                'total_progress': float(total_progress)
            'total_goals': 0,
            'completed_goals': 0,
            'total_target': 0.0,
            'total_current': 0.0,
            'total_progress': 0.0
        }
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {
            'total_goals': 0,
            'completed_goals': 0,
            'total_target': 0.0,
            'total_current': 0.0,
            'total_progress': 0.0
        }
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()