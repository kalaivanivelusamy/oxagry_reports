import streamlit as st
import pandas as pd
import plotly.express as px

# Basic Page Configuration
st.set_page_config(page_title="Ops Report Jan 2026", layout="wide")

# Title and Description
st.title("Machinery & Operator Productivity Dashboard")
st.markdown("Interactive analysis of work hours for January 2026.")

# 1. Data Loading and Processing
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

# 2. Sidebar Filters
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

# 3. Apply Filters to Data
filtered_df = df.copy()

if selected_operators:
    filtered_df = filtered_df[filtered_df['Operator Name'].isin(selected_operators)]

if selected_machines:
    filtered_df = filtered_df[filtered_df['Machinery Code'].isin(selected_machines)]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['Worked Date'].dt.date >= start_date) & 
                             (filtered_df['Worked Date'].dt.date <= end_date)]

# 4. Top Metrics (KPIs)
total_hrs = filtered_df['Hours'].sum()
avg_daily = total_hrs / len(filtered_df['Worked Date'].unique()) if not filtered_df.empty else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total Hours Logged", f"{total_hrs:.2f} hrs")
m2.metric("Active Operators", len(filtered_df['Operator Name'].unique()))
m3.metric("Avg Hours / Day", f"{avg_daily:.2f} hrs")

st.divider()

# 5. Visualizations
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Machinery Utilization (Stacked by Operator)")
    # This addresses the 'Many-to-Many' relationship
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
fig_trend = px.area(daily_trend, x="Worked Date", y="Hours", line_shape="spline")
st.plotly_chart(fig_trend, use_container_width=True)

# 6. Data Table
with st.expander("View Raw Filtered Data"):
    st.dataframe(filtered_df.drop(columns=['Hours']), use_container_width=True)