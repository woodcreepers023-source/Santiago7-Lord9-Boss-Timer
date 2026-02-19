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

    # Auto-add Supore if missing
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

# ------------------- Timer Class (OLD logic) -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = int(interval_minutes)
        self.interval = self.interval_minutes * 60  # seconds
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

# ------------------- Weekly Boss Data -------------------
weekly_boss_data = [
    ("Clemantis", ["Monday 11:30", "Thursday 19:00"]),
    ("Saphirus", ["Sunday 17:00", "Tuesday 11:30"]),
    ("Neutro", ["Tuesday 19:00", "Thursday 11:30"]),
    ("Thymele", ["Monday 19:00", "Wednesday 11:30"]),
    ("Milavy", ["Saturday 15:00"]),
    ("Ringor", ["Saturday 17:00"]),
    ("Roderick", ["Friday 19:00"]),
    ("Auraq", ["Friday 22:00", "Wednesday 21:00"]),
    ("Chaiflock", ["Saturday 22:00"]),
    ("Benji", ["Sunday 21:00"]),
    ("Tumier", ["Sunday 19:00"]),
    ("Icaruthia (Kransia)", ["Tuesday 21:00", "Friday 21:00"]),
    ("Motti (Kransia)", ["Wednesday 19:00", "Saturday 19:00"]),
    ("Nevaeh (Kransia)", ["Sunday 22:00"]),
]

def get_next_weekly_spawn(day_time: str):
    now = datetime.now(tz=MANILA)
    day_time = " ".join(day_time.split())
    day, time_str = day_time.split(" ", 1)
    target_time = datetime.strptime(time_str, "%H:%M").time()

    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    target_weekday = weekday_map[day]

    days_ahead = (target_weekday - now.weekday()) % 7
    spawn_date = (now + timedelta(days=days_ahead)).date()
    spawn_dt = datetime.combine(spawn_date, target_time).replace(tzinfo=MANILA)

    if spawn_dt <= now:
        spawn_dt += timedelta(days=7)
    return spawn_dt

# ------------------- Fancy Next Boss Banner (NEW design) -------------------
def next_boss_banner_combined(field_timers):
    if not field_timers:
        st.warning("No timers loaded.")
        return

    now = datetime.now(tz=MANILA)

    field_next = min(field_timers, key=lambda x: x.next_time)
    field_cd = field_next.next_time - now

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

    chosen_name = field_next.name
    chosen_time = field_next.next_time
    chosen_cd = field_cd
    if weekly_best_cd is not None and weekly_best_cd < field_cd:
        chosen_name = weekly_best_name
        chosen_time = weekly_best_time
        chosen_cd = weekly_best_cd

    remaining = chosen_cd.total_seconds()
    if remaining <= 60:
        cd_color = "red"
    elif remaining <= 300:
        cd_color = "orange"
    else:
        cd_color = "limegreen"

    time_only = chosen_time.strftime("%I:%M %p")
    cd_str = format_timedelta(chosen_cd)

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

# ------------------- Field Boss Table (NEW columns + emoji style) -------------------
def display_boss_table_sorted_newstyle(timers_list):
    timers_sorted = sorted(timers_list, key=lambda t: t.next_time)

    countdown_cells = []
    for t in timers_sorted:
        secs = t.countdown().total_seconds()
        if secs <= 60:
            color = "red"
        elif secs <= 300:
            color = "orange"
        else:
            color = "green"
        countdown_cells.append(f"<span style='color:{color}'>{t.format_countdown()}</span>")

    data = {
        "Boss Name": [t.name for t in timers_sorted],
        "Interval (min)": [t.interval_minutes for t in timers_sorted],
        "Last Spawn": [t.last_time.strftime("%m-%d-%Y | %H:%M") for t in timers_sorted],
        "Next Spawn Date": [t.next_time.strftime("%b %d, %Y (%a)") for t in timers_sorted],
        "Next Spawn Time": [t.next_time.strftime("%I:%M %p") for t in timers_sorted],
        "Countdown": countdown_cells,
    }

    df = pd.DataFrame(data)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ------------------- Weekly Table (NEW style) -------------------
