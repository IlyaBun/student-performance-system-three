"""
client.py - Клиентская часть системы оценки успеваемости студентов
Графический интерфейс на customtkinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Dict, Any, List

from server import get_database, close_database


class App(ctk.CTk):
    """Основное приложение"""
    
    def __init__(self):
        super().__init__()
        
        self.db = get_database()
        self.current_user: Optional[Dict[str, Any]] = None
        self.theme_mode = "dark"
        
        # Настройка окна
        self.title("ИАС ПолесГУ - Система оценки успеваемости")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Настройка темы
        ctk.set_appearance_mode(self.theme_mode)
        ctk.set_default_color_theme("blue")
        
        # Создание виджетов
        self._create_login_screen()
    
    def _create_login_screen(self):
        """Создание экрана авторизации"""
        self.login_frame = ctk.CTkFrame(self, width=400, height=300)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.login_frame, 
            text="ИАС ПолесГУ", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.login_frame, 
            text="Система оценки успеваемости",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Поле логина
        login_label = ctk.CTkLabel(self.login_frame, text="Логин:")
        login_label.pack(anchor="w", padx=20)
        
        self.login_entry = ctk.CTkEntry(self.login_frame, width=300)
        self.login_entry.pack(pady=(5, 15))
        
        # Поле пароля
        password_label = ctk.CTkLabel(self.login_frame, text="Пароль:")
        password_label.pack(anchor="w", padx=20)
        
        self.password_entry = ctk.CTkEntry(self.login_frame, width=300, show="*")
        self.password_entry.pack(pady=(5, 20))
        
        # Кнопка входа
        login_button = ctk.CTkButton(
            self.login_frame, 
            text="Войти", 
            command=self._login,
            width=300,
            height=40
        )
        login_button.pack(pady=10)
        
        # Привязка Enter
        self.bind("<Return>", lambda e: self._login())
    
    def _login(self):
        """Обработка входа"""
        login = self.login_entry.get().strip()
        password = self.password_entry.get()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        user = self.db.authenticate(login, password)
        
        if user:
            self.current_user = user
            self._show_main_interface()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
    
    def _show_main_interface(self):
        """Показ основного интерфейса"""
        self.login_frame.destroy()
        
        # Верхняя панель
        self._create_top_bar()
        
        # Вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Добавление вкладок в зависимости от роли
        self.tabview.add("Главная")
        self.tabview.add("Студенты")
        self.tabview.add("Журнал")
        self.tabview.add("Аналитика")
        
        if self.current_user["role"] == "admin":
            self.tabview.add("Пользователи")
        
        self.tabview.add("Настройки")
        
        # Инициализация вкладок
        self._init_dashboard_tab()
        self._init_students_tab()
        self._init_gradebook_tab()
        self._init_analytics_tab()
        
        if self.current_user["role"] == "admin":
            self._init_users_tab()
        
        self._init_settings_tab()
    
    def _create_top_bar(self):
        """Создание верхней панели"""
        top_bar = ctk.CTkFrame(self, height=50)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        
        # Информация о пользователе
        user_info = f"{self.current_user['full_name']} ({self.current_user['role']})"
        user_label = ctk.CTkLabel(top_bar, text=user_info, font=ctk.CTkFont(size=14))
        user_label.pack(side="left", padx=20, pady=10)
    
    # ==================== Вкладка Главная ====================
    
    def _init_dashboard_tab(self):
        """Инициализация вкладки Dashboard"""
        dashboard_frame = self.tabview.tab("Главная")
        
        # KPI карточки
        kpi_frame = ctk.CTkFrame(dashboard_frame)
        kpi_frame.pack(fill="x", padx=20, pady=20)
        
        self.kpi_labels = {}
        kpi_titles = [
            ("Всего студентов", "total_students"),
            ("Средний балл", "avg_grade"),
            ("Успеваемость %", "success_rate"),
            ("Качество %", "quality_rate")
        ]
        
        for i, (title, key) in enumerate(kpi_titles):
            card = ctk.CTkFrame(kpi_frame, width=200, height=100)
            card.grid(row=0, column=i, padx=10, pady=10)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
            value_label = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=24, weight="bold"))
            value_label.pack()
            self.kpi_labels[key] = value_label
        
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Группа риска
        risk_frame = ctk.CTkFrame(dashboard_frame)
        risk_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(risk_frame, text="Группа риска (оценки ≤ 4)", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Treeview для группы риска
        risk_container = ctk.CTkFrame(risk_frame)
        risk_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("name", "group", "min_grade")
        self.risk_tree = ttk.Treeview(risk_container, columns=columns, show="headings", height=10)
        self.risk_tree.heading("name", text="ФИО")
        self.risk_tree.heading("group", text="Группа")
        self.risk_tree.heading("min_grade", text="Мин. оценка")
        self.risk_tree.column("name", width=300)
        self.risk_tree.column("group", width=100)
        self.risk_tree.column("min_grade", width=100)
        
        risk_scrollbar = ttk.Scrollbar(risk_container, orient="vertical", command=self.risk_tree.yview)
        self.risk_tree.configure(yscrollcommand=risk_scrollbar.set)
        
        self.risk_tree.pack(side="left", fill="both", expand=True)
        risk_scrollbar.pack(side="right", fill="y")
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(dashboard_frame, text="Обновить", command=self._refresh_dashboard)
        refresh_btn.pack(pady=10)
        
        # Загрузка данных
        self._refresh_dashboard()
    
    def _refresh_dashboard(self):
        """Обновление данных Dashboard"""
        stats = self.db.get_dashboard_stats()
        
        self.kpi_labels["total_students"].configure(text=str(stats.get("total_students", 0)))
        self.kpi_labels["avg_grade"].configure(text=str(stats.get("avg_grade", 0)))
        self.kpi_labels["success_rate"].configure(text=f"{stats.get('success_rate', 0)}%")
        self.kpi_labels["quality_rate"].configure(text=f"{stats.get('quality_rate', 0)}%")
        
        # Обновление группы риска
        for item in self.risk_tree.get_children():
            self.risk_tree.delete(item)
        
        risk_students = self.db.get_at_risk_students()
        for student in risk_students:
            grade_text = "Зачтено" if student["min_grade"] == 5 else str(student["min_grade"])
            self.risk_tree.insert("", "end", values=(
                student["full_name"],
                student["group_name"],
                grade_text
            ))
    
    # ==================== Вкладка Студенты ====================
    
    def _init_students_tab(self):
        """Инициализация вкладки Студенты"""
        students_frame = self.tabview.tab("Студенты")
        
        # Фильтр по группе
        filter_frame = ctk.CTkFrame(students_frame)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Группа:").pack(side="left", padx=5)
        
        groups = ["Все"] + self.db.get_all_groups()
        self.group_filter_var = ctk.StringVar(value="Все")
        group_combo = ctk.CTkComboBox(
            filter_frame, 
            values=groups, 
            variable=self.group_filter_var,
            command=self._filter_students,
            width=200
        )
        group_combo.pack(side="left", padx=5)
        
        # Таблица студентов
        table_frame = ctk.CTkFrame(students_frame)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("name", "group", "course", "avg_grade")
        self.students_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.students_tree.heading("name", text="ФИО")
        self.students_tree.heading("group", text="Группа")
        self.students_tree.heading("course", text="Курс")
        self.students_tree.heading("avg_grade", text="Средний балл")
        
        self.students_tree.column("name", width=300)
        self.students_tree.column("group", width=100)
        self.students_tree.column("course", width=60)
        self.students_tree.column("avg_grade", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)
        
        self.students_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Двойной клик для просмотра оценок
        self.students_tree.bind("<Double-1>", self._show_student_grades)
        
        # Загрузка данных
        self._filter_students("Все")
    
    def _filter_students(self, event=None):
        """Фильтрация студентов по группе"""
        group = self.group_filter_var.get()
        
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
        
        students = self.db.get_students(group if group != "Все" else None)
        for student in students:
            self.students_tree.insert("", "end", values=(
                student["full_name"],
                student["group_name"],
                student["course"],
                student["avg_grade"]
            ))
    
    def _show_student_grades(self, event=None):
        """Показ оценок студента в модальном окне"""
        selection = self.students_tree.selection()
        if not selection:
            return
        
        item = self.students_tree.item(selection[0])
        name = item["values"][0]
        
        # Поиск ID студента
        students = self.db.get_students()
        student_id = None
        for s in students:
            if s["full_name"] == name:
                student_id = s["id"]
                break
        
        if not student_id:
            return
        
        # Модальное окно
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Оценки: {name}")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Текст с оценками
        text_frame = ctk.CTkFrame(dialog)
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        grades = self.db.get_student_grades(student_id)
        
        text_widget = ctk.CTkTextbox(text_frame, wrap="word")
        text_widget.pack(fill="both", expand=True)
        
        if grades:
            for grade in grades:
                grade_type_ru = {
                    "exam": "Экзамен",
                    "lab": "Лабораторная",
                    "practice": "Практика",
                    "zachet": "Зачет"
                }.get(grade["grade_type"], grade["grade_type"])
                
                value_text = "Зачтено" if grade["value"] == 5 and grade["grade_type"] == "zachet" else str(grade["value"])
                if grade["value"] == 2 and grade["grade_type"] == "zachet":
                    value_text = "Не зачтено"
                
                line = f"{grade['date']} | {grade['discipline']} | {grade_type_ru}: {value_text}\n"
                text_widget.insert("end", line)
        else:
            text_widget.insert("end", "Оценок нет")
        
        text_widget.configure(state="disabled")
        
        close_btn = ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy)
        close_btn.pack(pady=10)
    
    # ==================== Вкладка Журнал ====================
    
    def _init_gradebook_tab(self):
        """Инициализация вкладки Журнал"""
        gradebook_frame = self.tabview.tab("Журнал")
        
        # Фильтры
        filter_frame = ctk.CTkFrame(gradebook_frame)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Группа:").pack(side="left", padx=5)
        
        groups = self.db.get_all_groups()
        self.gradebook_group_var = ctk.StringVar(value=groups[0] if groups else "")
        group_combo = ctk.CTkComboBox(
            filter_frame, 
            values=groups, 
            variable=self.gradebook_group_var,
            width=200
        )
        group_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Предмет:").pack(side="left", padx=(20, 5))
        
        disciplines = self.db.get_all_disciplines()
        self.discipline_ids = {d["name"]: d["id"] for d in disciplines}
        discipline_names = list(self.discipline_ids.keys())
        
        self.gradebook_discipline_var = ctk.StringVar(value=discipline_names[0] if discipline_names else "")
        discipline_combo = ctk.CTkComboBox(
            filter_frame, 
            values=discipline_names, 
            variable=self.gradebook_discipline_var,
            width=250,
            command=self._load_gradebook
        )
        discipline_combo.pack(side="left", padx=5)
        
        load_btn = ctk.CTkButton(filter_frame, text="Загрузить", command=self._load_gradebook)
        load_btn.pack(side="left", padx=10)
        
        # Таблица журнала
        table_frame = ctk.CTkFrame(gradebook_frame)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("name", "value", "type", "date")
        self.gradebook_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.gradebook_tree.heading("name", text="ФИО")
        self.gradebook_tree.heading("value", text="Оценка")
        self.gradebook_tree.heading("type", text="Тип работы")
        self.gradebook_tree.heading("date", text="Дата")
        
        self.gradebook_tree.column("name", width=300)
        self.gradebook_tree.column("value", width=80)
        self.gradebook_tree.column("type", width=100)
        self.gradebook_tree.column("date", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.gradebook_tree.yview)
        self.gradebook_tree.configure(yscrollcommand=scrollbar.set)
        
        self.gradebook_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Двойной клик для редактирования
        if self.current_user["role"] in ["admin", "teacher"]:
            self.gradebook_tree.bind("<Double-1>", self._edit_grade)
        
        # Загрузка данных
        if groups and discipline_names:
            self._load_gradebook()
    
    def _load_gradebook(self, event=None):
        """Загрузка журнала оценок"""
        group = self.gradebook_group_var.get()
        discipline_name = self.gradebook_discipline_var.get()
        
        if not group or not discipline_name:
            return
        
        discipline_id = self.discipline_ids.get(discipline_name)
        if not discipline_id:
            return
        
        for item in self.gradebook_tree.get_children():
            self.gradebook_tree.delete(item)
        
        grades = self.db.get_gradebook(group, discipline_id)
        for grade in grades:
            value_text = ""
            if grade["value"] is not None:
                if grade["grade_type"] == "zachet":
                    value_text = "Зачтено" if grade["value"] == 5 else "Не зачтено"
                else:
                    value_text = str(grade["value"])
            
            type_text = {
                "exam": "Экзамен",
                "lab": "Лабораторная",
                "practice": "Практика",
                "zachet": "Зачет"
            }.get(grade["grade_type"], grade["grade_type"])
            
            self.gradebook_tree.insert("", "end", values=(
                grade["full_name"],
                value_text,
                type_text,
                grade["date"] or ""
            ), tags=(grade["student_id"], grade["grade_id"]))
    
    def _edit_grade(self, event=None):
        """Редактирование оценки"""
        selection = self.gradebook_tree.selection()
        if not selection:
            return
        
        item = self.gradebook_tree.item(selection[0])
        tags = item["tags"]
        
        if len(tags) < 2:
            return
        
        student_id = int(tags[0])
        grade_id = int(tags[1]) if tags[1] else None
        
        # Диалоговое окно
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактирование оценки")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Поле оценки
        ctk.CTkLabel(dialog, text="Оценка (2-10):").pack(pady=(20, 5))
        
        grade_entry = ctk.CTkEntry(dialog, width=200)
        grade_entry.pack()
        
        # Подсказка для зачета
        hint_label = ctk.CTkLabel(
            dialog, 
            text="Для зачета: 5 = Зачтено, 2 = Не зачтено",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        hint_label.pack(pady=5)
        
        # Тип работы
        ctk.CTkLabel(dialog, text="Тип работы:").pack(pady=(10, 5))
        
        grade_types = ["exam", "lab", "practice", "zachet"]
        grade_type_names = ["Экзамен", "Лабораторная", "Практика", "Зачет"]
        self.edit_grade_type_var = ctk.StringVar(value=grade_types[0])
        type_combo = ctk.CTkComboBox(
            dialog, 
            values=grade_type_names, 
            variable=self.edit_grade_type_var,
            width=200
        )
        type_combo.pack()
        
        # Сохранение
        def save():
            try:
                value = int(grade_entry.get())
                if value < 2 or value > 10:
                    messagebox.showerror("Ошибка", "Оценка должна быть от 2 до 10")
                    return
                
                grade_type_map = dict(zip(grade_type_names, grade_types))
                grade_type = grade_type_map[self.edit_grade_type_var.get()]
                
                discipline_name = self.gradebook_discipline_var.get()
                discipline_id = self.discipline_ids.get(discipline_name)
                
                if self.db.update_grade(grade_id, student_id, discipline_id, value, grade_type, self.current_user["id"]):
                    messagebox.showinfo("Успех", "Оценка сохранена")
                    dialog.destroy()
                    self._load_gradebook()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить оценку")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число")
        
        save_btn = ctk.CTkButton(dialog, text="Сохранить", command=save)
        save_btn.pack(pady=20)
    
    # ==================== Вкладка Аналитика ====================
    
    def _init_analytics_tab(self):
        """Инициализация вкладки Аналитика"""
        analytics_frame = self.tabview.tab("Аналитика")
        
        ctk.CTkLabel(analytics_frame, text="Средний балл по группам", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Фрейм для графика
        chart_frame = ctk.CTkFrame(analytics_frame)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.chart_frame_container = chart_frame
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(analytics_frame, text="Обновить график", command=self._refresh_analytics)
        refresh_btn.pack(pady=10)
        
        # Загрузка графика
        self._refresh_analytics()
    
    def _refresh_analytics(self):
        """Обновление графика аналитики"""
        # Очистка предыдущего графика
        for widget in self.chart_frame_container.winfo_children():
            widget.destroy()
        
        data = self.db.get_group_averages()
        
        if not data:
            ctk.CTkLabel(self.chart_frame_container, text="Нет данных для отображения").pack()
            return
        
        # Создание графика matplotlib
        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)
        
        groups = list(data.keys())
        averages = list(data.values())
        
        bars = ax.bar(groups, averages, color='steelblue')
        ax.set_xlabel('Группа')
        ax.set_ylabel('Средний балл')
        ax.set_title('Средний балл по группам')
        ax.set_ylim(0, 10)
        ax.grid(axis='y', alpha=0.3)
        
        # Поворот подписей групп
        plt = fig.get_canvas()
        for label in ax.get_xticklabels():
            label.set_rotation(45)
        
        # Встраивание в GUI
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # ==================== Вкладка Пользователи (Admin) ====================
    
    def _init_users_tab(self):
        """Инициализация вкладки Пользователи"""
        users_frame = self.tabview.tab("Пользователи")
        
        # Таблица пользователей
        table_frame = ctk.CTkFrame(users_frame)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("login", "name", "role")
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.users_tree.heading("login", text="Логин")
        self.users_tree.heading("name", text="ФИО")
        self.users_tree.heading("role", text="Роль")
        
        self.users_tree.column("login", width=150)
        self.users_tree.column("name", width=300)
        self.users_tree.column("role", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Контекстное меню для повышения
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Назначить преподавателем", command=self._promote_to_teacher)
        
        self.users_tree.bind("<Button-3>", self._show_context_menu)
        
        # Загрузка данных
        self._load_users()
    
    def _load_users(self):
        """Загрузка списка пользователей"""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        users = self.db.get_all_users()
        role_names = {"admin": "Админ", "teacher": "Преподаватель", "student": "Студент"}
        
        for user in users:
            self.users_tree.insert("", "end", values=(
                user["login"],
                user["full_name"],
                role_names.get(user["role"], user["role"])
            ), tags=(user["id"], user["role"]))
    
    def _show_context_menu(self, event):
        """Показ контекстного меню"""
        item = self.users_tree.identify_row(event.y)
        if item:
            tags = self.users_tree.item(item)["tags"]
            if tags and tags[1] == "student":
                self.users_tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
    
    def _promote_to_teacher(self):
        """Повышение до преподавателя"""
        selection = self.users_tree.selection()
        if not selection:
            return
        
        item = self.users_tree.item(selection[0])
        tags = item["tags"]
        
        if not tags or tags[1] != "student":
            return
        
        user_id = int(tags[0])
        
        if messagebox.askyesno("Подтверждение", "Повысить пользователя до преподавателя?"):
            if self.db.promote_to_teacher(user_id, self.current_user["id"]):
                messagebox.showinfo("Успех", "Пользователь повышен")
                self._load_users()
            else:
                messagebox.showerror("Ошибка", "Не удалось повысить пользователя")
    
    # ==================== Вкладка Настройки ====================
    
    def _init_settings_tab(self):
        """Инициализация вкладки Настройки"""
        settings_frame = self.tabview.tab("Настройки")
        
        # Информация о пользователе
        info_frame = ctk.CTkFrame(settings_frame)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(info_frame, text="Информация о пользователе", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(info_frame, text=f"ФИО: {self.current_user['full_name']}").pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"Логин: {self.current_user['login']}").pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"Роль: {self.current_user['role']}").pack(pady=5)
        
        # Переключатель темы
        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(theme_frame, text="Тема оформления", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        theme_btn = ctk.CTkButton(
            theme_frame, 
            text="Переключить тему", 
            command=self._toggle_theme
        )
        theme_btn.pack(pady=10)
        
        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            settings_frame, 
            text="Выйти", 
            command=self._logout,
            fg_color="red",
            hover_color="darkred"
        )
        logout_btn.pack(pady=20)
    
    def _toggle_theme(self):
        """Переключение темы"""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
        else:
            self.theme_mode = "dark"
        
        ctk.set_appearance_mode(self.theme_mode)
    
    def _logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.current_user = None
            self.destroy()
            self._create_login_screen()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        close_database()
        self.destroy()


def run_app():
    """Запуск приложения"""
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    run_app()
