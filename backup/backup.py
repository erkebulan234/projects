import os
import subprocess
from datetime import datetime
import sys

def backup_database():
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_db = os.getenv("PG_DB", "finance_tracker")
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "1234")
    os.environ["PGPASSWORD"] = pg_password
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{backup_dir}/backup_{pg_db}_{timestamp}.sql"

    print(f"Начинаю создание бэкапа базы {pg_db}...")
    command = [
        "pg_dump",
        "-h", pg_host,
        "-p", pg_port,
        "-U", pg_user,
        "-F", "p",
        "-f", filename,
        print(f"✅ Успешно! Бэкап сохранен в: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании бэкапа (pg_dump вернул код ошибки): {e}")
        if e.output:
            print(f"Подробности: {e.output.decode(sys.getdefaultencoding())}")
    except FileNotFoundError:
        print("❌ Ошибка: Утилита pg_dump не найдена. Убедитесь, что PostgreSQL установлен и добавлен в PATH.")

if __name__ == "__main__":
    backup_database()