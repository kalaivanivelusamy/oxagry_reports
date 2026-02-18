import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Ops Report Jan 2026", layout="wide")

# Constants
HOURS_PER_DAY = 8 

# --- CSS FOR PURPLE THEME & HIGH VISIBILITY TEXT ---
st.markdown("""
    <style>
    /* Purple background for the app */
    .stApp { background-color: #f5f3ff; }
    
    /* White KPI Cards with Purple Borders */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #ddd6fe !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border-left: 5px solid #7e22ce !important;
    }
    
    /* Ensuring text is dark and highly visible against white background */
    div[data-testid="stMetricLabel"] > div {
        color: #4b5563 !important; /* Dark grey for labels */
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #1e1b4b !important; /* Deep navy for numbers */
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Loading (Designed for Master Sheet with all months)
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('operator_work_hours_jan_2026.csv')
    
    def time_to_hours(time_str):
        try:
            h, m, s = map(int, str(time_str).split(':'))
            return h + m/60 + s/3600
        except: return 0.0
            
    df['Hours'] = df['Total Hours'].apply(time_to_hours)
    df['Worked Date'] = pd.to_datetime(df['Worked Date']).dt.date
    return df

df = load_and_process_data()

# 3. Sidebar Filters
st.sidebar.header("Filter Dashboard")
selected_ops = st.sidebar.multiselect("Select Operator", options=sorted(df['Operator Name'].unique()))
selected_mach = st.sidebar.multiselect("Select Machinery", options=sorted(df['Machinery Code'].unique()))

min_date = df['Worked Date'].min()
max_date = df['Worked Date'].max()
date_range = st.sidebar.date_input("Filter by Date Range", value=(min_date, max_date))

st.sidebar.divider()
st.sidebar.subheader("Analytics Settings")

# RE-ADDED: Toggle between Unique Days and Every Log Entry
day_method = st.sidebar.radio(
    "Day Count Method", 
    ["Unique Calendar Days", "Total Log Entries"],
    help="Unique: Counts distinct dates. Log Entries: Counts every row in your Master Sheet."
)

# 4. Apply Filters
filtered_df = df.copy()
if selected_ops:
    filtered_df = filtered_df[filtered_df['Operator Name'].isin(selected_ops)]
if selected_mach:
    filtered_df = filtered_df[filtered_df['Machinery Code'].isin(selected_mach)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['Worked Date'] >= start_date) & 
                             (filtered_df['Worked Date'] <= end_date)]

# 5. Metrics Logic
total_hrs = filtered_df['Hours'].sum()

# Day Count based on the sidebar selection
if day_method == "Unique Calendar Days":
    day_count = filtered_df['Worked Date'].nunique()
    day_label = "Calendar Days Active"
else:
    day_count = len(filtered_df)
    day_label = "Total Log Entries"

standard_days = total_hrs / HOURS_PER_DAY
# Intensity is always calculated against actual unique days
actual_days = filtered_df['Worked Date'].nunique()
intensity = (standard_days / actual_days * 100) if actual_days > 0 else 0

# 6. Dynamic Header (Shows selection)
target_suffix = ""
if len(selected_mach) == 1: target_suffix = f" for {selected_mach[0]}"
elif len(selected_ops) == 1: target_suffix = f" for {selected_ops[0]}"

st.title(f"🚜 Operational Performance{target_suffix}")

# 7. KPI Row with Visible Text
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Hours", f"{total_hrs:.2f} hrs")
m2.metric(f"{day_label}", f"{day_count}")
m3.metric("Standard Days", f"{standard_days:.2f}")
m4.metric("Daily Intensity", f"{intensity:.1f}%")

st.divider()

# 8. Visualizations
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Machine Usage by Operator")
    fig_mach = px.bar(filtered_df, x="Machinery Code", y="Hours", color="Operator Name",
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    st.plotly_chart(fig_mach, use_container_width=True)

with col2:
    st.subheader("Operator Work Share")
    op_sum = filtered_df.groupby('Operator Name')['Hours'].sum().reset_index()
    fig_pie = px.pie(op_sum, values='Hours', names='Operator Name', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Daily Workload Trend")
daily_trend = filtered_df.groupby('Worked Date')['Hours'].sum().reset_index()
fig_trend = px.area(daily_trend, x="Worked Date", y="Hours", color_discrete_sequence=['#7e22ce'])
st.plotly_chart(fig_trend, use_container_width=True)

# 9. Master Sheet Log View
with st.expander("🔍 View Raw Master Sheet Data"):
    st.write(f"Showing {len(filtered_df)} total log entries")
    st.dataframe(filtered_df.drop(columns=['Hours']), use_container_width=True)