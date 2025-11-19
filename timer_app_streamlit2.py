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

def send_discord_message(message: str):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
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
def load_boss_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = default_boss_data.copy()

    # Auto-add Supore if missing
    if not any(boss[0] == "Supore" for boss in data):
        data.append(("Supore", 3720, "2025-09-20 07:15 AM"))
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    return data

def save_boss_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_edit(boss_name, old_time, new_time):
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append({
        "boss": boss_name,
        "old_time": old_time,
        "new_time": new_time,
        "edited_at": datetime.now(tz=MANILA).strftime("%Y-%m-%d %I:%M %p"),
        "edited_by": st.session_state.username
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = interval_minutes
        self.interval = interval_minutes * 60
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

# Helper for weekly countdown formatting
def format_timedelta(td: timedelta) -> str:
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

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")
st_autorefresh(interval=1000, key="timer_refresh")

if "timers" not in st.session_state:
    st.session_state.timers = build_timers()
timers = st.session_state.timers

# ------------------- Password Gate -------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    username = st.text_input("Enter your name:")
    password = st.text_input("🔑 Enter password to edit timers:", type="password")
    if password == ADMIN_PASSWORD and username.strip():
        st.session_state.auth = True
        st.session_state.username = username.strip()
        st.success(f"✅ Access granted for {st.session_state.username}")

# ------------------- Weekly Boss Data -------------------
weekly_boss_data = [
    ("Clemantis", ["Monday 11:30", "Thursday 19:00"]),
    ("Saphirus", ["Sunday 17:00", "Tuesday 11:30"]),
    ("Neutro", ["Tuesday 19:00", "Thursday 11:30"]),
    ("Thymele", ["Monday 19:00", "Wednesday 11:30"]),
    ("Milavy", ["Saturday 15:00"]),
    ("Ringor", ["Saturday 17:00"]),
    ("Roderick", ["Friday 19:00"]),
    ("Auraq", ["Sunday 21:00", "Wednesday 21:00"]),
    ("Chaiflock", ["Saturday 22:00"]),
]

def get_next_weekly_spawn(day_time: str):
    """Convert 'Monday 11:30' to next datetime in Manila timezone."""
    now = datetime.now(tz=MANILA)
    day, time_str = day_time.split()
    target_time = datetime.strptime(time_str, "%H:%M").time()

    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_weekday = weekday_map[day]

    days_ahead = (target_weekday - now.weekday()) % 7
    spawn_date = (now + timedelta(days=days_ahead)).date()
    spawn_dt = datetime.combine(spawn_date, target_time).replace(tzinfo=MANILA)

    if spawn_dt <= now:
        spawn_dt += timedelta(days=7)

    return spawn_dt

# ------------------- Next Boss Banner -------------------
def next_boss_banner(timers_list):
    # Update field timers
    for t in timers_list:
        t.update_next()

    # Soonest field boss
    field_next = min(timers_list, key=lambda x: x.countdown())
    field_cd = field_next.countdown()

    # Soonest weekly boss
    now = datetime.now(tz=MANILA)
    weekly_best_name = None
    weekly_best_time = None
    weekly_best_cd = None

    for boss, times in weekly_boss_data:
        for sched in times:
            spawn_dt = get_next_weekly_spawn(sched)
            cd = spawn_dt - now
            if weekly_best_cd is None or cd < weekly_best_cd:
                weekly_best_cd = cd
                weekly_best_name = boss
                weekly_best_time = spawn_dt

    # Decide which spawns next (field vs weekly)
    chosen_name = field_next.name
    chosen_time = field_next.next_time
    chosen_cd = field_cd
    from_weekly = False

    if weekly_best_cd is not None and weekly_best_cd < field_cd:
        from_weekly = True
        chosen_name = weekly_best_name
        chosen_time = weekly_best_time
        chosen_cd = weekly_best_cd

    remaining = chosen_cd.total_seconds()

    # Color logic for countdown
    if remaining <= 60:
        cd_color = "red"
    elif remaining <= 300:
        cd_color = "orange"
    else:
        cd_color = "limegreen"

    time_only = chosen_time.strftime("%I:%M %p")
    cd_str = format_timedelta(chosen_cd) if from_weekly else field_next.format_countdown()

    st.markdown(
        f"""
        <style>
        .banner-container {{
            display: flex;
            justify-content: center;
            margin: 20px 0 5px 0;
        }}
        .boss-banner {{
            background: linear-gradient(90deg, #0f172a, #1d4ed8, #16a34a);
            padding: 14px 28px;
            border-radius: 999px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.75);
            color: #f9fafb;
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        .boss-banner-title {{
            font-size: 28px;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0.03em;
        }}
        .boss-banner-row {{
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 18px;
        }}
        .banner-chip {{
            padding: 4px 12px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.7);
        }}
        </style>

        <div class="banner-container">
            <div class="boss-banner">
                <h2 class="boss-banner-title">
                    Next Boss: <strong>{chosen_name}</strong>
                </h2>
                <div class="boss-banner-row">
                    <span class="banner-chip">
                        🕒 <strong>{time_only}</strong>
                    </span>
                    <span class="banner-chip" style="color:{cd_color}; border-color:{cd_color};">
                        ⏳ <strong>{cd_str}</strong>
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------- Auto-Sorted Field Boss Table -------------------
def display_boss_table_sorted(timers_list):
    for t in timers_list:
        t.update_next()

    timers_sorted = sorted(timers_list, key=lambda t: t.next_time)

    # Build colored countdown values
    countdown_cells = []
    for t in timers_sorted:
        secs = t.countdown().total_seconds()
        if secs <= 60:
            color = "red"
        elif secs <= 300:
            color = "orange"
        else:
            color = "green"
        countdown_cells.append(
            f"<span style='color:{color}'>{t.format_countdown()}</span>"
        )

    data = {
        "Boss Name": [t.name for t in timers_sorted],
        "Interval (min)": [t.interval_minutes for t in timers_sorted],

        # Last spawn with your chosen format
        "Last Spawn": [
            t.last_time.strftime("%b %d, %Y | %I:%M %p")
            for t in timers_sorted
        ],

        # ⬇⬇⬇ UPDATED — date only, NO TIME
        "Next Spawn Date": [
            t.next_time.strftime("%b %d, %Y (%a)")
            for t in timers_sorted
        ],

        "Next Spawn Time": [
            t.next_time.strftime("%I:%M %p")
            for t in timers_sorted
        ],

        "Countdown": countdown_cells,
    }

    df = pd.DataFrame(data)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ------------------- NEW Weekly Table: Boss | Day | Time | Countdown -------------------
def display_weekly_boss_table():
    """Display sorted weekly bosses by nearest spawn time with columns:
       Boss, Day, Time (12h), Countdown."""
    upcoming = []
    now = datetime.now(tz=MANILA)

    for boss, times in weekly_boss_data:
        for sched in times:  # multiple fixed schedules per boss
            spawn_dt = get_next_weekly_spawn(sched)
            countdown = spawn_dt - now
            upcoming.append((boss, spawn_dt, countdown))

    # Sort by soonest spawn
    upcoming_sorted = sorted(upcoming, key=lambda x: x[1])

    data = {
        "Boss Name": [row[0] for row in upcoming_sorted],
        "Day": [row[1].strftime("%A") for row in upcoming_sorted],
        "Time": [row[1].strftime("%I:%M %p") for row in upcoming_sorted],
        "Countdown": [
            f"<span style='color:{'red' if row[2].total_seconds() <= 60 else 'orange' if row[2].total_seconds() <= 300 else 'green'}'>{format_timedelta(row[2])}</span>"
            for row in upcoming_sorted
        ],
    }

    df = pd.DataFrame(data)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ---- Show the combined (field + weekly) next boss banner ----
next_boss_banner(timers)

# ------------------- Tabs -------------------
tabs = ["World Boss Spawn"]
if st.session_state.auth:
    tabs.append("Manage & Edit Timers")
    tabs.append("Edit History")
tab_selection = st.tabs(tabs)

# Tab 1: World Boss Spawn
with tab_selection[0]:
    st.subheader("Field Boss Spawn Table")

    # Side-by-side layout
    col1, col2 = st.columns([2, 1])  # left = bigger
    with col1:
        display_boss_table_sorted(timers)
    with col2:
        st.subheader("📅 Fixed Time Field Boss Spawn Table")
        display_weekly_boss_table()

# Tab 2: Manage & Edit Timers
if st.session_state.auth:
    with tab_selection[1]:
        st.subheader("Edit Boss Timers (Edit Last Time, Next auto-updates)")
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
                    step=60  # <-- 1-minute increments
                )
                if st.button(f"Save {timer.name}", key=f"save_{timer.name}"):
                    old_time_str = timer.last_time.strftime("%Y-%m-%d %I:%M %p")
                    updated_last_time = datetime.combine(new_date, new_time).replace(tzinfo=MANILA)
                    updated_next_time = updated_last_time + timedelta(seconds=timer.interval)

                    st.session_state.timers[i].last_time = updated_last_time
                    st.session_state.timers[i].next_time = updated_next_time

                    # Save to JSON
                    save_boss_data([
                        (t.name, t.interval_minutes, t.last_time.strftime("%Y-%m-%d %I:%M %p"))
                        for t in st.session_state.timers
                    ])

                    # Log edit
                    log_edit(timer.name, old_time_str, updated_last_time.strftime("%Y-%m-%d %I:%M %p"))

                    st.success(
                        f"✅ {timer.name} updated! Next: {updated_next_time.strftime('%Y-%m-%d %I:%M %p')}"
                    )

# Tab 3: Edit History
if st.session_state.auth:
    with tab_selection[2]:
        st.subheader("Edit History")
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
            if history:
                df_history = pd.DataFrame(history).sort_values("edited_at", ascending=False)
                st.dataframe(df_history)
            else:
                st.info("No edits yet.")
        else:
            st.info("No edit history yet.")











