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

# მონაცემთა ფაილი და აუდიტორიების სია
DATA_FILE = "schedule_data.csv"
AUDITORIUMS = ["აუდიტორია 1", "აუდიტორია 2", "აუდიტორია 3", "აუდიტორია 4", "საკონფერენციო დარბაზი"]
DAY_NAMES_KA = ["ორშაბათი", "სამშაბათი", "ოთხშაბათი", "ხუთშაბათი", "პარასკევი", "შაბათი", "კვირა"]
MONTHS_GE = {
    1: "იანვარი", 2: "თებერვალი", 3: "მარტი", 4: "აპრილი",
    5: "მაისი", 6: "ივნისი", 7: "ივლისი", 8: "აგვისტო",
    9: "სექტემბერი", 10: "ოქტომბერი", 11: "ნოემბერი", 12: "დეკემბერი"
}

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
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 1rem !important;
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
            records = df.to_dict('records')
            for r in records:
                if r.get('auditorium') == 'აუდიტორია 5':
                    r['auditorium'] = 'საკონფერენციო დარბაზი'
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

# კვირის გადართვის ოფსეტი სესიის მეხსიერებაში
if 'week_offset' not in st.session_state:
    st.session_state.week_offset = 0

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

        date_overlap = not (new_edate < item_sdate or new_sdate > item_edate)
        time_overlap = not (new_etime <= item_stime or new_stime >= item_etime)

        if date_overlap and time_overlap:
            item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
            new_aud = "საკონფერენციო დარბაზი" if new_entry['auditorium'] == "აუდიტორია 5" else new_entry['auditorium']
            
            if item_aud == new_aud:
                aud_conflicts.append(item)
            if item['lecturer'].strip().lower() == new_entry['lecturer'].strip().lower():
                lec_conflicts.append(item)

    return aud_conflicts, lec_conflicts

# მთავარი სათაური
st.title("🎓 სასწავლო პროცესის ორგანიზებისა და განრიგის სოფტი")

# განლაგება: ეკრანის ~30% ფორმა, ~70% მთავარი პანელი
col_form, col_main = st.columns((3, 7), gap="large")

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

