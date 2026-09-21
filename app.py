import streamlit as st
import pandas as pd
import datetime
import os
import json
import urllib.request

# გვერდის კონფიგურაცია
st.set_page_config(
    page_title="სასწავლო განრიგის მართვის სისტემა",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# მუდმივები
DATA_FILE = "schedule_data.csv"
AUDITORIUMS = ["აუდიტორია 1", "აუდიტორია 2", "აუდიტორია 3", "აუდიტორია 4", "საკონფერენციო დარბაზი"]
DAY_NAMES_KA = ["ორშაბათი", "სამშაბათი", "ოთხშაბათი", "ხუთშაბათი", "პარასკევი", "შაბათი", "კვირა"]
MONTHS_GE = {
    1: "იანვარი", 2: "თებერვალი", 3: "მარტი", 4: "აპრილი",
    5: "მაისი", 6: "ივნისი", 7: "ივლისი", 8: "აგვისტო",
    9: "სექტემბერი", 10: "ოქტომბერი", 11: "ნოემბერი", 12: "დეკემბერი"
}

# CSS სტილები
st.markdown("""
<style>
    html, body, [class*="css"] { font-size: 16px; }
    div[role="radiogroup"] {
        background-color: var(--secondary-background-color);
        padding: 6px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 20px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;
    }
    div[role="radiogroup"] label {
        padding: 8px 18px !important; font-size: 1.05rem !important; font-weight: 700 !important; border-radius: 8px !important;
    }
    .table-scroll-wrapper {
        width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;
        margin-top: 15px; border-radius: 10px; border: 1.5px solid rgba(128,128,128,0.3);
    }
    .full-grid-table { width: 100%; border-collapse: collapse; min-width: 950px; }
    .full-grid-table th {
        background-color: #1E3A8A; color: #FFFFFF; padding: 12px 6px;
        border: 1px solid rgba(128,128,128,0.3); font-size: 1.05rem; text-align: center;
    }
    .full-grid-table td { border: 1px solid rgba(128,128,128,0.25); padding: 6px; vertical-align: top; }
    .slot-card {
        background-color: var(--secondary-background-color); border: 1.5px solid #EF4444;
        border-radius: 8px; padding: 8px 10px; margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08); text-align: left;
    }
    .slot-time {
        background-color: #EF4444; color: #FFFFFF; font-weight: 800; font-size: 0.95rem;
        padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 4px;
    }
    .slot-subject { font-weight: 800; font-size: 1.05rem; color: var(--text-color); line-height: 1.25; margin-bottom: 3px; }
    .slot-lecturer { font-size: 0.95rem; color: var(--text-color); opacity: 0.9; }
    .slot-univ { font-size: 0.85rem; color: var(--text-color); opacity: 0.75; }
    .stButton>button {
        width: 100%; font-size: 1.1rem !important; font-weight: 700 !important;
        padding: 0.6rem 1rem !important; border-radius: 8px !important;
        background-color: #2563EB !important; color: #FFFFFF !important; border: none !important;
    }
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.5rem !important; }
        div[role="radiogroup"] { flex-direction: column !important; }
    }
</style>
""", unsafe_allow_html=True)

# ავტორიზაციის შემოწმება
def check_auth():
    if st.session_state.get("authenticated", False):
        return True
    c_left, c_mid, c_right = st.columns((1, 2, 1))
    with c_mid:
        st.markdown("<div style='text-align: center; margin-top: 40px;'><h1>🔐 სისტემაში შესვლა</h1></div>", unsafe_allow_html=True)
        with st.form("auth_form"):
            username = st.text_input("მომხმარებელი", placeholder="admin")
            password = st.text_input("პაროლი", type="password", placeholder="••••••••")
            login_btn = st.form_submit_button("შესვლა", use_container_width=True)
        if login_btn:
            valid_user = st.secrets.get("AUTH_USER", "admin") if hasattr(st, "secrets") and "AUTH_USER" in st.secrets else "admin"
            valid_pass = st.secrets.get("AUTH_PASSWORD", "admin2026") if hasattr(st, "secrets") and "AUTH_PASSWORD" in st.secrets else "admin2026"
            if username.strip() == str(valid_user).strip() and password.strip() == str(valid_pass).strip():
                st.session_state.authenticated = True
                st.session_state.current_user = username.strip()
                st.rerun()
            else:
                st.error("მომხმარებლის სახელი ან პაროლი არასწორია!")
    return False

if not check_auth():
    st.stop()

# ჰედერი და გამოსვლა
top_info, top_logout = st.columns((8, 2))
with top_info:
    st.caption(f"👤 ავტორიზებული: **{st.session_state.get('current_user', 'admin')}**")
with top_logout:
    if st.button("🚪 გამოსვლა", key="logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# მონაცემების შენახვა/ჩატვირთვა
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            records = df.to_dict('records')
            for r in records:
                if r.get('auditorium') == 'აუდიტორია 5':
                    r['auditorium'] = 'საკონფერენციო დარბაზი'
                r['include_saturday'] = bool(r.get('include_saturday', False))
                r['include_sunday'] = bool(r.get('include_sunday', False))
            return records
        except Exception:
            return []
    return []

def save_data(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv(DATA_FILE, index=False)

if 'schedule' not in st.session_state:
    st.session_state.schedule = load_data()

today = datetime.date.today()
base_monday = today - datetime.timedelta(days=today.weekday())

if 'current_monday' not in st.session_state:
    st.session_state.current_monday = base_monday

def is_event_active_on_date(item, date_obj):
    sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
    edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
    if not (sdate <= date_obj <= edate):
        return False
    if date_obj.weekday() == 5 and not item.get('include_saturday', False):
        return False
    if date_obj.weekday() == 6 and not item.get('include_sunday', False):
        return False
    return True

def check_conflicts(new_entry):
    new_sdate = datetime.datetime.strptime(str(new_entry['start_date']), "%Y-%m-%d").date()
    new_edate = datetime.datetime.strptime(str(new_entry['end_date']), "%Y-%m-%d").date()
    new_stime = datetime.datetime.strptime(str(new_entry['start_time']), "%H:%M").time()
    new_etime = datetime.datetime.strptime(str(new_entry['end_time']), "%H:%M").time()
    
    aud_conflicts, lec_conflicts = [], []
    for item in st.session_state.schedule:
        item_stime = datetime.datetime.strptime(str(item['start_time']), "%H:%M").time()
        item_etime = datetime.datetime.strptime(str(item['end_time']), "%H:%M").time()
        if not (new_etime > item_stime and new_stime < item_etime):
            continue

        item_sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
        item_edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
        overlap_start = max(new_sdate, item_sdate)
        overlap_end = min(new_edate, item_edate)
        if overlap_start > overlap_end:
            continue

        has_common = False
        cur_d = overlap_start
        while cur_d <= overlap_end:
            if is_event_active_on_date(new_entry, cur_d) and is_event_active_on_date(item, cur_d):
                has_common = True
                break
            cur_d += datetime.timedelta(days=1)

        if has_common:
            item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
            new_aud = "საკონფერენციო დარბაზი" if new_entry['auditorium'] == "აუდიტორია 5" else new_entry['auditorium']
            if item_aud == new_aud:
                aud_conflicts.append(item)
            if str(item['lecturer']).strip().lower() == str(new_entry['lecturer']).strip().lower():
                lec_conflicts.append(item)
    return aud_conflicts, lec_conflicts

def call_gemini_parser(api_key, raw_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"""
მომხმარებელმა მოგაწოდა არეული ტექსტი ლექციების შესახებ.
ამოიღე ყველა ლექცია და დააბრუნე მკაცრად JSON მასივი:
[
  {{
    "university": "უნივერსიტეტი",
    "subject": "საგანი",
    "lecturer": "ლექტორი",
    "auditorium": "ერთ-ერთი: 'აუდიტორია 1', 'აუდიტორია 2', 'აუდიტორია 3', 'აუდიტორია 4', 'საკონფერენციო დარბაზი'",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "include_saturday": false,
    "include_sunday": false
  }}
]
წელი: {datetime.date.today().year}. დააბრუნე მხოლოდ სუფთა JSON, ```json მარკდაუნის გარეშე.
ტექსტი:
{raw_text}
"""
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=35) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        for prefix in ["```json", "```"]:
            if text.startswith(prefix): text = text[len(prefix):]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text.strip())

# ზედა ნავიგაცია
selected_page = st.radio(
    "გვერდის არჩევა",
    (
        "📅 კვირის სრული ბადე (სრული ეკრანი)", 
        "➕ ახალი ჯგუფის დამატება & მართვა",
        "🤖 AI ჭკვიანი იმპორტი (ტექსტიდან)",
        "📊 საათების რეპორტი & სია"
    ),
    horizontal=True,
    label_visibility="collapsed"
)

# 1. კვირის სრული ბადე
if selected_page == "📅 კვირის სრული ბადე (სრული ეკრანი)":
    cur_mon = st.session_state.current_monday
    cur_sun = cur_mon + datetime.timedelta(days=6)
    week_dates = [cur_mon + datetime.timedelta(days=i) for i in range(7)]

    m1, m2 = MONTHS_GE[cur_mon.month], MONTHS_GE[cur_sun.month]
    week_label = f"{cur_mon.day} – {cur_sun.day} {m1}, {cur_mon.year}" if cur_mon.month == cur_sun.month else f"{cur_mon.day} {m1} – {cur_sun.day} {m2}, {cur_mon.year}"
    st.markdown(f"## 📅 {week_label}")

    n_col1, n_col2, n_col3, n_col4 = st.columns((1, 1, 1, 2))
    with n_col1:
        if st.button("⬅️ წინა კვირა", use_container_width=True):
            st.session_state.current_monday -= datetime.timedelta(days=7)
            st.rerun()
    with n_col2:
        if st.button("📍 მიმდინარე კვირა", use_container_width=True):
            st.session_state.current_monday = base_monday
            st.rerun()
    with n_col3:
        if st.button("შემდეგი კვირა ➡️", use_container_width=True):
            st.session_state.current_monday += datetime.timedelta(days=7)
            st.rerun()
    with n_col4:
        picked = st.date_input("თარიღზე გადასვლა:", value=cur_mon, label_visibility="collapsed")
        new_mon = picked - datetime.timedelta(days=picked.weekday())
        if new_mon != cur_mon:
            st.session_state.current_monday = new_mon
            st.rerun()

    grid_html = ['<div class="table-scroll-wrapper"><table class="full-grid-table"><thead><tr><th style="width:14%; min-width:150px;">აუდიტორია</th>']
    for d, name in zip(week_dates, DAY_NAMES_KA):
        d_short = f"{d.day} {MONTHS_GE[d.month][:3]}"
        bg = "#2563EB" if d == today else "#1E3A8A"
        grid_html.append(f'<th style="background-color:{bg};"><b>{name}</b><br><span style="font-size:0.95rem; opacity:0.9;">{d_short}</span></th>')
    grid_html.append('</tr></thead><tbody>')

    for aud in AUDITORIUMS:
        grid_html.append(f'<tr><td style="background-color:var(--secondary-background-color); color:var(--text-color); font-weight:800; font-size:1.15rem; text-align:center; vertical-align:middle;">{aud}</td>')
        for d in week_dates:
            matching = [item for item in st.session_state.schedule if (("საკონფერენციო დარბაზი" if item.get('auditorium')=="აუდიტორია 5" else item.get('auditorium')) == aud) and is_event_active_on_date(item, d)]
            matching.sort(key=lambda x: str(x['start_time']))
            if matching:
                grid_html.append('<td style="background-color:rgba(239,68,68,0.06); min-width:135px;">')
                for m in matching:
                    grid_html.append(f'<div class="slot-card"><div class="slot-time">⏰ {m["start_time"]} - {m["end_time"]}</div><div class="slot-subject">{m["subject"]}</div><div class="slot-lecturer">👨‍🏫 {m["lecturer"]}</div><div class="slot-univ">🏛️ {m["university"]}</div></div>')
                grid_html.append('</td>')
            else:
                grid_html.append('<td style="text-align:center; vertical-align:middle; opacity:0.25; font-size:1.2rem; min-width:135px;">—</td>')
        grid_html.append('</tr>')
    grid_html.append('</tbody></table></div>')
    st.markdown("".join(grid_html), unsafe_allow_html=True)

# 2. ახალი ჯგუფის დამატება & მართვა
elif selected_page == "➕ ახალი ჯგუფის დამატება & მართვა":
    st.subheader("➕ ახალი ჯგუფის დამატება და მართვა")
    col_add, col_list = st.columns((4, 6), gap="large")
    
    with col_add:
        with st.form(key="lecture_form_page", clear_on_submit=False):
            university = st.text_input("1. უნივერსიტეტი*", placeholder="მაგ. თსუ")
            subject = st.text_input("2. საგანი*", placeholder="მაგ. საზოგადოებრივი ჯანდაცვა")
            lecturer = st.text_input("3. ლექტორი*", placeholder="მაგ. გიორგი ბერიძე")
            auditorium = st.selectbox("აუდიტორია*", AUDITORIUMS)
            
            c_d1, c_d2 = st.columns(2)
            with c_d1: start_date = st.date_input("4. დაწყების თარიღი*", value=today)
            with c_d2: end_date = st.date_input("5. დასრულების თარიღი*", value=today)
                
            c_t1, c_t2 = st.columns(2)
            with c_t1: start_time = st.time_input("6. დაწყების საათი*", value=datetime.time(10, 0))
            with c_t2: end_time = st.time_input("დასრულების საათი*", value=datetime.time(12, 0))

            c_sat, c_sun = st.columns(2)
            with c_sat: include_sat = st.checkbox("შაბათის ჩათვლით", value=False)
            with c_sun: include_sun = st.checkbox("კვირის ჩათვლით", value=False)

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
                    "university": university.strip(), "subject": subject.strip(),
                    "lecturer": lecturer.strip(), "auditorium": auditorium,
                    "start_date": str(start_date), "end_date": str(end_date),
                    "start_time": start_time.strftime("%H:%M"), "end_time": end_time.strftime("%H:%M"),
                    "include_saturday": bool(include_sat), "include_sunday": bool(include_sun)
                }
                aud_c, lec_c = check_conflicts(new_entry)
                if aud_c and lec_c:
                    st.error("❌ ლექტორი დაკავებულია და აუდიტორია დაკავებულია")
                elif aud_c:
                    st.error(f"❌ აუდიტორია დაკავებულია საგნით '{aud_c[0]['subject']}'")
                elif lec_c:
                    st.error(f"❌ ლექტორი {new_entry['lecturer']} უკვე დაკავებულია")
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
            del_options = {f"#{i+1} {d['subject']} ({d['auditorium']}, {d['lecturer']} [{d['start_time']}-{d['end_time']}])": i for i, d in enumerate(st.session_state.schedule)}
            to_delete = st.selectbox("აირჩიეთ წასაშლელი ჩანაწერი:", list(del_options.keys()))
            if st.button("🗑️ არჩეული ჯგუფის წაშლა", use_container_width=True):
                st.session_state.schedule.pop(del_options[to_delete])
                save_data(st.session_state.schedule)
                st.success("ჩანაწერი წაშლილია!")
                st.rerun()

            st.markdown("---")
            df_export = pd.DataFrame(st.session_state.schedule)
            csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 ბაზის გადმოწერა (CSV)", data=csv_bytes, file_name="lecture_schedule.csv", mime="text/csv", use_container_width=True)

# 3. AI ჭკვიანი იმპორტი
elif selected_page == "🤖 AI ჭკვიანი იმპორტი (ტექსტიდან)":
    st.subheader("🤖 ხელოვნური ინტელექტით არეული ტექსტის ამოცნობა")
    st.caption("ჩასვით ნებისმიერი არეული ტექსტი. AI ავტომატურად ამოიღებს ყველა პარამეტრს და ასახავს განრიგში.")
    
    ai_col1, ai_col2 = st.columns((7, 3), gap="large")
    with ai_col2:
        saved_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets else ""
        api_key_input = st.text_input("🔑 Gemini API Key:", value=saved_key, type="password", placeholder="AIzaSy...")
        st.caption("უფასო გასაღების აღება: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    with ai_col1:
        raw_text = st.text_area("📋 ჩასვით არეული ტექსტი აქ:", height=180, placeholder="მაგ. 25 სექტემბერს დავით შოვნაძეს აქვს საზოგადოებრივი ჯანდაცვა აუდიტორია 1-ში 10:00-12:00 GAU-ში...")
        parse_btn = st.button("✨ ტექსტის გაანალიზება AI-ით", use_container_width=True)

    if parse_btn:
        if not api_key_input.strip():
            st.error("⚠️ გთხოვთ შეიყვანოთ Gemini API Key!")
        elif not raw_text.strip():
            st.error("⚠️ გთხოვთ ჩასვათ ტექსტი გასაანალიზებლად!")
        else:
            with st.spinner("⏳ AI აანალიზებს ტექსტს..."):
                try:
                    items = call_gemini_parser(api_key_input.strip(), raw_text.strip())
                    if isinstance(items, list) and len(items) > 0:
                        st.session_state.ai_parsed_results = items
                        st.success(f"🎉 ამოცნობილია {len(items)} ლექცია/ჯგუფი!")
                    else:
                        st.warning("AI-მ მონაცემების ამოცნობა ვერ შეძლო.")
                except Exception as err:
                    st.error(f"❌ შეცდომა: {err}")

    if st.session_state.get('ai_parsed_results'):
        st.markdown("---")
        st.markdown("### 📋 ამოცნობილი ლექციები (Preview):")
        items_to_add = st.session_state.ai_parsed_results
        st.dataframe(pd.DataFrame(items_to_add), use_container_width=True)
        
        c_btn1, c_btn2 = st.columns((4, 2))
        with c_btn1:
            if st.button("📥 ყველა ამოცნობილი ჯგუფის დამატება განრიგში", use_container_width=True):
                for it in items_to_add:
                    st.session_state.schedule.append(it)
                save_data(st.session_state.schedule)
                st.session_state.ai_parsed_results = []
                st.success("✅ ყველა ჯგუფი დაემატა განრიგში!")
                st.rerun()
        with c_btn2:
            if st.button("🗑️ გასუფთავება", use_container_width=True):
                st.session_state.ai_parsed_results = []
                st.rerun()

# 4. საათების რეპორტი & სია
elif selected_page == "📊 საათების რეპორტი & სია":
    st.subheader("📊 ლექტორების ჩატარებული საათების რეპორტი")
    st.caption("საათები ზუსტად ითვლება იმ დღეების მიხედვით, როდესაც ლექცია რეალურად ტარდება.")

    if not st.session_state.schedule:
        st.info("რეპორტისთვის მონაცემები ჯერ არ არის.")
    else:
        summary = {}
        for item in st.session_state.schedule:
            lec = str(item['lecturer']).strip()
            sdate = datetime.datetime.strptime(str(item['start_date']), "%Y-%m-%d").date()
            edate = datetime.datetime.strptime(str(item['end_date']), "%Y-%m-%d").date()
            stime = datetime.datetime.strptime(str(item['start_time']), "%H:%M")
            etime = datetime.datetime.strptime(str(item['end_time']), "%H:%M")
            dur = (etime - stime).total_seconds() / 3600.0

            sessions = 0
            cur_d = sdate
            while cur_d <= edate:
                if is_event_active_on_date(item, cur_d): sessions += 1
                cur_d += datetime.timedelta(days=1)

            if lec not in summary:
                summary[lec] = {"ლექტორი": lec, "უნივერსიტეტი": set(), "საგნები": set(), "ლექციების რაოდენობა": 0, "სრული საათები": 0.0}
            summary[lec]["უნივერსიტეტი"].add(str(item['university']))
            summary[lec]["საგნები"].add(str(item['subject']))
            summary[lec]["ლექციების რაოდენობა"] += sessions
            summary[lec]["სრული საათები"] += round(sessions * dur, 2)

        rows = [{"ლექტორი": d["ლექტორი"], "უნივერსიტეტი": ", ".join(d["უნივერსიტეტი"]), "საგნები": ", ".join(d["საგნები"]), "სულ ლექციები": d["ლექციების რაოდენობა"], "სრული საათები": round(d["სრული საათები"], 2)} for d in summary.values()]
        df_rep = pd.DataFrame(rows).sort_values(by="სრული საათები", ascending=False)
        st.dataframe(df_rep, use_container_width=True, hide_index=True)
        st.download_button("📥 რეპორტის გადმოწერა (CSV)", data=df_rep.to_csv(index=False).encode('utf-8-sig'), file_name="lecturers_hours_report.csv", mime="text/csv", use_container_width=True)

        st.markdown("---")
        st.markdown("### 📋 ყველა ჯგუფის ბარათები")
        grid_cols = st.columns(2)
        for i, row in enumerate(st.session_state.schedule):
            with grid_cols[i % 2]:
                sat = " • შაბ" if row.get('include_saturday') else ""
                sun = " • კვ" if row.get('include_sunday') else ""
                card_html = (
                    f'<div class="slot-card" style="border-radius:12px; padding:16px; margin-bottom:14px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">'
                    f'<span class="slot-subject">{row["subject"]}</span>'
                    f'<span style="background-color:#2563EB; color:#FFF; font-size:0.9rem; font-weight:700; padding:2px 8px; border-radius:4px;">{row["auditorium"]}</span>'
                    f'</div>'
                    f'<div class="slot-time">⏰ {row["start_time"]} – {row["end_time"]}</div>'
                    f'<div class="slot-lecturer"><b>👨‍🏫</b> {row["lecturer"]} | <b>🏛️</b> {row["university"]}</div>'
                    f'<div class="slot-univ"><b>📅</b> {row["start_date"]} — {row["end_date"]} (ორშ-პარ{sat}{sun})</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
