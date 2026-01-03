
import os
from dotenv import load_dotenv
load_dotenv()

import flet as ft
import json
import threading
import datetime
import calendar
import uuid
import google.generativeai as genai
import random
import time


load_dotenv()

# --- CONSTANTS ---
DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"
APP_TITLE = "LEONIS"

# ⚠️ BURAYA KENDİ API KEY'İNİ YAPIŞTIRMAYI UNUTMA!

API_KEY = os.getenv("GOOGLE_API_KEY")

# Colors
COLOR_BG = ft.Colors.BLACK
COLOR_CARD = ft.Colors.GREY_900
COLOR_TEXT = ft.Colors.WHITE
COLOR_HIGH = ft.Colors.RED_ACCENT_400
COLOR_MED = ft.Colors.ORANGE_ACCENT_400
COLOR_LOW = ft.Colors.GREEN_ACCENT_400
COLOR_NONE = ft.Colors.GREY_600
COLOR_CYAN = ft.Colors.CYAN_ACCENT

# Gamification
RANKS = [
    {"threshold": 0, "title": "Neophyte", "color": ft.Colors.GREEN_400, "icon": ft.Icons.NATURE},
    {"threshold": 501, "title": "Operative", "color": ft.Colors.CYAN_400, "icon": ft.Icons.SETTINGS},
    {"threshold": 1501, "title": "System Architect", "color": ft.Colors.BLUE_400, "icon": ft.Icons.ARCHITECTURE},
    {"threshold": 3501, "title": "Tech Visionary", "color": ft.Colors.PURPLE_400, "icon": ft.Icons.VISIBILITY},
    {"threshold": 6000, "title": "Grandmaster", "color": ft.Colors.AMBER_400, "icon": ft.Icons.WORKSPACE_PREMIUM}
]

CONFETTI_SRC = "https://assets9.lottiefiles.com/packages/lf20_u4yrau.json" 

class ConfettiControl(ft.Stack):
    def __init__(self):
        super().__init__()
        self.lottie = ft.Lottie(src=CONFETTI_SRC, repeat=False, reverse=False, animate=False, visible=False, width=500, height=500)
        self.controls = [self.lottie]

    def fire(self):
        self.lottie.visible = True; self.lottie.animate = True; self.lottie.update()
        threading.Timer(2.0, self.stop).start()

    def stop(self):
        self.lottie.animate = False; self.lottie.visible = False; self.lottie.update()

