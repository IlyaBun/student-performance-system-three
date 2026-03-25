"""
client.py - Клиентская часть ИС ПолесГУ
Графический интерфейс на customtkinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from typing import Dict, List

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    'primary': '#2E86AB', 'secondary': '#56C596', 'accent': '#F6AE2D',
    'danger': '#E74C3C', 'warning': '#F39C12', 'success': '#27AE60',
    'info': '#3498DB', 'admin_bg': '#9B59B6', 'teacher_bg': '#3498DB',
    'student_bg': '#2ECC71', 'card_bg': '#FFFFFF', 'hover': '#ECF0F1',
}

class LoginWindow(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("ИС ПолесГУ - Вход")
        self.geometry("500x650")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        main_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(main_frame, text="ИС ПОЛЕСГУ", font=ctk.CTkFont(size=36, weight="bold"), text_color=COLORS['primary']).grid(row=0, column=0, pady=(30, 5))
        ctk.CTkLabel(main_frame, text="Информационная система", font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=0)
        
        self.mode_var = tk.StringVar(value="login")
        mode_switch = ctk.CTkSegmentedButton(main_frame, values=["login", "register"], variable=self.mode_var, command=self.switch_mode, font=ctk.CTkFont(size=13))
        mode_switch.grid(row=2, column=0, pady=25)
        
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.grid(row=3, column=0, sticky="ew", padx=30)
        form_frame.grid_columnconfigure(1, weight=1)
        
        self.login_entry = self._create_field(form_frame, "Логин:", 0)
        self.password_entry = self._create_field(form_frame, "Пароль:", 1, show="•")
        self.reg_fields = {
            'full_name': self._create_field(form_frame, "ФИО:", 2),
            'email': self._create_field(form_frame, "Email:", 3),
            'specialty': self._create_field(form_frame, "Специальность:", 5),
        }
        
        ctk.CTkLabel(form_frame, text="Группа:", font=ctk.CTkFont(size=13)).grid(row=4, column=0, sticky="w", pady=8)
        self.group_combo = ttk.Combobox(form_frame, values=["ИТ-11","ИТ-12","ИТ-13","ЛП-11","ЛП-12","ЛП-13","ПР-11","ПР-12","ПР-13"], height=200, font=("Arial",12), state="disabled")
        self.group_combo.grid(row=4, column=1, sticky="ew", pady=8, padx=(10,0))
        self.group_combo.set("ИТ-11")
        
        ctk.CTkLabel(form_frame, text="Курс:", font=ctk.CTkFont(size=13)).grid(row=6, column=0, sticky="w", pady=8)
        self.course_combo = ttk.Combobox(form_frame, values=[1,2,3,4,5], height=100, font=("Arial",12), state="disabled")
        self.course_combo.grid(row=6, column=1, sticky="w", pady=8, padx=(10,0))
        self.course_combo.set(1)
        
        self.action_button = ctk.CTkButton(main_frame, text="Войти", height=45, font=ctk.CTkFont(size=16, weight="bold"), fg_color=COLORS['primary'], hover_color=COLORS['secondary'], command=self.authenticate)
        self.action_button.grid(row=4, column=0, pady=25, padx=30, sticky="ew")
        self.toggle_reg_fields(False)

    def _create_field(self, parent, label_text, row, show=None):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=13)).grid(row=row, column=0, sticky="w", pady=8)
        entry = ctk.CTkEntry(parent, height=40, font=ctk.CTkFont(size=13), show=show)
        entry.grid(row=row, column=1, sticky="ew", pady=8, padx=(10,0))
        return entry

    def switch_mode(self, value):
        is_reg = value == "register"
        self.toggle_reg_fields(is_reg)
        self.action_button.configure(text="Зарегистрироваться" if is_reg else "Войти")

    def toggle_reg_fields(self, show):
        state = "normal" if show else "disabled"
        for w in self.reg_fields.values(): w.configure(state=state)
        self.group_combo.configure(state="readonly" if show else "disabled")
        self.course_combo.configure(state="readonly" if show else "disabled")

    def authenticate(self):
        login, password = self.login_entry.get().strip(), self.password_entry.get().strip()
        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        if self.mode_var.get() == "register":
            self.register_user(login, password)
        else:
            self.login_user(login, password)

    def register_user(self, login, password):
        full_name = self.reg_fields['full_name'].get().strip()
        email = self.reg_fields['email'].get().strip()
        specialty = self.reg_fields['specialty'].get().strip()
        if not full_name or not specialty:
            messagebox.showerror("Ошибка", "Заполните ФИО и специальность")
            return
        success, msg = self.db.register_user(login, password, full_name, 'student', email or None, self.group_combo.get(), int(self.course_combo.get()), 1, specialty)
        if success:
            messagebox.showinfo("Успех", msg)
            self.mode_var.set("login")
            self.switch_mode("login")
        else:
            messagebox.showerror("Ошибка", msg)

    def login_user(self, login, password):
        user, msg = self.db.authenticate(login, password)
        if user:
            self.destroy()
            MainWindow(self.db, user).mainloop()
        else:
            messagebox.showerror("Ошибка", msg)


class MainWindow(ctk.CTk):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.title(f"ИС ПолесГУ - {user['full_name']} ({user['role']})")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)
        
        ctk.CTkLabel(sidebar, text="ИС ПОЛЕСГУ", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS['primary']).grid(row=0, column=0, pady=20)
        
        role_colors = {'admin': COLORS['admin_bg'], 'teacher': COLORS['teacher_bg'], 'student': COLORS['student_bg']}
        user_info = ctk.CTkFrame(sidebar, fg_color=role_colors.get(user['role'], 'gray'))
        user_info.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(user_info, text=user['full_name'], font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(user_info, text=f"Роль: {user['role']}", font=ctk.CTkFont(size=11), text_color="white").pack(pady=2)
        
        self.tabs = {}
        buttons = [("Главная", "home"), ("Студенты", "students")]
        if user['role'] != 'student':
            buttons += [("Журнал", "grades"), ("Аналитика", "analytics")]
        if user['role'] == 'admin':
            buttons += [("Пользователи", "users"), ("Логи", "logs")]
        buttons += [("Настройки", "settings")]
        
        for i, (text, key) in enumerate(buttons, start=2):
            btn = ctk.CTkButton(sidebar, text=text, command=lambda k=key: self.show_tab(k), anchor="w", height=40)
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            self.tabs[key] = btn
        
        self.main_area = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkButton(sidebar, text="Выход", command=self.logout, fg_color=COLORS['danger'], hover_color="#C0392B").grid(row=11, column=0, padx=10, pady=20)
        self.show_tab("home")

    def show_tab(self, tab_name):
        for widget in self.main_area.winfo_children(): widget.destroy()
        if tab_name == "home": self.create_home_tab()
        elif tab_name == "students": self.create_students_tab()
        elif tab_name == "grades" and self.user['role'] != 'student': self.create_grades_tab()
        elif tab_name == "analytics" and self.user['role'] != 'student': self.create_analytics_tab()
        elif tab_name == "users" and self.user['role'] == 'admin': self.create_users_tab()
        elif tab_name == "logs" and self.user['role'] == 'admin': self.create_logs_tab()
        elif tab_name == "settings": self.create_settings_tab()

    def create_home_tab(self):
        ctk.CTkLabel(self.main_area, text="Панель управления", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,20))
        stats = self.db.get_dashboard_stats()
        cards_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        cards_frame.pack(fill="x", pady=10)
        kpi_data = [
            ("Студентов", stats.get('total_students', 0), "Общее количество", COLORS['primary']),
            ("Средний балл", stats.get('faculty_average', 0), "Средняя оценка (2-10)", COLORS['secondary']),
            ("Успеваемость", f"{stats.get('success_rate', 0)}%", "% студентов со средней > 3", COLORS['success']),
            ("Качество", f"{stats.get('quality_rate', 0)}%", "% оценок 8-10", COLORS['accent']),
        ]
        for i, (title, value, desc, color) in enumerate(kpi_data):
            card = ctk.CTkFrame(cards_frame, corner_radius=10)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            cards_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(15,5))
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=10), text_color="gray", wraplength=180).pack(pady=(5,15), padx=10)
        
        risk_frame = ctk.CTkFrame(self.main_area)
        risk_frame.pack(fill="both", expand=True, pady=20)
        ctk.CTkLabel(risk_frame, text=f"Группа риска ({stats.get('at_risk_count', 0)} чел.)", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS['danger']).pack(anchor="w", padx=15, pady=10)
        if stats.get('at_risk_students'):
            columns = ("name", "group", "avg")
            tree = ttk.Treeview(risk_frame, columns=columns, show="headings", height=8)
            tree.heading("name", text="ФИО"); tree.heading("group", text="Группа"); tree.heading("avg", text="Балл")
            tree.column("name", width=300); tree.column("group", width=100); tree.column("avg", width=80)
            for s in stats['at_risk_students'][:10]:
                tree.insert("", "end", values=(s['full_name'], s['group_name'], f"{s['avg_grade']:.2f}"))
            tree.pack(fill="x", padx=15, pady=10)
        
        debt_frame = ctk.CTkFrame(self.main_area)
        debt_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(debt_frame, text=f"Должники ({stats.get('debtors_count', 0)} чел.)", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS['warning']).pack(anchor="w", padx=15, pady=10)
        if stats.get('debtors'):
            columns = ("name", "group", "debts")
            tree = ttk.Treeview(debt_frame, columns=columns, show="headings", height=6)
            tree.heading("name", text="ФИО"); tree.heading("group", text="Группа"); tree.heading("debts", text="Долги")
            tree.column("name", width=300); tree.column("group", width=100); tree.column("debts", width=80)
            for d in stats['debtors'][:8]:
                tree.insert("", "end", values=(d['full_name'], d['group_name'], d['debt_count']))
            tree.pack(fill="x", padx=15, pady=10)

    def create_students_tab(self):
        ctk.CTkLabel(self.main_area, text="Студенты", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,15))
        filter_frame = ctk.CTkFrame(self.main_area)
        filter_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(filter_frame, text="Группа:").pack(side="left", padx=10)
        groups = ["Все"] + self.db.get_all_groups()
        group_var = tk.StringVar(value="Все")
        group_combo = ttk.Combobox(filter_frame, textvariable=group_var, values=groups, width=15, state="readonly")
        group_combo.pack(side="left", padx=5)
        ctk.CTkLabel(filter_frame, text="Курс:").pack(side="left", padx=10)
        course_var = tk.StringVar(value="0")
        course_combo = ttk.Combobox(filter_frame, textvariable=course_var, values=["0","1","2","3","4","5"], width=5, state="readonly")
        course_combo.pack(side="left", padx=5)
        ctk.CTkLabel(filter_frame, text="Поиск:").pack(side="left", padx=10)
        search_entry = ctk.CTkEntry(filter_frame, width=200, placeholder_text="ФИО")
        search_entry.pack(side="left", padx=5)
        
        students_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        students_frame.pack(fill="both", expand=True, pady=10)
        
        def apply_filters():
            for w in students_frame.winfo_children(): w.destroy()
            course = int(course_var.get()) if course_var.get() != "0" else None
            self.render_students_table(students_frame, group_var.get() if group_var.get() != "Все" else None, course, search_entry.get())
        
        group_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())
        course_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())
        search_entry.bind("<KeyRelease>", lambda e: apply_filters())
        apply_filters()

    def render_students_table(self, parent, group=None, course=None, search=None):
        students = self.db.get_all_students(group, course, search)
        columns = ("fio", "group", "course", "avg", "status")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
        tree.heading("fio", text="ФИО"); tree.heading("group", text="Группа"); tree.heading("course", text="Курс"); tree.heading("avg", text="Балл"); tree.heading("status", text="Статус")
        tree.column("fio", width=250); tree.column("group", width=80); tree.column("course", width=50); tree.column("avg", width=70); tree.column("status", width=100)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        for s in students:
            status = "Отличник" if s['average_grade'] >= 9 else "Хорошист" if s['average_grade'] >= 7 else "Удовл." if s['average_grade'] >= 4 else "Должник"
            color = COLORS['success'] if s['average_grade'] >= 8 else COLORS['info'] if s['average_grade'] >= 6 else COLORS['warning'] if s['average_grade'] >= 4 else COLORS['danger']
            tree.insert("", "end", values=(s['full_name'], s['group_name'], s['course'], f"{s['average_grade']:.2f}", status), tags=(color,))
            tree.tag_configure(color, foreground=color)
        def on_double_click(event):
            sel = tree.selection()
            if sel:
                student_id = students[tree.index(sel[0])]['id']
                self.show_student_details(student_id)
        tree.bind("<Double-1>", on_double_click)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_student_details(self, student_id):
        details = self.db.get_student_details(student_id)
        if not details: return
        win = ctk.CTkToplevel(self)
        win.title(f"Студент: {details['full_name']}")
        win.geometry("700x600")
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(scroll, text=details['full_name'], font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"Группа: {details['group_name']}, Курс: {details['course']}", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        ctk.CTkLabel(scroll, text=f"Средний балл: {details['average_grade']:.2f}", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS['primary']).pack(anchor="w", pady=10)
        stats_frame = ctk.CTkFrame(scroll)
        stats_frame.pack(fill="x", pady=10)
        stats = [("Отлично", details['excellent_count'], COLORS['success']), ("Хорошо", details['good_count'], COLORS['info']), ("Удовл.", details['satisfactory_count'], COLORS['warning']), ("Неуд.", details['poor_count'], COLORS['danger'])]
        for i, (label, count, color) in enumerate(stats):
            ctk.CTkLabel(stats_frame, text=f"{label}: {count}", font=ctk.CTkFont(size=14), text_color=color).grid(row=0, column=i, padx=15, pady=10)
        if details['passed_subjects']:
            ctk.CTkLabel(scroll, text="Сданные предметы:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15,5))
            for subj in details['passed_subjects'][:10]:
                ctk.CTkLabel(scroll, text=f"• {subj['name']} (ср: {subj['avg_value']:.1f})", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)
        if details['debt_subjects']:
            ctk.CTkLabel(scroll, text="ЗАДОЛЖЕННОСТИ:", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS['danger']).pack(anchor="w", pady=(15,5))
            for subj in details['debt_subjects']:
                ctk.CTkLabel(scroll, text=f"⚠ {subj['name']} (мин: {subj['min_value']})", font=ctk.CTkFont(size=12), text_color=COLORS['danger']).pack(anchor="w", padx=20)
        comments_frame = ctk.CTkFrame(scroll)
        comments_frame.pack(fill="x", pady=15)
        ctk.CTkLabel(comments_frame, text="Комментарии:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=5)
        for comment in details.get('comments', []):
            cmt_frame = ctk.CTkFrame(comments_frame, fg_color="#F5F5F5")
            cmt_frame.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(cmt_frame, text=comment['comment_text'], wraplength=600, justify="left").pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(cmt_frame, text=f"— {comment['author_name']}, {comment['created_at'][:10]}", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="e", padx=10, pady=(0,5))
        if self.user['role'] != 'student':
            ctk.CTkLabel(scroll, text="Добавить комментарий:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(15,5))
            comment_entry = ctk.CTkEntry(scroll, width=500, placeholder_text="Текст")
            comment_entry.pack(anchor="w", padx=20)
            def add_comment():
                text = comment_entry.get().strip()
                if text:
                    self.db.add_student_comment(student_id, self.user['id'], text, details['has_debts'])
                    messagebox.showinfo("Успех", "Комментарий добавлен")
                    win.destroy()
                    self.show_student_details(student_id)
            ctk.CTkButton(scroll, text="Добавить", command=add_comment).pack(anchor="w", padx=20, pady=10)

    def create_grades_tab(self):
        ctk.CTkLabel(self.main_area, text="Журнал оценок", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,15))
        filter_frame = ctk.CTkFrame(self.main_area)
        filter_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(filter_frame, text="Группа:").pack(side="left", padx=10)
        groups = ["Все"] + self.db.get_all_groups()
        group_var = tk.StringVar(value="Все")
        group_combo = ttk.Combobox(filter_frame, textvariable=group_var, values=groups, width=15, state="readonly")
        group_combo.pack(side="left", padx=5)
        ctk.CTkLabel(filter_frame, text="Предмет:").pack(side="left", padx=10)
        disciplines = [(None, "Все")] + [(d['id'], d['name']) for d in self.db.get_all_disciplines()]
        disc_var = tk.StringVar(value="Все")
        disc_combo = ttk.Combobox(filter_frame, textvariable=disc_var, values=[v for k,v in disciplines], width=25, state="readonly")
        disc_combo.pack(side="left", padx=5)
        grades_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grades_frame.pack(fill="both", expand=True, pady=10)
        def refresh():
            for w in grades_frame.winfo_children(): w.destroy()
            g_filter = group_var.get() if group_var.get() != "Все" else None
            d_filter = next((k for k,v in disciplines if v==disc_var.get()), None)
            self.render_grades_table(grades_frame, g_filter, d_filter)
        group_combo.bind("<<ComboboxSelected>>", lambda e: refresh())
        disc_combo.bind("<<ComboboxSelected>>", lambda e: refresh())
        refresh()

    def render_grades_table(self, parent, group=None, discipline=None):
        grades = self.db.get_grades(group, discipline)
        columns = ("student", "group", "discipline", "value", "type", "date")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)
        tree.heading("student", text="Студент"); tree.heading("group", text="Группа"); tree.heading("discipline", text="Предмет"); tree.heading("value", text="Оценка"); tree.heading("type", text="Тип"); tree.heading("date", text="Дата")
        tree.column("student", width=200); tree.column("group", width=70); tree.column("discipline", width=180); tree.column("value", width=60); tree.column("type", width=80); tree.column("date", width=90)
        for g in grades:
            color = COLORS['success'] if g['value'] >= 8 else COLORS['info'] if g['value'] >= 6 else COLORS['warning'] if g['value'] >= 4 else COLORS['danger']
            tree.insert("", "end", values=(g['student_name'], g['group_name'], g['discipline_name'], g['value'], g['grade_type'], g['date'][:10]), tags=(color,))
            tree.tag_configure(color, foreground=color)
        def on_double_click(event):
            if self.user['role'] == 'student': return
            sel = tree.selection()
            if sel:
                grade = grades[tree.index(sel[0])]
                self.edit_grade(grade)
        tree.bind("<Double-1>", on_double_click)
        tree.pack(fill="both", expand=True)

    def edit_grade(self, grade):
        win = ctk.CTkToplevel(self)
        win.title("Редактирование оценки")
        win.geometry("400x350")
        ctk.CTkLabel(win, text=f"Студент: {grade['student_name']}", font=ctk.CTkFont(size=14)).pack(pady=10)
        ctk.CTkLabel(win, text=f"Предмет: {grade['discipline_name']}", font=ctk.CTkFont(size=14)).pack(pady=5)
        ctk.CTkLabel(win, text="Оценка (2-10):").pack(pady=5)
        value_entry = ctk.CTkEntry(win, width=200)
        value_entry.insert(0, str(grade['value']))
        value_entry.pack(pady=5)
        ctk.CTkLabel(win, text="Тип работы:").pack(pady=5)
        type_var = tk.StringVar(value=grade['grade_type'])
        type_combo = ttk.Combobox(win, textvariable=type_var, values=["exam","lab","practice","zachet","coursework"], state="readonly", width=20)
        type_combo.pack(pady=5)
        ctk.CTkLabel(win, text="Комментарий:").pack(pady=5)
        comment_entry = ctk.CTkEntry(win, width=300)
        comment_entry.insert(0, grade['comment'] or "")
        comment_entry.pack(pady=5)
        def save():
            try:
                new_val = int(value_entry.get())
                if 2 <= new_val <= 10:
                    ok, msg = self.db.update_grade(grade['id'], new_val, type_var.get(), comment_entry.get(), self.user['id'])
                    if ok:
                        messagebox.showinfo("Успех", msg)
                        win.destroy()
                    else:
                        messagebox.showerror("Ошибка", msg)
                else:
                    messagebox.showerror("Ошибка", "Оценка должна быть 2-10")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число")
        ctk.CTkButton(win, text="Сохранить", command=save).pack(pady=20)

    def create_analytics_tab(self):
        ctk.CTkLabel(self.main_area, text="Аналитика успеваемости", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,15))
        scroll = ctk.CTkScrollableFrame(self.main_area)
        scroll.pack(fill="both", expand=True)
        self.create_bar_chart(scroll, "Средний балл по группам", self.db.get_group_averages(), "group_name", "avg_grade", "#2E86AB")
        self.create_bar_chart(scroll, "Средний балл по курсам", self.db.get_course_averages(), "course", "avg_grade", "#56C596")
        dist = self.db.get_grade_distribution()
        if dist:
            fig = Figure(figsize=(10, 5), dpi=100)
            ax = fig.add_subplot(111)
            grades_labels = ['2','3','4','5','6','7','8','9','10']
            values = [dist[0].get(str(g), 0) for g in range(2, 11)]
            colors = [COLORS['danger'], COLORS['danger'], COLORS['warning'], COLORS['warning'], COLORS['info'], COLORS['info'], COLORS['success'], COLORS['success'], COLORS['success']]
            ax.bar(grades_labels, values, color=colors)
            ax.set_title("Распределение оценок")
            ax.set_xlabel("Оценка")
            ax.set_ylabel("Количество")
            canvas = FigureCanvasTkAgg(fig, master=scroll)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=20)

    def create_bar_chart(self, parent, title, data, x_key, y_key, color):
        if not data: return
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        labels = [str(d[x_key]) for d in data]
        values = [d[y_key] for d in data]
        ax.bar(labels, values, color=color)
        ax.set_title(title)
        ax.set_ylim(0, 10)
        ax.axhline(y=4, color='red', linestyle='--', label='Мин. порог (4)')
        ax.legend()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    def create_users_tab(self):
        ctk.CTkLabel(self.main_area, text="Управление пользователями", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,15))
        users = self.db.get_all_users()
        columns = ("login", "fio", "role", "group", "status")
        tree = ttk.Treeview(self.main_area, columns=columns, show="headings", height=20)
        tree.heading("login", text="Логин"); tree.heading("fio", text="ФИО"); tree.heading("role", text="Роль"); tree.heading("group", text="Группа"); tree.heading("status", text="Статус")
        tree.column("login", width=120); tree.column("fio", width=250); tree.column("role", width=100); tree.column("group", width=100); tree.column("status", width=80)
        role_colors_map = {'admin': COLORS['admin_bg'], 'teacher': COLORS['teacher_bg'], 'student': COLORS['student_bg']}
        for u in users:
            status = "Активен" if u['is_active'] else "Заблокирован"
            color = role_colors_map.get(u['role'], 'gray')
            tree.insert("", "end", values=(u['login'], u['full_name'], u['role'], u.get('group_name',''), status), tags=(u['role'],))
            tree.tag_configure(u['role'], foreground=color)
        def on_right_click(event):
            if self.user['role'] != 'admin': return
            sel = tree.selection()
            if not sel: return
            idx = tree.index(sel[0])
            user = users[idx]
            menu = tk.Menu(self, tearoff=0)
            if user['role'] == 'student':
                menu.add_command(label="Назначить преподавателем", command=lambda: self.change_role(user['id'], 'teacher'))
                menu.add_command(label="Назначить админом", command=lambda: self.change_role(user['id'], 'admin'))
            elif user['role'] == 'teacher':
                menu.add_command(label="Вернуть в студенты", command=lambda: self.change_role(user['id'], 'student'))
            menu.add_separator()
            menu.add_command(label="Заблокировать/Разблокировать", command=lambda: self.toggle_active(user['id']))
            menu.tk_popup(event.x_root, event.y_root)
        tree.bind("<Button-3>", on_right_click)
        tree.pack(fill="both", expand=True, pady=10)

    def change_role(self, user_id, new_role):
        ok, msg = self.db.update_user_role(user_id, new_role, self.user['id'])
        messagebox.showinfo("Результат", msg)
        if ok: self.create_users_tab()

    def toggle_active(self, user_id):
        ok, msg = self.db.toggle_user_active(user_id, self.user['id'])
        messagebox.showinfo("Результат", msg)
        if ok: self.create_users_tab()

    def create_logs_tab(self):
        ctk.CTkLabel(self.main_area, text="Журнал действий", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,15))
        logs = self.db.get_logs(200)
        columns = ("time", "user", "action", "details")
        tree = ttk.Treeview(self.main_area, columns=columns, show="headings", height=25)
        tree.heading("time", text="Время"); tree.heading("user", text="Пользователь"); tree.heading("action", text="Действие"); tree.heading("details", text="Детали")
        tree.column("time", width=150); tree.column("user", width=150); tree.column("action", width=120); tree.column("details", width=400)
        for log in logs:
            tree.insert("", "end", values=(log['timestamp'][:19], log['user_name'] or 'System', log['action'], log['details'] or ''))
        tree.pack(fill="both", expand=True, pady=10)

    def create_settings_tab(self):
        ctk.CTkLabel(self.main_area, text="Настройки", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0,20))
        settings_frame = ctk.CTkFrame(self.main_area)
        settings_frame.pack(fill="x", padx=50, pady=10)
        ctk.CTkLabel(settings_frame, text=f"Пользователь: {self.user['full_name']}", font=ctk.CTkFont(size=16)).pack(anchor="w", pady=10)
        ctk.CTkLabel(settings_frame, text=f"Роль: {self.user['role']}", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        ctk.CTkLabel(settings_frame, text=f"Логин: {self.user['login']}", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        ctk.CTkLabel(settings_frame, text="Тема оформления:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(20,5))
        def toggle_theme():
            current = ctk.get_appearance_mode()
            new = "dark" if current == "light" else "light"
            ctk.set_appearance_mode(new)
        ctk.CTkButton(settings_frame, text="Переключить тему", command=toggle_theme).pack(anchor="w", pady=10)
        ctk.CTkButton(settings_frame, text="Выход", fg_color=COLORS['danger'], command=self.logout).pack(anchor="w", pady=20)

    def logout(self):
        self.destroy()
        LoginWindow(self.db).mainloop()


if __name__ == "__main__":
    from server import Database
    db = Database()
    LoginWindow(db).mainloop()
