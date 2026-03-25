"""
server.py - Серверная часть системы оценки успеваемости студентов
База данных, бизнес-логика, аутентификация
"""

import sqlite3
import bcrypt
import os
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = "polesgu_system.db"


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
        
    def _connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Ошибка подключения к БД: {e}")
            raise
    
    def _create_tables(self):
        """Создание таблиц базы данных"""
        if self.conn is None:
            return
            
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
                full_name TEXT NOT NULL
            )
        """)
        
        # Таблица студентов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                group_name TEXT NOT NULL,
                course INTEGER NOT NULL,
                specialty TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица дисциплин
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS disciplines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL
            )
        """)
        
        # Таблица оценок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                discipline_id INTEGER NOT NULL,
                value INTEGER NOT NULL CHECK(value >= 2 AND value <= 10),
                grade_type TEXT NOT NULL CHECK(grade_type IN ('exam', 'lab', 'practice', 'zachet')),
                date TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (discipline_id) REFERENCES disciplines(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица логов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        self.conn.commit()
        
        # Проверка на пустую БД и генерация демо-данных
        self._check_and_seed()
    
    def _check_and_seed(self):
        """Проверка наличия данных и генерация демо-данных при необходимости"""
        if self.conn is None:
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("База данных пуста. Генерация демо-данных...")
            self._generate_demo_data()
            print("Демо-данные успешно созданы!")
            print("Логин админа: admin / Пароль: RwQNt")
    
    def _generate_demo_data(self):
        """Генерация демонстрационных данных"""
        if self.conn is None:
            return
            
        cursor = self.conn.cursor()
        
        # Предварительно генерируем хеши для ускорения
        admin_hash = bcrypt.hashpw("RwQNt".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        teacher_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        student_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Создание админа
        cursor.execute(
            "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ("admin", admin_hash, "admin", "Администратор Системы")
        )
        
        # Создание преподавателей
        teacher_ids = []
        for i in range(1, 4):
            cursor.execute(
                "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                (f"teacher{i}", teacher_hash, "teacher", f"Преподаватель {i}")
            )
            teacher_ids.append(cursor.lastrowid)
        
        # Создание студентов (250 шт) - используем пакетную вставку
        groups = [
            ("ИВТ-11", 1, "Информатика"), ("ИВТ-12", 1, "Информатика"),
            ("ИВТ-21", 2, "Информатика"), ("ИВТ-22", 2, "Информатика"),
            ("Мех-11", 1, "Механика"), ("Мех-12", 1, "Механика"),
            ("Мех-21", 2, "Механика"), ("Мех-22", 2, "Механика"),
            ("Энер-11", 1, "Энергетика"), ("Энер-21", 2, "Энергетика")
        ]
        
        # Пакетная вставка пользователей-студентов
        students_data = []
        for i in range(1, 251):
            group_info = groups[(i - 1) % len(groups)]
            students_data.append((
                f"student{i}",
                student_hash,
                "student",
                f"Студент {i} Иванов",
                group_info[0],
                group_info[1],
                group_info[2]
            ))
        
        cursor.executemany(
            "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            [(s[0], s[1], s[2], s[3]) for s in students_data]
        )
        
        # Получаем ID всех студентов
        cursor.execute("SELECT id FROM users WHERE role = 'student' ORDER BY login")
        student_user_ids = [row[0] for row in cursor.fetchall()]
        
        # Пакетная вставка записей о студентах
        students_records = []
        for idx, user_id in enumerate(student_user_ids):
            group_info = groups[idx % len(groups)]
            students_records.append((user_id, group_info[0], group_info[1], group_info[2]))
        
        cursor.executemany(
            "INSERT INTO students (user_id, group_name, course, specialty) VALUES (?, ?, ?, ?)",
            students_records
        )
        
        # Получаем ID записей студентов
        cursor.execute("SELECT id FROM students ORDER BY group_name, id")
        student_ids = [row[0] for row in cursor.fetchall()]
        
        # Создание дисциплин (12 шт)
        disciplines = [
            ("Высшая математика", "Кафедра математики"),
            ("Физика", "Кафедра физики"),
            ("Программирование", "Кафедра ИТ"),
            ("Базы данных", "Кафедра ИТ"),
            ("Инженерная графика", "Кафедра графики"),
            ("Теоретическая механика", "Кафедра механики"),
            ("Сопротивление материалов", "Кафедра механики"),
            ("Электротехника", "Кафедра энергетики"),
            ("Иностранный язык", "Кафедра языков"),
            ("Философия", "Кафедра гуманитарных наук"),
            ("Экономика", "Кафедра экономики"),
            ("Безопасность жизнедеятельности", "Кафедра БЖД")
        ]
        
        discipline_ids = []
        for disc in disciplines:
            cursor.execute(
                "INSERT INTO disciplines (name, department) VALUES (?, ?)",
                disc
            )
            discipline_ids.append(cursor.lastrowid)
        
        # Генерация оценок (~3000 шт) - пакетная вставка для скорости
        grade_types = ["exam", "lab", "practice", "zachet"]
        base_date = datetime(2024, 9, 1)
        
        grades_data = []
        for _ in range(3000):
            student_id = random.choice(student_ids)
            discipline_id = random.choice(discipline_ids)
            grade_type = random.choice(grade_types)
            
            # Логика оценок
            if grade_type == "zachet":
                # 90% вероятность зачета (5), 10% незачета (2)
                value = 5 if random.random() < 0.9 else 2
            else:
                # Обычные оценки 2-10 с нормальным распределением
                value = random.choices(
                    [2, 3, 4, 5, 6, 7, 8, 9, 10],
                    weights=[1, 2, 5, 8, 10, 12, 15, 12, 10]
                )[0]
            
            # Случайная дата в пределах семестра
            days_offset = random.randint(0, 120)
            date_str = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            
            grades_data.append((student_id, discipline_id, value, grade_type, date_str))
        
        cursor.executemany(
            "INSERT INTO grades (student_id, discipline_id, value, grade_type, date) VALUES (?, ?, ?, ?, ?)",
            grades_data
        )
        
        self.conn.commit()
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
    
    # ==================== Аутентификация ====================
    
    def authenticate(self, login: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя"""
        if self.conn is None:
            return None
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, login, password_hash, role, full_name FROM users WHERE login = ?",
                (login,)
            )
            row = cursor.fetchone()
            
            if row and bcrypt.checkpw(password.encode('utf-8'), row["password_hash"].encode('utf-8')):
                return {
                    "id": row["id"],
                    "login": row["login"],
                    "role": row["role"],
                    "full_name": row["full_name"]
                }
            return None
        except sqlite3.Error as e:
            print(f"Ошибка аутентификации: {e}")
            return None
    
    # ==================== Логи ====================
    
    def log_action(self, user_id: int, action: str, details: str):
        """Запись действия в лог"""
        if self.conn is None:
            return
            
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, action, details, timestamp)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка записи лога: {e}")
    
    # ==================== Статистика ====================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получение статистики для Dashboard"""
        if self.conn is None:
            return {}
            
        try:
            cursor = self.conn.cursor()
            
            # Всего студентов
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]
            
            # Средний балл факультета
            cursor.execute("SELECT AVG(value) FROM grades")
            avg_grade = cursor.fetchone()[0] or 0.0
            
            # Успеваемость (>3)
            cursor.execute("SELECT COUNT(*) FROM grades WHERE value > 3")
            passed_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM grades")
            total_grades = cursor.fetchone()[0] or 1
            success_rate = (passed_count / total_grades) * 100 if total_grades > 0 else 0
            
            # Качество (8-10)
            cursor.execute("SELECT COUNT(*) FROM grades WHERE value >= 8")
            quality_count = cursor.fetchone()[0] or 0
            quality_rate = (quality_count / total_grades) * 100 if total_grades > 0 else 0
            
            return {
                "total_students": total_students,
                "avg_grade": round(avg_grade, 2),
                "success_rate": round(success_rate, 2),
                "quality_rate": round(quality_rate, 2)
            }
        except sqlite3.Error as e:
            print(f"Ошибка получения статистики: {e}")
            return {}
    
    def get_at_risk_students(self) -> List[Dict[str, Any]]:
        """Получение студентов группы риска (есть оценка <= 4)"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT u.full_name, s.group_name, MIN(g.value) as min_grade
                FROM students s
                JOIN users u ON s.user_id = u.id
                JOIN grades g ON s.id = g.student_id
                WHERE g.value <= 4
                ORDER BY min_grade ASC, u.full_name ASC
                LIMIT 20
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "full_name": row["full_name"],
                    "group_name": row["group_name"],
                    "min_grade": row["min_grade"]
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения группы риска: {e}")
            return []
    
    # ==================== Студенты ====================
    
    def get_all_groups(self) -> List[str]:
        """Получение списка всех групп"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT group_name FROM students ORDER BY group_name")
            return [row["group_name"] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Ошибка получения групп: {e}")
            return []
    
    def get_students(self, group_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение списка студентов с фильтрацией по группе"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            
            if group_filter and group_filter != "Все":
                cursor.execute("""
                    SELECT u.id, u.full_name, s.group_name, s.course, 
                           COALESCE((SELECT AVG(g.value) FROM grades g WHERE g.student_id = s.id), 0) as avg_grade
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.group_name = ?
                    ORDER BY u.full_name
                """, (group_filter,))
            else:
                cursor.execute("""
                    SELECT u.id, u.full_name, s.group_name, s.course, 
                           COALESCE((SELECT AVG(g.value) FROM grades g WHERE g.student_id = s.id), 0) as avg_grade
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    ORDER BY s.group_name, u.full_name
                """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "full_name": row["full_name"],
                    "group_name": row["group_name"],
                    "course": row["course"],
                    "avg_grade": round(row["avg_grade"], 2) if row["avg_grade"] else 0.0
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения студентов: {e}")
            return []
    
    def get_student_grades(self, student_id: int) -> List[Dict[str, Any]]:
        """Получение оценок конкретного студента"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT d.name as discipline, g.value, g.grade_type, g.date
                FROM grades g
                JOIN disciplines d ON g.discipline_id = d.id
                WHERE g.student_id = ?
                ORDER BY g.date DESC
            """, (student_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "discipline": row["discipline"],
                    "value": row["value"],
                    "grade_type": row["grade_type"],
                    "date": row["date"]
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения оценок студента: {e}")
            return []
    
    # ==================== Дисциплины ====================
    
    def get_all_disciplines(self) -> List[Dict[str, Any]]:
        """Получение списка всех дисциплин"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name FROM disciplines ORDER BY name")
            return [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Ошибка получения дисциплин: {e}")
            return []
    
    # ==================== Журнал оценок ====================
    
    def get_gradebook(self, group_name: str, discipline_id: int) -> List[Dict[str, Any]]:
        """Получение журнала оценок для группы по предмету"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT s.id as student_id, u.full_name, g.value, g.grade_type, g.date, g.id as grade_id
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN grades g ON s.id = g.student_id AND g.discipline_id = ?
                WHERE s.group_name = ?
                ORDER BY u.full_name
            """, (discipline_id, group_name))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "student_id": row["student_id"],
                    "full_name": row["full_name"],
                    "value": row["value"],
                    "grade_type": row["grade_type"],
                    "date": row["date"],
                    "grade_id": row["grade_id"]
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения журнала: {e}")
            return []
    
    def update_grade(self, grade_id: Optional[int], student_id: int, discipline_id: int,
                     value: int, grade_type: str, user_id: int) -> bool:
        """Обновление или создание оценки"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            if grade_id:
                # Получаем старое значение для лога
                cursor.execute("SELECT value FROM grades WHERE id = ?", (grade_id,))
                old_row = cursor.fetchone()
                old_value = old_row["value"] if old_row else None
                
                # Обновляем существующую оценку
                cursor.execute(
                    "UPDATE grades SET value = ?, grade_type = ?, date = ? WHERE id = ?",
                    (value, grade_type, date_str, grade_id)
                )
                
                # Запись в лог
                details = f"Оценка изменена: {old_value} -> {value} (Тип: {grade_type})"
                self.log_action(user_id, "UPDATE_GRADE", details)
            else:
                # Создаем новую оценку
                cursor.execute(
                    "INSERT INTO grades (student_id, discipline_id, value, grade_type, date) VALUES (?, ?, ?, ?, ?)",
                    (student_id, discipline_id, value, grade_type, date_str)
                )
                
                # Запись в лог
                details = f"Создана оценка: {value} (Тип: {grade_type})"
                self.log_action(user_id, "CREATE_GRADE", details)
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка обновления оценки: {e}")
            return False
    
    # ==================== Аналитика ====================
    
    def get_group_averages(self) -> Dict[str, float]:
        """Получение среднего балла по группам"""
        if self.conn is None:
            return {}
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT s.group_name, AVG(g.value) as avg_grade
                FROM students s
                JOIN grades g ON s.id = g.student_id
                GROUP BY s.group_name
                ORDER BY s.group_name
            """)
            
            return {row["group_name"]: round(row["avg_grade"], 2) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"Ошибка получения аналитики: {e}")
            return {}
    
    # ==================== Пользователи ====================
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, login, full_name, role
                FROM users
                ORDER BY 
                    CASE role 
                        WHEN 'admin' THEN 1 
                        WHEN 'teacher' THEN 2 
                        WHEN 'student' THEN 3 
                    END,
                    full_name
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "login": row["login"],
                    "full_name": row["full_name"],
                    "role": row["role"]
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения пользователей: {e}")
            return []
    
    def promote_to_teacher(self, user_id: int, admin_user_id: int) -> bool:
        """Повышение студента до преподавателя"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            
            # Проверяем текущую роль
            cursor.execute("SELECT role, full_name FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row or row["role"] != "student":
                return False
            
            # Обновляем роль
            cursor.execute("UPDATE users SET role = 'teacher' WHERE id = ?", (user_id,))
            self.conn.commit()
            
            # Запись в лог
            details = f"Пользователь {row['full_name']} повышен до преподавателя"
            self.log_action(admin_user_id, "PROMOTE_USER", details)
            
            return True
        except sqlite3.Error as e:
            print(f"Ошибка повышения пользователя: {e}")
            return False
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение последних записей лога"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT l.id, u.full_name, l.action, l.details, l.timestamp
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "user_name": row["full_name"] or "Unknown",
                    "action": row["action"],
                    "details": row["details"],
                    "timestamp": row["timestamp"]
                })
            return results
        except sqlite3.Error as e:
            print(f"Ошибка получения логов: {e}")
            return []


# Глобальный экземпляр БД
db: Optional[Database] = None


def get_database() -> Database:
    """Получение экземпляра базы данных"""
    global db
    if db is None:
        db = Database()
    return db


def close_database():
    """Закрытие соединения с базой данных"""
    global db
    if db:
        db.close()
        db = None
