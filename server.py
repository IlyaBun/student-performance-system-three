"""
server.py - Серверная часть ИС ПолесГУ
База данных, бизнес-логика, аутентификация
"""

import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = "polesgu_system.db"

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Подключение к БД"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def create_tables(self):
        """Создание таблиц"""
        try:
            # Таблица пользователей
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
                    full_name TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Таблица студентов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    group_name TEXT NOT NULL,
                    course INTEGER NOT NULL CHECK(course BETWEEN 1 AND 5),
                    semester INTEGER NOT NULL CHECK(semester BETWEEN 1 AND 2),
                    specialty TEXT NOT NULL,
                    enrollment_year INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица дисциплин
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS disciplines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    department TEXT,
                    hours INTEGER,
                    control_type TEXT CHECK(control_type IN ('exam', 'zachet', 'coursework'))
                )
            ''')
            
            # Таблица оценок
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    discipline_id INTEGER NOT NULL,
                    value INTEGER NOT NULL CHECK(value BETWEEN 2 AND 10),
                    grade_type TEXT NOT NULL CHECK(grade_type IN ('exam', 'lab', 'practice', 'zachet', 'coursework')),
                    date TEXT NOT NULL,
                    semester INTEGER NOT NULL,
                    comment TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (discipline_id) REFERENCES disciplines(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица комментариев к студентам
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    comment_text TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_debt_related INTEGER DEFAULT 0,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица логов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            self.conn.commit()
            
            # Генерация демо-данных если БД пуста
            self._seed_data()
            
        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")
            raise
    
    def _seed_data(self):
        """Генерация демо-данных"""
        # Проверка наличия данных
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] > 0:
            return
            
        print("Генерация демо-данных...")
        
        # Создание админа
        admin_hash = bcrypt.hashpw("RwQNt".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.cursor.execute('''
            INSERT INTO users (login, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_hash, 'admin', 'Администратор Системы', 'admin@polesgu.by'))
        admin_id = self.cursor.lastrowid
        
        # Создание преподавателей
        teacher_ids = []
        for i in range(1, 6):
            pwd_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.cursor.execute('''
                INSERT INTO users (login, password_hash, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'teacher{i}', pwd_hash, 'teacher', f'Преподаватель {i}', f'teacher{i}@polesgu.by'))
            teacher_ids.append(self.cursor.lastrowid)
        
        # Группы и специальности
        groups_data = [
            ("ИТ", "Информационные технологии"),
            ("ЛП", "Лесное дело и ландшафтный дизайн"),
            ("ПР", "Природопользование и экология")
        ]
        
        # Создание студентов (250 штук)
        student_count = 0
        specialties_map = {
            "ИТ": "Информатика и программное обеспечение",
            "ЛП": "Лесное хозяйство",
            "ПР": "Природопользование"
        }
        
        for course in range(1, 6):
            for group_prefix, specialty in groups_data:
                for group_num in range(1, 4):  # 3 группы на курс
                    group_name = f"{group_prefix}-{course}{group_num}"
                    
                    for student_num in range(1, 6 if course < 5 else 5):  # ~250 студентов
                        student_count += 1
                        login = f"student{student_count}"
                        pwd_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        full_name = f"Студентов Студент {student_count}ович"
                        
                        self.cursor.execute('''
                            INSERT INTO users (login, password_hash, role, full_name, email)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (login, pwd_hash, 'student', full_name, f'{login}@polesgu.by'))
                        user_id = self.cursor.lastrowid
                        
                        enrollment_year = 2024 - course + 1
                        
                        self.cursor.execute('''
                            INSERT INTO students (user_id, group_name, course, semester, specialty, enrollment_year)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_id, group_name, course, 1, specialty, enrollment_year))
        
        # Создание дисциплин
        disciplines = [
            ("Высшая математика", "Кафедра математики", 144, "exam"),
            ("Физика", "Кафедра физики", 108, "exam"),
            ("Программирование", "Кафедра ИТ", 180, "exam"),
            ("Базы данных", "Кафедра ИТ", 72, "exam"),
            ("Web-технологии", "Кафедра ИТ", 72, "zachet"),
            ("Лесоводство", "Кафедра лесного дела", 108, "exam"),
            ("Ландшафтный дизайн", "Кафедра дизайна", 72, "zachet"),
            ("Экология", "Кафедра экологии", 72, "exam"),
            ("Природопользование", "Кафедра экологии", 90, "exam"),
            ("Философия", "Кафедра гуманитарных наук", 72, "zachet"),
            ("Иностранный язык", "Кафедра языков", 108, "zachet"),
            ("Физическая культура", "Кафедра спорта", 144, "zachet"),
            ("Экономика", "Кафедра экономики", 72, "exam"),
            ("Право", "Кафедра права", 54, "zachet"),
        ]
        
        for disc in disciplines:
            self.cursor.execute('''
                INSERT INTO disciplines (name, department, hours, control_type)
                VALUES (?, ?, ?, ?)
            ''', disc)
        
        # Генерация оценок (~3000)
        self.cursor.execute("SELECT id FROM students")
        student_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM disciplines")
        discipline_ids = [row[0] for row in self.cursor.fetchall()]
        
        grade_types = ['exam', 'lab', 'practice', 'zachet']
        
        import random
        random.seed(42)  # Для воспроизводимости
        
        grade_count = 0
        for student_id in student_ids:
            # Каждый студент имеет оценки по 8-12 предметам
            num_disciplines = random.randint(8, 12)
            selected_disciplines = random.sample(discipline_ids, num_disciplines)
            
            for disc_id in selected_disciplines:
                # Получаем тип контроля
                self.cursor.execute("SELECT control_type FROM disciplines WHERE id=?", (disc_id,))
                control_type = self.cursor.fetchone()[0]
                
                # Генерируем 1-3 оценки по предмету
                num_grades = random.randint(1, 3)
                
                for _ in range(num_grades):
                    grade_count += 1
                    
                    # Логика оценок: очень мало плохих (ниже 4)
                    rand_val = random.random()
                    if rand_val < 0.03:  # 3% - должники (оценка 2-3)
                        value = random.choice([2, 3])
                    elif rand_val < 0.10:  # 7% - удовлетворительно (4-5)
                        value = random.choice([4, 5])
                    elif rand_val < 0.35:  # 25% - хорошо (6-7)
                        value = random.choice([6, 7])
                    else:  # 65% - отлично (8-10)
                        value = random.choice([8, 9, 10])
                    
                    # Для зачетов особая логика
                    if control_type == 'zachet' or random.choice(grade_types) == 'zachet':
                        g_type = 'zachet'
                        # 90% зачтено, 10% не зачтено
                        value = 5 if random.random() < 0.90 else 2
                    else:
                        g_type = random.choice(['exam', 'lab', 'practice'])
                    
                    # Дата в пределах учебного года
                    month = random.choice([9, 10, 11, 12, 1, 2, 3, 4, 5])
                    day = random.randint(1, 28)
                    date_str = f"2024-{month:02d}-{day:02d}"
                    
                    semester = 1 if month <= 12 else 2
                    
                    self.cursor.execute('''
                        INSERT INTO grades (student_id, discipline_id, value, grade_type, date, semester, comment)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, disc_id, value, g_type, date_str, semester, None))
        
        self.conn.commit()
        print(f"Создано: {student_count} студентов, {grade_count} оценок")
    
    # ==================== АУТЕНТИФИКАЦИЯ ====================
    
    def register_user(self, login: str, password: str, full_name: str, 
                      role: str = 'student', email: str = None,
                      group_name: str = None, course: int = 1, 
                      semester: int = 1, specialty: str = None) -> Tuple[bool, str]:
        """Регистрация нового пользователя"""
        try:
            # Проверка существования логина
            self.cursor.execute("SELECT id FROM users WHERE login=?", (login,))
            if self.cursor.fetchone():
                return False, "Пользователь с таким логином уже существует"
            
            # Хэширование пароля
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Создание пользователя
            self.cursor.execute('''
                INSERT INTO users (login, password_hash, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (login, password_hash, role, full_name, email))
            
            user_id = self.cursor.lastrowid
            
            # Если студент - создаем запись в students
            if role == 'student' and group_name:
                enrollment_year = 2024 - course + 1
                self.cursor.execute('''
                    INSERT INTO students (user_id, group_name, course, semester, specialty, enrollment_year)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, group_name, course, semester, specialty or "", enrollment_year))
            
            self.conn.commit()
            self.log_action(user_id, "register", f"Регистрация пользователя {login}")
            
            return True, "Регистрация успешна"
            
        except Exception as e:
            return False, f"Ошибка регистрации: {str(e)}"
    
    def authenticate(self, login: str, password: str) -> Tuple[Optional[Dict], str]:
        """Аутентификация пользователя"""
        try:
            self.cursor.execute('''
                SELECT id, login, password_hash, role, full_name, email, created_at, last_login, is_active
                FROM users WHERE login=?
            ''', (login,))
            
            row = self.cursor.fetchone()
            if not row:
                return None, "Пользователь не найден"
            
            user = dict(row)
            
            if not user['is_active']:
                return None, "Аккаунт деактивирован"
            
            # Проверка пароля
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return None, "Неверный пароль"
            
            # Обновление last_login
            self.cursor.execute('''
                UPDATE users SET last_login=? WHERE id=?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user['id']))
            self.conn.commit()
            
            self.log_action(user['id'], "login", "Вход в систему")
            
            # Удаляем хэш из возвращаемых данных
            del user['password_hash']
            
            # Добавляем информацию о студенте если есть
            if user['role'] == 'student':
                self.cursor.execute('''
                    SELECT group_name, course, semester, specialty, enrollment_year
                    FROM students WHERE user_id=?
                ''', (user['id'],))
                student_row = self.cursor.fetchone()
                if student_row:
                    user['student_info'] = dict(student_row)
            
            return user, "Вход успешен"
            
        except Exception as e:
            return None, f"Ошибка аутентификации: {str(e)}"
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    def get_all_users(self, role_filter: str = None) -> List[Dict]:
        """Получение всех пользователей с фильтрацией"""
        try:
            query = '''
                SELECT u.id, u.login, u.role, u.full_name, u.email, 
                       u.created_at, u.last_login, u.is_active,
                       s.group_name, s.course, s.semester, s.specialty
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
            '''
            
            if role_filter:
                query += " WHERE u.role=?"
                self.cursor.execute(query, (role_filter,))
            else:
                # Сортировка: админы, преподаватели, студенты
                query += " ORDER BY CASE u.role WHEN 'admin' THEN 1 WHEN 'teacher' THEN 2 ELSE 3 END, u.full_name"
                self.cursor.execute(query)
            
            return [dict(row) for row in self.cursor.fetchall()]
            
        except Exception as e:
            print(f"Ошибка получения пользователей: {e}")
            return []
    
    def update_user_role(self, user_id: int, new_role: str, admin_id: int) -> Tuple[bool, str]:
        """Изменение роли пользователя"""
        try:
            if new_role not in ('admin', 'teacher', 'student'):
                return False, "Недопустимая роль"
            
            self.cursor.execute('''
                UPDATE users SET role=? WHERE id=?
            ''', (new_role, user_id))
            
            self.conn.commit()
            self.log_action(admin_id, "change_role", f"Смена роли пользователя {user_id} на {new_role}")
            
            return True, "Роль изменена"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def toggle_user_active(self, user_id: int, admin_id: int) -> Tuple[bool, str]:
        """Активация/деактивация пользователя"""
        try:
            self.cursor.execute("SELECT is_active FROM users WHERE id=?", (user_id,))
            row = self.cursor.fetchone()
            if not row:
                return False, "Пользователь не найден"
            
            new_status = 0 if row['is_active'] else 1
            self.cursor.execute('''
                UPDATE users SET is_active=? WHERE id=?
            ''', (new_status, user_id))
            
            self.conn.commit()
            self.log_action(admin_id, "toggle_active", f"Статус пользователя {user_id} изменен на {'активен' if new_status else 'неактивен'}")
            
            return True, "Статус изменен"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    # ==================== СТУДЕНТЫ ====================
    
    def get_all_students(self, group_filter: str = None, course_filter: int = None, 
                         search_query: str = None) -> List[Dict]:
        """Получение списка студентов с фильтрами"""
        try:
            query = '''
                SELECT u.id, u.login, u.full_name, u.email,
                       s.group_name, s.course, s.semester, s.specialty, s.enrollment_year
                FROM users u
                JOIN students s ON u.id = s.user_id
                WHERE u.role='student'
            '''
            params = []
            
            if group_filter and group_filter != "Все":
                query += " AND s.group_name=?"
                params.append(group_filter)
            
            if course_filter:
                query += " AND s.course=?"
                params.append(course_filter)
            
            if search_query:
                query += " AND (u.full_name LIKE ? OR u.login LIKE ?)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param])
            
            query += " ORDER BY s.group_name, u.full_name"
            
            self.cursor.execute(query, params)
            students = [dict(row) for row in self.cursor.fetchall()]
            
            # Добавляем средний балл
            for student in students:
                avg = self.get_student_average(student['id'])
                student['average_grade'] = round(avg, 2) if avg else 0.0
            
            return students
            
        except Exception as e:
            print(f"Ошибка получения студентов: {e}")
            return []
    
    def get_student_details(self, student_id: int) -> Dict:
        """Подробная информация о студенте"""
        try:
            # Основная информация
            self.cursor.execute('''
                SELECT u.id, u.login, u.full_name, u.email, u.created_at,
                       s.group_name, s.course, s.semester, s.specialty, s.enrollment_year
                FROM users u
                JOIN students s ON u.id = s.user_id
                WHERE u.id=?
            ''', (student_id,))
            
            row = self.cursor.fetchone()
            if not row:
                return {}
            
            student = dict(row)
            
            # Средний балл
            student['average_grade'] = round(self.get_student_average(student_id), 2)
            
            # Количество оценок
            self.cursor.execute("SELECT COUNT(*) as cnt FROM grades WHERE student_id=?", (student_id,))
            student['grades_count'] = self.cursor.fetchone()['cnt']
            
            # Статистика по оценкам
            self.cursor.execute('''
                SELECT 
                    SUM(CASE WHEN value >= 8 THEN 1 ELSE 0 END) as excellent,
                    SUM(CASE WHEN value BETWEEN 6 AND 7 THEN 1 ELSE 0 END) as good,
                    SUM(CASE WHEN value BETWEEN 4 AND 5 THEN 1 ELSE 0 END) as satisfactory,
                    SUM(CASE WHEN value <= 3 THEN 1 ELSE 0 END) as poor
                FROM grades WHERE student_id=?
            ''', (student_id,))
            stats = self.cursor.fetchone()
            student['excellent_count'] = stats['excellent'] or 0
            student['good_count'] = stats['good'] or 0
            student['satisfactory_count'] = stats['satisfactory'] or 0
            student['poor_count'] = stats['poor'] or 0
            
            # Долги (оценки ниже 4)
            student['has_debts'] = student['poor_count'] > 0
            
            # Список предметов с долгами
            self.cursor.execute('''
                SELECT d.name, MIN(g.value) as min_value, COUNT(g.id) as grades_count
                FROM grades g
                JOIN disciplines d ON g.discipline_id = d.id
                WHERE g.student_id=? AND g.value <= 3
                GROUP BY d.id
            ''', (student_id,))
            student['debt_subjects'] = [dict(row) for row in self.cursor.fetchall()]
            
            # Сданные предметы (средняя >= 4)
            self.cursor.execute('''
                SELECT d.name, AVG(g.value) as avg_value
                FROM grades g
                JOIN disciplines d ON g.discipline_id = d.id
                WHERE g.student_id=?
                GROUP BY d.id
                HAVING AVG(g.value) >= 4
            ''', (student_id,))
            student['passed_subjects'] = [dict(row) for row in self.cursor.fetchall()]
            
            # Комментарии
            self.cursor.execute('''
                SELECT sc.*, u.full_name as author_name
                FROM student_comments sc
                JOIN users u ON sc.author_id = u.id
                WHERE sc.student_id=?
                ORDER BY sc.created_at DESC
            ''', (student_id,))
            student['comments'] = [dict(row) for row in self.cursor.fetchall()]
            
            return student
            
        except Exception as e:
            print(f"Ошибка получения деталей студента: {e}")
            return {}
    
    def add_student_comment(self, student_id: int, author_id: int, 
                           comment_text: str, is_debt_related: bool = False) -> Tuple[bool, str]:
        """Добавление комментария к студенту"""
        try:
            self.cursor.execute('''
                INSERT INTO student_comments (student_id, author_id, comment_text, is_debt_related)
                VALUES (?, ?, ?, ?)
            ''', (student_id, author_id, comment_text, 1 if is_debt_related else 0))
            
            self.conn.commit()
            self.log_action(author_id, "add_comment", f"Комментарий к студенту {student_id}")
            
            return True, "Комментарий добавлен"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def delete_comment(self, comment_id: int, user_id: int) -> Tuple[bool, str]:
        """Удаление комментария"""
        try:
            self.cursor.execute("DELETE FROM student_comments WHERE id=?", (comment_id,))
            self.conn.commit()
            self.log_action(user_id, "delete_comment", f"Удаление комментария {comment_id}")
            return True, "Комментарий удален"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    # ==================== ОЦЕНКИ ====================
    
    def get_grades(self, group_filter: str = None, discipline_filter: int = None,
                   student_id: int = None) -> List[Dict]:
        """Получение оценок с фильтрами"""
        try:
            query = '''
                SELECT g.id, g.student_id, u.full_name as student_name, s.group_name,
                       g.discipline_id, d.name as discipline_name,
                       g.value, g.grade_type, g.date, g.semester, g.comment
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN disciplines d ON g.discipline_id = d.id
            '''
            params = []
            conditions = []
            
            if student_id:
                conditions.append("g.student_id=?")
                params.append(student_id)
            
            if group_filter and group_filter != "Все":
                conditions.append("s.group_name=?")
                params.append(group_filter)
            
            if discipline_filter:
                conditions.append("g.discipline_id=?")
                params.append(discipline_filter)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY s.group_name, u.full_name, g.date DESC"
            
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
            
        except Exception as e:
            print(f"Ошибка получения оценок: {e}")
            return []
    
    def update_grade(self, grade_id: int, new_value: int, new_type: str, 
                     comment: str, user_id: int) -> Tuple[bool, str]:
        """Обновление оценки"""
        try:
            if new_value < 2 or new_value > 10:
                return False, "Оценка должна быть от 2 до 10"
            
            if new_type not in ('exam', 'lab', 'practice', 'zachet', 'coursework'):
                return False, "Недопустимый тип оценки"
            
            # Получаем старую оценку для лога
            self.cursor.execute("SELECT value, grade_type FROM grades WHERE id=?", (grade_id,))
            old = self.cursor.fetchone()
            
            self.cursor.execute('''
                UPDATE grades SET value=?, grade_type=?, comment=?
                WHERE id=?
            ''', (new_value, new_type, comment, grade_id))
            
            self.conn.commit()
            
            log_details = f"Оценка {grade_id}: {old['value']}->{new_value}, тип: {old['grade_type']}->{new_type}"
            self.log_action(user_id, "update_grade", log_details)
            
            return True, "Оценка обновлена"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def add_grade(self, student_id: int, discipline_id: int, value: int,
                  grade_type: str, date_str: str, semester: int,
                  user_id: int) -> Tuple[bool, str]:
        """Добавление новой оценки"""
        try:
            if value < 2 or value > 10:
                return False, "Оценка должна быть от 2 до 10"
            
            self.cursor.execute('''
                INSERT INTO grades (student_id, discipline_id, value, grade_type, date, semester)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, discipline_id, value, grade_type, date_str, semester))
            
            self.conn.commit()
            self.log_action(user_id, "add_grade", f"Добавлена оценка студенту {student_id}")
            
            return True, "Оценка добавлена"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def get_student_average(self, student_id: int) -> Optional[float]:
        """Средний балл студента"""
        try:
            self.cursor.execute('''
                SELECT AVG(value) as avg FROM grades WHERE student_id=?
            ''', (student_id,))
            row = self.cursor.fetchone()
            return row['avg'] if row and row['avg'] else None
        except:
            return None
    
    # ==================== АНАЛИТИКА ====================
    
    def get_dashboard_stats(self) -> Dict:
        """Статистика для дашборда"""
        try:
            stats = {}
            
            # Всего студентов
            self.cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role='student'")
            stats['total_students'] = self.cursor.fetchone()['cnt']
            
            # Средний балл по факультету
            self.cursor.execute("SELECT AVG(value) as avg FROM grades")
            stats['faculty_average'] = round(self.cursor.fetchone()['avg'] or 0, 2)
            
            # Успеваемость (% студентов со средней > 3)
            self.cursor.execute('''
                SELECT COUNT(DISTINCT student_id) as total,
                       COUNT(DISTINCT CASE WHEN avg_grade > 3 THEN student_id END) as passed
                FROM (
                    SELECT student_id, AVG(value) as avg_grade
                    FROM grades
                    GROUP BY student_id
                )
            ''')
            row = self.cursor.fetchone()
            total = row['total'] or 1
            stats['success_rate'] = round((row['passed'] / total) * 100, 1)
            
            # Качество (% оценок 8-10)
            self.cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN value >= 8 THEN 1 ELSE 0 END) as excellent
                FROM grades
            ''')
            row = self.cursor.fetchone()
            total = row['total'] or 1
            stats['quality_rate'] = round((row['excellent'] / total) * 100, 1)
            
            # Группа риска (студенты со средней < 4)
            self.cursor.execute('''
                SELECT u.id, u.full_name, s.group_name, AVG(g.value) as avg_grade
                FROM users u
                JOIN students s ON u.id = s.user_id
                JOIN grades g ON u.id = g.student_id
                WHERE u.role='student'
                GROUP BY u.id
                HAVING AVG(g.value) < 4
                ORDER BY avg_grade ASC
            ''')
            stats['at_risk_students'] = [dict(row) for row in self.cursor.fetchall()]
            stats['at_risk_count'] = len(stats['at_risk_students'])
            
            # Должники (имеющие оценки <= 3)
            self.cursor.execute('''
                SELECT DISTINCT u.id, u.full_name, s.group_name,
                       COUNT(g.id) as debt_count
                FROM users u
                JOIN students s ON u.id = s.user_id
                JOIN grades g ON u.id = g.student_id
                WHERE u.role='student' AND g.value <= 3
                GROUP BY u.id
                ORDER BY debt_count DESC
            ''')
            stats['debtors'] = [dict(row) for row in self.cursor.fetchall()]
            stats['debtors_count'] = len(stats['debtors'])
            
            return stats
            
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {}
    
    def get_group_averages(self) -> List[Dict]:
        """Средний балл по группам"""
        try:
            self.cursor.execute('''
                SELECT s.group_name, AVG(g.value) as avg_grade, COUNT(g.id) as grades_count
                FROM students s
                JOIN grades g ON s.id = g.student_id
                GROUP BY s.group_name
                ORDER BY s.group_name
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_course_averages(self) -> List[Dict]:
        """Средний балл по курсам"""
        try:
            self.cursor.execute('''
                SELECT s.course, AVG(g.value) as avg_grade, COUNT(g.id) as grades_count
                FROM students s
                JOIN grades g ON s.id = g.student_id
                GROUP BY s.course
                ORDER BY s.course
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_semester_comparison(self) -> List[Dict]:
        """Сравнение семестров"""
        try:
            self.cursor.execute('''
                SELECT g.semester, AVG(g.value) as avg_grade, COUNT(g.id) as grades_count
                FROM grades g
                GROUP BY g.semester
                ORDER BY g.semester
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_grade_distribution(self) -> List[Dict]:
        """Распределение оценок"""
        try:
            self.cursor.execute('''
                SELECT 
                    SUM(CASE WHEN value = 10 THEN 1 ELSE 0 END) as "10",
                    SUM(CASE WHEN value = 9 THEN 1 ELSE 0 END) as "9",
                    SUM(CASE WHEN value = 8 THEN 1 ELSE 0 END) as "8",
                    SUM(CASE WHEN value = 7 THEN 1 ELSE 0 END) as "7",
                    SUM(CASE WHEN value = 6 THEN 1 ELSE 0 END) as "6",
                    SUM(CASE WHEN value = 5 THEN 1 ELSE 0 END) as "5",
                    SUM(CASE WHEN value = 4 THEN 1 ELSE 0 END) as "4",
                    SUM(CASE WHEN value = 3 THEN 1 ELSE 0 END) as "3",
                    SUM(CASE WHEN value = 2 THEN 1 ELSE 0 END) as "2"
                FROM grades
            ''')
            row = self.cursor.fetchone()
            return [dict(row)] if row else []
        except:
            return []
    
    def get_specialty_stats(self) -> List[Dict]:
        """Статистика по специальностям"""
        try:
            self.cursor.execute('''
                SELECT s.specialty, AVG(g.value) as avg_grade, COUNT(DISTINCT s.id) as students_count
                FROM students s
                JOIN grades g ON s.id = g.student_id
                GROUP BY s.specialty
                ORDER BY avg_grade DESC
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    # ==================== ДИСЦИПЛИНЫ ====================
    
    def get_all_disciplines(self) -> List[Dict]:
        """Получение всех дисциплин"""
        try:
            self.cursor.execute("SELECT * FROM disciplines ORDER BY name")
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    def add_discipline(self, name: str, department: str, hours: int, 
                       control_type: str, user_id: int) -> Tuple[bool, str]:
        """Добавление дисциплины"""
        try:
            self.cursor.execute('''
                INSERT INTO disciplines (name, department, hours, control_type)
                VALUES (?, ?, ?, ?)
            ''', (name, department, hours, control_type))
            self.conn.commit()
            self.log_action(user_id, "add_discipline", f"Добавлена дисциплина {name}")
            return True, "Дисциплина добавлена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    # ==================== ЛОГИ ====================
    
    def log_action(self, user_id: int, action: str, details: str = None, ip_address: str = None):
        """Запись действия в лог"""
        try:
            self.cursor.execute('''
                INSERT INTO logs (user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, details, ip_address))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка записи лога: {e}")
    
    def get_logs(self, limit: int = 100, user_filter: int = None) -> List[Dict]:
        """Получение логов"""
        try:
            query = '''
                SELECT l.id, l.action, l.details, l.timestamp, l.ip_address,
                       u.full_name as user_name, u.role
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
            '''
            
            if user_filter:
                query += " WHERE l.user_id=?"
                self.cursor.execute(query, (user_filter,))
            else:
                query += " ORDER BY l.timestamp DESC LIMIT ?"
                self.cursor.execute(query, (limit,))
            
            return [dict(row) for row in self.cursor.fetchall()]
        except:
            return []
    
    # ==================== ГРУППЫ ====================
    
    def get_all_groups(self) -> List[str]:
        """Получение всех групп"""
        try:
            self.cursor.execute("SELECT DISTINCT group_name FROM students ORDER BY group_name")
            return [row['group_name'] for row in self.cursor.fetchall()]
        except:
            return []
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()


# Глобальный экземпляр БД
db = None

def get_db() -> Database:
    """Получение экземпляра БД"""
    global db
    if db is None:
        db = Database()
    return db


if __name__ == "__main__":
    # Тестирование
    database = Database()
    print("БД инициализирована")
    stats = database.get_dashboard_stats()
    print(f"Статистика: {stats}")
