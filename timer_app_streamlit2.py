import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import requests
import json
from pathlib import Path

# ------------------- Config -------------------
MANILA = ZoneInfo("Asia/Manila")
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"
DATA_FILE = Path("boss_timers.json")
HISTORY_FILE = Path("boss_history.json")
ADMIN_PASSWORD = "bestgame"


def send_discord_message(message: str):
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_HERE":
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=5)
    except Exception as e:
        print(f"Discord webhook error: {e}")


# ------------------- Default Boss Data -------------------
default_boss_data = [
    ("Venatus", 600, "2025-09-19 12:31 PM"),
    ("Viorent", 600, "2025-09-19 12:32 PM"),
    ("Ego", 1260, "2025-09-19 04:32 PM"),
    ("Livera", 1440, "2025-09-19 04:36 PM"),
    ("Araneo", 1440, "2025-09-19 04:33 PM"),
    ("Undomiel", 1440, "2025-09-19 04:42 PM"),
    ("Lady Dalia", 1080, "2025-09-19 05:58 AM"),
    ("General Aquleus", 1740, "2025-09-18 09:45 PM"),
    ("Amentis", 1740, "2025-09-18 09:42 PM"),
    ("Baron Braudmore", 1920, "2025-09-19 12:37 AM"),
    ("Wannitas", 2880, "2025-09-19 04:46 PM"),
    ("Metus", 2880, "2025-09-18 06:53 AM"),
    ("Duplican", 2880, "2025-09-19 04:40 PM"),
    ("Shuliar", 2100, "2025-09-19 03:49 AM"),
    ("Gareth", 1920, "2025-09-19 12:38 AM"),
    ("Titore", 2220, "2025-09-19 04:36 PM"),
    ("Larba", 2100, "2025-09-19 03:55 AM"),
    ("Catena", 2100, "2025-09-19 04:12 AM"),
    ("Secreta", 3720, "2025-09-17 05:15 PM"),
    ("Ordo", 3720, "2025-09-17 05:07 PM"),
    ("Asta", 3720, "2025-09-17 04:59 PM"),
    ("Supore", 3720, "2025-09-20 07:15 AM"),
]


# ------------------- JSON Persistence -------------------
def _safe_load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_boss_data():
    data = _safe_load_json(DATA_FILE, None)
    if data is None:
        data = default_boss_data.copy()
        save_boss_data(data)
    return data


def save_boss_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def log_edit(boss_name, old_time, new_time):
    history = _safe_load_json(HISTORY_FILE, [])
    edited_by = st.session_state.get("username", "Unknown")

    history.append({
        "boss": boss_name,
        "old_time": old_time,
        "new_time": new_time,
        "edited_at": datetime.now(tz=MANILA).strftime("%Y-%m-%d %I:%M %p"),
        "edited_by": edited_by,
    })

    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    send_discord_message(
        f"🛠 {boss_name} updated by {edited_by}\n{old_time} → {new_time}"
    )


# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = interval_minutes
        self.interval = timedelta(minutes=interval_minutes)
        self.last_time = datetime.strptime(
            last_time_str, "%Y-%m-%d %I:%M %p"
        ).replace(tzinfo=MANILA)
        self.next_time = self.last_time + self.interval

    def update_next(self):
        now = datetime.now(tz=MANILA)
        while self.next_time < now:
            self.last_time = self.next_time
            self.next_time = self.last_time + self.interval

    def countdown(self):
        return self.next_time - datetime.now(tz=MANILA)

    def format_countdown(self):
        td = self.countdown()
        total = int(td.total_seconds())
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02}:{m:02}:{s:02}"


def build_timers():
    return [TimerEntry(*d) for d in load_boss_data()]


# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")
st_autorefresh(interval=1000, key="timer_refresh")

if "timers" not in st.session_state:
    st.session_state.timers = build_timers()
timers = st.session_state.timers


# ------------------- LOGIN (FORM-BASED) -------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.subheader("🔐 Login to Edit Timers")

    with st.form("login_form"):
        username = st.text_input("Enter your name")
        password = st.text_input("Enter password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if password.strip() == ADMIN_PASSWORD and username.strip():
                st.session_state.auth = True
                st.session_state.username = username.strip()
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid name or password")


# ------------------- Manage & Edit Timers -------------------
if st.session_state.auth:
    st.subheader("Edit Boss Timers")

    for i, timer in enumerate(timers):
        with st.expander(f"Edit {timer.name}"):

            today = datetime.now(tz=MANILA).date()
            stored_time = timer.last_time.time().replace(second=0, microsecond=0)

            new_date = st.date_input("Last Date", value=today, key=f"{timer.name}_date")
            new_time = st.time_input(
                "Last Time",
                value=stored_time,
                step=timedelta(minutes=1),
                key=f"{timer.name}_time",
            )

            if st.button(f"Save {timer.name}", key=f"save_{timer.name}"):
                old = timer.last_time.strftime("%Y-%m-%d %I:%M %p")
                updated = datetime.combine(new_date, new_time).replace(tzinfo=MANILA)

                timers[i].last_time = updated
                timers[i].next_time = updated + timer.interval

                save_boss_data([
                    (t.name, t.interval_minutes, t.last_time.strftime("%Y-%m-%d %I:%M %p"))
                    for t in timers
                ])

                log_edit(timer.name, old, updated.strftime("%Y-%m-%d %I:%M %p"))
                st.success("Saved")
