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

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")
st_autorefresh(interval=1000, key="timer_refresh")

# ------------------- SIDEBAR LOGIN -------------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "username" not in st.session_state:
    st.session_state.username = ""

with st.sidebar:
    st.markdown("### 🔐 Login")

    if not st.session_state.auth:
        with st.form("login_form_sidebar"):
            username = st.text_input("Name", key="login_username_sidebar")
            password = st.text_input("Password", type="password", key="login_password_sidebar")
            login_clicked = st.form_submit_button("Login", use_container_width=True)

        if login_clicked:
            if password.strip() == ADMIN_PASSWORD and username.strip():
                st.session_state.auth = True
                st.session_state.username = username.strip()
                st.success(f"✅ Logged in as {st.session_state.username}")
                st.rerun()
            else:
                st.error("❌ Invalid name or password.")
    else:
        st.success(f"✅ Admin: {st.session_state.username}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.auth = False
            st.session_state.username = ""
            st.rerun()

# ------------------- Discord -------------------
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

def save_boss_data(data):
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    tmp.replace(DATA_FILE)

def parse_dt(last_time_str: str) -> datetime:
    dt = datetime.strptime(last_time_str, "%Y-%m-%d %I:%M %p")
    return dt.replace(tzinfo=MANILA)

def load_boss_data():
    data = _safe_load_json(DATA_FILE, None)
    if data is None:
        data = default_boss_data.copy()
        save_boss_data(data)
    return data

# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = int(interval_minutes)
        self.interval = timedelta(minutes=self.interval_minutes)
        self.last_time = parse_dt(last_time_str)
        self.next_time = self.last_time + self.interval

    def promote_if_due(self, now):
        changed = False
        while self.next_time <= now:
            self.last_time = self.next_time
            self.next_time = self.last_time + self.interval
            changed = True
        return changed

    def countdown(self):
        return self.next_time - datetime.now(tz=MANILA)

    def format_countdown(self):
        td = self.countdown()
        total_seconds = int(td.total_seconds())
        if total_seconds < 0:
            return "00:00:00"
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        if days > 0:
            return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
        return f"{hours:02}:{minutes:02}:{seconds:02}"

# ------------------- Build Timers -------------------
def build_timers():
    return [TimerEntry(*data) for data in load_boss_data()]

if "timers" not in st.session_state:
    st.session_state.timers = build_timers()

timers = st.session_state.timers

# ------------------- Display Table -------------------
def display_boss_table_sorted(timers_list):
    timers_sorted = sorted(timers_list, key=lambda t: t.next_time)

    data = {
        "Boss Name": [t.name for t in timers_sorted],
        "Interval (min)": [t.interval_minutes for t in timers_sorted],
        "Last Spawn": [t.last_time.strftime("%m-%d-%Y | %H:%M") for t in timers_sorted],
        "Next Spawn": [t.next_time.strftime("%m-%d-%Y | %I:%M %p") for t in timers_sorted],
        "Countdown": [t.format_countdown() for t in timers_sorted],
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

st.subheader("🗡️ Field Boss Spawn Table")
display_boss_table_sorted(timers)

# ------------------- Admin Tools -------------------
if st.session_state.auth:
    st.subheader("🛠️ Admin Controls")

    if st.button("🔄 Reload timers from JSON"):
        st.session_state.timers = build_timers()
        st.success("Reloaded from JSON")
        st.rerun()
