import streamlit as st
import pandas as pd
import datetime
import os

# გვერდის კონფიგურაცია - Wide რეჟიმი (მთელი ეკრანის ასათვისებლად)
st.set_page_config(
    page_title="სასწავლო ცხრილის მართვის სისტემა",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# მონაცემთა ფაილი ავტომატური შენახვისთვის (Persistence)
DATA_FILE = "schedule_data.csv"
AUDITORIUMS = ["აუდიტორია 1", "აუდიტორია 2", "აუდიტორია 3", "აუდიტორია 4", "აუდიტორია 5"]

# CSS სტილები დიდი, მსხვილი და მკაფიო ვიზუალისთვის (ეკრანის 70%-ის ხედით)
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 16px;
    }
    
    h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #1E3A8A;
        margin-bottom: 1rem !important;
    }
    h2, h3 {
        font-weight: 700 !important;
        color: #1E293B;
    }

    /* დიდი და მსხვილი ცხრილის სტილი */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 1.1rem;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #1E3A8A;
        color: #ffffff;
        text-align: left;
        font-weight: bold;
        font-size: 1.15rem;
    }
    .styled-table th, .styled-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #CBD5E1;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #F8FAFC;
    }
    .styled-table tbody tr:hover {
        background-color: #EEF2F6;
        font-weight: 600;
    }

    /* აუდიტორიის მონიტორინგის ბარათები */
    .room-card {
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
    .room-free {
        border-left: 6px solid #10B981;
        background-color: #ECFDF5;
    }
    .room-busy {
        border-left: 6px solid #EF4444;
        background-color: #FEF2F2;
    }

    /* შენახვის ღილაკის სტილი */
    .stButton>button {
        width: 100%;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        padding: 0.65rem 1rem !important;
        border-radius: 8px !important;
        background-color: #1E3A8A !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# მონაცემების ჩატვირთვა ფაილიდან
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            return df.to_dict('records')
        except Exception:
            return []
    return []

# მონაცემების შენახვა CSV-ში
def save_data(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv(DATA_FILE, index=False)

if 'schedule' not in st.session_state:
    st.session_state.schedule = load_data()

# გადაკვეთების (კონფლიქტების) შემოწმების ლოგიკა
def check_conflicts(new_entry):
    new_sdate = datetime.datetime.strptime(new_entry['start_date'], "%Y-%m-%d").date()
    new_edate = datetime.datetime.strptime(new_entry['end_date'], "%Y-%m-%d").date()
    new_stime = datetime.datetime.strptime(new_entry['start_time'], "%H:%M").time()
    new_etime = datetime.datetime.strptime(new_entry['end_time'], "%H:%M").time()
    
    aud_conflicts = []
    lec_conflicts = []

    for item in st.session_state.schedule:
        item_sdate = datetime.datetime.strptime(item['start_date'], "%Y-%m-%d").date()
        item_edate = datetime.datetime.strptime(item['end_date'], "%Y-%m-%d").date()
        item_stime = datetime.datetime.strptime(item['start_time'], "%H:%M").time()
        item_etime = datetime.datetime.strptime(item['end_time'], "%H:%M").time()

        # თარიღების გადაკვეთა: [start1, end1] იკვეთება [start2, end2]-თან
        date_overlap = not (new_edate < item_sdate or new_sdate > item_edate)

        # საათების გადაკვეთა: [time1, endtime1] იკვეთება [time2, endtime2]-თან
        time_overlap = not (new_etime <= item_stime or new_stime >= item_etime)

        if date_overlap and time_overlap:
            # აუდიტორიის დაკავებულობის შემოწმება
            if item['auditorium'] == new_entry['auditorium']:
                aud_conflicts.append(item)
            # ლექტორის დაკავებულობის შემოწმება
            if item['lecturer'].strip().lower() == new_entry['lecturer'].strip().lower():
                lec_conflicts.append(item)

    return aud_conflicts, lec_conflicts

# მთავარი სათაური
st.title("🎓 სასწავლო პროცესის ორგანიზებისა და განრიგის სოფტი")

# განლაგება: ეკრანის ~30% ფორმა, ~70% ცხრილი და რეალური დროის მონიტორინგი
col_form, col_main = st.columns([3, 7], gap="large")

# --- მარცხენა მხარე: ფორმა (30%) ---
with col_form:
    st.subheader("➕ ახალი ჯგუფის დამატება")
    st.markdown("---")
    
    with st.form(key="lecture_form", clear_on_submit=False):
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

        submitted = st.form_submit_button("💾 ჯგუფის შენახვა")

    if submitted:
        # ვალიდაცია
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
                "end_time": end_time.strftime("%H:%M")
            }

            aud_conflicts, lec_conflicts = check_conflicts(new_entry)

            # შეტყობინებები მოთხოვნის შესაბამისად
            if aud_conflicts and lec_conflicts:
                st.error("❌ ლექტორი დაკავებულია და აუდიტორია დაკავებულია")
                for c in aud_conflicts:
                    st.warning(f"📌 {c['auditorium']}: უკვე დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
                for c in lec_conflicts:
                    st.warning(f"📌 {c['lecturer']}: უკვე კითხულობს ლექციას '{c['subject']}' ({c['start_time']} - {c['end_time']})")
            elif aud_conflicts:
                st.error("❌ აუდიტორია დაკავებულია")
                for c in aud_conflicts:
                    st.warning(f"📌 {c['auditorium']}: უკვე დაკავებულია საგნით '{c['subject']}' ({c['lecturer']}) [{c['start_time']} - {c['end_time']}]")
            elif lec_conflicts:
                st.error("❌ ლექტორი დაკავებულია")
                for c in lec_conflicts:
                    st.warning(f"📌 ლექტორი {c['lecturer']} უკვე დაკავებულია საგნით '{c['subject']}' [{c['start_time']} - {c['end_time']}]")
            else:
                # კონფლიქტი არ არის -> შენახვა
                st.session_state.schedule.append(new_entry)
                save_data(st.session_state.schedule)
                st.success("✅ ჯგუფი წარმატებით შეინახა!")
                st.rerun()

# --- მარჯვენა მხარე: ინტერაქტიული ცხრილი და Real-Time მონიტორინგი (70%) ---
with col_main:
    st.subheader("📊 სასწავლო განრიგის მონიტორინგი")
    
    tab1, tab2 = st.tabs(["🏛️ 5 აუდიტორიის Real-Time სტატუსი", "📋 სრული ცხრილი"])
    
    # 1. 5 აუდიტორიის სტატუსი კონკრეტულ თარიღზე
    with tab1:
        selected_monitor_date = st.date_input(
            "აირჩიეთ თარიღი აუდიტორიების გადასამოწმებლად:", 
            value=datetime.date.today(), 
            key="mon_date"
        )
        sel_date_str = str(selected_monitor_date)
        
        # 5 აუდიტორიის სვეტებად გადანაწილება
        room_cols = st.columns(5)
        for i, room in enumerate(AUDITORIUMS):
            with room_cols[i]:
                st.markdown(f"### {room}")
                
                # მოვძებნოთ მიმდინარე ლექციები ამ აუდიტორიაში
                room_events = [
                    item for item in st.session_state.schedule 
                    if item['auditorium'] == room and (item['start_date'] <= sel_date_str <= item['end_date'])
                ]
                room_events.sort(key=lambda x: x['start_time'])
                
                if room_events:
                    for ev in room_events:
                        st.markdown(f"""
                        <div class="room-card room-busy">
                            <b style="font-size:1.15rem; color:#991B1B;">⛔ {ev['start_time']} - {ev['end_time']}</b><br>
                            <b>საგანი:</b> {ev['subject']}<br>
                            <b>ლექტორი:</b> {ev['lecturer']}<br>
                            <span style="font-size:0.9rem; color:#4B5563;">{ev['university']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="room-card room-free">
                        <b style="color:#065F46; font-size:1.1rem;">✅ თავისუფალია</b><br>
                        <span style="color:#047857;">მთელი დღის განმავლობაში</span>
                    </div>
                    """, unsafe_allow_html=True)

    # 2. სრული მონაცემთა ცხრილი
    with tab2:
        if not st.session_state.schedule:
            st.info("ცხრილში ჯერ მონაცემები არ არის. დაამატეთ ახალი ჯგუფი მარცხენა პანელიდან.")
        else:
            # ფილტრები
            f_col1, f_col2 = st.columns([1, 2])
            with f_col1:
                filter_aud = st.multiselect("ფილტრი აუდიტორიით:", AUDITORIUMS, default=AUDITORIUMS)
            with f_col2:
                filter_search = st.text_input("ძიება (უნივერსიტეტი, საგანი, ლექტორი):", "")

            filtered_data = []
            for idx, item in enumerate(st.session_state.schedule):
                if item['auditorium'] in filter_aud:
                    text_blob = f"{item['university']} {item['subject']} {item['lecturer']}".lower()
                    if not filter_search or filter_search.lower() in text_blob:
                        filtered_data.append({**item, "_idx": idx})

            if filtered_data:
                # დიდი და მსხვილი ცხრილის გენერაცია
                table_html = """
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>უნივერსიტეტი</th>
                            <th>საგანი</th>
                            <th>ლექტორი</th>
                            <th>აუდიტორია</th>
                            <th>დაწყების თარიღი</th>
                            <th>დასრულების თარიღი</th>
                            <th>საათები</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for i, row in enumerate(filtered_data, 1):
                    table_html += f"""
                        <tr>
                            <td><b>{i}</b></td>
                            <td><b>{row['university']}</b></td>
                            <td style="color:#1E3A8A; font-weight:700;">{row['subject']}</td>
                            <td><b>{row['lecturer']}</b></td>
                            <td><span style="background-color:#E0E7FF; color:#1E3A8A; padding:4px 10px; border-radius:6px; font-weight:700;">{row['auditorium']}</span></td>
                            <td>{row['start_date']}</td>
                            <td>{row['end_date']}</td>
                            <td><b style="color:#047857; font-size:1.15rem;">{row['start_time']} – {row['end_time']}</b></td>
                        </tr>
                    """
                table_html += "</tbody></table>"
                st.markdown(table_html, unsafe_allow_html=True)
                
                # ჩანაწერის წაშლის მენიუ
                st.markdown("---")
                with st.expander("🗑️ ჩანაწერის წაშლა"):
                    del_options = {
                        f"#{i+1} {d['subject']} ({d['auditorium']}, {d['lecturer']} [{d['start_time']}-{d['end_time']}])": d['_idx'] 
                        for i, d in enumerate(filtered_data)
                    }
                    to_delete = st.selectbox("აირჩიეთ წასაშლელი ლექცია:", list(del_options.keys()))
                    if st.button("ჩანაწერის წაშლა"):
                        idx_to_del = del_options[to_delete]
                        st.session_state.schedule.pop(idx_to_del)
                        save_data(st.session_state.schedule)
                        st.success("ჩანაწერი წაშლილია!")
                        st.rerun()
            else:
                st.warning("მითითებული პარამეტრებით ჩანაწერი არ მოიძებნა.")

            # CSV ექსპორტი
            df_export = pd.DataFrame(st.session_state.schedule)
            csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ცხრილის გადმოწერა (CSV ფორმატში)",
                data=csv_bytes,
                file_name="lecture_schedule.csv",
                mime="text/csv"
            )
