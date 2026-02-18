import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration & Theme
st.set_page_config(page_title="Ops Report Jan 2026", layout="wide")

# Constants
HOURS_PER_DAY = 8 

# Custom Styling for Purple Theme
st.markdown("""
    <style>
    .main { background-color: #f5f3ff; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #ddd6fe;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #7e22ce;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Loading (Keeps all months in Master Sheet)
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('operator_work_hours_jan_2026.csv')
    
    def time_to_hours(time_str):
        try:
            h, m, s = map(int, str(time_str).split(':'))
            return h + m/60 + s/3600
        except: return 0.0
            
    df['Hours'] = df['Total Hours'].apply(time_to_hours)
    df['Worked Date'] = pd.to_datetime(df['Worked Date'])
    return df

df = load_and_process_data()

# 3. Sidebar Filters
st.sidebar.header("Filter Dashboard")
selected_ops = st.sidebar.multiselect("Select Operator", options=sorted(df['Operator Name'].unique()))
selected_mach = st.sidebar.multiselect("Select Machinery", options=sorted(df['Machinery Code'].unique()))

st.sidebar.divider()
st.sidebar.subheader("Settings")
# NEW: Option to toggle how days are counted
day_method = st.sidebar.radio(
    "Day Count Method",
    ["Unique Calendar Days", "Total Log Entries"],
    help="Unique: Counts distinct dates. Log Entries: Counts every row in the master sheet."
)

# Apply Filters
filtered_df = df.copy()
if selected_ops:
    filtered_df = filtered_df[filtered_df['Operator Name'].isin(selected_ops)]
if selected_mach:
    filtered_df = filtered_df[filtered_df['Machinery Code'].isin(selected_mach)]

# 4. Metrics Logic
total_hrs = filtered_df['Hours'].sum()

# Conditional Logic for Day Count
if day_method == "Unique Calendar Days":
    day_count = filtered_df['Worked Date'].nunique()
    day_label = "Calendar Days Active"
    day_help = "Unique dates the asset was utilized"
else:
    day_count = len(filtered_df)
    day_label = "Total Log Entries"
    day_help = "Every single log entry recorded in the period"

standard_days = total_hrs / HOURS_PER_DAY
# Intensity is always calculated against unique days to show real daily workload
actual_days = filtered_df['Worked Date'].nunique()
intensity = (standard_days / actual_days * 100) if actual_days > 0 else 0

# 5. Dynamic Naming for Indicators
target_name = ""
if len(selected_mach) == 1:
    target_name = f" - {selected_mach[0]}"
elif len(selected_ops) == 1:
    target_name = f" - {selected_ops[0]}"

st.title(f"🚜 Operational Performance{target_name}")
st.markdown("---")

# 6. KPI Row with Dynamic Labels
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Hours Logged", f"{total_hrs:.2f} hrs")

# Displays the selected day count method
m2.metric(f"{day_label}", f"{day_count}")
m2.caption(day_help)

m3.metric(f"Work Days (8hr Equivalent)", f"{standard_days:.2f}")
m3.caption(f"Actual output / {HOURS_PER_DAY}hr shift")

m4.metric("Daily Intensity", f"{intensity:.1f}%")

st.divider()

# 7. Visualizations
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Machinery Usage (Stacked by Operator)")
    fig_mach = px.bar(
        filtered_df, x="Machinery Code", y="Hours", color="Operator Name",
        color_discrete_sequence=px.colors.sequential.Purples_r
    )
    st.plotly_chart(fig_mach, use_container_width=True)

with col2:
    st.subheader("Operator Work Share")
    op_sum = filtered_df.groupby('Operator Name')['Hours'].sum().reset_index()
    fig_pie = px.pie(op_sum, values='Hours', names='Operator Name', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Daily Work Trend")
daily_trend = filtered_df.groupby('Worked Date')['Hours'].sum().reset_index()
fig_trend = px.area(daily_trend, x="Worked Date", y="Hours", color_discrete_sequence=['#7e22ce'])
st.plotly_chart(fig_trend, use_container_width=True)

# 8. Raw Data View
with st.expander("🔍 View Raw Log Details"):
    st.write(f"Showing {len(filtered_df)} log entries")
    st.dataframe(filtered_df.drop(columns=['Hours']), use_container_width=True)