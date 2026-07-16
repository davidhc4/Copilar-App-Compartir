# -*- coding: utf-8 -*-
import asyncio
import json
import os
import uuid
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import flet as ft

# ============================================================
# CONFIGURACIÓN DE PARTICIPANTES (SOLO CAMBIA ESTO)
# ============================================================
PARTICIPANTE_1 = "David"   # ← Cambia aquí
PARTICIPANTE_2 = "Santiago"      # ← Cambia aquí
# ============================================================

NOMBRE_RETO = f"{PARTICIPANTE_1} vs {PARTICIPANTE_2}"
ARCHIVO_DATOS = f"deuda_{PARTICIPANTE_1.lower()}_{PARTICIPANTE_2.lower()}.json"
APP_NAME = f"Deuda Gym - {NOMBRE_RETO}"
APP_VERSION = "1.8.0"
MINUTE_PRICE = 500
FIXED_FINE = 5000
ALERT_LIMIT = 50000

C = ft.Colors
I = ft.Icons
CENTER = ft.Alignment(0, 0)

MONTHS = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
}

# ========== FRASES MOTIVACIONALES POR DÍA (con tu numeración) ==========
def frase_del_dia():
    hoy = datetime.now()
    # Convertir a tu numeración: 1=Lunes, 2=Martes, ..., 7=Domingo
    dia_semana = hoy.weekday() + 1

    # Todas las frases organizadas por día (usando tu numeración)
    frases = [
        # LUNES (1)
        f"¡Lunes de cobrar esa deuda! 💪",
        f"La deuda no espera ni los lunes, ¡cóbrala ahora! 🚀",
        f"La perseverancia cobra los lunes. 💋",

        # MARTES (2)
        f"Cada peso cuenta, más un martes y {PARTICIPANTE_1} lo sabe. 💰",
        f"Hoy es martes de cobro. 😈",

        # MIÉRCOLES (3)
        f"Recuérdale a {PARTICIPANTE_1} que hoy miércoles pague lo que debe. 😤",
        f"No olvides que aparte de ser miércoles, {PARTICIPANTE_1} te debe. 💢",

        # JUEVES (4)
        f"¡No dejes que la deuda crezca un jueves! 📈",
        f"La deuda crece como la marihuana y más hoy jueves, ¡arráncala! 🍃",

        # VIERNES (5)
        f"Un viernes sin cobrar es un día perdido. ⏰",
        f"{PARTICIPANTE_1}, hoy es viernes de no hacerse el mk. 💀",

        # SÁBADO (6)
        f"El dinero llama y más un sábado como hoy, ¿lo escuchas? 🔔",
        f"El que debe, paga con el culo. 😻",

        # DOMINGO (7)
        f"{PARTICIPANTE_2}, ¿crees que un domingo sin plata es domingo? 💸",
        f"Tu dinero está en manos de {PARTICIPANTE_1}, ¡recupéralo antes del lunes! 🤝",
    ]

    # Filtrar correctamente las frases según el día (con tu numeración)
    frases_del_dia = []
    for frase in frases:
        if dia_semana == 1 and "lunes" in frase.lower():
            frases_del_dia.append(frase)
        elif dia_semana == 2 and "martes" in frase.lower():
            frases_del_dia.append(frase)
        elif dia_semana == 3 and ("miércoles" in frase.lower() or "miercoles" in frase.lower()):
            frases_del_dia.append(frase)
        elif dia_semana == 4 and "jueves" in frase.lower():
            frases_del_dia.append(frase)
        elif dia_semana == 5 and "viernes" in frase.lower():
            frases_del_dia.append(frase)
        elif dia_semana == 6 and ("sábado" in frase.lower() or "sabado" in frase.lower()):
            frases_del_dia.append(frase)
        elif dia_semana == 7 and "domingo" in frase.lower():
            frases_del_dia.append(frase)

    # Si hay frases para hoy, elige una aleatoria
    if frases_del_dia:
        random.seed(hoy.strftime("%Y-%m-%d"))  # Siempre la misma frase por día
        return random.choice(frases_del_dia)
    else:
        return "¡Cobra esa deuda! 💪"  # Frase de respaldo

# ========== FUNCIONES AUXILIARES ==========
def pad(left=0, top=0, right=0, bottom=0):
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)

def money(value):
    return f"${int(value):,}".replace(",", ".")

def today_iso():
    return datetime.now().strftime("%Y-%m-%d")

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def app_data_dir():
    base = (
        os.getenv("FLET_APP_STORAGE_DATA")
        or os.getenv("APPDATA")
        or os.getenv("LOCALAPPDATA")
        or str(Path.home())
    )
    path = Path(base) / "deuda_gym"
    path.mkdir(parents=True, exist_ok=True)
    return path