# --- მარჯვენა პანელი: 3 ინტერაქტიული ტაბი (70%) ---
with col_main:
    st.subheader("📊 სასწავლო განრიგის მონიტორინგი")
    
    tab_matrix, tab_day, tab_cards = st.tabs([
        "📅 კვირის ინტერაქტიული ბადე", 
        "🏛️ 5 აუდიტორიის Real-Time სტატუსი", 
        "📋 სრული განრიგი (ბარათები)"
    ])
    
    # ------------------ ტაბი 1: კვირის ინტერაქტიული ცხრილი ------------------
    with tab_matrix:
        today = datetime.date.today()
        base_monday = today - datetime.timedelta(days=today.weekday())
        current_monday = base_monday + datetime.timedelta(weeks=st.session_state.week_offset)
        current_sunday = current_monday + datetime.timedelta(days=6)
        week_dates = [current_monday + datetime.timedelta(days=i) for i in range(7)]

        m1 = MONTHS_GE[current_monday.month]
        m2 = MONTHS_GE[current_sunday.month]
        if current_monday.month == current_sunday.month:
            week_title = f"{current_monday.day} – {current_sunday.day} {m1}, {current_monday.year}"
        else:
            week_title = f"{current_monday.day} {m1} – {current_sunday.day} {m2}, {current_monday.year}"

        # კვირის ნავიგაცია
        nav1, nav2, nav3, nav4 = st.columns((1, 1, 1, 2))
        with nav1:
            if st.button("⬅️ წინა კვირა", key="prev_w"):
                st.session_state.week_offset -= 1
                st.rerun()
        with nav2:
            if st.button("📍 მიმდინარე კვირა", key="cur_w"):
                st.session_state.week_offset = 0
                st.rerun()
        with nav3:
            if st.button("შემდეგი კვირა ➡️", key="next_w"):
                st.session_state.week_offset += 1
                st.rerun()
        with nav4:
            jump_date = st.date_input("თარიღზე გადასვლა:", value=current_monday, key="week_jump")
            jump_monday = jump_date - datetime.timedelta(days=jump_date.weekday())
            new_off = (jump_monday - base_monday).days // 7
            if new_off != st.session_state.week_offset:
                st.session_state.week_offset = new_off
                st.rerun()

        st.markdown(f"#### 🗓️ {week_title}")

        # ცხრილის მატრიცის გენერაცია
        matrix_html = [
            '<div style="overflow-x: auto; margin-top: 10px;">'
            '<table style="width:100%; border-collapse: collapse; min-width: 950px; text-align: center; border-radius: 8px; overflow: hidden; border: 1.5px solid rgba(128,128,128,0.3);">'
            '<thead><tr style="background-color: #1E3A8A; color: #FFFFFF;">'
            '<th style="padding: 14px 10px; border: 1px solid rgba(128,128,128,0.3); width: 15%; font-size: 1.1rem;">აუდიტორია</th>'
        ]

        for d, name in zip(week_dates, DAY_NAMES_KA):
            d_short = f"{d.day} {MONTHS_GE[d.month][:3]}"
            is_today = (d == today)
            bg_header = "#2563EB" if is_today else "#1E3A8A"
            matrix_html.append(
                f'<th style="padding: 12px 6px; border: 1px solid rgba(128,128,128,0.3); background-color: {bg_header}; font-size: 1.05rem;">'
                f'<b>{name}</b><br><span style="font-size: 0.9rem; opacity: 0.9;">{d_short}</span>'
                f'</th>'
            )
        matrix_html.append('</tr></thead><tbody>')

        for aud in AUDITORIUMS:
            matrix_html.append(
                f'<tr style="border-bottom: 1px solid rgba(128,128,128,0.2);">'
                f'<td style="padding: 14px 10px; font-weight: 800; font-size: 1.05rem; background-color: var(--secondary-background-color); color: var(--text-color); border: 1px solid rgba(128,128,128,0.3); vertical-align: middle;">'
                f'{aud}'
                f'</td>'
            )

            for d in week_dates:
                d_str = str(d)
                matching = []
                for item in st.session_state.schedule:
                    item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
                    if item_aud == aud and (item['start_date'] <= d_str <= item['end_date']):
                        matching.append(item)

                matching.sort(key=lambda x: x['start_time'])

                if matching:
                    cell_content = '<td style="padding: 6px; vertical-align: top; border: 1px solid rgba(128,128,128,0.3); background-color: rgba(239, 68, 68, 0.08);">'
                    for m in matching:
                        cell_content += (
                            f'<div style="background-color: var(--secondary-background-color); border: 1.5px solid #EF4444; border-radius: 8px; padding: 8px; margin-bottom: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); text-align: left;">'
                            f'<div style="background-color: #EF4444; color: #FFFFFF; font-weight: 800; font-size: 0.95rem; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 4px;">⏰ {m["start_time"]} - {m["end_time"]}</div>'
                            f'<div style="font-weight: 700; font-size: 0.95rem; color: var(--text-color); line-height: 1.2;">{m["subject"]}</div>'
                            f'<div style="font-size: 0.85rem; color: var(--text-color); opacity: 0.85; margin-top: 2px;">{m["lecturer"]}</div>'
                            f'</div>'
                        )
                    cell_content += '</td>'
                    matrix_html.append(cell_content)
                else:
                    matrix_html.append(
                        '<td style="padding: 12px; vertical-align: middle; border: 1px solid rgba(128,128,128,0.3); color: var(--text-color); opacity: 0.3; font-size: 1.1rem;">—</td>'
                    )
            matrix_html.append('</tr>')

        matrix_html.append('</tbody></table></div>')
        st.markdown("".join(matrix_html), unsafe_allow_html=True)

    # ------------------ ტაბი 2: 5 აუდიტორიის Real-Time სტატუსი (დღიური) ------------------
    with tab_day:
        selected_monitor_date = st.date_input(
            "აირჩიეთ თარიღი აუდიტორიების შესამოწმებლად:", 
            value=datetime.date.today(), 
            key="mon_date_day"
        )
        sel_date_str = str(selected_monitor_date)
        
        room_cols = st.columns(5)
        for i, room in enumerate(AUDITORIUMS):
            with room_cols[i]:
                st.markdown(f"### {room}")
                
                room_events = []
                for item in st.session_state.schedule:
                    item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
                    if item_aud == room and (item['start_date'] <= sel_date_str <= item['end_date']):
                        room_events.append(item)
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

    # ------------------ ტაბი 3: სრული განრიგი (კვადრატული ბარათები) ------------------
    with tab_cards:
        if not st.session_state.schedule:
            st.info("განრიგში ჯერ მონაცემები არ არის. დაამატეთ ახალი ჯგუფი მარცხენა პანელიდან.")
        else:
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_aud = st.multiselect("ფილტრი აუდიტორიით:", AUDITORIUMS, default=AUDITORIUMS)
            with f_col2:
                filter_search = st.text_input("ძიება (უნივერსიტეტი, საგანი, ლექტორი):", "")

            filtered_data = []
            for idx, item in enumerate(st.session_state.schedule):
                item_aud = "საკონფერენციო დარბაზი" if item['auditorium'] == "აუდიტორია 5" else item['auditorium']
                if item_aud in filter_aud:
                    text_blob = f"{item['university']} {item['subject']} {item['lecturer']}".lower()
                    if not filter_search or filter_search.lower() in text_blob:
                        filtered_data.append({**item, "_idx": idx, "display_aud": item_aud})

            if filtered_data:
                st.markdown(f"**სულ ნაპოვნია: {len(filtered_data)} ჯგუფი**")
                
                grid_cols = st.columns(2)
                for i, row in enumerate(filtered_data):
                    target_col = grid_cols[i % 2]
                    with target_col:
                        card_html = (
                            f'<div class="schedule-card">'
                            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">'
                            f'<span style="font-size: 1.25rem; font-weight: 800; color: var(--text-color);">{row["subject"]}</span>'
                            f'<span style="background-color: #2563EB; color: #FFFFFF; font-size: 0.95rem; font-weight: 700; padding: 4px 10px; border-radius: 6px;">{row["display_aud"]}</span>'
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

                st.markdown("---")
                with st.expander("🗑️ ჩანაწერის წაშლა"):
                    del_options = {
                        f"#{i+1} {d['subject']} ({d['display_aud']}, {d['lecturer']} [{d['start_time']}-{d['end_time']}])": d['_idx'] 
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

            st.markdown("---")
            df_export = pd.DataFrame(st.session_state.schedule)
            csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 მონაცემების გადმოწერა (CSV ფორმატში)",
                data=csv_bytes,
                file_name="lecture_schedule.csv",
                mime="text/csv"
            )
