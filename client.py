"""
client.py - Клиентская часть системы оценки успеваемости (ИАС ПолесГУ)
Графический интерфейс на customtkinter со всеми вкладками
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Dict, Any, List
import server


# Настройка стиля
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LoginWindow(ctk.CTk):
    """Окно авторизации"""
    
    def __init__(self, on_login_success):
        super().__init__()
        
        self.on_login_success = on_login_success
        
        self.title("ИАС ПолесГУ - Авторизация")
        self.geometry("450x350")
        self.resizable(False, False)
        
        # Центрирование окна
        self.center_window()
        
        self.create_widgets()
    
    def center_window(self):
        """Центрировать окно на экране"""
        self.update_idletasks()
        width = 450
        height = 350
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Создание виджетов авторизации"""
        # Заголовок
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(40, 30))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="ИАС ПолесГУ",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Система оценки успеваемости",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack()
        
        # Форма входа
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, fill="x")
        
        # Логин
        login_label = ctk.CTkLabel(form_frame, text="Логин:", font=ctk.CTkFont(size=14))
        login_label.pack(anchor="w", pady=(0, 5))
        
        self.login_entry = ctk.CTkEntry(
            form_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="Введите логин"
        )
        self.login_entry.pack(fill="x", pady=(0, 20))
        self.login_entry.bind("<Return>", lambda e: self.attempt_login())
        
        # Пароль
        password_label = ctk.CTkLabel(form_frame, text="Пароль:", font=ctk.CTkFont(size=14))
        password_label.pack(anchor="w", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="Введите пароль",
            show="*"
        )
        self.password_entry.pack(fill="x", pady=(0, 20))
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())
        
        # Кнопка входа
        login_button = ctk.CTkButton(
            form_frame,
            text="Войти в систему",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.attempt_login
        )
        login_button.pack(fill="x")
    
    def attempt_login(self):
        """Попытка входа"""
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        user = server.db.authenticate(login, password)
        
        if user:
            self.destroy()
            self.on_login_success(user)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            self.password_entry.delete(0, "end")