def display_weekly_boss_table_newstyle():
    upcoming = []
    now = datetime.now(tz=MANILA)

    for boss, times in weekly_boss_data:
        for sched in times:
            spawn_dt = get_next_weekly_spawn(sched)
            countdown = spawn_dt - now
            upcoming.append((boss, spawn_dt, countdown))

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

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")

# ------------------- Session defaults -------------------
st.session_state.setdefault("auth", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("page", "world")  # world | login | manage | history

def goto(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ------------------- Auto-refresh ONLY on World page -------------------
if st.session_state.page == "world":
    st_autorefresh(interval=1000, key="timer_refresh")

# ------------------- Load timers -------------------
if "timers" not in st.session_state:
    st.session_state.timers = build_timers()
timers = st.session_state.timers

for t in timers:
    t.update_next()

# ------------------- WORLD PAGE: LEFT BUTTON + CENTER BANNER (same row) -------------------
if st.session_state.page == "world":
    left_btn, mid_banner, right_space = st.columns([2, 6, 2])

    with left_btn:
        if not st.session_state.auth:
            if st.button("🔐 Admin Login"):
                goto("login")
        else:
            if st.button("🛠️ Manage / Edit"):
                goto("manage")

    with mid_banner:
        next_boss_banner_combined(timers)

else:
    # On other pages, just show the banner normally (optional)
    next_boss_banner_combined(timers)

st.divider()

# ------------------- WORLD PAGE CONTENT -------------------
if st.session_state.page == "world":
    st.subheader("🗡️ Field Boss Spawn Table (Auto-Sorted)")

    col1, col2 = st.columns([2, 1])
    with col1:
        display_boss_table_sorted_newstyle(timers)
    with col2:
        st.subheader("📅 Weekly Bosses (Auto-Sorted)")
        display_weekly_boss_table_newstyle()

# ------------------- LOGIN PAGE -------------------
elif st.session_state.page == "login":
    st.subheader("🔐 Login (Edit Access)")
    st.caption("Auto-refresh is paused here so the page won’t fold while you type.")

    with st.form("login_form_page"):
        username_in = st.text_input("Name", key="login_username_page")
        password_in = st.text_input("Password", type="password", key="login_password_page")
        login_clicked = st.form_submit_button("Login", use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back", use_container_width=True):
            goto("world")

    if login_clicked:
        if password_in == ADMIN_PASSWORD and username_in.strip():
            st.session_state.auth = True
            st.session_state.username = username_in.strip()
            st.success(f"✅ Access granted for {st.session_state.username}")
            goto("manage")
        else:
            st.error("❌ Invalid name or password.")

# ------------------- MANAGE PAGE -------------------
elif st.session_state.page == "manage":
    if not st.session_state.auth:
        st.warning("You must login first.")
        if st.button("Go to Login", use_container_width=True):
            goto("login")
    else:
        top1, top2, top3, top4 = st.columns([1.2, 1.2, 1.2, 2.4])

        with top1:
            if st.button("⏱️ Boss Tracker", use_container_width=True):
                goto("world")
        with top2:
            if st.button("📜 History", use_container_width=True):
                goto("history")
        with top3:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.auth = False
                st.session_state.username = ""
                goto("world")
        with top4:
            st.success(f"✅ Admin: {st.session_state.username}")

        st.subheader("🛠️ Edit Boss Timers (Edit Last Time, Next auto-updates)")

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

                    st.success(f"✅ {timer.name} updated! Next: {updated_next_time.strftime('%Y-%m-%d %I:%M %p')}")

# ------------------- HISTORY PAGE -------------------
elif st.session_state.page == "history":
    if not st.session_state.auth:
        st.warning("You must login first.")
        if st.button("Go to Login", use_container_width=True):
            goto("login")
    else:
        t1, t2, t3 = st.columns([1.2, 1.2, 3.6])
        with t1:
            if st.button("🛠️ Manage", use_container_width=True):
                goto("manage")
        with t2:
            if st.button("⏱️ Boss Tracker", use_container_width=True):
                goto("world")
        with t3:
            st.success(f"✅ Admin: {st.session_state.username}")

        st.subheader("📜 Edit History")

        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)

            if history:
                df_history = pd.DataFrame(history).sort_values("edited_at", ascending=False)
                st.dataframe(df_history, use_container_width=True)
            else:
                st.info("No edits yet.")
        else:
            st.info("No edit history yet.")