def main(page: ft.Page):
    # A. CONFIG
    page.title = APP_TITLE
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family="Poppins")
    page.scroll = None
    page.padding = 0
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = True

    # Setup Gemini AI (Doğru Model ile)
    if API_KEY != "BURAYA_API_KEY_YAPISTIR":
        try:
            genai.configure(api_key=API_KEY)
            # Senin hesabında bulunan en yeni modeli kullanıyoruz
            model = genai.GenerativeModel('gemini-flash-latest')
            print("✅ Model başarıyla tanımlandı: gemini-flash-latest")
        except Exception as e:
            print(f"❌ Model tanımlama hatası: {e}")
            model = None
    else:
        print("⚠️ UYARI: API Key girilmemiş!")
        model = None

    # B. DATA INIT
    tasks = []
    history = {"total_completed": 0, "streak_count": 0, "last_login": None, "login_history": [], "user_xp": 0, "daily_stats": {}}
    view_mode = ["list"] 
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                raw_data = json.load(f)
                for item in raw_data:
                    if "task" not in item and "name" in item: item["task"] = item.pop("name")
                    if "id" not in item: item["id"] = str(uuid.uuid4())
                    item.setdefault("priority", "Medium"); item.setdefault("done", False)
                    item.setdefault("date", datetime.date.today().isoformat())
                    item.setdefault("notes", ""); item.setdefault("category", "Personal")
                    tasks.append(item)
        except: pass

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f: history.update(json.load(f))
            if "daily_stats" not in history: history["daily_stats"] = {}
        except: pass

    confetti = ConfettiControl()
    page.overlay.append(confetti)
    tasks_container = ft.Column(spacing=10)
    
    def save_all():
        try:
            with open(DATA_FILE, 'w') as f: json.dump(tasks, f, indent=4)
            with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=4)
        except: pass

    def check_streak():
        today = datetime.date.today().isoformat()
        last = history["last_login"]
        if last != today:
             if last:
                 diff = (datetime.date.today() - datetime.date.fromisoformat(last)).days
                 if diff == 1: history["streak_count"] += 1
                 elif diff > 1: history["streak_count"] = 1
             else: history["streak_count"] = 1
        history["last_login"] = today
        if today not in history["login_history"]: history["login_history"].append(today)
        save_all()
    check_streak()

    # --- UI CONTAINERS ---

    # 1. TRIBUTE SCREEN
    tribute_view = ft.Container(
        visible=False, 
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column([
            ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=80, color=ft.Colors.AMBER),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Text("Yerinde duran, geriye gidiyor demektir.", italic=True, size=18, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
            ft.Text("İleri, daima ileri!", italic=True, size=22, color=ft.Colors.WHITE, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Divider(height=40, color=ft.Colors.WHITE10),
            ft.Text("MUSTAFA KEMAL ATATÜRK", weight="bold", color=ft.Colors.RED_700, size=24, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
            ft.ElevatedButton("Geri Dön", icon=ft.Icons.ARROW_BACK, on_click=lambda e: toggle_tribute_screen(False), bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # --- HELPER: GET RANK ---
    def get_rank(xp):
        current_rank = RANKS[0]
        next_rank = None
        for i, r in enumerate(RANKS):
            if xp >= r["threshold"]:
                current_rank = r
                if i + 1 < len(RANKS): next_rank = RANKS[i+1]
                else: next_rank = None # Max level
        
        # Calculate progress
        if next_rank:
            needed = next_rank["threshold"] - current_rank["threshold"]
            current_prog = xp - current_rank["threshold"]
            prog_val = current_prog / needed
            next_threshold = next_rank["threshold"]
        else:
            prog_val = 1.0
            next_threshold = xp # Maxed out
            
        return current_rank, prog_val, next_threshold

    # 2. MAIN APP SCREEN
    main_view = ft.Column()

    def toggle_tribute_screen(show):
        if show:
            main_view.visible = False; tribute_view.visible = True; page.title = "Atatürk Köşesi"
        else:
            main_view.visible = True; tribute_view.visible = False; page.title = APP_TITLE
        page.update()

    # --- AI LOGIC (DEDEKTİF MODU 🕵️‍♂️) ---
    # --- AI LOGIC (DEDEKTİF MODU 🕵️‍♂️) ---
    def generate_ai_subtasks(e, override_prompt=None):
        print("\n--- 1. AI GENERATION STARTED ---")
        
        # Determine the task input source
        target_task = override_prompt if override_prompt else field_task.value
        
        if not target_task:
            print("HATA: Görev kutusu boş.")
            page.snack_bar = ft.SnackBar(ft.Text("Lütfen bir görev yazın!"), bgcolor=ft.Colors.RED_900)
            page.snack_bar.open = True; page.update()
            return

        if not model:
            print("HATA: 'model' değişkeni yok.")
            page.snack_bar = ft.SnackBar(ft.Text("Model yüklenemedi! Terminale bakın."), bgcolor=ft.Colors.RED_900)
            page.snack_bar.open = True; page.update()
            return

        print(f"Hedef Görev: {target_task}")
        print("Google'a istek gönderiliyor...")
        btn_magic.icon = ft.Icons.HOURGLASS_TOP; btn_magic.disabled = True; page.update()

        try:
            prompt = f"'{target_task}' için yapılacaklar listesi oluştur. Sadece 3 ile 5 arası kısa ve net madde yaz. Madde işaretleri kullanma. Her satıra bir görev yaz."
            
            response = model.generate_content(prompt)
            print(f"Cevap:\n{response.text}")
            
            raw_lines = response.text.strip().split('\n')
            suggestions = [line.strip().replace('*', '').replace('-', '').strip() for line in raw_lines if line.strip()]

            # --- REVIEW DIALOG ---
            checkboxes = [ft.Checkbox(label=s, value=True, active_color=ft.Colors.PURPLE_ACCENT) for s in suggestions]
            
            def confirm_add(e):
                added_count = 0
                for cb in checkboxes:
                    if cb.value:
                        tasks.append({
                            "id": str(uuid.uuid4()), "task": cb.label, "priority": "Medium",
                            "category": "Personal", "done": False, "notes": f"AI: {target_task}", "date": datetime.date.today().isoformat()
                        })
                        added_count += 1
                
                if added_count > 0:
                    field_task.value = ""
                    save_all(); render_tasks() # Re-render will clear empty state if tasks added
                    page.snack_bar = ft.SnackBar(ft.Text(f"🦁 {added_count} görev eklendi!"), bgcolor=ft.Colors.GREEN_900)
                    page.snack_bar.open = True
                
                page.close(dlg)

            dlg = ft.AlertDialog(
                title=ft.Text("AI Önerileri 🕵️‍♂️"),
                content=ft.Column([ft.Text("Eklemek istediklerinizi seçin:", color=ft.Colors.GREY_400)] + checkboxes, tight=True),
                actions=[
                    ft.TextButton("İptal", on_click=lambda e: page.close(dlg)),
                    ft.ElevatedButton("Seçilenleri Ekle", on_click=confirm_add, bgcolor=ft.Colors.INDIGO_ACCENT, color=ft.Colors.WHITE)
                ],
            )
            page.open(dlg)

        except Exception as err:
            print(f"Hata Detayı: {err}")
            page.snack_bar = ft.SnackBar(ft.Text("Hata oluştu! Terminale bakın."), bgcolor=ft.Colors.RED_900)
            page.snack_bar.open = True
        
        btn_magic.icon = ft.Icons.AUTO_FIX_HIGH; btn_magic.disabled = False; page.update()

    # --- DIALOGS ---
    def show_streak_dialog(e):
        days = []
        today = datetime.datetime.now()
        hist = history["login_history"]
        for d in range(1, calendar.monthrange(today.year, today.month)[1] + 1):
            ds = datetime.date(today.year, today.month, d).isoformat()
            bg = ft.Colors.GREEN_600 if ds in hist else ft.Colors.GREY_800
            border = ft.border.all(1, ft.Colors.WHITE) if d == today.day else None
            days.append(ft.Container(width=30, height=30, bgcolor=bg, border=border, border_radius=15, content=ft.Text(str(d), size=10), alignment=ft.alignment.center))
        dlg = ft.AlertDialog(title=ft.Row([ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE), ft.Text(f"{history['streak_count']} Day Streak")]), content=ft.Container(ft.Row(days, wrap=True, width=300, spacing=5), padding=10), actions=[ft.TextButton("Close", on_click=lambda e: page.close(dlg))])
        page.open(dlg)

    def show_stats_dialog(e):
        # --- 1. BAR CHART LOGIC (Existing) ---
        today = datetime.date.today()
        dates = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
        stats = history.get("daily_stats", {})
        
        rods = []
        x_labels = []
        max_y = 0
        
        for i, d in enumerate(dates):
            val = stats.get(d.isoformat(), 0)
            max_y = max(max_y, val)
            rods.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[ft.BarChartRod(
                        from_y=0, to_y=val, 
                        width=16, 
                        color=ft.Colors.CYAN, 
                        border_radius=ft.border_radius.vertical(top=5),
                        tooltip=f"{d.strftime('%d %b')}: {val} Tasks"
                    )]
                )
            )
            x_labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(d.strftime("%a"), size=10, color=ft.Colors.GREY_400)))

        chart = ft.BarChart(
            bar_groups=rods,
            bottom_axis=ft.ChartAxis(labels=x_labels),
            left_axis=ft.ChartAxis(labels_size=40),
            border=ft.border.all(1, ft.Colors.TRANSPARENT),
            horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_800, width=1, dash_pattern=[3, 3]),
            tooltip_bgcolor=ft.Colors.GREY_900,
            max_y=max(5, max_y + 2), 
            interactive=True,
            expand=True
        )

        # --- 2. HEATMAP LOGIC (New) ---
        # Calculate Start Date (approx 6 months ago, aligned to Sunday)
        start_date = today - datetime.timedelta(days=180)
        days_to_shift = (start_date.weekday() + 1) % 7
        current_date_iter = start_date - datetime.timedelta(days=days_to_shift)
        
        weeks_row = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=2)
        
        # Build Grid
        while current_date_iter <= today:
            week_col = ft.Column(spacing=2)
            for _ in range(7):
                date_str = current_date_iter.isoformat()
                count = stats.get(date_str, 0)
                
                # Color Coding
                cell_color = ft.Colors.GREY_900
                if count >= 5: cell_color = ft.Colors.AMBER_300   # High (Burning Gold)
                elif count >= 3: cell_color = ft.Colors.AMBER_600 # Medium
                elif count >= 1: cell_color = ft.Colors.AMBER_900 # Low
                
                # Future/Empty check
                if current_date_iter > today:
                    cell_color = ft.Colors.with_opacity(0.1, ft.Colors.GREY_900)
                    tooltip_text = None
                else:
                    tooltip_text = f"{date_str}: {count} Tasks"

                cell = ft.Container(
                    width=12, height=12, 
                    bgcolor=cell_color, 
                    border_radius=2,
                    tooltip=tooltip_text,
                    margin=1
                )
                week_col.controls.append(cell)
                current_date_iter += datetime.timedelta(days=1)
            
            weeks_row.controls.append(week_col)

        # --- 3. ASSEMBLY ---
        content_col = ft.Column([
            ft.Text("Weekly Performance", size=16, weight="bold"),
            ft.Container(chart, height=200),
            ft.Divider(height=20, color=ft.Colors.GREY_800),
            ft.Text("Consistency Map (Last 6 Months)", style=ft.TextStyle(font_family="Montserrat", weight="bold", size=16, color=ft.Colors.AMBER_500)),
            ft.Container(weeks_row, height=120, padding=5, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK), border_radius=10),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.CYAN), ft.Text("Productivity Stats")]),
            content=ft.Container(content_col, width=600, height=500), 
            actions=[ft.TextButton("Close", on_click=lambda e: page.close(dlg))]
        )
        page.open(dlg)

    def show_app_info(e):
        dlg = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.Icon(ft.Icons.DIAMOND_OUTLINED, size=50, color=ft.Colors.AMBER_500),
                    ft.Text("LEONIS", size=24, weight="bold", font_family="Montserrat"),
                    ft.Text("v6.0 - Stable Release", color=ft.Colors.GREY_500, size=12, font_family="Montserrat"),
                    
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    
                    # Developer Section
                    ft.Text("Developed by", font_family="Montserrat", color=ft.Colors.GREY_500),
                    ft.Text("Mustafa Bera Ekmekçi", font_family="Montserrat", weight="bold", size=20, color=ft.Colors.AMBER_500),
                    
                    ft.Divider(height=20, color=ft.Colors.GREY_800),
                    
                    # Copyright & Small Icons
                    ft.Text("© 2025 Leonis Inc. All rights reserved.", size=10, color=ft.Colors.GREY_600, font_family="Montserrat"),
                    ft.Row([
                        ft.IconButton(ft.Icons.CODE, tooltip="GitHub", url="https://github.com"), 
                        ft.IconButton(ft.Icons.PERSON_ADD, tooltip="LinkedIn", url="https://linkedin.com")
                    ], alignment=ft.MainAxisAlignment.CENTER),

                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                    # Contact Cards
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON, color=ft.Colors.AMBER_500),
                        title=ft.Text("Mustafa Bera Ekmekçi", weight="bold", font_family="Montserrat"),
                        subtitle=ft.Text("Developer & MIS Student", size=12, color=ft.Colors.GREY_500, font_family="Montserrat"),
                        trailing=ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=ft.Colors.BLUE_400),
                        on_click=lambda e: page.launch_url("https://www.linkedin.com/in/mustafa-bera-ekmekci/"),
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    ft.Container(height=5),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CODE, color=ft.Colors.GREY_300),
                        title=ft.Text("Mustafa Bera Ekmekçi", weight="bold", font_family="Montserrat"),
                        subtitle=ft.Text("GitHub Portfolio & Projects", size=12, color=ft.Colors.GREY_500, font_family="Montserrat"),
                        trailing=ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=ft.Colors.BLUE_400),
                        on_click=lambda e: page.launch_url("https://github.com/BeraEkmekci"),
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    )

                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=400, padding=10
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: page.close(dlg))]
        )
        page.open(dlg)

    def open_task_details(task):
        t_name = ft.TextField(label="Task", value=task["task"])
        t_notes = ft.TextField(label="Notes", value=task.get("notes", ""), multiline=True, min_lines=3)
        def save_details(e):
            task["task"] = t_name.value; task["notes"] = t_notes.value
            save_all(); page.close(bs); render_tasks()
        bs = ft.BottomSheet(ft.Container(ft.Column([ft.Text("Task Details", size=20, weight="bold"), t_name, t_notes, ft.ElevatedButton("Save", on_click=save_details, bgcolor=ft.Colors.INDIGO_ACCENT, color=ft.Colors.WHITE)], tight=True), padding=20, bgcolor=COLOR_CARD, border_radius=ft.border_radius.only(top_left=20, top_right=20)))
        page.open(bs)

    def show_tour_dialog(e):
        # Mutable state containers
        step_index = [0]
        dlg_handle = [] # To hold the dialog reference for the closure

        # UI Elements
        img_icon = ft.Icon(ft.Icons.DIAMOND, size=80, color=ft.Colors.AMBER)
        txt_title = ft.Text("Welcome", size=24, weight="bold", font_family="Montserrat", color=ft.Colors.WHITE)
        txt_desc = ft.Text("Description here...", size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        btn_next = ft.ElevatedButton("Start Tour", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK)

        # Content Container (Defined BEFORE dlg so we can update it)
        content_container = ft.Container(
            content=ft.Column([
                img_icon,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                txt_title,
                ft.Container(height=10),
                txt_desc,
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                btn_next
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            padding=40,
            width=400,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
            alignment=ft.alignment.center
        )
        
        # Step Data
        steps = [
            {
                "icon": ft.Icons.DIAMOND, "color": ft.Colors.AMBER, 
                "title": "Welcome to LEONIS", 
                "desc": "Your AI-powered productivity companion. Let's take a quick tour.",
                "btn": "Start Tour", "btn_icon": ft.Icons.ARROW_FORWARD
            },
            {
                "icon": ft.Icons.WORKSPACE_PREMIUM, "color": ft.Colors.AMBER,
                "title": "Rank Up",
                "desc": "Complete tasks to earn XP and unlock the 'Expert' badge.",
                "btn": "Next", "btn_icon": ft.Icons.ARROW_FORWARD
            },
            {
                "icon": ft.Icons.AUTO_AWESOME, "color": ft.Colors.PURPLE,
                "title": "AI Power",
                "desc": "Use the Magic Wand to break down complex missions automatically.",
                "btn": "Next", "btn_icon": ft.Icons.ARROW_FORWARD
            },
            {
                "icon": ft.Icons.GRID_ON, "color": ft.Colors.BLUE,
                "title": "Consistency",
                "desc": "Track your daily habits on the golden heatmap dashboard.",
                "btn": "Let's Go!", "btn_icon": ft.Icons.CHECK
            }
        ]

        def update_step_ui(do_update=True):
            s = steps[step_index[0]]
            img_icon.name = s["icon"]; img_icon.color = s["color"]
            txt_title.value = s["title"]
            txt_desc.value = s["desc"]
            btn_next.text = s["btn"]; btn_next.icon = s["btn_icon"]
            
            if do_update:
                content_container.update()

        def next_step(e):
            if step_index[0] < len(steps) - 1:
                step_index[0] += 1
                update_step_ui(do_update=True)
            else:
                if dlg_handle:
                    page.close(dlg_handle[0])

        btn_next.on_click = next_step
        
        # Initial Population (No update() call yet because it's not in tree)
        update_step_ui(do_update=False)

        dlg = ft.AlertDialog(
            content=content_container,
            modal=True,
            bgcolor=ft.Colors.GREY_900,
            shape=ft.RoundedRectangleBorder(radius=20)
        )
        dlg_handle.append(dlg) # Provide the reference
        page.open(dlg)

    def open_focus_mode(task_name):
        # State
        state = {"minutes": 25, "running": False}
        
        # THE TIMER TEXT (Clean, no letter_spacing)
        timer_text = ft.Text(
            "25:00", 
            size=80, 
            weight="bold", 
            font_family="Montserrat", 
            color=ft.Colors.AMBER_500
        )
        
        # Controls
        slider = ft.Slider(
            min=5, max=120, divisions=23, value=25, 
            label="{value} min", 
            active_color=ft.Colors.AMBER_500
        )

        def update_time_text(e):
            if not state["running"]:
                m = int(e.control.value)
                state["minutes"] = m
                timer_text.value = f"{m}:00"
                timer_text.update()
        
        slider.on_change = update_time_text # Bind manually to ensure closure access

        def run_timer(total_seconds):
            # Using dlg.open check carefully
            while total_seconds > 0 and state["running"]:
                mins, secs = divmod(total_seconds, 60)
                timer_text.value = "{:02d}:{:02d}".format(mins, secs)
                timer_text.update()
                time.sleep(1)
                total_seconds -= 1
            
            if total_seconds <= 0 and state["running"]:
                 timer_text.value = "DONE!"
                 timer_text.color = ft.Colors.GREEN_400
                 timer_text.update()

        def start_session(e):
            if state["running"]: return
            state["running"] = True
            
            # Update UI: Hide slider, show Stop button
            slider.visible = False
            start_btn.visible = False
            stop_btn.visible = True
            page.update()
            
            # Start background thread
            threading.Thread(target=run_timer, args=(state["minutes"] * 60,), daemon=True).start()

        def stop_session(e):
            state["running"] = False
            page.close(dlg)

        start_btn = ft.ElevatedButton("START FOCUS", bgcolor=ft.Colors.AMBER_700, color=ft.Colors.BLACK, on_click=start_session)
        stop_btn = ft.ElevatedButton("GIVE UP", bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE, visible=False, on_click=stop_session)

        # The Dialog Window
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.BLACK,
            content=ft.Column(
                controls=[
                    ft.Text("HYPER-FOCUS SETUP", color=ft.Colors.GREY_500), # Removed letter_spacing to fix crash
                    ft.Divider(color=ft.Colors.TRANSPARENT, height=10),
                    ft.Text(task_name, size=20, weight="bold", color=ft.Colors.WHITE, text_align="center"),
                    ft.Divider(color=ft.Colors.TRANSPARENT, height=30),
                    ft.Stack(
                        controls=[
                            ft.ProgressRing(width=250, height=250, stroke_width=5, color=ft.Colors.AMBER_500),
                            ft.Container(content=timer_text, alignment=ft.alignment.center, width=250, height=250)
                        ],
                        width=250, height=250
                    ),
                    ft.Divider(color=ft.Colors.TRANSPARENT, height=20),
                    slider, 
                    ft.Divider(color=ft.Colors.TRANSPARENT, height=20),
                    start_btn,
                    stop_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=550,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True
            )
        )
        page.open(dlg)

    def show_me_panel(e):
        # 1. Calc Rank Info
        xp = history["user_xp"]
        r_current, _, next_val = get_rank(xp)
        
        # 2. Content
        content = ft.Column([
            # — Profile Header —
            ft.ListTile(
                leading=ft.Icon(r_current["icon"], size=40, color=r_current["color"]),
                title=ft.Text(f"Mustafa ({r_current['title']})", size=18, weight="bold", color=ft.Colors.WHITE, font_family="Montserrat"),
                subtitle=ft.Text(f"XP: {xp} / {next_val}", color=ft.Colors.GREY_400),
            ),
            ft.Divider(color=ft.Colors.GREY_700),
            
            # — Settings —
            ft.Row([
                ft.Text("AI Persona: Formal", size=14, color=ft.Colors.GREY_300),
                ft.Switch(value=True, active_color=ft.Colors.PURPLE_400)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Row([
                ft.Text("Dark Mode Active", size=14, color=ft.Colors.GREY_300),
                ft.Switch(value=True, active_color=ft.Colors.AMBER_500)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.TextButton(
                "Manage Notifications", 
                icon=ft.Icons.NOTIFICATIONS_OUTLINED, 
                style=ft.ButtonStyle(color=ft.Colors.GREY_500)
            ),

            ft.Divider(color=ft.Colors.GREY_700),

            # — Footer —
            ft.TextButton(
                "Reset All Data", 
                icon=ft.Icons.DELETE_SWEEP_OUTLINED, 
                style=ft.ButtonStyle(color=ft.Colors.RED_400),
                on_click=lambda e: delete_all_tasks(e) # Re-using existing delete all function for now
            )
        ], tight=True, width=350)

        dlg = ft.AlertDialog(
            title=ft.Text("User Command Center", size=20, weight="bold", color=ft.Colors.AMBER_500, font_family="Montserrat"),
            content=ft.Container(content, bgcolor=ft.Colors.GREY_900, padding=10, border_radius=10),
            bgcolor=ft.Colors.GREY_900,
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.close(dlg), style=ft.ButtonStyle(color=ft.Colors.WHITE))
            ]
        )
        page.open(dlg)

    # --- CORE LOGIC ---
    def update_xp_ui():
        xp = history["user_xp"]
        r_current, prog, next_val = get_rank(xp)
        
        # Update UI
        txt_level_info.value = r_current["title"].upper()
        
        # ⚠️ İPTAL EDİLEN SATIR: txt_level_info.color = r_current["color"] 
        # Artık rengi değiştirmiyoruz, yukarıda tanımladığımız (Beyaz + Gölgeli) haliyle kalıyor.
        
        txt_xp_info.value = f"{xp} / {next_val} XP"
        
        # Animate Width
        xp_fill.width = 400 * prog
        
        txt_level_info.update()
        txt_xp_info.update()
        xp_fill.update()

    def toggle_done(task):
        today = datetime.date.today().isoformat()
        
        # Guard Clause: Time Lock for Future Tasks
        if task.get("date") and task["date"] > today:
            page.snack_bar = ft.SnackBar(ft.Text("🔒 Bu görev kilitli! Zamanı gelmesini bekleyin."), bgcolor=ft.Colors.RED_900)
            page.snack_bar.open = True; page.update()
            return

        # Standard Done Logic (First, mark this task as done)
        task["done"] = not task["done"]
        if "daily_stats" not in history: history["daily_stats"] = {}

        if task["done"]:
            # --- WEIGHTED XP LOGIC ---
            earned_xp = 50 # Base
            
            # Check conditions
            if "AI:" in task.get("notes", ""): earned_xp = 150
            elif task.get("priority") == "High": earned_xp = 100
            elif task.get("recurring"): earned_xp = 30
            
            history["user_xp"] += earned_xp
            history["total_completed"] += 1; confetti.fire()
            history["daily_stats"][today] = history["daily_stats"].get(today, 0) + 1
            
            # Feedback
            _, _, next_t = get_rank(history["user_xp"])
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Mission Complete! +{earned_xp} XP | Next Rank: {next_t}"), 
                bgcolor=ft.Colors.GREEN_900
            )
            page.snack_bar.open = True
            
            # --- CLONE STRATEGY FOR RECURRING TASKS ---
            if task.get("recurring"):
                # Create a fresh copy for tomorrow
                tomorrow = datetime.date.today() + datetime.timedelta(days=1)
                new_task = {
                    "id": str(uuid.uuid4()),
                    "task": task["task"],
                    "priority": task["priority"],
                    "category": task["category"],
                    "done": False,
                    "date": tomorrow.isoformat(),
                    "recurring": True,
                    "notes": "🔄 Previous streak kept. " + task.get("notes", "")
                }
                tasks.append(new_task)

        else: 
            history["user_xp"] = max(0, history["user_xp"] - 50) # Penalize base
            cur = history["daily_stats"].get(today, 0)
            if cur > 0: history["daily_stats"][today] = cur - 1
            
        save_all(); update_xp_ui(); render_tasks()

    def delete_task(task):
        for i, t in enumerate(tasks):
             if t["id"] == task["id"]: tasks.pop(i); break
        save_all(); render_tasks()
    
    def delete_all_tasks(e):
        tasks.clear(); save_all(); render_tasks()
        
    def select_all_tasks(e):
        count = 0
        for t in tasks:
            if not t["done"]:
                t["done"] = True
                count += 1
        
        if count > 0:
            earned_xp = count * 10
            history["user_xp"] += earned_xp
            history["total_completed"] += count
            confetti.fire()
            
            # Update daily stats
            today = datetime.date.today().isoformat()
            if "daily_stats" not in history: history["daily_stats"] = {}
            history["daily_stats"][today] = history["daily_stats"].get(today, 0) + count
            
            page.snack_bar = ft.SnackBar(ft.Text(f"🦁 {count} tasks completed! +{earned_xp} XP earned"), bgcolor=ft.Colors.GREEN_900)
            page.snack_bar.open = True
            
            save_all(); update_xp_ui(); render_tasks()

    def add_task(e):
        if not field_task.value: return
        tasks.append({
            "id": str(uuid.uuid4()), "task": field_task.value, "priority": priority_val[0],
            "category": category_val[0], "done": False, "notes": "", 
            "date": datetime.date.today().isoformat(),
            "recurring": is_recurring_mode[0]
        })
        # Reset recurring toggle after adding? Or keep it? keeping it might be better for bulk entry.
        # Let's keep it for now as per "mode" implication.

        field_task.value = ""; save_all(); history["user_xp"] += 5; update_xp_ui(); render_tasks()

    def toggle_view(e):
        view_mode[0] = "matrix" if view_mode[0] == "list" else "list"
        e.control.icon = ft.Icons.LIST if view_mode[0] == "matrix" else ft.Icons.GRID_VIEW
        e.control.update(); render_tasks()

    def create_task_card(task):
        c = {"High": COLOR_HIGH, "Medium": COLOR_MED, "Low": COLOR_LOW, "None": COLOR_NONE}.get(task.get("priority"), COLOR_MED)
        today_date = datetime.date.today().isoformat()
        
        label_text = task["task"]
        is_future = task.get("date") > today_date if task.get("date") else False
        
        chk_disabled = False
        chk_sub = None
        
        if is_future:
            chk_disabled = True
            label_text += " (🔒 Yarın)"
        
        if task.get("notes"): 
            chk_sub = ft.Text("Has notes...", size=10, italic=True, color=ft.Colors.GREY_500)

        chk = ft.Checkbox(
            value=task["done"], 
            label=label_text, 
            active_color=ft.Colors.INDIGO_ACCENT, 
            disabled=chk_disabled,
            on_change=lambda e, t=task: toggle_done(t)
        )
        
        if task["done"]: 
            chk.label_style = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH, color=ft.Colors.GREY_600)
        elif is_future:
            chk.label_style = ft.TextStyle(color=ft.Colors.GREY_700) 
        
        if chk_sub: chk.subtitle = chk_sub

        controls_row = [ft.Container(width=4, height=30, bgcolor=c, border_radius=2), chk]
        if task.get("recurring"):
            controls_row.insert(1, ft.Icon(ft.Icons.REPEAT, size=14, color=ft.Colors.GREY_600))

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Row(controls_row),
                    ft.Row([
                        ft.IconButton(ft.Icons.PLAY_CIRCLE_FILLED_OUTLINED, icon_color=ft.Colors.AMBER_400, tooltip="Start Focus Mode", on_click=lambda e, t=task["task"]: open_focus_mode(t)),
                        ft.IconButton(ft.Icons.EDIT, icon_color=COLOR_CYAN, on_click=lambda e, t=task: open_task_details(t)),
                        ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_300, on_click=lambda e, t=task: delete_task(t))
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15
            ),
            color=ft.Colors.GREY_900,
            elevation=5,
            shape=ft.RoundedRectangleBorder(radius=15),
            margin=ft.margin.only(bottom=10)
        )

    def render_tasks(e=None):
        tasks_container.controls.clear()
        
        # 0. Empty State
        if not tasks:
            ai_input_field = ft.TextField(
                hint_text="e.g., Generate a study plan for the MIS final exam and break it into weekly tasks.",
                hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
                multiline=True,
                min_lines=3,
                max_lines=5,
                border=ft.InputBorder.OUTLINE,
                border_color=ft.Colors.AMBER_700,
                text_style=ft.TextStyle(font_family="Montserrat", color=ft.Colors.WHITE),
                cursor_color=ft.Colors.AMBER,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
            )

            def animate_console(e):
                is_hovering = e.data == "true"
                if is_hovering:
                    console_box.border = ft.border.all(2, ft.Colors.AMBER_400)
                else:
                    console_box.border = ft.border.all(1, ft.Colors.GREY_700)
                console_box.update()

            console_box = ft.Container(
                content=ft.Column([
                    ft.Text("WHAT'S THE NEXT MISSION?", size=22, weight="bold", color=ft.Colors.AMBER_500, font_family="Montserrat"),
                    ft.Divider(height=15, color=ft.Colors.GREY_800),
                    ai_input_field,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "AI START GENERATION", 
                        icon=ft.Icons.ROCKET_LAUNCH, 
                        bgcolor=ft.Colors.PURPLE_500, 
                        color=ft.Colors.WHITE, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=15),
                        on_click=lambda e: generate_ai_subtasks(None, override_prompt=ai_input_field.value)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
                border_radius=25,
                border=ft.border.all(1, ft.Colors.GREY_700),
                padding=40,
                margin=ft.margin.symmetric(horizontal=50 if page.window_width > 600 else 20),
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK), spread_radius=5),
                on_hover=animate_console,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
            )

            tasks_container.controls.append(ft.Container(console_box, alignment=ft.alignment.center, margin=ft.margin.only(top=50)))
            page.update()
            return

        # 1. Segmentation Logic
        priority_tasks = []
        habit_tasks = []
        pending_tasks = []
        completed_tasks = []

        for t in reversed(tasks): # Reversed to show newest first generally
            if t["done"]:
                completed_tasks.append(t)
            elif t.get("priority") == "High":
                priority_tasks.append(t)
            elif t.get("recurring"):
                habit_tasks.append(t)
            else:
                pending_tasks.append(t)

        # 2. Section Helper
        def add_section(title, task_list, icon=None, color=ft.Colors.AMBER_500):
            if not task_list: return
            
            # Header
            header = ft.Row([
                ft.Text(title, font_family="Montserrat", size=18, weight="bold", color=color)
            ], spacing=10)
            if icon: header.controls.insert(0, ft.Icon(icon, color=color, size=20))
            
            tasks_container.controls.append(ft.Container(content=header, margin=ft.margin.only(top=25, bottom=10)))
            
            # Tasks
            for t in task_list:
                tasks_container.controls.append(create_task_card(t))

        # 3. Render Sections
        add_section("Priority Missions", priority_tasks, ft.Icons.LOCAL_FIRE_DEPARTMENT, ft.Colors.RED_ACCENT)
        add_section("Habit Missions", habit_tasks, ft.Icons.UPDATE, ft.Colors.BLUE_ACCENT)
        add_section("Pending Missions", pending_tasks, ft.Icons.ASSIGNMENT, ft.Colors.WHITE)
        add_section("Completed", completed_tasks, ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_400)

        page.update()

    # --- UI ASSEMBLY ---
    # --- UI ASSEMBLY ---
    app_header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.DIAMOND_OUTLINED, color=ft.Colors.AMBER, size=26),
                ft.Text("LEONIS", style=ft.TextStyle(font_family="Montserrat", weight=ft.FontWeight.BOLD, letter_spacing=1.5, size=24, color=ft.Colors.WHITE))
            ], spacing=10),
            ft.Row([
                ft.IconButton(ft.Icons.GRID_VIEW, on_click=toggle_view, tooltip="View Mode"),
                ft.IconButton(ft.Icons.BAR_CHART, on_click=show_stats_dialog, icon_color=ft.Colors.CYAN, tooltip="Weekly Stats"),
                ft.IconButton(ft.Icons.LOCAL_FIRE_DEPARTMENT, on_click=show_streak_dialog, icon_color=ft.Colors.ORANGE, tooltip="Streak"),
                ft.IconButton(ft.Icons.HELP_OUTLINE, on_click=show_tour_dialog, tooltip="Quick Guide"),
                ft.IconButton(ft.Icons.INFO_OUTLINE, on_click=show_app_info, tooltip="Info"),
                ft.IconButton(ft.Icons.WORKSPACE_PREMIUM, on_click=lambda e: toggle_tribute_screen(True), icon_color=ft.Colors.AMBER, tooltip="Atatürk Köşesi"),
                ft.Container(
                    content=ft.CircleAvatar(
                        radius=16, 
                        bgcolor=ft.Colors.GREY_900, 
                        content=ft.Text("ME", weight="bold", color=ft.Colors.CYAN)
                    ),
                    padding=3,
                    border=ft.border.all(2, ft.Colors.CYAN),
                    shape=ft.BoxShape.CIRCLE,
                    on_click=lambda e: show_me_panel(e),
                    tooltip="User Command Center"
                ),
                ft.Container(width=10)
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=10, vertical=10)
    )



    # --- GAMING XP BAR ---
    MAX_BAR_WIDTH = 400

    xp_track = ft.Container(
        width=MAX_BAR_WIDTH, height=35, bgcolor=ft.Colors.BLACK,
        border=ft.border.all(1, ft.Colors.GREY_800), border_radius=20
    )

    xp_fill = ft.Container(
        width=0, height=35, border_radius=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=[
                "#5B3D7F", # Deep Violet-Purple
                "#D8AE33", # Rich, Deep Gold
                "#FFEB3B"  # Bright Gold Highlight
            ],
        ),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.ORANGE_900),
        animate=ft.Animation(1000, ft.AnimationCurve.EASE_OUT_CUBIC)
    )
    
    txt_level_info = ft.Text(
        "NOVICE", 
        style=ft.TextStyle(
            font_family="Montserrat", 
            weight=ft.FontWeight.W_900, 
            color=ft.Colors.WHITE, 
            size=14,
            shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK, offset=ft.Offset(1, 1))
        )
    )
    txt_xp_info = ft.Text(
        "0 / 100 XP", 
        font_family="Roboto Mono", 
        weight=ft.FontWeight.BOLD,
        size=12,
        color=ft.Colors.WHITE,
        style=ft.TextStyle(shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK, offset=ft.Offset(1, 1)))
    )
    
    xp_overlay = ft.Container(
        content=ft.Row([
            ft.Row([ft.Icon(ft.Icons.WORKSPACE_PREMIUM, color=ft.Colors.WHITE), txt_level_info], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            txt_xp_info
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, width=MAX_BAR_WIDTH),
        padding=ft.padding.symmetric(horizontal=15), height=35, alignment=ft.alignment.center
    )

    xp_stack = ft.Stack([xp_track, xp_fill, xp_overlay], width=MAX_BAR_WIDTH, height=35)
    xp_container = ft.Container(content=xp_stack, padding=10, alignment=ft.alignment.center)

    # --- INPUT AREA ---
    priority_val = ["Medium"]
    category_val = ["Personal"]
    is_recurring_mode = [False]
    
    txt_priority = ft.Text("Medium", color=COLOR_MED, weight="bold", size=12, visible=False) # Hidden but kept for any legacy ref I might have missed, or just safe removal. Actually, logic below doesn't use it.
    # Safe to remove txt_priority if I update rotate_prio.

    def rotate_prio(e):
        p = priority_val[0]
        if p == "Medium": priority_val[0] = "High"
        elif p == "High": priority_val[0] = "Low"
        elif p == "Low": priority_val[0] = "None"
        else: priority_val[0] = "Medium"
        
        new_c = {"High": COLOR_HIGH, "Medium": COLOR_MED, "Low": COLOR_LOW, "None": ft.Colors.GREY_500}[priority_val[0]]
        e.control.icon_color = new_c
        e.control.tooltip = f"Priority: {priority_val[0]}"
        e.control.update()

    def rotate_cat(e):
        order = ["Personal", "Work", "School"]; category_val[0] = order[(order.index(category_val[0])+1)%3]
        icons = {"Personal": ft.Icons.HOME, "Work": ft.Icons.WORK, "School": ft.Icons.SCHOOL}
        e.control.icon = icons[category_val[0]]; e.control.update()

    def toggle_recurring(e):
        is_recurring_mode[0] = not is_recurring_mode[0]
        e.control.icon_color = ft.Colors.AMBER_400 if is_recurring_mode[0] else ft.Colors.GREY_500
        e.control.tooltip = "Recurring: ON" if is_recurring_mode[0] else "Recurring"
        e.control.update()

    field_task = ft.TextField(
        hint_text="Add a new mission...", 
        hint_style=ft.TextStyle(font_family="Montserrat", color=ft.Colors.GREY_600),
        text_style=ft.TextStyle(font_family="Montserrat", size=16, color=ft.Colors.WHITE),
        border=ft.InputBorder.NONE,
        expand=True,
        on_submit=add_task
    )

    btn_magic = ft.IconButton(ft.Icons.AUTO_AWESOME, icon_color=ft.Colors.PURPLE_300, tooltip="AI Assistant", on_click=generate_ai_subtasks)

    input_area = ft.Container(
        content=ft.Row([
            field_task, 
            ft.Row([
                btn_magic, 
                ft.IconButton(ft.Icons.UPDATE, icon_color=ft.Colors.GREY_500, tooltip="Recurring Task", on_click=toggle_recurring),
                ft.IconButton(ft.Icons.FLAG_OUTLINED, icon_color=COLOR_MED, tooltip="Set Priority", on_click=rotate_prio),
                ft.Container(width=5),
                ft.Container(
                    content=ft.Icon(ft.Icons.ADD, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.AMBER_600,
                    tooltip="Add Mission",
                    shape=ft.BoxShape.CIRCLE,
                    width=45, height=45,
                    alignment=ft.alignment.center,
                    on_click=add_task,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.5, ft.Colors.AMBER_900)),
                    # A container on_click? Flet Containers have on_click.
                    ink=True,
                )
            ], spacing=0)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
        bgcolor=ft.Colors.GREY_900,
        border_radius=30,
        padding=ft.padding.only(left=20, right=5, top=5, bottom=5),
        border=ft.border.all(1, ft.Colors.GREY_800),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), spread_radius=1)
    )

    bulk_actions = ft.Row([
        ft.TextButton("Hepsini Seç", icon=ft.Icons.CHECK_CIRCLE_OUTLINE, on_click=select_all_tasks, style=ft.ButtonStyle(color=ft.Colors.GREY_500)),
        ft.TextButton("Temizle", icon=ft.Icons.DELETE_SWEEP, on_click=delete_all_tasks, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
    ], alignment=ft.MainAxisAlignment.END)

    main_view.controls = [xp_container, ft.Divider(height=10, color=ft.Colors.TRANSPARENT), input_area, bulk_actions, tasks_container]
    
    main_container = ft.Container(
        expand=True,
        gradient=ft.RadialGradient(
            center=ft.Alignment(0, -0.3),
            radius=1.8,
            colors=[
                "#262b36", # Center: Deep Blue-Grey (Subtle light)
                "#121212", # Mid: Very Dark Grey
                "#000000", # Edge: Pure Black
            ],
        ),
        padding=20,
        content=ft.Column(
            controls=[
                app_header,
                main_view,
                tribute_view
            ],
            scroll=ft.ScrollMode.AUTO
        )
    )

    page.add(main_container)
    
    update_xp_ui(); render_tasks(); page.on_resized = lambda e: render_tasks()
    show_tour_dialog(None)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")