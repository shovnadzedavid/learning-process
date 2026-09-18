import streamlit as st
import pandas as pd
import datetime
import os

# გვერდის კონფიგურაცია - Wide რეჟიმი
st.set_page_config(
    page_title="სასწავლო ცხრილის მართვის სისტემა",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# მონაცემთა ფაილი
DATA_FILE = "schedule_data.csv"
AUDITORIUMS = ["აუდიტორია 1", "აუდიტორია 2", "აუდიტორია 3", "აუდიტორია 4", "აუდიტორია 5"]

# CSS სტილები - Dark / Light რეჟიმებთან სრული თავსებადობით
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 16px;
    }
    
    h1 {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.8rem !important;
        color: var(--text-color) !important;
    }
    h2, h3 {
        font-weight: 700 !important;
        color: var(--text-color) !important;
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

    /* სრული განრიგის კვადრატული ბარათები */
    .schedule-card {
        background-color: var(--secondary-background-color) !important;
        border: 1.5px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.06);
    }

    /* ღილაკის სტილი */
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
</style>
""", unsafe_allow_html=True)

# მონაცემების ჩატვირთვა
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            return df.to_dict('records')
        except Exception:
            return []
    return []

# მონაცემების შენახვა
def save_data(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv(DATA_FILE, index=False)

if 'schedule' not in st.session_state:
    st.session_state.schedule = load_data()

# გადაკვეთის შემოწმების ალგორითმი
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

        # თარიღების გადაკვეთა
        date_overlap = not (new_edate < item_sdate or new_sdate > item_edate)
        # საათების გადაკვეთა
        time_overlap = not (new_etime <= item_stime or new_stime >= item_etime)

        if date_overlap and time_overlap:
            if item['auditorium'] == new_entry['auditorium']:
                aud_conflicts.append(item)
            if item['lecturer'].strip().lower() == new_entry['lecturer'].strip().lower():
                lec_conflicts.append(item)

    return aud_conflicts, lec_conflicts

# მთავარი სათაური
st.title("🎓 სასწავლო პროცესის ორგანიზებისა და განრიგის სოფტი")

# განლაგება: ეკრანის ~30% ფორმა, ~70% მთავარი პანელი
col_form, col_main = st.columns(, gap="large")

# --- მარცხენა პანელი: ფორმა (30%) ---
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

            if aud_conflicts and lec_conflicts:
                st.error("❌ ლექტორი დაკავებულია და აუდიტორია დაკავებულია")
                for c in aud_conflicts:
                    st.warning(f"📌 {c['auditorium']}: დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
                for c in lec_conflicts:
                    st.warning(f"📌 {c['lecturer']}: დაკავებულია საგნით '{c['subject']}' ({c['start_time']} - {c['end_time']})")
            elif aud_conflicts:
                st.error("❌ აუდიტორია დაკავებულია")
                for c in aud_conflicts:
                    st.warning(f"📌 {c['auditorium']}: უკვე დაკავებულია საგნით '{c['subject']}' ({c['lecturer']}) [{c['start_time']} - {c['end_time']}]")
            elif lec_conflicts:
                st.error("❌ ლექტორი დაკავებულია")
                for c in lec_conflicts:
                    st.warning(f"📌 ლექტორი {c['lecturer']} უკვე დაკავებულია საგნით '{c['subject']}' [{c['start_time']} - {c['end_time']}]")
            else:
                st.session_state.schedule.append(new_entry)
                save_data(st.session_state.schedule)
                st.success("✅ ჯგუფი წარმატებით შეინახა!")
                st.rerun()

# --- მარჯვენა პანელი: Real-Time და კვადრატებად დაყოფილი განრიგი (70%) ---
with col_main:
    st.subheader("📊 სასწავლო განრიგის მონიტორინგი")
    
    tab1, tab2 = st.tabs(["🏛️ 5 აუდიტორიის Real-Time სტატუსი", "📋 სრული განრიგი (ბარათებად დაყოფილი)"])
    
    # 1. 5 აუდიტორიის სტატუსი (დღიური ხედი)
    with tab1:
        selected_monitor_date = st.date_input(
            "აირჩიეთ თარიღი აუდიტორიების შესამოწმებლად:", 
            value=datetime.date.today(), 
            key="mon_date"
        )
        sel_date_str = str(selected_monitor_date)
        
        room_cols = st.columns(5)
        for i, room in enumerate(AUDITORIUMS):
            with room_cols[i]:
                st.markdown(f"### {room}")
                
                room_events = [
                    item for item in st.session_state.schedule 
                    if item['auditorium'] == room and (item['start_date'] <= sel_date_str <= item['end_date'])
                ]
                room_events.sort(key=lambda x: x['start_time'])
                
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

    # 2. სრული განრიგი კვადრატებად (Grid Cards)
    with tab2:
        if not st.session_state.schedule:
            st.info("განრიგში ჯერ მონაცემები არ არის. დაამატეთ ახალი ჯგუფი მარცხენა პანელიდან.")
        else:
            # ფილტრები - აქ გასწორდა st.columns(2)
            f_col1, f_col2 = st.columns(2)
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
                st.markdown(f"**სულ ნაპოვნია: {len(filtered_data)} ჯგუფი**")
                
                # კვადრატებად დაყოფა 2 სვეტად
                grid_cols = st.columns(2)
                for i, row in enumerate(filtered_data):
                    target_col = grid_cols[i % 2]
                    with target_col:
                        card_html = (
                            f'<div class="schedule-card">'
                            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">'
                            f'<span style="font-size: 1.25rem; font-weight: 800; color: var(--text-color);">{row["subject"]}</span>'
                            f'<span style="background-color: #2563EB; color: #FFFFFF; font-size: 0.95rem; font-weight: 700; padding: 4px 10px; border-radius: 6px;">{row["auditorium"]}</span>'
                            f'</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 6px;"><b>👨‍🏫 ლექტორი:</b> {row["lecturer"]}</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 6px;"><b>🏛️ უნივერსიტეტი:</b> {row["university"]}</div>'
                            f'<div style="font-size: 1.05rem; color: var(--text-color); margin-bottom: 10px;"><b>📅 პერიოდი:</b> {row["start_date"]} — {row["end_date"]}</div>'
                            f'<div style="display: inline-block; background-color: rgba(37, 99, 235, 0.15); border: 1.5px solid #2563EB; color: var(--text-color); font-size: 1.1rem; font-weight: 800; padding: 5px 12px; border-radius: 8px;">'
                            f'⏰ {row["start_time"]} – {row["end_time"]}'
                            f'</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

                # ჩანაწერის წაშლა
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
                st.warning("მითითებული ფილტრით ჩანაწერი არ მოიძებნა.")

            # CSV ექსპორტი
            st.markdown("---")
            df_export = pd.DataFrame(st.session_state.schedule)
            csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 მონაცემების გადმოწერა (CSV ფორმატში)",
                data=csv_bytes,
                file_name="lecture_schedule.csv",
                mime="text/csv"
            )