def month_title(month_key):
    year, month = month_key.split("-")
    return f"{MONTHS.get(month, month)} {year}"

# ========== ALMACENAMIENTO ==========
class Store:
    def __init__(self):
        self.data_file = app_data_dir() / ARCHIVO_DATOS
        self.config_file = app_data_dir() / "config.json"
        self.records = []
        self.settings = {
            "dark_mode": False,
            "notifications": True,
            "reminder_time": "04:40",
            "last_alert_level": 0,
        }
        self.load()

    def load(self):
        self.records = self.load_records()
        self.settings.update(self.load_settings())

    def load_records(self):
        if not self.data_file.exists():
            return []
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = raw.get("records", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return []
        records = []
        for item in items:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind") or "minutes"
            if kind == "minutos":
                kind = "minutes"
            if kind == "multa":
                kind = "fine"
            amount = item.get("amount", 0)
            minutes = item.get("minutes")
            date = item.get("date") or today_iso()
            created_at = item.get("created_at") or f"{date}T00:00:00"
            try:
                amount = int(amount)
            except Exception:
                amount = 0
            try:
                minutes = None if minutes is None else int(minutes)
            except Exception:
                minutes = None
            records.append({
                "id": str(item.get("id") or uuid.uuid4()),
                "date": str(date)[:10],
                "created_at": str(created_at),
                "kind": kind,
                "minutes": minutes,
                "amount": amount,
            })
        return records

    def load_settings(self):
        if not self.config_file.exists():
            return {}
        try:
            raw = json.loads(self.config_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return {
            "dark_mode": bool(raw.get("dark_mode", False)),
            "notifications": bool(raw.get("notifications", True)),
            "reminder_time": str(raw.get("reminder_time", "04:40")),
            "last_alert_level": int(raw.get("last_alert_level", 0)),
        }

    def save_records(self):
        self.data_file.write_text(
            json.dumps({"records": self.records}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_settings(self):
        self.config_file.write_text(
            json.dumps(self.settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_minutes(self, minutes, date=None):
        if minutes < 0:
            raise ValueError("No se permiten minutos negativos.")
        if minutes > 1440:
            raise ValueError("No pueden ser más de 1440 minutos.")
        amount = minutes * MINUTE_PRICE
        date_str = date or today_iso()
        self.records.append({
            "id": str(uuid.uuid4()),
            "date": date_str,
            "created_at": now_iso(),
            "kind": "participante1",
            "minutes": minutes,
            "amount": amount,
        })
        self.save_records()
        return amount

    def add_user_minutes(self, minutes, date=None):
        if minutes < 0:
            raise ValueError("No se permiten minutos negativos.")
        if minutes > 1440:
            raise ValueError("No pueden ser más de 1440 minutos.")
        amount = - (minutes * MINUTE_PRICE)
        date_str = date or today_iso()
        self.records.append({
            "id": str(uuid.uuid4()),
            "date": date_str,
            "created_at": now_iso(),
            "kind": "participante2",
            "minutes": minutes,
            "amount": amount,
        })
        self.save_records()
        return amount

    def add_fine(self, date=None):
        date_str = date or today_iso()
        self.records.append({
            "id": str(uuid.uuid4()),
            "date": date_str,
            "created_at": now_iso(),
            "kind": "fine",
            "minutes": None,
            "amount": FIXED_FINE,
        })
        self.save_records()
        return FIXED_FINE

    def add_fine_participante2(self, date=None):
        date_str = date or today_iso()
        self.records.append({
            "id": str(uuid.uuid4()),
            "date": date_str,
            "created_at": now_iso(),
            "kind": "fine_participante2",
            "minutes": None,
            "amount": -FIXED_FINE,
        })
        self.save_records()
        return -FIXED_FINE

    def delete_record(self, record_id):
        self.records = [r for r in self.records if r["id"] != record_id]
        self.save_records()

    def clear_all(self):
        self.records = []
        self.save_records()

    def sorted_records(self):
        return sorted(
            self.records,
            key=lambda r: (r.get("date", ""), r.get("created_at", "")),
            reverse=True,
        )

    def total(self):
        return sum(int(r.get("amount", 0)) for r in self.records)

    def total_today(self):
        today = today_iso()
        return sum(int(r.get("amount", 0)) for r in self.records if r.get("date") == today)

    def daily_totals(self):
        totals = defaultdict(int)
        for r in self.records:
            totals[r["date"]] += int(r["amount"])
        return dict(totals)

    def monthly_totals(self):
        totals = defaultdict(int)
        for r in self.records:
            totals[r["date"][:7]] += int(r["amount"])
        return dict(sorted(totals.items()))

    def stats(self):
        daily = self.daily_totals()
        values = list(daily.values())
        fines = sum(1 for r in self.records if r.get("kind") == "fine")
        p1_days = sum(1 for r in self.records if r.get("kind") == "participante1")
        p2_days = sum(1 for r in self.records if r.get("kind") == "participante2")
        return {
            "days": len(daily),
            "avg": int(sum(values) / len(values)) if values else 0,
            "max": max(values) if values else 0,
            "fines": fines,
            "p1_days": p1_days,
            "p2_days": p2_days,
        }

    def get_alert_level(self):
        total = self.total()
        if total <= 0:
            return 0
        return (total // ALERT_LIMIT) * ALERT_LIMIT

    def should_alert(self):
        current_level = self.get_alert_level()
        last_level = self.settings.get("last_alert_level", 0)
        return current_level > 0 and current_level > last_level

    def update_alert_level(self):
        self.settings["last_alert_level"] = self.get_alert_level()
        self.save_settings()

# ========== APLICACIÓN PRINCIPAL ==========
class DeudaGymApp:
    def __init__(self, page):
        self.page = page
        self.store = Store()
        self.root = ft.Container(expand=True)
        self.minutes_field = None
        self.user_minutes_field = None
        self.reminder_field = None
        self.last_reminder_date = ""
        self.selected_date = today_iso()
        self.bubble_container = None

    @property
    def dark(self):
        return self.store.settings["dark_mode"]

    @property
    def bg(self):
        return C.GREY_900 if self.dark else C.GREY_50

    @property
    def card_bg(self):
        return C.GREY_800 if self.dark else C.WHITE

    @property
    def text_color(self):
        return C.WHITE if self.dark else C.BLACK

    @property
    def muted_color(self):
        return C.GREY_400 if self.dark else C.GREY_600

    @property
    def soft_bg(self):
        return C.GREY_700 if self.dark else C.GREY_100

    def run(self):
        self.configure_page()
        self.root.content = self.main_view()
        self.page.add(self.root)
        self.page.run_task(self.reminder_loop)
        self.page.run_task(self.check_alerts_loop)

    def configure_page(self):
        self.page.title = APP_NAME
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.bgcolor = self.bg
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark else ft.ThemeMode.LIGHT
        try:
            self.page.window.width = 420
            self.page.window.height = 860
            self.page.window.min_width = 340
            self.page.window.min_height = 620
        except Exception:
            self.page.window_width = 420
            self.page.window_height = 860
            self.page.window_min_width = 340
            self.page.window_min_height = 620

    def refresh(self):
        self.page.bgcolor = self.bg
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark else ft.ThemeMode.LIGHT
        self.root.content = self.main_view()
        self.page.update()

    # ========== CONTROLES DE DIÁLOGO ==========
    def open_control(self, control):
        try:
            if isinstance(control, ft.SnackBar):
                self.page.snack_bar = control
            elif isinstance(control, ft.AlertDialog):
                self.page.dialog = control
            else:
                self.page.overlay.append(control)
            control.open = True
            self.page.update()
        except Exception as e:
            print(f"Error opening control: {e}")

    def close_control(self, control):
        try:
            control.open = False
            self.page.update()
        except Exception as e:
            print(f"Error closing control: {e}")

    def snack(self, message, error=False):
        self.open_control(
            ft.SnackBar(
                content=ft.Text(message, color=C.WHITE),
                bgcolor=C.RED_600 if error else C.GREEN_600,
                behavior=ft.SnackBarBehavior.FLOATING,
                duration=2200,
            )
        )

    def dialog(self, title, message, actions=None):
        dialog_box = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=actions or [],
        )
        if actions is None:
            dialog_box.actions = [
                ft.Button("OK", on_click=lambda e: self.close_control(dialog_box))
            ]
        self.open_control(dialog_box)
        return dialog_box

    # ========== BURBUJA MOTIVACIONAL COMPACTA ==========
    def show_motivational_bubble(self, frase):
        overlay = ft.Container(
            expand=True,
            bgcolor=C.with_opacity(0.3, C.BLACK),
            alignment=CENTER,
            padding=20,
        )

        bubble = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=I.CLOSE,
                                icon_color=C.WHITE,
                                icon_size=20,
                                on_click=lambda e: self.close_motivational_bubble(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(
                        content=ft.Text(
                            frase,
                            size=18,
                            color=C.WHITE,
                            text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.W_500,
                        ),
                        padding=ft.Padding(left=20, top=0, right=20, bottom=20),
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            bgcolor=C.BLUE_600,
            border_radius=20,
            padding=ft.Padding(left=0, top=5, right=0, bottom=5),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=C.with_opacity(0.3, C.BLACK),
                offset=ft.Offset(0, 8),
            ),
            width=None,
            height=None,
        )

        overlay.content = bubble
        self.bubble_container = overlay
        self.page.overlay.append(overlay)
        self.page.update()

    def close_motivational_bubble(self):
        if self.bubble_container:
            self.page.overlay.remove(self.bubble_container)
            self.bubble_container = None
            self.page.update()

    # ========== NOTIFICACIONES (SnackBar) ==========
    async def show_notification(self, title, body):
        snack = ft.SnackBar(
            content=ft.Text(f"{title}: {body}", color=C.WHITE),
            bgcolor=C.BLUE_600,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=5000,
        )
        self.page.snack_bar = snack
        snack.open = True
        self.page.update()
        await asyncio.sleep(0.5)

    async def bounce(self, control):
        try:
            control.scale = 0.96
            self.page.update()
            await asyncio.sleep(0.07)
            control.scale = 1
            self.page.update()
        except Exception:
            pass

    def shadow(self):
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=18,
            color=C.with_opacity(0.10, C.BLACK),
            offset=ft.Offset(0, 6),
        )

    def card(self, content, padding=16, animate=True):
        if animate:
            anim = ft.Animation(400, curve=ft.AnimationCurve.EASE_OUT)
        else:
            anim = None
        return ft.Container(
            content=content,
            padding=padding,
            bgcolor=self.card_bg,
            border_radius=18,
            shadow=self.shadow(),
            animate=anim,
        )

    def primary_button(self, text, icon, color, on_click):
        return ft.Button(
            text,
            icon=icon,
            bgcolor=color,
            color=C.WHITE,
            height=52,
            elevation=2,
            animate_scale=ft.Animation(140, curve=ft.AnimationCurve.EASE_OUT),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=18),
                padding=pad(14, 12, 14, 12),
            ),
            on_click=on_click,
        )

    def stat_card(self, title, value, color, icon):
        return self.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=18),
                            ft.Text(title, size=12, color=self.muted_color),
                        ],
                        spacing=6,
                    ),
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=color),
                ],
                spacing=8,
            ),
            animate=True,
        )

    # ========== SELECTOR DE FECHA ==========
    def open_date_picker(self, e):
        def on_date_change(e):
            if e.control.value:
                self.selected_date = e.control.value.strftime("%Y-%m-%d")
                self.date_field.value = self.selected_date
                self.date_field.update()
                self.snack(f"Fecha seleccionada: {self.selected_date}")

        date_picker = ft.DatePicker(on_change=on_date_change)
        self.page.overlay.append(date_picker)
        date_picker.open = True
        self.page.update()

    def update_date_from_text(self, e):
        raw = (self.date_field.value or "").strip()
        if raw == "":
            self.selected_date = today_iso()
            self.date_field.value = self.selected_date
            self.date_field.update()
            return
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            self.selected_date = raw
            self.snack(f"Fecha actualizada: {self.selected_date}")
        except ValueError:
            self.snack("Formato inválido. Usa YYYY-MM-DD", True)
            self.date_field.value = self.selected_date
            self.date_field.update()

    # ========== VISTA PRINCIPAL ==========
    def main_view(self):
        total = self.store.total()
        today = self.store.total_today()
        frase = frase_del_dia()

        self.minutes_field = ft.TextField(
            hint_text=PARTICIPANTE_1,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=18,
            filled=True,
            bgcolor=self.card_bg,
            border_color=C.TRANSPARENT,
            text_style=ft.TextStyle(color=self.text_color),
            hint_style=ft.TextStyle(color=self.muted_color),
            prefix_icon=I.PERSON,
            on_submit=self.add_minutes,
            width=150,
        )

        self.user_minutes_field = ft.TextField(
            hint_text=PARTICIPANTE_2,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=18,
            filled=True,
            bgcolor=self.card_bg,
            border_color=C.TRANSPARENT,
            text_style=ft.TextStyle(color=self.text_color),
            hint_style=ft.TextStyle(color=self.muted_color),
            prefix_icon=I.PERSON_OUTLINE,
            on_submit=self.add_user_minutes,
            width=150,
        )

        self.date_field = ft.TextField(
            value=self.selected_date,
            hint_text="YYYY-MM-DD",
            border_radius=18,
            filled=True,
            bgcolor=self.card_bg,
            border_color=C.TRANSPARENT,
            text_style=ft.TextStyle(color=self.text_color),
            hint_style=ft.TextStyle(color=self.muted_color),
            prefix_icon=I.CALENDAR_TODAY,
            on_submit=self.update_date_from_text,
            expand=True,
        )
        date_button = ft.IconButton(
            icon=I.EVENT,
            icon_color=C.BLUE_600,
            tooltip="Seleccionar fecha",
            on_click=self.open_date_picker,
        )

        frase_button = ft.IconButton(
            icon=I.LIGHTBULB,
            icon_color=C.ORANGE_600,
            tooltip="Frase del día",
            on_click=lambda e: self.show_motivational_bubble(frase),
        )

        add_p1_button = self.primary_button(
            f"Agregar {PARTICIPANTE_1}",
            I.ADD,
            C.RED_600,
            self.add_minutes,
        )

        add_p2_button = self.primary_button(
            f"Agregar {PARTICIPANTE_2}",
            I.REMOVE,
            C.GREEN_600,
            self.add_user_minutes,
        )

        fine_button = self.primary_button(
            f"Multa 5.000 ({PARTICIPANTE_1})",
            I.WARNING_AMBER,
            C.RED_600,
            self.add_fine,
        )

        fine_p2_button = self.primary_button(
            f"Multa 5.000 ({PARTICIPANTE_2})",
            I.WARNING_AMBER,
            C.ORANGE_600,
            self.add_fine_participante2,
        )

        return ft.Container(
            bgcolor=self.bg,
            padding=pad(16, 18, 16, 18),
            content=ft.Column(
                [
                    self.header(frase_button),
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                col={"xs": 12, "sm": 6},
                                content=self.stat_card(
                                    "Deuda neta",
                                    money(total),
                                    C.RED_600 if total >= 0 else C.GREEN_600,
                                    I.ACCOUNT_BALANCE_WALLET,
                                ),
                            ),
                            ft.Container(
                                col={"xs": 12, "sm": 6},
                                content=self.stat_card(
                                    "Deuda de hoy",
                                    money(today),
                                    C.BLUE_600,
                                    I.TODAY,
                                ),
                            ),
                        ],
                        spacing=10,
                        run_spacing=10,
                    ),
                    self.input_panel(add_p1_button, add_p2_button, fine_button, fine_p2_button, date_button),
                    self.chart_card(),
                    self.history_header(),
                    self.history_list(),
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def header(self, frase_button):
        return ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(APP_NAME, size=26, weight=ft.FontWeight.BOLD, color=self.text_color),
                        ft.Text(f"{PARTICIPANTE_1} vs {PARTICIPANTE_2} · Control de retrasos", size=13, color=self.muted_color),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.Row(
                    [
                        frase_button,
                        ft.IconButton(
                            icon=I.SETTINGS,
                            icon_color=self.text_color,
                            tooltip="Configuración",
                            on_click=lambda e: self.open_settings_animated(),
                        ),
                    ],
                    spacing=5,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def input_panel(self, add_p1, add_p2, fine_button, fine_p2_button, date_button):
        return self.card(
            ft.Column(
                [
                    ft.Text("Nuevo registro", size=17, weight=ft.FontWeight.BOLD, color=self.text_color),
                    ft.Row(
                        [
                            ft.Container(content=self.date_field, expand=True),
                            ft.Container(content=date_button, width=50),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.Container(content=self.minutes_field, expand=True),
                            ft.Container(content=self.user_minutes_field, expand=True),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Container(content=add_p1, expand=True),
                            ft.Container(content=add_p2, expand=True),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Container(content=fine_button, expand=True),
                            ft.Container(content=fine_p2_button, expand=True),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=12,
            ),
            animate=True,
        )

    def chart_card(self):
        monthly = self.store.monthly_totals()
        if not monthly:
            body = ft.Container(
                height=150,
                alignment=CENTER,
                content=ft.Text("Aún no hay datos para el gráfico.", color=self.muted_color),
            )
        else:
            max_value = max(monthly.values()) or 1
            bars = []
            for month, value in list(monthly.items())[-8:]:
                height = max(18, int((value / max_value) * 110))
                color = C.RED_600 if value >= 0 else C.GREEN_600
                bars.append(
                    ft.Column(
                        [
                            ft.Text(money(value), size=10, color=self.muted_color, no_wrap=True),
                            ft.Container(
                                width=28,
                                height=height,
                                bgcolor=color,
                                border_radius=ft.BorderRadius(
                                    top_left=8,
                                    top_right=8,
                                    bottom_left=0,
                                    bottom_right=0,
                                ),
                                animate=ft.Animation(500, curve=ft.AnimationCurve.EASE_OUT),
                            ),
                            ft.Text(month_title(month), size=10, color=self.muted_color),
                        ],
                        spacing=5,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.END,
                    )
                )
            body = ft.Container(
                height=180,
                content=ft.Row(
                    bars,
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        return self.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(I.BAR_CHART, color=C.BLUE_600, size=20),
                            ft.Text("Deuda neta por mes", size=17, weight=ft.FontWeight.BOLD, color=self.text_color),
                        ],
                        spacing=8,
                    ),
                    body,
                ],
                spacing=12,
            ),
            animate=True,
        )

    def history_header(self):
        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Text("Historial", size=19, weight=ft.FontWeight.BOLD, color=self.text_color),
                        ft.Text(f"{len(self.store.records)} registros", size=13, color=self.muted_color),
                    ],
                    spacing=8,
                    expand=True,
                ),
                ft.Button(
                    "Limpiar",
                    icon=I.DELETE_SWEEP,
                    color=C.RED_500,
                    on_click=lambda e: self.confirm_clear(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def history_list(self):
        records = self.store.sorted_records()
        if not records:
            return self.card(
                ft.Container(
                    height=130,
                    alignment=CENTER,
                    content=ft.Text("Aún no hay registros.", color=self.muted_color),
                ),
                animate=True,
            )
        return ft.Column([self.record_tile(r) for r in records], spacing=8)

    def record_tile(self, record):
        kind = record["kind"]
        is_fine = kind == "fine"
        is_fine_p2 = kind == "fine_participante2"
        is_p1 = kind == "participante1"
        is_p2 = kind == "participante2"

        if is_fine:
            title = f"Multa: {PARTICIPANTE_1} debe pagar"
            icon = I.WARNING_AMBER
            color = C.RED_600
            circle_bg = C.RED_50 if not self.dark else C.GREY_700
        elif is_fine_p2:
            title = f"Multa: {PARTICIPANTE_2} debe pagar"
            icon = I.WARNING_AMBER
            color = C.ORANGE_600
            circle_bg = C.ORANGE_50 if not self.dark else C.GREY_700
        elif is_p1:
            title = f"{PARTICIPANTE_1}: {record.get('minutes', 0)} min tarde"
            icon = I.PERSON
            color = C.RED_600
            circle_bg = C.RED_50 if not self.dark else C.GREY_700
        else:  # participante2
            title = f"{PARTICIPANTE_2}: {record.get('minutes', 0)} min tarde (resta)"
            icon = I.PERSON_OUTLINE
            color = C.GREEN_600
            circle_bg = C.GREEN_50 if not self.dark else C.GREY_700

        amount_color = color
        if is_p2:
            amount_color = C.GREEN_600
        elif is_fine_p2:
            amount_color = C.ORANGE_600

        return self.card(
            ft.Row(
                [
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=21,
                        bgcolor=circle_bg,
                        alignment=CENTER,
                        content=ft.Icon(icon, color=color, size=22),
                    ),
                    ft.Column(
                        [
                            ft.Text(record["date"], size=12, color=self.muted_color),
                            ft.Text(title, size=15, color=self.text_color, weight=ft.FontWeight.W_500),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Text(money(record["amount"]), size=17, weight=ft.FontWeight.BOLD, color=amount_color),
                    ft.IconButton(
                        icon=I.DELETE_OUTLINE,
                        icon_color=C.RED_400,
                        tooltip="Eliminar",
                        on_click=lambda e, record_id=record["id"]: self.delete_record(record_id),
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=12,
            animate=True,
        )

    # ========== ACCIONES ==========
    async def add_minutes(self, e):
        await self.bounce(e.control)
        raw = (self.minutes_field.value or "").strip()
        if raw == "":
            self.snack(f"Ingresa los minutos de {PARTICIPANTE_1}.", True)
            return
        try:
            minutes = int(raw)
            if minutes < 0:
                self.snack("No se permiten minutos negativos.", True)
                return
            amount = self.store.add_minutes(minutes, self.selected_date)
        except ValueError as error:
            self.snack(str(error), True)
            return
        self.minutes_field.value = ""
        self.refresh()
        self.snack(f"{PARTICIPANTE_1}: {minutes} min = {money(amount)}")
        self.check_and_notify_alert()
        self.alert_if_needed()

    async def add_user_minutes(self, e):
        await self.bounce(e.control)
        raw = (self.user_minutes_field.value or "").strip()
        if raw == "":
            self.snack(f"Ingresa los minutos de {PARTICIPANTE_2}.", True)
            return
        try:
            minutes = int(raw)
            if minutes < 0:
                self.snack("No se permiten minutos negativos.", True)
                return
            amount = self.store.add_user_minutes(minutes, self.selected_date)
        except ValueError as error:
            self.snack(str(error), True)
            return
        self.user_minutes_field.value = ""
        self.refresh()
        self.snack(f"{PARTICIPANTE_2}: {minutes} min = {money(amount)} (restado)")
        self.check_and_notify_alert()
        self.alert_if_needed()

    async def add_fine(self, e):
        await self.bounce(e.control)
        amount = self.store.add_fine(self.selected_date)
        self.refresh()
        self.snack(f"Multa de {PARTICIPANTE_1}: {money(amount)}")
        self.check_and_notify_alert()
        self.alert_if_needed()

    async def add_fine_participante2(self, e):
        await self.bounce(e.control)
        amount = self.store.add_fine_participante2(self.selected_date)
        self.refresh()
        self.snack(f"Multa de {PARTICIPANTE_2}: {money(amount)}")
        self.check_and_notify_alert()
        self.alert_if_needed()

    def delete_record(self, record_id):
        self.store.delete_record(record_id)
        self.refresh()
        self.snack("Registro eliminado.")

    def confirm_clear(self):
        def cancel(e):
            self.close_control(dialog)

        def confirm(e):
            self.store.clear_all()
            self.close_control(dialog)
            self.refresh()
            self.snack("Historial eliminado.")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar todo"),
            content=ft.Text("Esta acción borrará todo el historial local."),
            actions=[
                ft.Button("Cancelar", on_click=cancel),
                ft.Button("Eliminar", bgcolor=C.RED_600, color=C.WHITE, on_click=confirm),
            ],
        )
        self.open_control(dialog)

    def check_and_notify_alert(self):
        if self.store.should_alert():
            total = self.store.total()
            level = self.store.get_alert_level()
            self.page.run_task(
                self.show_notification,
                "💰 ¡Deuda acumulada!",
                f"Has alcanzado {money(level)} en deudas. ¡Cóbralas!",
            )
            self.store.update_alert_level()

    def alert_if_needed(self):
        total = self.store.total()
        if total >= ALERT_LIMIT:
            self.dialog(
                "Alerta de deuda",
                f"{PARTICIPANTE_1} ya debe {money(total)}. Superó el límite de {money(ALERT_LIMIT)}.",
            )
        elif total <= -ALERT_LIMIT:
            self.dialog(
                "Alerta de crédito",
                f"Tienes crédito a favor de {money(abs(total))}. {PARTICIPANTE_1} te debe menos.",
            )

    # ========== CONFIGURACIÓN CON ANIMACIÓN ==========
    def open_settings_animated(self):
        settings_content = self.settings_view()
        container = ft.Container(
            content=settings_content,
            opacity=0,
            scale=0.9,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
        self.root.content = container
        self.page.update()
        container.opacity = 1
        container.scale = 1
        self.page.update()

    def close_settings_animated(self):
        container = self.root.content
        if container:
            container.opacity = 0
            container.scale = 0.9
            self.page.update()
            async def set_main():
                await asyncio.sleep(0.3)
                self.root.content = self.main_view()
                self.page.update()
            self.page.run_task(set_main)

    def settings_view(self):
        stats = self.store.stats()

        dark_switch = ft.Switch(
            value=self.dark,
            active_color=C.BLUE_600,
            on_change=self.change_dark_mode,
        )

        notifications_switch = ft.Switch(
            value=self.store.settings["notifications"],
            active_color=C.BLUE_600,
            on_change=self.change_notifications,
        )

        self.reminder_field = ft.TextField(
            value=self.store.settings["reminder_time"],
            label="Hora",
            hint_text="04:40",
            width=120,
            border_radius=14,
            text_style=ft.TextStyle(color=self.text_color),
            on_submit=self.change_reminder_time,
        )

        test_notif_button = ft.Button(
            "🔔 Probar notificación",
            icon=I.NOTIFICATIONS,
            bgcolor=C.BLUE_600,
            color=C.WHITE,
            height=48,
            on_click=self.test_notification,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
        )

        return ft.Container(
            bgcolor=self.bg,
            padding=pad(16, 18, 16, 18),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=I.ARROW_BACK,
                                icon_color=self.text_color,
                                tooltip="Volver",
                                on_click=lambda e: self.close_settings_animated(),
                            ),
                            ft.Text("Configuración", size=25, weight=ft.FontWeight.BOLD, color=self.text_color),
                        ],
                        spacing=4,
                    ),
                    self.card(
                        ft.Column(
                            [
                                ft.Text("Apariencia", size=17, weight=ft.FontWeight.BOLD, color=self.text_color),
                                self.setting_row("Modo oscuro", I.DARK_MODE, dark_switch),
                            ],
                            spacing=12,
                        ),
                        animate=True,
                    ),
                    self.card(
                        ft.Column(
                            [
                                ft.Text("Recordatorios", size=17, weight=ft.FontWeight.BOLD, color=self.text_color),
                                self.setting_row("Notificaciones", I.NOTIFICATIONS_ACTIVE, notifications_switch),
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(I.SCHEDULE, color=C.BLUE_600, size=21),
                                                ft.Text("Hora diaria", color=self.text_color, size=15),
                                            ],
                                            spacing=8,
                                            expand=True,
                                        ),
                                        self.reminder_field,
                                        ft.IconButton(
                                            icon=I.SAVE,
                                            icon_color=C.BLUE_600,
                                            tooltip="Guardar hora",
                                            on_click=self.change_reminder_time,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                test_notif_button,
                            ],
                            spacing=12,
                        ),
                        animate=True,
                    ),
                    self.card(
                        ft.Column(
                            [
                                ft.Text("Estadísticas", size=17, weight=ft.FontWeight.BOLD, color=self.text_color),
                                ft.ResponsiveRow(
                                    [
                                        self.small_stat("Días", str(stats["days"])),
                                        self.small_stat("Promedio", money(stats["avg"])),
                                        self.small_stat("Máximo", money(stats["max"])),
                                        self.small_stat("Multas", str(stats["fines"])),
                                        self.small_stat(f"Días {PARTICIPANTE_1}", str(stats["p1_days"])),
                                        self.small_stat(f"Días {PARTICIPANTE_2}", str(stats["p2_days"])),
                                    ],
                                    spacing=8,
                                    run_spacing=8,
                                ),
                            ],
                            spacing=12,
                        ),
                        animate=True,
                    ),
                    self.card(
                        ft.Column(
                            [
                                ft.Row(
                                    [ft.Text("Versión", color=self.muted_color), ft.Text(APP_VERSION, color=self.text_color, weight=ft.FontWeight.BOLD)],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Row(
                                    [ft.Text("Almacenamiento", color=self.muted_color), ft.Text("JSON local offline", color=self.text_color, weight=ft.FontWeight.BOLD)],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=10,
                        ),
                        animate=True,
                    ),
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def setting_row(self, label, leading_icon, trailing):
        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(leading_icon, color=C.BLUE_600, size=21),
                        ft.Text(label, color=self.text_color, size=15),
                    ],
                    spacing=8,
                    expand=True,
                ),
                trailing,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def small_stat(self, label, value):
        return ft.Container(
            col={"xs": 6, "sm": 3},
            content=ft.Container(
                padding=12,
                border_radius=14,
                bgcolor=self.soft_bg,
                content=ft.Column(
                    [
                        ft.Text(label, size=12, color=self.muted_color),
                        ft.Text(value, size=16, color=self.text_color, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        )

    def change_dark_mode(self, e):
        self.store.settings["dark_mode"] = bool(e.control.value)
        self.store.save_settings()
        self.open_settings_animated()
        self.snack("Tema actualizado.")

    def change_notifications(self, e):
        self.store.settings["notifications"] = bool(e.control.value)
        self.store.save_settings()
        state = "activadas" if e.control.value else "desactivadas"
        self.snack(f"Notificaciones {state}.")

    def change_reminder_time(self, e):
        value = (self.reminder_field.value or "").strip()
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            self.snack("Usa formato HH:MM, por ejemplo 04:40.", True)
            return
        self.store.settings["reminder_time"] = value
        self.store.save_settings()
        self.snack(f"Recordatorio guardado a las {value}.")

    def test_notification(self, e):
        if not self.store.settings["notifications"]:
            self.snack("Activa las notificaciones primero.", True)
            return
        self.dialog(
            "Notificación de prueba",
            "La app está lista para recordarte registrar la deuda.",
        )
        self.page.run_task(
            self.show_notification,
            "🔔 Notificación de prueba",
            "¡La app funciona correctamente!",
        )

    async def reminder_loop(self):
        while True:
            await asyncio.sleep(30)
            if not self.store.settings["notifications"]:
                continue
            current = datetime.now()
            current_time = current.strftime("%H:%M")
            current_date = current.strftime("%Y-%m-%d")
            if (
                current_time == self.store.settings["reminder_time"]
                and self.last_reminder_date != current_date
            ):
                self.last_reminder_date = current_date
                await self.show_notification(
                    "⏰ Recordatorio diario",
                    "No olvides registrar las deudas de hoy.",
                )
                self.dialog(
                    "Recordatorio diario",
                    "Revisa si alguien llegó tarde y registra los minutos.",
                )

    async def check_alerts_loop(self):
        while True:
            await asyncio.sleep(30)
            if self.store.should_alert():
                total = self.store.total()
                level = self.store.get_alert_level()
                await self.show_notification(
                    "💰 ¡Deuda acumulada!",
                    f"Has alcanzado {money(level)} en deudas. ¡Cóbralas!",
                )
                self.store.update_alert_level()

# ========== PUNTO DE ENTRADA ==========
def main(page: ft.Page):
    DeudaGymApp(page).run()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)