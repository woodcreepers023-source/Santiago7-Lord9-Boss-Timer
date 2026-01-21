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
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"  # <-- put your webhook here
DATA_FILE = Path("boss_timers.json")
HISTORY_FILE = Path("boss_history.json")
ADMIN_PASSWORD = "bestgame"

# ------------------- Discord -------------------
def send_discord_message(message: str):
    """Send a message to Discord via webhook."""
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
    # Atomic-ish write to reduce corruption risk on frequent refresh
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    tmp.replace(DATA_FILE)

def parse_dt(last_time_str: str) -> datetime:
    dt = datetime.strptime(last_time_str, "%Y-%m-%d %I:%M %p")
    return dt.replace(tzinfo=MANILA)

def load_boss_data():
    """
    Stored format in JSON: [ [name, interval_minutes, last_time_str], ... ]
    """
    data = _safe_load_json(DATA_FILE, None)

    if data is None:
        data = default_boss_data.copy()
        save_boss_data(data)
    else:
        # normalize if list[dict]
        if data and isinstance(data[0], dict):
            normalized = []
            for d in data:
                name = d.get("name")
                interval = d.get("interval_minutes")
                last_str = d.get("last_time_str")
                if name is not None and interval is not None and last_str:
                    normalized.append((name, int(interval), last_str))
            data = normalized
            save_boss_data(data)

    # ensure Supore exists
    if not any(str(boss[0]).strip().lower() == "supore" for boss in data):
        data.append(("Supore", 3720, "2025-09-20 07:15 AM"))
        save_boss_data(data)

    return data

# ------------------- Edit History -------------------
def log_edit(boss_name, old_time, new_time):
    history = _safe_load_json(HISTORY_FILE, [])
    edited_by = st.session_state.get("username", "Unknown")

    entry = {
        "boss": boss_name,
        "old_time": old_time,
        "new_time": new_time,
        "edited_at": datetime.now(tz=MANILA).strftime("%m-%d-%Y : %I:%M %p"),
        "edited_by": edited_by,
    }

    history.append(entry)
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    send_discord_message(
        f"🛠 **{boss_name}** time updated by **{edited_by}**\n"
        f"Old: `{old_time}` → New: `{new_time}` (Manila time)"
    )

def _parse_history_dt(s: str):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    fmts = [
        "%m-%d-%Y | %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %H:%M",
        "%m-%d-%Y %H:%M",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).replace(tzinfo=MANILA)
        except Exception:
            pass
    return None

def _parse_edited_at(s: str):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    fmts = [
        "%m-%d-%Y : %I:%M %p",
        "%Y-%m-%d %I:%M %p",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).replace(tzinfo=MANILA)
        except Exception:
            pass
    return None

def normalize_history_file():
    if not HISTORY_FILE.exists():
        return

    history = _safe_load_json(HISTORY_FILE, [])
    if not history:
        return

    changed = False
    for row in history:
        if not isinstance(row, dict):
            continue

        for k in ["old_time", "new_time"]:
            dt = _parse_history_dt(row.get(k, ""))
            if dt is not None:
                new_val = dt.strftime("%m-%d-%Y | %H:%M")
                if row.get(k) != new_val:
                    row[k] = new_val
                    changed = True

        dt_e = _parse_edited_at(row.get("edited_at", ""))
        if dt_e is not None:
            new_val = dt_e.strftime("%m-%d-%Y : %I:%M %p")
            if row.get("edited_at") != new_val:
                row["edited_at"] = new_val
                changed = True

    if changed:
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)

# ------------------- Timer Class -------------------
class TimerEntry:
    def __init__(self, name, interval_minutes, last_time_str):
        self.name = name
        self.interval_minutes = int(interval_minutes)
        self.interval = timedelta(minutes=self.interval_minutes)

        self._parse_fixed = False
        try:
            parsed_time = parse_dt(last_time_str)
        except Exception:
            parsed_time = datetime.now(tz=MANILA)
            self._parse_fixed = True

        self.last_time = parsed_time
        self.next_time = self.last_time + self.interval

    def promote_if_due(self, now: datetime) -> bool:
        """
        If next_time already passed, promote:
        last_time = next_time, next_time = last_time + interval
        Returns True if changed.
        """
        changed = False
        # Use <= so exact hit promotes too
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

# ------------------- Maintenance-safe refresh -------------------
def refresh_and_maybe_save(timers_list):
    """
    Auto-promote last spawn WHEN due, and save to JSON,
    BUT only when Maintenance Mode is OFF.
    """
    now = datetime.now(tz=MANILA)
    changed = False

    for t in timers_list:
        if getattr(t, "_parse_fixed", False):
            changed = True
            t._parse_fixed = False

        if t.promote_if_due(now):
            changed = True

    # Only write JSON when maintenance mode is OFF
    if changed and not st.session_state.get("maintenance_mode", False):
        save_boss_data(
            [(t.name, t.interval_minutes, t.last_time.strftime("%Y-%m-%d %I:%M %p")) for t in timers_list]
        )

# ------------------- Edit Inputs Sync Helpers -------------------
def _mark_dirty(timer_name: str):
    st.session_state[f"{timer_name}_dirty"] = True

def sync_edit_widgets_from_timer(timer: TimerEntry):
    """
    Keep Edit tab inputs matching Field Boss Table 'Last Spawn',
    unless user is currently editing that boss (dirty flag).
    """
    date_key = f"{timer.name}_last_date"
    time_key = f"{timer.name}_last_time"
    dirty_key = f"{timer.name}_dirty"

    if not st.session_state.get(dirty_key, False):
        st.session_state[date_key] = timer.last_time.date()
        st.session_state[time_key] = timer.last_time.time().replace(second=0, microsecond=0)

