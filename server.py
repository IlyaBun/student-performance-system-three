"""
server.py - Серверная часть системы оценки успеваемости (ИАС ПолесГУ)
Содержит: БД SQLite, бизнес-логику, аутентификацию, CRUD операции
"""

import sqlite3
import bcrypt
import os
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any

DB_PATH = "polesgu_system.db"


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация БД: создание таблиц и демо-данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
                    full_name TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица студентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    group_name TEXT NOT NULL,
                    course INTEGER NOT NULL CHECK(course BETWEEN 1 AND 5),
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
                    value INTEGER NOT NULL CHECK(value BETWEEN 2 AND 10),
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
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            conn.commit()
            
            # Проверка на наличие данных
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                self._seed_data(cursor)
                conn.commit()
                print("[INFO] База данных создана и заполнена демо-данными")
                print("[INFO] Admin: admin / RwQNt")
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _seed_data(self, cursor: sqlite3.Cursor):
        """Генерация демо-данных"""
        
        # Предварительно вычисленные хеши (для ускорения)
        admin_hash = bcrypt.hashpw("RwQNt".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        teacher_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        student_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Создание админа
        cursor.execute(
            "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ("admin", admin_hash, "admin", "Администратор Системы")
        )
        
        # Создание преподавателей
        for i in range(1, 4):
            cursor.execute(
                "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                (f"teacher{i}", teacher_hash, "teacher", f"Преподаватель {i} Иванович")
            )
        
        # Группы и специальности
        groups = [
            ("ИВТ-11", 1, "Информатика и вычислительная техника"),
            ("ИВТ-12", 1, "Информатика и вычислительная техника"),
            ("ИВТ-21", 2, "Информатика и вычислительная техника"),
            ("ИВТ-22", 2, "Информатика и вычислительная техника"),
            ("Мех-11", 1, "Мехатроника и робототехника"),
            ("Мех-12", 1, "Мехатроника и робототехника"),
            ("Мех-21", 2, "Мехатроника и робототехника"),
            ("Энер-11", 1, "Электроэнергетика"),
            ("Энер-21", 2, "Электроэнергетика"),
            ("Строй-11", 1, "Строительство"),
        ]
        
        # Создание студентов (пакетная вставка для скорости)
        students_data = []
        for i in range(1, 251):
            group_idx = (i - 1) % len(groups)
            group_name, course, specialty = groups[group_idx]
            full_name = f"Студентов Студент {i}ович"
            students_data.append((f"student{i}", student_hash, "student", full_name, group_name, course, specialty))
        
        cursor.executemany(
            "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            [(s[0], s[1], s[2], s[3]) for s in students_data]
        )
        
        # Получаем ID созданных пользователей
        for i, student_data in enumerate(students_data, 1):
            user_id = i + 3  # 1 admin + 3 teachers
            cursor.execute(
                "INSERT INTO students (user_id, group_name, course, specialty) VALUES (?, ?, ?, ?)",
                (user_id, student_data[4], student_data[5], student_data[6])
            )
        
        student_ids = list(range(4, 254))  # IDs студентов
        
        # Создание дисциплин
        disciplines = [
            ("Высшая математика", "Кафедра математики"),
            ("Физика", "Кафедра физики"),
            ("Информатика", "Кафедра информатики"),
            ("Программирование", "Кафедра информатики"),
            ("Базы данных", "Кафедра информатики"),
            ("Алгоритмы и структуры данных", "Кафедра информатики"),
            ("Компьютерные сети", "Кафедра информатики"),
            ("Операционные системы", "Кафедра информатики"),
            ("Инженерная графика", "Кафедра черчения"),
            ("Сопротивление материалов", "Кафедра механики"),
            ("Теоретическая механика", "Кафедра механики"),
            ("Электротехника", "Кафедра энергетики"),
        ]
        
        for name, dept in disciplines:
            cursor.execute(
                "INSERT INTO disciplines (name, department) VALUES (?, ?)",
                (name, dept)
            )
        
        # Генерация оценок (~3000 штук)
        grade_types = ["exam", "lab", "practice", "zachet"]
        start_date = datetime(2024, 9, 1)
        
        for student_id in student_ids:
            # Каждый студент имеет оценки по 8-12 предметам
            num_disciplines = random.randint(8, 12)
            selected_disciplines = random.sample(range(1, 13), num_disciplines)
            
            for disc_id in selected_disciplines:
                num_grades = random.randint(2, 5)
                
                for _ in range(num_grades):
                    grade_type = random.choice(grade_types)
                    
                    if grade_type == "zachet":
                        # 90% зачтено, 10% не зачтено
                        value = 5 if random.random() < 0.9 else 2
                    else:
                        # Обычная оценка 2-10 с смещением к хорошим оценкам
                        weights = [0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10]
                        value = random.choices(range(2, 11), weights=weights)[0]
                    
                    days_offset = random.randint(0, 120)
                    grade_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                    
                    cursor.execute(
                        "INSERT INTO grades (student_id, discipline_id, value, grade_type, date) VALUES (?, ?, ?, ?, ?)",
                        (student_id, disc_id, value, grade_type, grade_date)
                    )
    
    # ==================== АУТЕНТИФИКАЦИЯ ====================
    
    def authenticate(self, login: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
        finally:
            conn.close()
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    def get_all_users(self, role_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить всех пользователей с сортировкой по роли"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if role_filter:
                cursor.execute("""
                    SELECT u.id, u.login, u.full_name, u.role, 
                           s.group_name, s.course, s.specialty
                    FROM users u
                    LEFT JOIN students s ON u.id = s.user_id
                    WHERE u.role = ?
                    ORDER BY 
                        CASE u.role WHEN 'admin' THEN 1 WHEN 'teacher' THEN 2 ELSE 3 END,
                        u.full_name
                """, (role_filter,))
            else:
                cursor.execute("""
                    SELECT u.id, u.login, u.full_name, u.role, 
                           s.group_name, s.course, s.specialty
                    FROM users u
                    LEFT JOIN students s ON u.id = s.user_id
                    ORDER BY 
                        CASE u.role WHEN 'admin' THEN 1 WHEN 'teacher' THEN 2 ELSE 3 END,
                        u.full_name
                """)
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def update_user_role(self, user_id: int, new_role: str, admin_id: int):
        """Обновить роль пользователя (только admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
            cursor.execute(
                "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                (admin_id, "change_role", f"User {user_id} role changed to {new_role}")
            )
            conn.commit()
        finally:
            conn.close()
    
    def add_user(self, login: str, password: str, role: str, full_name: str, 
                 group_name: Optional[str] = None, course: Optional[int] = None,
                 specialty: Optional[str] = None, admin_id: int = None):
        """Добавить нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                (login, pwd_hash, role, full_name)
            )
            user_id = cursor.lastrowid
            
            if role == "student" and group_name and course and specialty:
                cursor.execute(
                    "INSERT INTO students (user_id, group_name, course, specialty) VALUES (?, ?, ?, ?)",
                    (user_id, group_name, course, specialty)
                )
            
            if admin_id:
                cursor.execute(
                    "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                    (admin_id, "add_user", f"Added user {login} ({role})")
                )
            
            conn.commit()
            return user_id
        finally:
            conn.close()
    
    def delete_user(self, user_id: int, admin_id: int):
        """Удалить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            cursor.execute(
                "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                (admin_id, "delete_user", f"Deleted user {user_id}")
            )
            conn.commit()
        finally:
            conn.close()
    
    # ==================== СТУДЕНТЫ ====================
    
    def get_all_students(self, group_filter: Optional[str] = None, 
                         search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить всех студентов с фильтрацией и поиском"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT u.id, u.full_name, s.group_name, s.course, s.specialty,
                       COALESCE(AVG(g.value), 0) as avg_grade
                FROM users u
                JOIN students s ON u.id = s.user_id
                LEFT JOIN grades g ON u.id = g.student_id
                WHERE u.role = 'student'
            """
            params = []
            
            if group_filter and group_filter != "Все":
                query += " AND s.group_name = ?"
                params.append(group_filter)
            
            if search_query:
                query += " AND u.full_name LIKE ?"
                params.append(f"%{search_query}%")
            
            query += " GROUP BY u.id ORDER BY u.full_name"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_student_grades(self, student_id: int) -> List[Dict[str, Any]]:
        """Получить все оценки студента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT g.id, g.value, g.grade_type, g.date, d.name as discipline
                FROM grades g
                JOIN disciplines d ON g.discipline_id = d.id
                WHERE g.student_id = ?
                ORDER BY g.date DESC
            """, (student_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_groups(self) -> List[str]:
        """Получить список всех групп"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT group_name FROM students ORDER BY group_name")
            return [row["group_name"] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ==================== ДИСЦИПЛИНЫ ====================
    
    def get_all_disciplines(self) -> List[Dict[str, Any]]:
        """Получить все дисциплины"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, name, department FROM disciplines ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ==================== ОЦЕНКИ ====================
    
    def get_grades_for_group(self, group_name: str, discipline_id: Optional[int] = None,
                             search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить оценки для группы с фильтрацией по предмету и поиску"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT g.id, u.id as student_id, u.full_name, s.group_name,
                       g.value, g.grade_type, g.date, d.name as discipline
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN disciplines d ON g.discipline_id = d.id
                WHERE s.group_name = ?
            """
            params = [group_name]
            
            if discipline_id:
                query += " AND g.discipline_id = ?"
                params.append(discipline_id)
            
            if search_query:
                query += " AND u.full_name LIKE ?"
                params.append(f"%{search_query}%")
            
            query += " ORDER BY u.full_name, g.date DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def update_grade(self, grade_id: int, new_value: int, new_type: str, 
                     user_id: int) -> bool:
        """Обновить оценку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Получить старое значение
            cursor.execute("SELECT value, grade_type FROM grades WHERE id = ?", (grade_id,))
            old_row = cursor.fetchone()
            
            if not old_row:
                return False
            
            old_value = old_row["value"]
            old_type = old_row["grade_type"]
            
            cursor.execute(
                "UPDATE grades SET value = ?, grade_type = ? WHERE id = ?",
                (new_value, new_type, grade_id)
            )
            
            cursor.execute(
                "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "update_grade", 
                 f"Grade {grade_id}: {old_value}({old_type}) -> {new_value}({new_type})")
            )
            
            conn.commit()
            return True
        finally:
            conn.close()
    
    def add_grade(self, student_id: int, discipline_id: int, value: int, 
                  grade_type: str, date: str, user_id: int) -> int:
        """Добавить новую оценку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO grades (student_id, discipline_id, value, grade_type, date) VALUES (?, ?, ?, ?, ?)",
                (student_id, discipline_id, value, grade_type, date)
            )
            grade_id = cursor.lastrowid
            
            cursor.execute(
                "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "add_grade", f"Added grade {value} for student {student_id}")
            )
            
            conn.commit()
            return grade_id
        finally:
            conn.close()
    
    def delete_grade(self, grade_id: int, user_id: int) -> bool:
        """Удалить оценку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
            
            cursor.execute(
                "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "delete_grade", f"Deleted grade {grade_id}")
            )
            
            conn.commit()
            return True
        finally:
            conn.close()
    
    # ==================== СТАТИСТИКА И АНАЛИТИКА ====================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получить статистику для Dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Всего студентов
            cursor.execute("SELECT COUNT(*) as count FROM students")
            total_students = cursor.fetchone()["count"]
            
            # Средний балл по факультету
            cursor.execute("SELECT AVG(value) as avg FROM grades")
            avg_grade = cursor.fetchone()["avg"] or 0
            
            # Успеваемость (% оценок > 3)
            cursor.execute("SELECT COUNT(*) as total FROM grades")
            total_grades = cursor.fetchone()["total"] or 1
            
            cursor.execute("SELECT COUNT(*) as passed FROM grades WHERE value > 3")
            passed_grades = cursor.fetchone()["passed"] or 0
            success_rate = (passed_grades / total_grades) * 100
            
            # Качество (% оценок 8-10)
            cursor.execute("SELECT COUNT(*) as excellent FROM grades WHERE value >= 8")
            excellent_grades = cursor.fetchone()["excellent"] or 0
            quality_rate = (excellent_grades / total_grades) * 100
            
            return {
                "total_students": total_students,
                "avg_grade": round(avg_grade, 2),
                "success_rate": round(success_rate, 2),
                "quality_rate": round(quality_rate, 2)
            }
        finally:
            conn.close()
    
    def get_at_risk_students(self) -> List[Dict[str, Any]]:
        """Получить студентов группы риска (есть оценки <= 4)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT u.full_name, s.group_name, MIN(g.value) as min_grade
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE g.value <= 4
                GROUP BY u.id, s.group_name
                ORDER BY min_grade ASC, u.full_name
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_avg_by_group(self) -> List[Dict[str, Any]]:
        """Получить средний балл по группам для аналитики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT s.group_name, AVG(g.value) as avg_grade
                FROM grades g
                JOIN students s ON g.student_id = s.id
                GROUP BY s.group_name
                ORDER BY s.group_name
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ==================== ЛОГИ ====================
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить последние логи"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT l.id, u.full_name as user_name, l.action, l.details, l.timestamp
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


# Глобальный экземпляр БД
db = Database()
