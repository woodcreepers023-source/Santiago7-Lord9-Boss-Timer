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
ADMIN_PASSWORD = "password"

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
    ("Lady Dalia", 1080, "2025-09-19 05:58 AM"),
    ("Amentis", 1740, "2025-09-18 09:42 PM"),
    ("General Aqulcus", 1740, "2025-09-18 09:45 PM"),
    ("Metus", 2880, "2025-09-18 06:53 AM"),
    ("Asta", 3720, "2025-09-17 04:59 PM"),
    ("Ordo", 3720, "2025-09-17 05:07 PM"),
    ("Secreta", 3720, "2025-09-17 05:15 PM"),
    ("Baron Braudmore", 1920, "2025-09-19 12:37 AM"),
    ("Gareth", 1920, "2025-09-19 12:38 AM"),
    ("Ego", 1260, "2025-09-19 04:32 PM"),
    ("Shuliar", 2100, "2025-09-19 03:49 AM"),
    ("Larba", 2100, "2025-09-19 03:55 AM"),
    ("Catena", 2100, "2025-09-19 04:12 AM"),
    ("Araneo", 1440, "2025-09-19 04:33 PM"),
    ("Livera", 1440, "2025-09-19 04:36 PM"),
    ("Undomiel", 1440, "2025-09-19 04:42 PM"),
    ("Titore", 2220, "2025-09-19 04:36 PM"),
    ("Duplican", 2880, "2025-09-19 04:40 PM"),
    ("Wannitas", 2880, "2025-09-19 04:46 PM"),
    ("Supore", 3720, "2025-09-20 07:15 AM"),
]

# ------------------- JSON Persistence -------------------
def load_boss_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = default_boss_data.copy()

    if not any(boss[0] == "Supore" for boss in data):
        data.append(("Supore", 3720, "2025-09-20 07:15 AM"))
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    return data

def save_boss_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ------------------- Edit History -------------------
def log_edit(boss_name, old_time, new_time):
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    edited_by = st.session_state.get("username", "Unknown")
    entry = {
        "boss": boss_name,
        "old_time": old_time,
        "new_time": new_time,
        "edited_at": datetime.now(tz=MANILA).strftime("%Y-%m-%d %I:%M %p"),
        "edited_by": edited_by,
    }
    history.append(entry)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    send_discord_message(
        f"🛠 **{boss_name}** time updated by **{edited_by}**\n"
        f"Old: `{old_time}` → New: `{new_time}` (Manila time)"
    )

# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = int(interval_minutes)
        self.interval = self.interval_minutes * 60
        parsed_time = datetime.strptime(last_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=MANILA)
        self.last_time = parsed_time
        self.next_time = self.last_time + timedelta(seconds=self.interval)

    def update_next(self):
        now = datetime.now(tz=MANILA)
        while self.next_time < now:
            self.last_time = self.next_time
            self.next_time = self.last_time + timedelta(seconds=self.interval)

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

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")

# 🔥 MAKE MANAGE PAGE SMALLER
st.markdown("""
<style>
.manage-wrap {
    max-width: 700px;
    margin: auto;
}
.manage-wrap [data-testid="stExpanderDetails"] {
    padding-top: 0.25rem !important;
    padding-bottom: 0.25rem !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------- Session -------------------
st.session_state.setdefault("auth", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("page", "world")

def goto(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ------------------- Auto-refresh only world -------------------
if st.session_state.page == "world":
    st_autorefresh(interval=1000, key="timer_refresh")

# ------------------- Load timers -------------------
if "timers" not in st.session_state:
    st.session_state.timers = [TimerEntry(*data) for data in load_boss_data()]
timers = st.session_state.timers

for t in timers:
    t.update_next()

# ------------------- WORLD PAGE -------------------
if st.session_state.page == "world":
    st.subheader("🗺️ World Boss Spawn")
    st.subheader("🗡️ Field Boss Spawn Table")

    for t in timers:
        st.write(f"{t.name} - {t.format_countdown()}")

    if not st.session_state.auth:
        if st.button("🔐 Login to Edit"):
            goto("login")
    else:
        if st.button("🛠️ Manage / Edit"):
            goto("manage")

# ------------------- LOGIN PAGE -------------------
elif st.session_state.page == "login":
    st.subheader("🔐 Login")

    with st.form("login_form"):
        username_in = st.text_input("Name")
        password_in = st.text_input("Password", type="password")
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if password_in == ADMIN_PASSWORD and username_in.strip():
            st.session_state.auth = True
            st.session_state.username = username_in.strip()
            goto("manage")
        else:
            st.error("Invalid login")

    if st.button("⬅️ Back"):
        goto("world")

# ------------------- MANAGE PAGE -------------------
elif st.session_state.page == "manage":
    if not st.session_state.auth:
        goto("login")

    if st.button("🌍 Back to World"):
        goto("world")

    st.subheader("🛠️ Edit Boss Timers")

    st.markdown('<div class="manage-wrap">', unsafe_allow_html=True)

    for i, timer in enumerate(timers):
        with st.expander(f"Edit {timer.name}", expanded=False):
            new_date = st.date_input(
                f"{timer.name} Last Date",
                value=timer.last_time.date(),
                key=f"{timer.name}_last_date"
            )
            new_time = st.time_input(
                f"{timer.name} Last Time",
                value=timer.last_time.time(),
                key=f"{timer.name}_last_time",
                step=60
            )

            if st.button(f"Save {timer.name}", key=f"save_{timer.name}"):
                old_time_str = timer.last_time.strftime("%Y-%m-%d %I:%M %p")
                updated_last_time = datetime.combine(new_date, new_time).replace(tzinfo=MANILA)
                updated_next_time = updated_last_time + timedelta(seconds=timer.interval)

                st.session_state.timers[i].last_time = updated_last_time
                st.session_state.timers[i].next_time = updated_next_time

                save_boss_data([
                    (t.name, t.interval_minutes, t.last_time.strftime("%Y-%m-%d %I:%M %p"))
                    for t in st.session_state.timers
                ])

                log_edit(timer.name, old_time_str, updated_last_time.strftime("%Y-%m-%d %I:%M %p"))

                st.success("Updated!")

    st.markdown('</div>', unsafe_allow_html=True)