# ------------------- Streamlit Setup -------------------
st.set_page_config(page_title="Lord9 Santiago 7 Boss Timer", layout="wide")
st.title("🛡️ Lord9 Santiago 7 Boss Timer")
st_autorefresh(interval=1000, key="timer_refresh")

if "timers" not in st.session_state:
    st.session_state.timers = build_timers()

# ------------------- Password Gate -------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.subheader("🔐 Login to Edit Timers")

    with st.form("login_form"):
        username = st.text_input("Enter your name:", key="login_username")
        password = st.text_input("🔑 Enter password to edit timers:", type="password", key="login_password")
        login_clicked = st.form_submit_button("Login")  # ✅ must be inside the form

    if login_clicked:
        if password.strip() == ADMIN_PASSWORD and username.strip():
            st.session_state.auth = True
            st.session_state.username = username.strip()
            st.success(f"✅ Access granted for {st.session_state.username}")
            st.rerun()
        else:
            st.error("❌ Invalid name or password.")

# ✅ Admin tools
if st.session_state.get("auth", False):
    if st.button("🔄 Reload timers from JSON"):
        st.session_state.timers = build_timers()
        st.success("Reloaded timers from boss_timers.json")
        st.rerun()

# ------------------- Maintenance Mode Toggle -------------------
if "maintenance_mode" not in st.session_state:
    st.session_state.maintenance_mode = False

if st.session_state.get("auth", False):
    st.session_state.maintenance_mode = st.toggle(
        "🛠️ Maintenance Mode (prevents auto-changing + auto-save)",
        value=st.session_state.maintenance_mode,
        help="Turn ON during maintenance while you mass-edit times. Turn OFF after maintenance so timers auto-update again.",
    )

timers = st.session_state.timers
refresh_and_maybe_save(timers)

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

# ------------------- Next Boss Banner -------------------
def next_boss_banner(timers_list):
    if not timers_list:
        st.warning("No timers loaded.")
        return

    field_next = min(timers_list, key=lambda x: x.next_time)
    now = datetime.now(tz=MANILA)
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

# ------------------- Auto-Sorted Field Boss Table -------------------
def display_boss_table_sorted(timers_list):
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

# ------------------- Weekly Table -------------------
def display_weekly_boss_table():
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
    st.subheader("🗡️ Field Boss Spawn Table")

    col1, col2 = st.columns([2, 1])
    with col1:
        display_boss_table_sorted(timers)
    with col2:
        st.subheader("📅 Fixed Time Field Boss Spawn Table")
        display_weekly_boss_table()

# Tab 2: Manage & Edit Timers
if st.session_state.auth:
    with tab_selection[1]:
        st.subheader("Edit Boss Timers (Last Spawn auto-updates AFTER it passes, when Maintenance Mode is OFF)")

        for i, timer in enumerate(timers):
            with st.expander(f"Edit {timer.name}"):

                sync_edit_widgets_from_timer(timer)

                date_key = f"{timer.name}_last_date"
                time_key = f"{timer.name}_last_time"
                dirty_key = f"{timer.name}_dirty"

                new_date = st.date_input(
                    f"{timer.name} Last Date",
                    key=date_key,
                    on_change=_mark_dirty,
                    args=(timer.name,),
                )
                new_time = st.time_input(
                    f"{timer.name} Last Time",
                    key=time_key,
                    step=timedelta(minutes=1),
                    on_change=_mark_dirty,
                    args=(timer.name,),
                )

                notice_key = f"save_notice_{timer.name}"
                notice_ts_key = f"save_notice_ts_{timer.name}"

                if notice_key in st.session_state and notice_ts_key in st.session_state:
                    age = (datetime.now(tz=MANILA) - st.session_state[notice_ts_key]).total_seconds()
                    if age < 1:
                        st.success(st.session_state[notice_key])
                    else:
                        del st.session_state[notice_key]
                        del st.session_state[notice_ts_key]

                if st.button(f"Save {timer.name}", key=f"save_{timer.name}"):
                    old_time_str = timer.last_time.strftime("%m-%d-%Y | %H:%M")

                    updated_last_time = datetime.combine(new_date, new_time).replace(tzinfo=MANILA)
                    updated_next_time = updated_last_time + timer.interval

                    st.session_state.timers[i].last_time = updated_last_time
                    st.session_state.timers[i].next_time = updated_next_time

                    save_boss_data(
                        [
                            (t.name, t.interval_minutes, t.last_time.strftime("%Y-%m-%d %I:%M %p"))
                            for t in st.session_state.timers
                        ]
                    )

                    log_edit(
                        timer.name,
                        old_time_str,
                        updated_last_time.strftime("%m-%d-%Y | %H:%M"),
                    )

                    st.session_state[dirty_key] = False

                    st.session_state[notice_key] = (
                        f"✅ {timer.name} saved! Next: {updated_next_time.strftime('%m-%d-%Y | %H:%M')}"
                    )
                    st.session_state[notice_ts_key] = datetime.now(tz=MANILA)

                    st.rerun()

# Tab 3: Edit History
if st.session_state.auth:
    with tab_selection[2]:
        st.subheader("Edit History")

        normalize_history_file()

        if HISTORY_FILE.exists():
            history = _safe_load_json(HISTORY_FILE, [])
            if history:
                df_history = pd.DataFrame(history)

                df_history["edited_at_dt"] = pd.to_datetime(
                    df_history["edited_at"],
                    format="%m-%d-%Y : %I:%M %p",
                    errors="coerce",
                )

                df_history = (
                    df_history.sort_values("edited_at_dt", ascending=False)
                    .drop(columns=["edited_at_dt"])
                    .reset_index(drop=True)
                )

                st.dataframe(df_history, use_container_width=True)
            else:
                st.info("No edits yet.")
        else:
            st.info("No edit history yet.")
