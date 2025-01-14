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
def schedule_mentoring_sessions(mentors, startups, time_slots):
    mentor_preferences = {
        mentor["Name"]: [mentor["Sector 1"], mentor["Sector 2"], mentor["Sector 3"]]
        for _, mentor in mentors.iterrows()
    }

    mentor_schedule = {mentor["Name"]: [] for _, mentor in mentors.iterrows()}
    startup_counts = {startup["Name"]: 0 for _, startup in startups.iterrows()}

    for time_slot in time_slots:
        for _, mentor in mentors.iterrows():
            mentor_name = mentor["Name"]
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

# Schedule mentoring sessions
schedule = schedule_mentoring_sessions(mentors, startups, time_slots)

# Streamlit UI
st.title("Mentoring Schedule")
st.subheader("Search for a Mentor")

# Search bar for mentor filtering
mentor_search = st.text_input("Enter mentor name").strip().lower()

# Display the schedule for all mentors or filtered mentors
for mentor_name, sessions in schedule.items():
    if mentor_search and mentor_search not in mentor_name.lower():
        continue

    st.markdown(f"### Mentor: {mentor_name}")
    st.markdown("#### Scheduled Startups:")
    for session in sessions:
        st.write(f"- **{session['Name']}** ({session['Sector']}) at **{session['Time Slot']}**")
    st.markdown("---")
