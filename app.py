import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Care Transition Dashboard",
    layout="wide"
)

st.markdown("""
<style>

/* Main Background */
.stApp {
    background-color: #0E1117;
    color: #FFFFFF;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161B22;
}

/* Metric Cards */
div[data-testid="metric-container"] {
    background: linear-gradient(
        135deg,
        #1D4E89,
        #0A2342
    );

    border-radius: 18px;

    padding: 20px;

    border: 1px solid rgba(255,255,255,0.1);

    box-shadow:
        0 4px 20px rgba(0,0,0,0.35);

    text-align:center;
}

div[data-testid="metric-container"] label {
    color:white !important;
    font-size:14px !important;
}

div[data-testid="metric-container"] div {
    color:white !important;
}

/* Headers */
h1, h2, h3 {
    color: #FFFFFF;
}

.dashboard-title {
    background: linear-gradient(90deg,#0A2342,#1D4E89);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    color: white;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

df = pd.read_csv('cleaned_data.xls')

# ---------------------------------------------------
# DATE COLUMN
# ---------------------------------------------------

df['Date'] = pd.to_datetime(
    df['Date'],
    errors='coerce'
)

# Remove invalid dates
df = df.dropna(subset=['Date'])

# ---------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------

df['Transfer_Efficiency'] = (
        df['Transferred_Out'] /
        df['CBP_Custody']
)

df['Discharge_Effectiveness'] = (
    df['Discharged'] /
    df['HHS_Care']
)

df['Pipeline_Throughput'] = (
    df['Discharged'] /
    df['Apprehended']
)

df['Backlog_Accumulation'] = (
    df['Apprehended'] -
    df['Discharged']
)

df['Backlog_Size'] = abs(df['Backlog_Accumulation'])

# ---------------------------------------------------
# MOVING AVERAGES
# ---------------------------------------------------

df['Transfer_MA7'] = (
    df['Transfer_Efficiency']
    .rolling(7, min_periods=1)
    .mean()
)

df['Discharge_MA7'] = (
    df['Discharge_Effectiveness']
    .rolling(7, min_periods=1)
    .mean()
)

# ---------------------------------------------------
# STABILITY SCORE
# ---------------------------------------------------

df['Stability_Score'] = (
    df['Discharge_Effectiveness']
    .rolling(7, min_periods=1)
    .std()
)

df['Stability_Score'] = (
    df['Stability_Score']
    .fillna(0)
)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

st.sidebar.header("Filters")

start_date = st.sidebar.date_input(
    "Start Date",
    df['Date'].min(),
    key="start_date"
)

end_date = st.sidebar.date_input(
    "End Date",
    df['Date'].max(),
    key="end_date"
)

st.sidebar.subheader("Alert Thresholds")

efficiency_threshold = st.sidebar.slider(
    "Efficiency Threshold",
    0.0,
    1.0,
    0.60
)

st.sidebar.subheader("Metric Toggle")

selected_ratio = st.sidebar.selectbox(
    "Select Performance Metric",
    [
        "Transfer_Efficiency",
        "Discharge_Effectiveness",
        "Pipeline_Throughput"
    ]
)

# ---------------------------------------------------
# FILTER DATA
# ---------------------------------------------------

filtered_df = df[
    (df['Date'] >= pd.to_datetime(start_date)) &
    (df['Date'] <= pd.to_datetime(end_date))
]

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.markdown("""
<div class="dashboard-title">
<h1>UAC Care Pipeline Analytics Dashboard</h1>
<h4>HHS Child Welfare Monitoring & Process Efficiency System</h4>
</div>
""", unsafe_allow_html=True)


st.divider()

# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Apprehended",
        int(filtered_df['Apprehended'].sum())
    )

with col2:
    st.metric(
        "Total Discharged",
        int(filtered_df['Discharged'].sum())
    )

with col3:
    st.metric(
        "Avg Transfer Efficiency",
        round(
            filtered_df['Transfer_Efficiency'].mean(),
            2,
            
        )
    )

with col4:
    st.metric(
        "Peak Backlog",
        int(filtered_df['Backlog_Size'].max())
    )

st.divider()

# ---------------------------------------------------
# SYSTEM HEALTH STATUS
# ---------------------------------------------------

transfer_avg = filtered_df[
    'Transfer_Efficiency'
].mean()

discharge_avg = filtered_df[
    'Discharge_Effectiveness'
].mean()

throughput_avg = filtered_df[
    'Pipeline_Throughput'
].mean()

backlog_avg = filtered_df[
    'Backlog_Size'
].mean()

st.subheader("System Health Status")

col1, col2 = st.columns(2)

with col1:

    if transfer_avg >= efficiency_threshold:
        st.success("✓ Transfer Process Healthy")
    else:
        st.error("✗ Transfer Process Needs Attention")

with col2:

    if discharge_avg >= efficiency_threshold:
        st.success("✓ Discharge Process Healthy")
    else:
        st.error("✗ Discharge Process Needs Attention")

st.divider()

# ---------------------------------------------------
# SELECTED KPI TREND
# ---------------------------------------------------

st.subheader("Selected Performance Metric")

fig = px.line(
    filtered_df,
    x='Date',
    y=selected_ratio,
    title="Performance Metric Trend Over Time"
)

fig.update_layout(
    yaxis_title = "Ratio Value",
    xaxis_title = "Date"
    )

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# ---------------------------------------------------
# ALERT CENTER
# ---------------------------------------------------

st.subheader("🚨 Alert Center")

alert_count = 0

# Transfer Alert
if transfer_avg < efficiency_threshold:

    st.error(
        f"Transfer Efficiency is low ({transfer_avg:.2f}). Children may be experiencing delays moving into HHS care."
    )

    alert_count += 1

# Discharge Alert
if discharge_avg < efficiency_threshold:

    st.warning(
        f"Discharge Effectiveness is below target ({discharge_avg:.2f}). Reunification outcomes may be slowing."
    )

    alert_count += 1

# Throughput Alert
if throughput_avg < 1:

    st.warning(
        f"Pipeline Throughput is below 1 ({throughput_avg:.2f}). Exits are not keeping pace with entries."
    )

    alert_count += 1

# Backlog Alert
if backlog_avg > 1000:

    st.error(
        f"Critical backlog detected ({backlog_avg:,.0f} cases)."
    )

    alert_count += 1

# System Healthy
if alert_count == 0:

    st.success(
        "No critical alerts detected. Pipeline performance is within expected limits."
    )

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Efficiency",
    "Bottlenecks",
    "Stability"
])

# ===================================================
# TAB 1 — OVERVIEW
# ===================================================

with tab1:

    st.subheader("Care Pipeline Flow")

    latest = filtered_df.iloc[-1]

    col1, col2 = st.columns([2,1])

    with col1:

        fig = go.Figure(go.Funnel(
            y = [
                "Apprehended",
                "CBP Custody",
                "Transferred Out",
                "HHS Care",
                "Discharged"
            ],

            x = [
                latest['Apprehended'],
                latest['CBP_Custody'],
                latest['Transferred_Out'],
                latest['HHS_Care'],
                latest['Discharged']
            ]
        ))

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        st.info(
            "Transfer efficiency reflects how quickly children move from CBP custody into HHS care."
        )

        st.warning(
            "Backlog accumulation indicates unresolved cases increasing over time."
        )

        st.success(
            "Higher discharge effectiveness indicates faster reunification outcomes."
        )

    st.divider()

    st.subheader("Daily Flow Trends")

    fig = px.line(
        filtered_df,
        x='Date',
        y=[
            'Apprehended',
            'Transferred_Out',
            'Discharged'
        ],
        title='Daily Intake, Transfer, and Discharge Volumes'
    )

    fig.update_layout(
        yaxis_title = "Number of Children",
        xaxis_title = "Date"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ===================================================
# TAB 2 — EFFICIENCY
# ===================================================

with tab2:

    col1, col2 = st.columns(2)

    # -----------------------------------------------

    with col1:

        st.subheader("Transfer Efficiency Trend")

        fig = px.histogram(
            filtered_df,
            x='Transfer_Efficiency',
            nbins=20,
            title='Distribution of Transfer Efficiency'
        )
        
        fig.update_layout(
            yaxis_title="Frequency",
            xaxis_title="Transfer Efficiency Ratio"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        
    # -----------------------------------------------

    with col2:

        st.subheader("Discharge Effectiveness Trend")

        fig = px.histogram(
            filtered_df,
            x='Discharge_Effectiveness',
            nbins=20,
            title='Distribution of Discharge Effectiveness'
        )
        
        fig.update_layout(
            yaxis_title="Frequency",
            xaxis_title="Discharge Effectiveness Ratio"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # -----------------------------------------------

    st.subheader("Transfer Efficiency by Month and Day of Week")

    heatmap_data = filtered_df.pivot_table(
        values='Transfer_Efficiency',
        index='Day_name',
        columns='Month',
        aggfunc='mean'
    )

    fig = px.imshow(
        heatmap_data,
        text_auto=True
    )
    
    fig.update_layout(
        yaxis_title="Day of Week",
        xaxis_title="Month"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ===================================================
# TAB 3 — BOTTLENECKS
# ===================================================

with tab3:

    st.subheader("Backlog Growth Over Time")

    fig = px.area(
        filtered_df,
        x='Date',
        y='Backlog_Accumulation'
    )
    
    fig.update_layout(
        yaxis_title="Outstanding Cases",
        xaxis_title="Date"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # -----------------------------------------------

    st.subheader("Bottleneck Detection")

    filtered_df['Status'] = filtered_df[
        'Backlog_Accumulation'
    ].apply(
        lambda x:
        'Backlog Growing'
        if x > 0
        else 'Pipeline Clearing'
    )

    fig = px.scatter(
        filtered_df,
        x='Apprehended',
        y='Discharged',
        size='Backlog_Size',
        color='Status',
        hover_data=['Date'],
        title='Case Intake vs Discharge Relationship'
    )

    fig.update_layout(
        yaxis_title="Daily Discharges",
        xaxis_title="Daily Apprehensions"
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ===================================================
# TAB 4 — STABILITY
# ===================================================

with tab4:

    col1, col2 = st.columns(2)

    # -----------------------------------------------

    with col1:

        st.subheader("7-Day Moving Average Performance Trends")

        fig = px.line(
            filtered_df,
            x='Date',
            y=[
                'Transfer_MA7',
                'Discharge_MA7'
            ]
        )
        
        fig.update_layout(
            yaxis_title="Efficiency Ratio",
            xaxis_title="Date"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------

    with col2:

        st.subheader("Discharge Outcome Stability Over Time")

        fig = px.line(
            filtered_df,
            x='Date',
            y='Stability_Score'
        )

        fig.update_layout(
            yaxis_title="Stability Score",
            xaxis_title="Date"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # -----------------------------------------------

    st.subheader("Average Monthly Pipeline Throughput")

    monthly = filtered_df.groupby(
        'Month'
    ).mean(
        numeric_only=True
    ).reset_index()

    fig = px.bar(
        monthly,
        x='Month',
        y='Pipeline_Throughput'
    )

    fig.update_layout(
        yaxis_title="Throughput Ratio",
        xaxis_title="Month"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()