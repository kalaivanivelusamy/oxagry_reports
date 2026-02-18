import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Basic Page Configuration
st.set_page_config(page_title="Ops Report Jan 2026", layout="wide")

# Constants - Easy to change based on management policy
HOURS_PER_DAY = 8 

# Title and Description
st.title(" Machinery & Operator Productivity Dashboard")
st.markdown("Interactive analysis of work hours for January 2026.")

# 2. Data Loading and Processing
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('operator_work_hours_jan_2026.csv')
    
    # Convert HH:MM:SS to Decimal Hours
    def time_to_hours(time_str):
        try:
            h, m, s = map(int, str(time_str).split(':'))
            return h + m/60 + s/3600
        except:
            return 0.0
            
    df['Hours'] = df['Total Hours'].apply(time_to_hours)
    df['Worked Date'] = pd.to_datetime(df['Worked Date'])
    return df

df = load_and_process_data()

# 3. Sidebar Filters
st.sidebar.header("Data Filters")

# Operator Filter
all_operators = sorted(df['Operator Name'].unique())
selected_operators = st.sidebar.multiselect("Filter by Operator", options=all_operators, default=[])

# Machine Filter
all_machines = sorted(df['Machinery Code'].unique())
selected_machines = st.sidebar.multiselect("Filter by Machinery", options=all_machines, default=[])

# Date Filter
min_date = df['Worked Date'].min()
max_date = df['Worked Date'].max()
date_range = st.sidebar.date_input("Filter by Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# 4. Apply Filters to Data
filtered_df = df.copy()

if selected_operators:
    filtered_df = filtered_df[filtered_df['Operator Name'].isin(selected_operators)]

if selected_machines:
    filtered_df = filtered_df[filtered_df['Machinery Code'].isin(selected_machines)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['Worked Date'].dt.date >= start_date) & 
                             (filtered_df['Worked Date'].dt.date <= end_date)]

# 5. Modular Metrics Calculation (Safe Logic)
total_hrs = filtered_df['Hours'].sum()

# Calendar Days: Counting unique dates the machine/operator appeared
calendar_days = filtered_df['Worked Date'].nunique()

# Standard Days: Converting total hours into 8-hour shift equivalents
standard_days = total_hrs / HOURS_PER_DAY

# Intensity: Comparing actual hours vs potential shift hours
intensity = (standard_days / calendar_days * 100) if calendar_days > 0 else 0

# 6. Dashboard KPI Row
st.subheader("Key Performance Indicators")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Hours", f"{total_hrs:.2f} hrs")
m2.metric("Calendar Days Active", f"{calendar_days}")
m3.metric("Standard Work Days", f"{standard_days:.2f}")
m4.metric("Daily Intensity", f"{intensity:.1f}%")

st.divider()

# 7. Visualizations
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Machinery Utilization (Stacked by Operator)")
    # Visualizes the Many-to-Many relationship
    fig_mach = px.bar(
        filtered_df, 
        x="Machinery Code", 
        y="Hours", 
        color="Operator Name",
        title="Who worked on which machine?",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_mach, use_container_width=True)

with col2:
    st.subheader("Total Hours by Operator")
    op_sum = filtered_df.groupby('Operator Name')['Hours'].sum().reset_index().sort_values('Hours', ascending=False)
    fig_op = px.pie(op_sum, values='Hours', names='Operator Name', hole=0.4)
    st.plotly_chart(fig_op, use_container_width=True)

st.subheader("Daily Workload Trend")
daily_trend = filtered_df.groupby('Worked Date')['Hours'].sum().reset_index()
fig_trend = px.area(daily_trend, x="Worked Date", y="Hours", line_shape="spline", color_discrete_sequence=['#7e22ce'])
st.plotly_chart(fig_trend, use_container_width=True)

# 8. Data Table
with st.expander("View Raw Filtered Data"):
    st.dataframe(filtered_df.drop(columns=['Hours']), use_container_width=True)