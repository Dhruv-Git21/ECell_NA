import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# Load datasets
mentors = pd.read_csv("Mentor.csv")  # Columns: Name, Sector 1, Sector 2, Sector 3, Index
startups = pd.read_csv("Startups.csv")  # Columns: Name, Sector, Index

# Initialize time slots
start_time = datetime.strptime("11:00 AM", "%I:%M %p")
end_time = datetime.strptime("2:00 PM", "%I:%M %p")
time_slots = []
slot_duration = timedelta(minutes=15)
gap_duration = timedelta(minutes=5)

while start_time + slot_duration <= end_time:
    time_slots.append(start_time.strftime("%I:%M %p"))
    start_time += slot_duration + gap_duration

# Helper function to schedule mentoring sessions
def schedule_mentoring_sessions(mentors, startups, time_slots, excluded_mentors=[]):
    mentor_preferences = {
        mentor["Name"]: [mentor["Sector 1"], mentor["Sector 2"], mentor["Sector 3"]]
        for _, mentor in mentors.iterrows()
        if mentor["Name"] not in excluded_mentors  # Exclude unavailable mentors
    }

    mentor_schedule = {mentor["Name"]: [] for _, mentor in mentors.iterrows() if mentor["Name"] not in excluded_mentors}
    startup_counts = {startup["Name"]: 0 for _, startup in startups.iterrows()}

    for time_slot in time_slots:
        for mentor_name in mentor_schedule.keys():
            preferences = mentor_preferences[mentor_name]
            weights = [40, 30, 30]

            available_startups = startups[
                (startups["Name"].map(startup_counts) < 4) &
                (startups["Sector"].isin(preferences))
            ]

            if available_startups.empty:
                available_startups = startups[startups["Name"].map(startup_counts) < 4]

            if available_startups.empty:
                continue

            selected_startup = None
            if available_startups["Sector"].isin(preferences).any():
                chosen_sector = random.choices(preferences, weights=weights, k=1)[0]
                sector_startups = available_startups[available_startups["Sector"] == chosen_sector]
                if not sector_startups.empty:
                    selected_startup = sector_startups.sample(1).iloc[0]
            if selected_startup is None:
                selected_startup = available_startups.sample(1).iloc[0]

            startup_name = selected_startup["Name"]
            startup_sector = selected_startup["Sector"]

            mentor_schedule[mentor_name].append({
                "Name": startup_name,
                "Sector": startup_sector,
                "Time Slot": time_slot
            })
            startup_counts[startup_name] += 1

    return mentor_schedule

# Streamlit UI
st.title("Mentoring Schedule")
st.subheader("Search for a Mentor or Toggle Availability")

# Initialize session state to track mentor availability
if "excluded_mentors" not in st.session_state:
    st.session_state["excluded_mentors"] = []

# Toggle button for each mentor
schedule = schedule_mentoring_sessions(mentors, startups, time_slots, st.session_state["excluded_mentors"])

mentor_search = st.text_input("Enter mentor name").strip().lower()

for mentor_name in mentors["Name"]:
    if mentor_search and mentor_search not in mentor_name.lower():
        continue

    col1, col2 = st.columns([4, 1])
    col1.markdown(f"### Mentor: {mentor_name}")
    if mentor_name in st.session_state["excluded_mentors"]:
        status_text = "Unavailable"
        button_label = "Turn On"
    else:
        status_text = "Available"
        button_label = "Turn Off"

    if col2.button(button_label, key=mentor_name):
        if mentor_name in st.session_state["excluded_mentors"]:
            st.session_state["excluded_mentors"].remove(mentor_name)
        else:
            st.session_state["excluded_mentors"].append(mentor_name)
        # Force a rerun by setting a dummy query parameter
        st.query_params(rerun=str(random.randint(0, 10000)))


    col1.markdown(f"**Status:** {status_text}")
    col1.markdown("#### Scheduled Startups:")
    for session in schedule.get(mentor_name, []):
        col1.write(f"- **{session['Name']}** ({session['Sector']}) at **{session['Time Slot']}**")
    col1.markdown("---")