class MainWindow(ctk.CTk):
    """Основное окно приложения"""
    
    def __init__(self, user: Dict[str, Any]):
        super().__init__()
        
        self.user = user
        self.current_theme = "dark"
        
        self.title(f"ИАС ПолесГУ - {user['full_name']} ({user['role']})")
        self.geometry("1400x900")
        
        self.create_layout()
        self.load_tab_data()
    
    def create_layout(self):
        """Создание макета окна"""
        # Верхняя панель
        self.top_frame = ctk.CTkFrame(self, height=60, fg_color="#2b2b2b")
        self.top_frame.pack(fill="x", side="top")
        self.top_frame.pack_propagate(False)
        
        # Логотип/заголовок
        logo_label = ctk.CTkLabel(
            self.top_frame,
            text="🎓 ИАС ПолесГУ",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.pack(side="left", padx=20, pady=10)
        
        # Информация о пользователе
        user_info = f"{self.user['full_name']} | Роль: {self.translate_role(self.user['role'])}"
        user_label = ctk.CTkLabel(
            self.top_frame,
            text=user_info,
            font=ctk.CTkFont(size=14)
        )
        user_label.pack(side="right", padx=20, pady=10)
        
        # Основной контейнер с вкладками
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Создание вкладок в зависимости от роли
        self.create_tabs()
    
    def translate_role(self, role: str) -> str:
        """Перевод роли на русский"""
        roles = {"admin": "Администратор", "teacher": "Преподаватель", "student": "Студент"}
        return roles.get(role, role)
    
    def create_tabs(self):
        """Создание вкладок"""
        # Общие вкладки
        self.tab_dashboard = self.tabview.add("📊 Главная")
        self.tab_students = self.tabview.add("🎓 Студенты")
        self.tab_grades = self.tabview.add("📝 Журнал")
        self.tab_analytics = self.tabview.add("📈 Аналитика")
        self.tab_settings = self.tabview.add("⚙️ Настройки")
        
        # Вкладка пользователей только для админа
        if self.user["role"] == "admin":
            self.tab_users = self.tabview.add("👥 Пользователи")
            self.setup_users_tab()
        
        # Вкладка логов только для админа
        if self.user["role"] == "admin":
            self.tab_logs = self.tabview.add("📋 Логи")
            self.setup_logs_tab()
        
        # Настройка вкладок
        self.setup_dashboard_tab()
        self.setup_students_tab()
        self.setup_grades_tab()
        self.setup_analytics_tab()
        self.setup_settings_tab()
    
    def load_tab_data(self):
        """Загрузка данных во вкладки"""
        self.refresh_dashboard()
        self.refresh_students()
        self.refresh_grades()
        self.refresh_analytics()
        if self.user["role"] == "admin":
            self.refresh_users()
            self.refresh_logs()
    
    # ==================== DASHBOARD ====================
    
    def setup_dashboard_tab(self):
        """Настройка вкладки Dashboard"""
        # KPI карточки
        kpi_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=20, pady=20)
        
        self.kpi_labels = {}
        kpi_configs = [
            ("total_students", "Всего студентов", "#3498db"),
            ("avg_grade", "Средний балл", "#2ecc71"),
            ("success_rate", "Успеваемость %", "#f39c12"),
            ("quality_rate", "Качество %", "#9b59b6")
        ]
        
        for i, (key, title, color) in enumerate(kpi_configs):
            card = ctk.CTkFrame(kpi_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            value_label = ctk.CTkLabel(
                card,
                text="-",
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color="white"
            )
            value_label.pack(pady=(20, 5))
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            title_label.pack(pady=(0, 20))
            
            kpi_frame.grid_columnconfigure(i, weight=1)
            self.kpi_labels[key] = value_label
        
        # Блок группы риска
        risk_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="#2b2b2b")
        risk_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        risk_title = ctk.CTkLabel(
            risk_frame,
            text="⚠️ Группа риска (студенты с оценками ≤ 4)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        risk_title.pack(pady=10)
        
        # Таблица группы риска
        columns = ("full_name", "group_name", "min_grade")
        self.risk_tree = ttk.Treeview(risk_frame, columns=columns, show="headings", height=10)
        
        self.risk_tree.heading("full_name", text="ФИО")
        self.risk_tree.heading("group_name", text="Группа")
        self.risk_tree.heading("min_grade", text="Мин. оценка")
        
        self.risk_tree.column("full_name", width=300)
        self.risk_tree.column("group_name", width=100)
        self.risk_tree.column("min_grade", width=100)
        
        scrollbar = ttk.Scrollbar(risk_frame, orient="vertical", command=self.risk_tree.yview)
        self.risk_tree.configure(yscrollcommand=scrollbar.set)
        
        self.risk_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
    
    def refresh_dashboard(self):
        """Обновление данных Dashboard"""
        try:
            stats = server.db.get_dashboard_stats()
            
            self.kpi_labels["total_students"].configure(text=str(stats["total_students"]))
            self.kpi_labels["avg_grade"].configure(text=f"{stats['avg_grade']:.2f}")
            self.kpi_labels["success_rate"].configure(text=f"{stats['success_rate']:.1f}%")
            self.kpi_labels["quality_rate"].configure(text=f"{stats['quality_rate']:.1f}%")
            
            # Обновление таблицы группы риска
            for item in self.risk_tree.get_children():
                self.risk_tree.delete(item)
            
            risk_students = server.db.get_at_risk_students()
            for student in risk_students:
                grade_text = "Зачтено" if student["min_grade"] == 5 else str(student["min_grade"])
                self.risk_tree.insert("", "end", values=(
                    student["full_name"],
                    student["group_name"],
                    grade_text
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки Dashboard: {e}")
    
    # ==================== СТУДЕНТЫ ====================
    
    def setup_students_tab(self):
        """Настройка вкладки Студенты"""
        # Панель фильтров
        filter_frame = ctk.CTkFrame(self.tab_students, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Поиск по имени
        search_label = ctk.CTkLabel(filter_frame, text="🔍 Поиск:")
        search_label.pack(side="left", padx=(0, 5))
        
        self.student_search_entry = ctk.CTkEntry(
            filter_frame,
            width=250,
            placeholder_text="Введите ФИО..."
        )
        self.student_search_entry.pack(side="left", padx=(0, 10))
        self.student_search_entry.bind("<KeyRelease>", lambda e: self.refresh_students())
        
        # Фильтр по группе
        group_label = ctk.CTkLabel(filter_frame, text="Группа:")
        group_label.pack(side="left", padx=(20, 5))
        
        self.student_group_combo = ctk.CTkComboBox(
            filter_frame,
            width=150,
            values=["Все"],
            command=lambda _: self.refresh_students()
        )
        self.student_group_combo.pack(side="left", padx=(0, 10))
        self.student_group_combo.set("Все")
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄 Обновить",
            width=100,
            command=self.refresh_students
        )
        refresh_btn.pack(side="left")
        
        # Таблица студентов
        table_frame = ctk.CTkFrame(self.tab_students, fg_color="#2b2b2b")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("full_name", "group_name", "course", "specialty", "avg_grade")
        self.students_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.students_tree.heading("full_name", text="ФИО")
        self.students_tree.heading("group_name", text="Группа")
        self.students_tree.heading("course", text="Курс")
        self.students_tree.heading("specialty", text="Специальность")
        self.students_tree.heading("avg_grade", text="Средний балл")
        
        self.students_tree.column("full_name", width=250)
        self.students_tree.column("group_name", width=80)
        self.students_tree.column("course", width=60)
        self.students_tree.column("specialty", width=200)
        self.students_tree.column("avg_grade", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)
        
        self.students_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Двойной клик для просмотра оценок
        self.students_tree.bind("<Double-1>", self.show_student_grades)
    
    def refresh_students(self):
        """Обновление списка студентов"""
        try:
            # Обновление фильтра групп
            groups = server.db.get_groups()
            current = self.student_group_combo.get()
            self.student_group_combo.configure(values=["Все"] + groups)
            if current not in ["Все"] + groups:
                self.student_group_combo.set("Все")
            
            # Получение данных
            group_filter = self.student_group_combo.get()
            search_query = self.student_search_entry.get().strip()
            
            students = server.db.get_all_students(group_filter, search_query)
            
            # Очистка таблицы
            for item in self.students_tree.get_children():
                self.students_tree.delete(item)
            
            # Заполнение таблицы
            for student in students:
                avg = f"{student['avg_grade']:.2f}" if student['avg_grade'] > 0 else "-"
                self.students_tree.insert("", "end", values=(
                    student["full_name"],
                    student["group_name"],
                    student["course"],
                    student["specialty"],
                    avg
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки студентов: {e}")
    
    def show_student_grades(self, event=None):
        """Показать оценки студента в модальном окне"""
        selection = self.students_tree.selection()
        if not selection:
            return
        
        item = self.students_tree.item(selection[0])
        full_name = item["values"][0]
        
        # Найти ID студента
        students = server.db.get_all_students()
        student = next((s for s in students if s["full_name"] == full_name), None)
        
        if not student:
            return
        
        # Модальное окно
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Оценки: {full_name}")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Таблица оценок
        columns = ("discipline", "value", "grade_type", "date")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")
        
        tree.heading("discipline", text="Дисциплина")
        tree.heading("value", text="Оценка")
        tree.heading("grade_type", text="Тип")
        tree.heading("date", text="Дата")
        
        tree.column("discipline", width=250)
        tree.column("value", width=80)
        tree.column("grade_type", width=100)
        tree.column("date", width=100)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        grades = server.db.get_student_grades(student["id"])
        for grade in grades:
            type_text = {"exam": "Экзамен", "lab": "Лаба", "practice": "Практика", "zachet": "Зачет"}.get(grade["grade_type"], grade["grade_type"])
            value_text = "Зачтено" if grade["grade_type"] == "zachet" and grade["value"] == 5 else \
                        "Не зачтено" if grade["grade_type"] == "zachet" and grade["value"] == 2 else str(grade["value"])
            tree.insert("", "end", values=(grade["discipline"], value_text, type_text, grade["date"]))
    
    # ==================== ЖУРНАЛ ====================
    
    def setup_grades_tab(self):
        """Настройка вкладки Журнал"""
        # Панель фильтров
        filter_frame = ctk.CTkFrame(self.tab_grades, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Выбор группы
        group_label = ctk.CTkLabel(filter_frame, text="Группа:")
        group_label.pack(side="left", padx=(0, 5))
        
        self.grade_group_combo = ctk.CTkComboBox(
            filter_frame,
            width=150,
            values=[],
            command=lambda _: self.refresh_grades()
        )
        self.grade_group_combo.pack(side="left", padx=(0, 15))
        
        # Выбор предмета
        disc_label = ctk.CTkLabel(filter_frame, text="Предмет:")
        disc_label.pack(side="left", padx=(0, 5))
        
        self.grade_disc_combo = ctk.CTkComboBox(
            filter_frame,
            width=250,
            values=["Все предметы"],
            command=lambda _: self.refresh_grades()
        )
        self.grade_disc_combo.pack(side="left", padx=(0, 15))
        
        # Поиск
        search_label = ctk.CTkLabel(filter_frame, text="🔍 Поиск:")
        search_label.pack(side="left", padx=(20, 5))
        
        self.grade_search_entry = ctk.CTkEntry(
            filter_frame,
            width=200,
            placeholder_text="ФИО студента..."
        )
        self.grade_search_entry.pack(side="left", padx=(0, 10))
        self.grade_search_entry.bind("<KeyRelease>", lambda e: self.refresh_grades())
        
        # Кнопка добавления оценки (для преподавателя и админа)
        if self.user["role"] in ["admin", "teacher"]:
            add_btn = ctk.CTkButton(
                filter_frame,
                text="+ Добавить оценку",
                command=self.add_grade_dialog
            )
            add_btn.pack(side="left", padx=(10, 0))
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄 Обновить",
            command=self.refresh_grades
        )
        refresh_btn.pack(side="right")
        
        # Таблица оценок
        table_frame = ctk.CTkFrame(self.tab_grades, fg_color="#2b2b2b")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("full_name", "discipline", "value", "grade_type", "date")
        self.grades_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.grades_tree.heading("full_name", text="ФИО")
        self.grades_tree.heading("discipline", text="Дисциплина")
        self.grades_tree.heading("value", text="Оценка")
        self.grades_tree.heading("grade_type", text="Тип работы")
        self.grades_tree.heading("date", text="Дата")
        
        self.grades_tree.column("full_name", width=200)
        self.grades_tree.column("discipline", width=200)
        self.grades_tree.column("value", width=80)
        self.grades_tree.column("grade_type", width=120)
        self.grades_tree.column("date", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.grades_tree.yview)
        self.grades_tree.configure(yscrollcommand=scrollbar.set)
        
        self.grades_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Контекстное меню для редактирования
        self.grade_context_menu = tk.Menu(self, tearoff=0)
        self.grade_context_menu.add_command(label="✏️ Редактировать", command=self.edit_selected_grade)
        self.grade_context_menu.add_command(label="🗑️ Удалить", command=self.delete_selected_grade)
        
        self.grades_tree.bind("<Button-3>", self.show_grade_context_menu)
        self.grades_tree.bind("<Double-1>", lambda e: self.edit_selected_grade())
    
    def refresh_grades(self):
        """Обновление журнала оценок"""
        try:
            # Обновление списков
            groups = server.db.get_groups()
            disciplines = server.db.get_all_disciplines()
            
            current_group = self.grade_group_combo.get()
            current_disc = self.grade_disc_combo.get()
            
            self.grade_group_combo.configure(values=groups if groups else [])
            disc_values = ["Все предметы"] + [d["name"] for d in disciplines]
            self.grade_disc_combo.configure(values=disc_values)
            
            if not current_group and groups:
                self.grade_group_combo.set(groups[0])
            if current_disc not in disc_values:
                self.grade_disc_combo.set("Все предметы")
            
            # Получение данных
            group_name = self.grade_group_combo.get()
            search_query = self.grade_search_entry.get().strip()
            
            disc_id = None
            if self.grade_disc_combo.get() != "Все предметы":
                disc = next((d for d in disciplines if d["name"] == self.grade_disc_combo.get()), None)
                if disc:
                    disc_id = disc["id"]
            
            if not group_name:
                return
            
            grades = server.db.get_grades_for_group(group_name, disc_id, search_query)
            
            # Очистка таблицы
            for item in self.grades_tree.get_children():
                self.grades_tree.delete(item)
            
            # Заполнение
            for grade in grades:
                type_text = {"exam": "Экзамен", "lab": "Лаба", "practice": "Практика", "zachet": "Зачет"}.get(grade["grade_type"], grade["grade_type"])
                if grade["grade_type"] == "zachet":
                    value_text = "Зачтено" if grade["value"] == 5 else "Не зачтено"
                else:
                    value_text = str(grade["value"])
                
                self.grades_tree.insert("", "end", values=(
                    grade["full_name"],
                    grade["discipline"],
                    value_text,
                    type_text,
                    grade["date"]
                ), tags=(grade["id"],))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки журнала: {e}")
    
    def show_grade_context_menu(self, event):
        """Показать контекстное меню"""
        if self.user["role"] not in ["admin", "teacher"]:
            return
        
        self.grades_tree.selection_set(self.grades_tree.identify_row(event.y))
        if self.grades_tree.selection():
            self.grade_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_grade_id(self) -> Optional[int]:
        """Получить ID выбранной оценки"""
        selection = self.grades_tree.selection()
        if not selection:
            return None
        tags = self.grades_tree.item(selection[0])["tags"]
        return int(tags[0]) if tags else None
    
    def edit_selected_grade(self):
        """Редактирование выбранной оценки"""
        grade_id = self.get_selected_grade_id()
        if not grade_id:
            messagebox.showwarning("Предупреждение", "Выберите оценку для редактирования")
            return
        
        # Получить текущие данные из таблицы
        selection = self.grades_tree.selection()
        item = self.grades_tree.item(selection[0])
        current_value = item["values"][2]
        current_type = item["values"][3]
        
        # Преобразование значения
        if current_type == "Зачет":
            current_value_num = 5 if current_value == "Зачтено" else 2
        else:
            current_value_num = int(current_value)
        
        current_type_code = {"Экзамен": "exam", "Лаба": "lab", "Практика": "practice", "Зачет": "zachet"}.get(current_type, "exam")
        
        # Диалог редактирования
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактирование оценки")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Оценка
        ctk.CTkLabel(frame, text="Оценка:").pack(anchor="w", pady=(0, 5))
        value_entry = ctk.CTkEntry(frame, height=40)
        value_entry.pack(fill="x", pady=(0, 15))
        value_entry.insert(0, str(current_value_num))
        
        hint_label = ctk.CTkLabel(
            frame,
            text="Для зачета: 5 = Зачтено, 2 = Не зачтено",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        hint_label.pack(anchor="w", pady=(0, 15))
        
        # Тип работы
        ctk.CTkLabel(frame, text="Тип работы:").pack(anchor="w", pady=(0, 5))
        type_combo = ctk.CTkComboBox(frame, values=["exam", "lab", "practice", "zachet"])
        type_combo.pack(fill="x", pady=(0, 20))
        type_combo.set(current_type_code)
        
        def save():
            try:
                new_value = int(value_entry.get())
                if new_value < 2 or new_value > 10:
                    raise ValueError("Оценка должна быть от 2 до 10")
                
                new_type = type_combo.get()
                
                if server.db.update_grade(grade_id, new_value, new_type, self.user["id"]):
                    messagebox.showinfo("Успех", "Оценка обновлена")
                    dialog.destroy()
                    self.refresh_grades()
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить оценку")
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверное значение: {e}")
        
        ctk.CTkButton(frame, text="Сохранить", command=save).pack(fill="x")
    
    def delete_selected_grade(self):
        """Удаление выбранной оценки"""
        grade_id = self.get_selected_grade_id()
        if not grade_id:
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить эту оценку?"):
            if server.db.delete_grade(grade_id, self.user["id"]):
                messagebox.showinfo("Успех", "Оценка удалена")
                self.refresh_grades()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить оценку")
    
    def add_grade_dialog(self):
        """Диалог добавления оценки"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить оценку")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Выбор студента
        ctk.CTkLabel(frame, text="Студент:").pack(anchor="w", pady=(0, 5))
        
        group = self.grade_group_combo.get()
        students = server.db.get_all_students(group)
        student_values = [f"{s['full_name']} ({s['group_name']})" for s in students]
        
        student_combo = ctk.CTkComboBox(frame, values=student_values)
        student_combo.pack(fill="x", pady=(0, 15))
        if student_values:
            student_combo.set(student_values[0])
        
        # Выбор предмета
        ctk.CTkLabel(frame, text="Предмет:").pack(anchor="w", pady=(0, 5))
        disciplines = server.db.get_all_disciplines()
        disc_values = [d["name"] for d in disciplines]
        
        disc_combo = ctk.CTkComboBox(frame, values=disc_values)
        disc_combo.pack(fill="x", pady=(0, 15))
        if disc_values:
            disc_combo.set(disc_values[0])
        
        # Оценка
        ctk.CTkLabel(frame, text="Оценка:").pack(anchor="w", pady=(0, 5))
        value_entry = ctk.CTkEntry(frame, height=40)
        value_entry.pack(fill="x", pady=(0, 5))
        value_entry.insert(0, "5")
        
        ctk.CTkLabel(
            frame,
            text="Для зачета: 5 = Зачтено, 2 = Не зачтено",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 15))
        
        # Тип работы
        ctk.CTkLabel(frame, text="Тип работы:").pack(anchor="w", pady=(0, 5))
        type_combo = ctk.CTkComboBox(frame, values=["exam", "lab", "practice", "zachet"])
        type_combo.pack(fill="x", pady=(0, 15))
        type_combo.set("lab")
        
        # Дата
        ctk.CTkLabel(frame, text="Дата (ГГГГ-ММ-ДД):").pack(anchor="w", pady=(0, 5))
        from datetime import datetime
        date_entry = ctk.CTkEntry(frame, height=40)
        date_entry.pack(fill="x", pady=(0, 20))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        def save():
            try:
                student_str = student_combo.get()
                student = next((s for s in students if f"{s['full_name']} ({s['group_name']})" == student_str), None)
                if not student:
                    raise ValueError("Студент не найден")
                
                disc_name = disc_combo.get()
                discipline = next((d for d in disciplines if d["name"] == disc_name), None)
                if not discipline:
                    raise ValueError("Предмет не найден")
                
                value = int(value_entry.get())
                if value < 2 or value > 10:
                    raise ValueError("Оценка должна быть от 2 до 10")
                
                grade_type = type_combo.get()
                date = date_entry.get()
                
                server.db.add_grade(student["id"], discipline["id"], value, grade_type, date, self.user["id"])
                messagebox.showinfo("Успех", "Оценка добавлена")
                dialog.destroy()
                self.refresh_grades()
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверные данные: {e}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ctk.CTkButton(frame, text="Добавить", command=save).pack(fill="x")
    
    # ==================== АНАЛИТИКА ====================
    
    def setup_analytics_tab(self):
        """Настройка вкладки Аналитика"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.tab_analytics,
            text="📊 Средний балл по группам",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Контейнер для графика
        self.chart_frame = ctk.CTkFrame(self.tab_analytics, fg_color="#2b2b2b")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            self.tab_analytics,
            text="🔄 Обновить график",
            command=self.refresh_analytics
        )
        refresh_btn.pack(pady=10)
    
    def refresh_analytics(self):
        """Обновление аналитического графика"""
        try:
            # Очистка предыдущего графика
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            
            data = server.db.get_avg_by_group()
            
            if not data:
                ctk.CTkLabel(
                    self.chart_frame,
                    text="Нет данных для отображения",
                    font=ctk.CTkFont(size=16)
                ).pack(pady=50)
                return
            
            groups = [item["group_name"] for item in data]
            averages = [item["avg_grade"] for item in data]
            
            # Создание графика
            fig = Figure(figsize=(10, 6), facecolor="#2b2b2b")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#2b2b2b")
            
            # Цвета столбцов
            colors = ["#3498db" if avg >= 7 else "#f39c12" if avg >= 5 else "#e74c3c" for avg in averages]
            
            bars = ax.bar(range(len(groups)), averages, color=colors)
            
            # Настройка осей
            ax.set_xticks(range(len(groups)))
            ax.set_xticklabels(groups, rotation=45, ha="right", color="white")
            ax.set_yticks(range(0, 11, 2))
            ax.set_ylabel("Средний балл", color="white", fontsize=12)
            ax.set_xlabel("Группа", color="white", fontsize=12)
            ax.set_title("Сравнение успеваемости по группам", color="white", fontsize=14, pad=20)
            ax.set_ylim(0, 10)
            
            # Подписи значений
            for i, v in enumerate(averages):
                ax.text(i, v + 0.2, f"{v:.2f}", ha="center", va="bottom", color="white", fontsize=9)
            
            # Сетка
            ax.grid(axis="y", alpha=0.3, color="gray")
            
            # Вставка в GUI
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка построения графика: {e}")
    
    # ==================== ПОЛЬЗОВАТЕЛИ (Admin) ====================
    
    def setup_users_tab(self):
        """Настройка вкладки Пользователи"""
        # Панель управления
        control_frame = ctk.CTkFrame(self.tab_users, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Фильтр по роли
        role_label = ctk.CTkLabel(control_frame, text="Фильтр по роли:")
        role_label.pack(side="left", padx=(0, 5))
        
        self.user_role_combo = ctk.CTkComboBox(
            control_frame,
            width=150,
            values=["Все", "admin", "teacher", "student"],
            command=lambda _: self.refresh_users()
        )
        self.user_role_combo.pack(side="left", padx=(0, 15))
        self.user_role_combo.set("Все")
        
        # Поиск
        search_label = ctk.CTkLabel(control_frame, text="🔍 Поиск:")
        search_label.pack(side="left", padx=(20, 5))
        
        self.user_search_entry = ctk.CTkEntry(
            control_frame,
            width=200,
            placeholder_text="ФИО или логин..."
        )
        self.user_search_entry.pack(side="left", padx=(0, 10))
        self.user_search_entry.bind("<KeyRelease>", lambda e: self.refresh_users())
        
        # Кнопка добавления пользователя
        add_btn = ctk.CTkButton(
            control_frame,
            text="+ Добавить пользователя",
            command=self.add_user_dialog
        )
        add_btn.pack(side="left", padx=(10, 0))
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Обновить",
            command=self.refresh_users
        )
        refresh_btn.pack(side="right")
        
        # Таблица пользователей
        table_frame = ctk.CTkFrame(self.tab_users, fg_color="#2b2b2b")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("login", "full_name", "role", "group_name")
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.users_tree.heading("login", text="Логин")
        self.users_tree.heading("full_name", text="ФИО")
        self.users_tree.heading("role", text="Роль")
        self.users_tree.heading("group_name", text="Группа")
        
        self.users_tree.column("login", width=150)
        self.users_tree.column("full_name", width=250)
        self.users_tree.column("role", width=100)
        self.users_tree.column("group_name", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Контекстное меню
        self.user_context_menu = tk.Menu(self, tearoff=0)
        self.user_context_menu.add_command(label="📈 Назначить преподавателем", command=self.promote_to_teacher)
        self.user_context_menu.add_command(label="🗑️ Удалить", command=self.delete_user)
        
        self.users_tree.bind("<Button-3>", self.show_user_context_menu)
    
    def refresh_users(self):
        """Обновление списка пользователей"""
        try:
            role_filter = self.user_role_combo.get()
            search_query = self.user_search_entry.get().strip()
            
            if role_filter == "Все":
                role_filter = None
            
            users = server.db.get_all_users(role_filter)
            
            # Фильтрация по поиску
            if search_query:
                users = [u for u in users if search_query.lower() in u["full_name"].lower() or search_query.lower() in u["login"].lower()]
            
            # Очистка таблицы
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Заполнение
            role_names = {"admin": "Админ", "teacher": "Преподаватель", "student": "Студент"}
            for user in users:
                self.users_tree.insert("", "end", values=(
                    user["login"],
                    user["full_name"],
                    role_names.get(user["role"], user["role"]),
                    user.get("group_name", "-") or "-"
                ), tags=(user["id"], user["role"]))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки пользователей: {e}")
    
    def show_user_context_menu(self, event):
        """Показать контекстное меню пользователя"""
        self.users_tree.selection_set(self.users_tree.identify_row(event.y))
        if self.users_tree.selection():
            tags = self.users_tree.item(self.users_tree.selection()[0])["tags"]
            if len(tags) > 1 and tags[1] == "student":
                self.user_context_menu.post(event.x_root, event.y_root)
            else:
                # Показать только удаление для не-студентов
                delete_menu = tk.Menu(self, tearoff=0)
                delete_menu.add_command(label="🗑️ Удалить", command=self.delete_user)
                delete_menu.post(event.x_root, event.y_root)
    
    def get_selected_user_id(self) -> Optional[int]:
        """Получить ID выбранного пользователя"""
        selection = self.users_tree.selection()
        if not selection:
            return None
        tags = self.users_tree.item(selection[0])["tags"]
        return int(tags[0]) if tags else None
    
    def promote_to_teacher(self):
        """Повысить студента до преподавателя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
        
        if messagebox.askyesno("Подтверждение", "Повысить этого студента до преподавателя?"):
            server.db.update_user_role(user_id, "teacher", self.user["id"])
            messagebox.showinfo("Успех", "Пользователь повышен до преподавателя")
            self.refresh_users()
    
    def delete_user(self):
        """Удалить пользователя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
        
        if user_id == self.user["id"]:
            messagebox.showerror("Ошибка", "Нельзя удалить самого себя")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить этого пользователя?\nЭто действие необратимо!"):
            server.db.delete_user(user_id, self.user["id"])
            messagebox.showinfo("Успех", "Пользователь удален")
            self.refresh_users()
    
    def add_user_dialog(self):
        """Диалог добавления пользователя"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить пользователя")
        dialog.geometry("500x450")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Логин
        ctk.CTkLabel(frame, text="Логин:").pack(anchor="w", pady=(0, 5))
        login_entry = ctk.CTkEntry(frame, height=40)
        login_entry.pack(fill="x", pady=(0, 15))
        
        # Пароль
        ctk.CTkLabel(frame, text="Пароль:").pack(anchor="w", pady=(0, 5))
        password_entry = ctk.CTkEntry(frame, height=40, show="*")
        password_entry.pack(fill="x", pady=(0, 15))
        
        # ФИО
        ctk.CTkLabel(frame, text="ФИО:").pack(anchor="w", pady=(0, 5))
        fullname_entry = ctk.CTkEntry(frame, height=40)
        fullname_entry.pack(fill="x", pady=(0, 15))
        
        # Роль
        ctk.CTkLabel(frame, text="Роль:").pack(anchor="w", pady=(0, 5))
        role_combo = ctk.CTkComboBox(frame, values=["student", "teacher", "admin"])
        role_combo.pack(fill="x", pady=(0, 15))
        role_combo.set("student")
        
        # Поля для студента
        student_fields_frame = ctk.CTkFrame(frame)
        student_fields_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(student_fields_frame, text="Группа:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        group_entry = ctk.CTkEntry(student_fields_frame, width=100)
        group_entry.grid(row=0, column=1, padx=(0, 15), pady=5)
        group_entry.insert(0, "ИВТ-11")
        
        ctk.CTkLabel(student_fields_frame, text="Курс:").grid(row=0, column=2, padx=(0, 5), pady=5, sticky="w")
        course_entry = ctk.CTkEntry(student_fields_frame, width=60)
        course_entry.grid(row=0, column=3, padx=(0, 15), pady=5)
        course_entry.insert(0, "1")
        
        ctk.CTkLabel(student_fields_frame, text="Специальность:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky="w")
        specialty_entry = ctk.CTkEntry(student_fields_frame, width=300)
        specialty_entry.grid(row=1, column=1, columnspan=3, padx=(0, 15), pady=5, sticky="w")
        specialty_entry.insert(0, "Информатика и вычислительная техника")
        
        def toggle_student_fields(*args):
            if role_combo.get() == "student":
                student_fields_frame.pack(fill="x", pady=(0, 15))
            else:
                student_fields_frame.pack_forget()
        
        role_combo.configure(command=toggle_student_fields)
        
        def save():
            try:
                login = login_entry.get().strip()
                password = password_entry.get().strip()
                full_name = fullname_entry.get().strip()
                role = role_combo.get()
                
                if not login or not password or not full_name:
                    raise ValueError("Заполните все обязательные поля")
                
                group_name = None
                course = None
                specialty = None
                
                if role == "student":
                    group_name = group_entry.get().strip()
                    course = int(course_entry.get())
                    specialty = specialty_entry.get().strip()
                    if not group_name or not specialty:
                        raise ValueError("Заполните данные для студента")
                
                server.db.add_user(login, password, role, full_name, group_name, course, specialty, self.user["id"])
                messagebox.showinfo("Успех", "Пользователь добавлен")
                dialog.destroy()
                self.refresh_users()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка добавления: {e}")
        
        ctk.CTkButton(frame, text="Добавить", command=save).pack(fill="x")
    
    # ==================== ЛОГИ (Admin) ====================
    
    def setup_logs_tab(self):
        """Настройка вкладки Логи"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.tab_logs,
            text="📋 Журнал действий пользователей",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(
            self.tab_logs,
            text="🔄 Обновить",
            command=self.refresh_logs
        )
        refresh_btn.pack(pady=10)
        
        # Таблица логов
        table_frame = ctk.CTkFrame(self.tab_logs, fg_color="#2b2b2b")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("timestamp", "user_name", "action", "details")
        self.logs_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.logs_tree.heading("timestamp", text="Время")
        self.logs_tree.heading("user_name", text="Пользователь")
        self.logs_tree.heading("action", text="Действие")
        self.logs_tree.heading("details", text="Детали")
        
        self.logs_tree.column("timestamp", width=180)
        self.logs_tree.column("user_name", width=150)
        self.logs_tree.column("action", width=150)
        self.logs_tree.column("details", width=400)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.logs_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
    
    def refresh_logs(self):
        """Обновление логов"""
        try:
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            logs = server.db.get_logs(100)
            action_names = {
                "change_role": "Смена роли",
                "add_user": "Добавление пользователя",
                "delete_user": "Удаление пользователя",
                "update_grade": "Изменение оценки",
                "add_grade": "Добавление оценки",
                "delete_grade": "Удаление оценки"
            }
            
            for log in logs:
                self.logs_tree.insert("", "end", values=(
                    log["timestamp"],
                    log["user_name"] or "Система",
                    action_names.get(log["action"], log["action"]),
                    log["details"]
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки логов: {e}")
    
    # ==================== НАСТРОЙКИ ====================
    
    def setup_settings_tab(self):
        """Настройка вкладки Настройки"""
        settings_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Информация о пользователе
        info_card = ctk.CTkFrame(settings_frame, fg_color="#2b2b2b", corner_radius=10)
        info_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            info_card,
            text="ℹ️ Информация о пользователе",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15)
        
        info_text = f"""
Логин: {self.user['login']}
ФИО: {self.user['full_name']}
Роль: {self.translate_role(self.user['role'])}
ID: {self.user['id']}
        """.strip()
        
        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        ).pack(pady=15)
        
        # Переключатель темы
        theme_card = ctk.CTkFrame(settings_frame, fg_color="#2b2b2b", corner_radius=10)
        theme_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            theme_card,
            text="🎨 Тема оформления",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15)
        
        theme_frame = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_frame.pack(pady=10)
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Светлая тема",
            command=self.toggle_theme,
            onvalue="light",
            offvalue="dark"
        )
        self.theme_switch.pack()
        
        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            settings_frame,
            text="🚪 Выйти из системы",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.logout
        )
        logout_btn.pack(fill="x", pady=20)
        
        # Версия
        ctk.CTkLabel(
            settings_frame,
            text="ИАС ПолесГУ v1.0\nСистема оценки успеваемости студентов инженерного факультета",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=20)
    
    def toggle_theme(self):
        """Переключение темы"""
        if self.theme_switch.get() == "light":
            ctk.set_appearance_mode("light")
            self.top_frame.configure(fg_color="#f0f0f0")
        else:
            ctk.set_appearance_mode("dark")
            self.top_frame.configure(fg_color="#2b2b2b")
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.destroy()
            start_app()


def start_app():
    """Запуск приложения"""
    def on_login_success(user):
        app = MainWindow(user)
        app.mainloop()
    
    login = LoginWindow(on_login_success)
    login.mainloop()


if __name__ == "__main__":
    start_app()
