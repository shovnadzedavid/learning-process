import streamlit as st
import pandas as pd
import datetime
import os

# გვერდის კონფიგურაცია - Wide რეჟიმი
st.set_page_config(
    page_title="სასწავლო განრიგის მართვის სისტემა",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# მონაცემთა ფაილი და აუდიტორიების სია
DATA_FILE = "schedule_data.csv"
AUDITORIUMS = ["აუდიტორია 1", "აუდიტორია 2", "აუდიტორია 3", "აუდიტორია 4", "საკონფერენციო დარბაზი"]
DAY_NAMES_KA = ["ორშაბათი", "სამშაბათი", "ოთხშაბათი", "ხუთშაბათი", "პარასკევი", "შაბათი", "კვირა"]
MONTHS_GE = {
    1: "იანვარი", 2: "თებერვალი", 3: "მარტი", 4: "აპრილი",
    5: "მაისი", 6: "ივნისი", 7: "ივლისი", 8: "აგვისტო",
    9: "სექტემბერი", 10: "ოქტომბერი", 11: "ნოემბერი", 12: "დეკემბერი"
}

# CSS სტილები - მობილურზე მორგება (Responsive) და Dark/Light თავსებადობა
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 16px;
    }

    /* ზედა მენიუს ღილაკები */
    div[role="radiogroup"] {
        background-color: var(--secondary-background-color);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 20px;
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    div[role="radiogroup"] label {
        padding: 8px 18px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    /* კვირის სრული ბადის კონტეინერი და ცხრილი */
    .table-scroll-wrapper {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-top: 15px;
        border-radius: 10px;
        border: 1.5px solid rgba(128, 128, 128, 0.3);
    }
    .full-grid-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 950px;
    }
    .full-grid-table th {
        background-color: #1E3A8A;
        color: #FFFFFF;
        padding: 12px 6px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        font-size: 1.05rem;
        text-align: center;
    }
    .full-grid-table td {
        border: 1px solid rgba(128, 128, 128, 0.25);
        padding: 6px;
        vertical-align: top;
    }

    /* ბარათები ცხრილის უჯრებში */
    .slot-card {
        background-color: var(--secondary-background-color);
        border: 1.5px solid #EF4444;
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        text-align: left;
    }
    .slot-time {
        background-color: #EF4444;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.95rem;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 5px;
    }
    .slot-subject {
        font-weight: 800;
        font-size: 1.05rem;
        color: var(--text-color);
        line-height: 1.25;
        margin-bottom: 3px;
    }
    .slot-lecturer {
        font-size: 0.95rem;
        color: var(--text-color);
        opacity: 0.9;
    }
    .slot-univ {
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.75;
    }

    /* აუდიტორიის მონიტორინგის ბარათები */
    .room-box {
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }
    .room-busy {
        background-color: rgba(239, 68, 68, 0.14) !important;
        border: 2px solid #EF4444 !important;
    }
    .room-free {
        background-color: rgba(16, 185, 129, 0.14) !important;
        border: 2px solid #10B981 !important;
    }

    /* შენახვის ღილაკი */
    .stButton>button {
        width: 100%;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        padding: 0.65rem 1rem !important;
        border-radius: 8px !important;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }

    /* --- მობილური ეკრანების ადაპტაცია (Responsive) --- */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem !important;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.25rem !important;
        }
        div[role="radiogroup"] {
            flex-direction: column !important;
            align-items: stretch !important;
        }
        div[role="radiogroup"] label {
            width: 100% !important;
            text-align: center !important;
            font-size: 1.0rem !important;
            padding: 10px !important;
        }
        .full-grid-table {
            min-width: 850px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# ავტორიზაციის შემოწმება (Login Gate)
# ==============================================================================
def check_auth():
    if st.session_state.get("authenticated", False):
        return True

    c_left, c_mid, c_right = st.columns((1, 2, 1))
    with c_mid:
        st.markdown("<div style='text-align: center; margin-top: 40px;'><h1>🔐 სისტემაში შესვლა</h1></div>", unsafe_allow_html=True)
        st.info("სასწავლო განრიგის სისტემა დაცულია. გთხოვთ გაიაროთ ავტორიზაცია.")
        
        with st.form("auth_form"):
            username = st.text_input("მომხმარებელი", placeholder="შეიყვანეთ მომხმარებელი")
            password = st.text_input("პაროლი", type="password", placeholder="შეიყვანეთ პაროლი")
            login_btn = st.form_submit_button("შესვლა", use_container_width=True)

        if login_btn:
            # პაროლის გადამოწმება
            valid_user = st.secrets.get("AUTH_USER", "admin") if hasattr(st, "secrets") and "AUTH_USER" in st.secrets else "admin"
            valid_pass = st.secrets.get("AUTH_PASSWORD", "admin2026") if hasattr(st, "secrets") and "AUTH_PASSWORD" in st.secrets else "admin2026"

            if username.strip() == str(valid_user).strip() and password.strip() == str(valid_pass).strip():
                st.session_state.authenticated = True
                st.session_state.current_user = username.strip()
                st.success("ავტორიზაცია წარმატებულია!")
                st.rerun()
            else:
                st.error("მომხმარებლის სახელი ან პაროლი არასწორია!")

    return False

# არაავტორიზებული მომხმარებლისთვის საიტი აქ ჩერდება
if not check_auth():
    st.stop()

# ==============================================================================
# ავტორიზებული მომხმარებლის ინტერფეისი
# ==============================================================================

# ზედა სტატუსი და გამოსვლის ღილაკი
top_info, top_logout = st.columns((8, 2))
with top_info:
    st.caption(f"👤 ავტორიზებული მომხმარებელი: **{st.session_state.get('current_user', 'admin')}**")
with top_logout:
    if st.button("🚪 გამოსვლა", key="logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# მონაცემების ჩატვირთვა
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            records = df.to_dict('records')
            for r in records:
                if r.get('auditorium') == 'აუდიტორია 5':
                    r['auditorium'] = 'საკონფერენციო დარბაზი'
                if 'include_saturday' not in r:
                    r['include_saturday'] = False
                if 'include_sunday' not in r:
                    r['include_sunday'] = False
            return records
        except Exception:
            return []
    return []

# მონაცემების შენახვა
def save_data(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv(DATA_FILE, index=False)

if 'schedule' not in st.session_state:
    st.session_state.schedule = load_data()

# კვირის ინიციალიზაცია
today = datetime.date.today()
base_monday = today - datetime.timedelta(days=today.weekday())

if 'current_monday' not in st.session_state:
    st.session_state.current_monday = base_monday

# ამოწმებს, აქტიურია თუ არა ლექცია კონკრეტულ თარიღზე
def is_event_active_on_date(item, date_obj):
    sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
    edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
    if not (sdate <= date_obj <= edate):
        return False
    
    is_sat = bool(item.get('include_saturday', False))
    is_sun = bool(item.get('include_sunday', False))
    
    if date_obj.weekday() == 5 and not is_sat:
        return False
    if date_obj.weekday() == 6 and not is_sun:
        return False
        
    return True

# კონფლიქტების შემოწმება
def check_conflicts(new_entry):
    new_sdate = datetime.datetime.strptime(new_entry['start_date'], "%Y-%m-%d").date()
    new_edate = datetime.datetime.strptime(new_entry['end_date'], "%Y-%m-%d").date()
    new_stime = datetime.datetime.strptime(new_entry['start_time'], "%H:%M").time()
    new_etime = datetime.datetime.strptime(new_entry['end_time'], "%H:%M").time()
    
    aud_conflicts = []
    lec_conflicts = []

    for item in st.session_state.schedule:
        item_sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
        item_edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
        item_stime = datetime.datetime.strptime(str(item['start_time']), "%H:%M").time()
        item_etime = datetime.datetime.strptime(str(item['end_time']), "%H:%M").time()

        time_overlap = not (new_etime <= item_stime or new_stime >= item_etime)
        if not time_overlap:
            continue

        overlap_start = max(new_sdate, item_sdate)
        overlap_end = min(new_edate, item_edate)
        if overlap_start > overlap_end:
            continue

        has_common_active_day = False
        cur_d = overlap_start
        while cur_d <= overlap_end:
            if is_event_active_on_date(new_entry, cur_d) and is_event_active_on_date(item, cur_d):
                has_common_active_day = True
                break
            cur_d += datetime.timedelta(days=1)

        if has_common_active_day:
            item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
            new_aud = "საკონფერენციო დარბაზი" if new_entry['auditorium'] == "აუდიტორია 5" else new_entry['auditorium']
            
            if item_aud == new_aud:
                aud_conflicts.append(item)
            if str(item['lecturer']).strip().lower() == str(new_entry['lecturer']).strip().lower():
                lec_conflicts.append(item)

    return aud_conflicts, lec_conflicts

# ზედა ნავიგაცია
selected_page = st.radio(
    "გვერდის არჩევა",
    (
        "📅 კვირის სრული ბადე (სრული ეკრანი)", 
        "➕ ახალი ჯგუფის დამატება & მართვა", 
        "📊 საათების რეპორტი & მონიტორინგი"
    ),
    horizontal=True,
    label_visibility="collapsed"
)

# ==============================================================================
# გვერდი 1: კვირის სრული ბადე (100% ეკრანი, სენსორული სქროლით)
# ==============================================================================
if selected_page == "📅 კვირის სრული ბადე (სრული ეკრანი)":
    cur_mon = st.session_state.current_monday
    cur_sun = cur_mon + datetime.timedelta(days=6)
    week_dates = [cur_mon + datetime.timedelta(days=i) for i in range(7)]

    m1 = MONTHS_GE[cur_mon.month]
    m2 = MONTHS_GE[cur_sun.month]
    if cur_mon.month == cur_sun.month:
        week_label = f"{cur_mon.day} – {cur_sun.day} {m1}, {cur_mon.year}"
    else:
        week_label = f"{cur_mon.day} {m1} – {cur_sun.day} {m2}, {cur_mon.year}"

    st.markdown(f"## 📅 {week_label}")

    n_col1, n_col2, n_col3, n_col4 = st.columns((1, 1, 1, 2))
    with n_col1:
        if st.button("⬅️ წინა კვირა", key="btn_prev", use_container_width=True):
            st.session_state.current_monday -= datetime.timedelta(days=7)
            st.rerun()
    with n_col2:
        if st.button("📍 მიმდინარე კვირა", key="btn_cur", use_container_width=True):
            st.session_state.current_monday = base_monday
            st.rerun()
    with n_col3:
        if st.button("შემდეგი კვირა ➡️", key="btn_next", use_container_width=True):
            st.session_state.current_monday += datetime.timedelta(days=7)
            st.rerun()
    with n_col4:
        picked = st.date_input("თარიღზე გადასვლა:", value=cur_mon, label_visibility="collapsed")
        new_mon = picked - datetime.timedelta(days=picked.weekday())
        if new_mon != cur_mon:
            st.session_state.current_monday = new_mon
            st.rerun()

    st.caption("💡 მობილურზე/ტაბლეტზე: შეგიძლიათ ცხრილის თითით მარჯვნივ-მარცხნივ გადაფურცვლა.")

    grid_html = [
        '<div class="table-scroll-wrapper">',
        '<table class="full-grid-table">',
        '<thead><tr>',
        '<th style="width: 14%; min-width: 150px;">აუდიტორია</th>'
    ]

    for d, name in zip(week_dates, DAY_NAMES_KA):
        d_short = f"{d.day} {MONTHS_GE[d.month][:3]}"
        is_today = (d == today)
        bg = "#2563EB" if is_today else "#1E3A8A"
        grid_html.append(
            f'<th style="background-color: {bg};">'
            f'<b>{name}</b><br><span style="font-size: 0.95rem; opacity: 0.9;">{d_short}</span>'
            f'</th>'
        )
    grid_html.append('</tr></thead><tbody>')

    for aud in AUDITORIUMS:
        grid_html.append(
            f'<tr>'
            f'<td style="background-color: var(--secondary-background-color); color: var(--text-color); font-weight: 800; font-size: 1.15rem; text-align: center; vertical-align: middle;">'
            f'{aud}'
            f'</td>'
        )

        for d in week_dates:
            matching = []
            for item in st.session_state.schedule:
                item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
                if item_aud == aud and is_event_active_on_date(item, d):
                    matching.append(item)

            matching.sort(key=lambda x: str(x['start_time']))

            if matching:
                grid_html.append('<td style="background-color: rgba(239, 68, 68, 0.06); min-width: 135px;">')
                for m in matching:
                    grid_html.append(
                        f'<div class="slot-card">'
                        f'<div class="slot-time">⏰ {m["start_time"]} - {m["end_time"]}</div>'
                        f'<div class="slot-subject">{m["subject"]}</div>'
                        f'<div class="slot-lecturer">👨‍🏫 {m["lecturer"]}</div>'
                        f'<div class="slot-univ">🏛️ {m["university"]}</div>'
                        f'</div>'
                    )
                grid_html.append('</td>')
            else:
                grid_html.append(
                    '<td style="text-align: center; vertical-align: middle; color: var(--text-color); opacity: 0.25; font-size: 1.2rem; min-width: 135px;">—</td>'
                )
        grid_html.append('</tr>')

    grid_html.append('</tbody></table></div>')
    st.markdown("".join(grid_html), unsafe_allow_html=True)

# ==============================================================================
# გვერდი 2: ახალი ჯგუფის დამატება & მართვა
# ==============================================================================
elif selected_page == "➕ ახალი ჯგუფის დამატება & მართვა":
    st.subheader("➕ ახალი ჯგუფის დამატება და კონფლიქტების შემოწმება")
    
    col_add, col_list = st.columns((4, 6), gap="large")
    
    with col_add:
        with st.form(key="lecture_form_page", clear_on_submit=False):
            university = st.text_input("1. უნივერსიტეტი*", placeholder="მაგ. თბილისის სახელმწიფო უნივერსიტეტი")
            subject = st.text_input("2. საგანი*", placeholder="მაგ. საზოგადოებრივი ჯანდაცვა")
            lecturer = st.text_input("3. ლექტორი*", placeholder="მაგ. გიორგი ბერიძე")
            auditorium = st.selectbox("აუდიტორია*", AUDITORIUMS)
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                start_date = st.date_input("4. დაწყების თარიღი*", value=datetime.date.today())
            with c_d2:
                end_date = st.date_input("5. დასრულების თარიღი*", value=datetime.date.today())
                
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                start_time = st.time_input("6. დაწყების საათი*", value=datetime.time(10, 0))
            with c_t2:
                end_time = st.time_input("დასრულების საათი*", value=datetime.time(12, 0))

            st.markdown("<b>📅 უქმე დღეების ჩართვა (არასავალდებულო):</b>", unsafe_allow_html=True)
            c_sat, c_sun = st.columns(2)
            with c_sat:
                include_sat = st.checkbox("შაბათის ჩათვლით", value=False)
            with c_sun:
                include_sun = st.checkbox("კვირის ჩათვლით", value=False)

            st.caption("ℹ️ თუ არ მონიშნავთ, ლექცია ჩაისმება მხოლოდ ორშაბათიდან პარასკევის ჩათვლით.")

            submitted = st.form_submit_button("💾 ჯგუფის შენახვა")

        if submitted:
            if not university.strip() or not subject.strip() or not lecturer.strip():
                st.error("⚠️ გთხოვთ შეავსოთ ყველა სავალდებულო ველი!")
            elif start_date > end_date:
                st.error("⚠️ დაწყების თარიღი არ შეიძლება იყოს დასრულების თარიღზე გვიან!")
            elif start_time >= end_time:
                st.error("⚠️ დაწყების საათი უნდა უსწრებდეს დასრულების საათს!")
            else:
                new_entry = {
                    "university": university.strip(),
                    "subject": subject.strip(),
                    "lecturer": lecturer.strip(),
                    "auditorium": auditorium,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "start_time": start_time.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                    "include_saturday": bool(include_sat),
                    "include_sunday": bool(include_sun)
                }

                aud_conflicts, lec_conflicts = check_conflicts(new_entry)

                if aud_conflicts and lec_conflicts:
                    st.error("❌ ლექტორი დაკავებულია და აუდიტორია დაკავებულია")
                    for c in aud_conflicts:
                        st.warning(f"📌 {c['auditorium']}: დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
                    for c in lec_conflicts:
                        st.warning(f"📌 {c['lecturer']}: დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
                elif aud_conflicts:
                    st.error("❌ აუდიტორია დაკავებულია")
                    for c in aud_conflicts:
                        st.warning(f"📌 {c['auditorium']}: უკვე დაკავებულია საგნით '{c['subject']}' ({c['lecturer']}) ({c['start_time']} - {c['end_time']})")
                elif lec_conflicts:
                    st.error("❌ ლექტორი დაკავებულია")
                    for c in lec_conflicts:
                        st.warning(f"📌 ლექტორი {c['lecturer']} უკვე დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
                else:
                    st.session_state.schedule.append(new_entry)
                    save_data(st.session_state.schedule)
                    st.success("✅ ჯგუფი წარმატებით შეინახა!")
                    st.rerun()

    with col_list:
        st.subheader("📋 არსებული ჯგუფები და წაშლა")
        if not st.session_state.schedule:
            st.info("ბაზაში ჯერ ჩანაწერები არ არის.")
        else:
            del_options = {
                f"#{i+1} {d['subject']} ({d['auditorium']}, {d['lecturer']} [{d['start_time']}-{d['end_time']}])": i 
                for i, d in enumerate(st.session_state.schedule)
            }
            to_delete = st.selectbox("აირჩიეთ წასაშლელი ჩანაწერი:", list(del_options.keys()))
            if st.button("🗑️ არჩეული ჯგუფის წაშლა", use_container_width=True):
                idx_to_del = del_options[to_delete]
                st.session_state.schedule.pop(idx_to_del)
                save_data(st.session_state.schedule)
                st.success("ჩანაწერი წაშლილია!")
                st.rerun()

            st.markdown("---")
            df_export = pd.DataFrame(st.session_state.schedule)
            csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ბაზის გადმოწერა (CSV)",
                data=csv_bytes,
                file_name="lecture_schedule.csv",
                mime="text/csv",
                use_container_width=True
            )

# ==============================================================================
# გვერდი 3: საათების რეპორტი & მონიტორინგი
# ==============================================================================
elif selected_page == "📊 საათების რეპორტი & მონიტორინგი":
    tab_report, tab_day, tab_cards = st.tabs([
        "📊 ლექტორების საათების რეპორტი", 
        "🏛️ 5 აუდიტორიის დღიური სტატუსი", 
        "📋 ყველა ჯგუფის ბარათები"
    ])

    # 1. საათების ზუსტი რეპორტი
    with tab_report:
        st.subheader("📊 ლექტორების ჩატარებული საათების რეპორტი")
        st.caption("ℹ️ საათები ზუსტად ითვლება იმ დღეების მიხედვით, როდესაც ლექცია რეალურად ტარდება (შაბათ-კვირის გათვალისწინებით).")

        if not st.session_state.schedule:
            st.info("რეპორტისთვის მონაცემები ჯერ არ არის.")
        else:
            lecturer_summary = {}

            for item in st.session_state.schedule:
                lec = str(item['lecturer']).strip()
                sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
                edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
                
                stime = datetime.datetime.strptime(str(item['start_time']), "%H:%M")
                etime = datetime.datetime.strptime(str(item['end_time']), "%H:%M")
                session_duration = (etime - stime).total_seconds() / 3600.0

                actual_sessions = 0
                cur_d = sdate
                while cur_d <= edate:
                    if is_event_active_on_date(item, cur_d):
                        actual_sessions += 1
                    cur_d += datetime.timedelta(days=1)

                item_total_hours = round(actual_sessions * session_duration, 2)

                if lec not in lecturer_summary:
                    lecturer_summary[lec] = {
                        "ლექტორი": lec,
                        "უნივერსიტეტი": set(),
                        "საგნები": set(),
                        "ლექციების რაოდენობა": 0,
                        "სრული საათები": 0.0
                    }

                lecturer_summary[lec]["უნივერსიტეტი"].add(str(item['university']))
                lecturer_summary[lec]["საგნები"].add(str(item['subject']))
                lecturer_summary[lec]["ლექციების რაოდენობა"] += actual_sessions
                lecturer_summary[lec]["სრული საათები"] += item_total_hours

            report_rows = []
            for lec, data in lecturer_summary.items():
                report_rows.append({
                    "ლექტორი": data["ლექტორი"],
                    "უნივერსიტეტი": ", ".join(data["უნივერსიტეტი"]),
                    "საგნები": ", ".join(data["საგნები"]),
                    "სულ ლექციები": data["ლექციების რაოდენობა"],
                    "სრული საათები": round(data["სრული საათები"], 2)
                })

            df_rep = pd.DataFrame(report_rows)
            df_rep.sort_values(by="სრული საათები", ascending=False, inplace=True)
            
            st.dataframe(df_rep, use_container_width=True, hide_index=True)

            csv_rep_bytes = df_rep.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ლექტორების საათების რეპორტის გადმოწერა (CSV)",
                data=csv_rep_bytes,
                file_name="lecturers_hours_report.csv",
                mime="text/csv",
                use_container_width=True
            )

    # 2. დღიური მონიტორინგი
    with tab_day:
        selected_monitor_date = st.date_input("აირჩიეთ თარიღი:", value=datetime.date.today(), key="mon_day_p3")
        
        room_cols = st.columns(5)
        for i, room in enumerate(AUDITORIUMS):
            with room_cols[i]:
                st.markdown(f"### {room}")
                room_events = [
                    item for item in st.session_state.schedule 
                    if (item['auditorium'] == room or (item['auditorium'] == 'აუდიტორია 5' and room == 'საკონფერენციო დარბაზი'))
                    and is_event_active_on_date(item, selected_monitor_date)
                ]
                room_events.sort(key=lambda x: str(x['start_time']))
                
                if room_events:
                    for ev in room_events:
                        card_html = (
                            f'<div class="room-box room-busy">'
                            f'<div style="background-color: #EF4444; color: #FFFFFF; padding: 4px 8px; border-radius: 6px; font-weight: 800; display: inline-block; margin-bottom: 8px; font-size: 1.05rem;">⛔ {ev["start_time"]} - {ev["end_time"]}</div>'
                            f'<div style="font-size: 1.1rem; font-weight: 800; color: var(--text-color); margin-bottom: 4px;">{ev["subject"]}</div>'
                            f'<div style="font-size: 1.0rem; color: var(--text-color); margin-bottom: 4px;"><b>ლექტორი:</b> {ev["lecturer"]}</div>'
                            f'<div style="font-size: 0.95rem; color: var(--text-color); opacity: 0.85;"><b>უნივერსიტეტი:</b> {ev["university"]}</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                else:
                    free_html = (
                        f'<div class="room-box room-free">'
                        f'<div style="background-color: #10B981; color: #FFFFFF; padding: 4px 8px; border-radius: 6px; font-weight: 800; display: inline-block; margin-bottom: 8px; font-size: 1.05rem;">✅ თავისუფალია</div>'
                        f'<div style="font-size: 0.95rem; color: var(--text-color); opacity: 0.9;">მთელი დღის განმავლობაში</div>'
                        f'</div>'
                    )
                    st.markdown(free_html, unsafe_allow_html=True)

    # 3. ყველა ჯგუფის ბარათები
    with tab_cards:
        if not st.session_state.schedule:
            st.info("განრიგში ჯერ მონაცემები არ არის.")
        else:
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_aud = st.multiselect("ფილტრი აუდიტორიით:", AUDITORIUMS, default=AUDITORIUMS)
            with f_col2:
                filter_search = st.text_input("ძიება:", "")

            filtered_data = []
            for idx, item in enumerate(st.session_state.schedule):
                item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
                if item_aud in filter_aud:
                    text_blob = f"{item['university']} {item['subject']} {item['lecturer']}".lower()
                    if not filter_search or filter_search.lower() in text_blob:
                        filtered_data.append(item)

            if filtered_data:
                grid_cols = st.columns(2)
                for i, row in enumerate(filtered_data):
                    target_col = grid_cols[i % 2]
                    sat_label = " • შაბათი" if row.get('include_saturday') else ""
                    sun_label = " • კვირა" if row.get('include_sunday') else ""
                    days_note = f"ორშ-პარ{sat_label}{sun_label}"
                    
                    with target_col:
                        card_html = (
                            f'<div class="schedule-card" style="background-color: var(--secondary-background-color); border: 1.5px solid rgba(128, 128, 128, 0.25); border-radius: 12px; padding: 18px; margin-bottom: 16px;">'
                            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">'
                            f'<span style="font-size: 1.25rem; font-weight: 800; color: var(--text-color);">{row["subject"]}</span>'
                            f'<span style="background-color: #2563EB; color: #FFFFFF; font-size: 0.95rem; font-weight: 700; padding: 4px 10px; border-radius: 6px;">{row["auditorium"]}</span>'
                            f'</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 6px;"><b>👨‍🏫 ლექტორი:</b> {row["lecturer"]}</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 6px;"><b>🏛️ უნივერსიტეტი:</b> {row["university"]}</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 6px;"><b>📅 პერიოდი:</b> {row["start_date"]} — {row["end_date"]}</div>'
                            f'<div style="font-size: 0.95rem; color: #2563EB; font-weight: 700; margin-bottom: 10px;">📆 დღეები: {days_note}</div>'
                            f'<div style="display: inline-block; background-color: rgba(37, 99, 235, 0.15); border: 1.5px solid #2563EB; color: var(--text-color); font-size: 1.1rem; font-weight: 800; padding: 5px 12px; border-radius: 8px;">'
                            f'⏰ {row["start_time"]} – {row["end_time"]}'
                            f'</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
