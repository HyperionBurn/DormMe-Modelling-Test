import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from models import init_db
from metrics import get_monthly_mrr, get_nrr_and_grr, get_cac_ltv_payback, get_cohort_churn, get_monte_carlo_results

# Set page configuration
st.set_page_config(
    page_title="DormMe SaaS Operating System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium high-contrast UI
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00FFCC; /* Bright teal */
    }
    div[data-testid="stMetricDelta"] {
        font-size: 1.2rem;
    }
    /* Headers */
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #1A1C23;
    }
    /* Plotly background transparency handled in charts */
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_engine():
    return init_db()

engine = get_db_engine()

# Sidebar Navigation
st.sidebar.image("https://via.placeholder.com/150x50/0E1117/00FFCC?text=DORMME", width=150)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Historical Operations", "Financial Projections"])

if page == "Historical Operations":
    st.title("Historical Operations (24 Months)")
    st.markdown("---")

    # Fetch Data
    mrr_df = get_monthly_mrr(engine)
    nrr, grr = get_nrr_and_grr(engine)
    metrics = get_cac_ltv_payback(engine)

    # 1. Top-Level Metric Cards
    col1, col2, col3, col4 = st.columns(4)

    current_mrr = mrr_df.iloc[-1]['mrr']
    prev_mrr = mrr_df.iloc[-2]['mrr']
    mrr_delta = ((current_mrr - prev_mrr) / prev_mrr) * 100

    with col1:
        st.metric("Current MRR", f"AED {current_mrr:,.0f}", f"{mrr_delta:.1f}% MoM Growth", delta_color="normal")

    with col2:
        st.metric("Net Revenue Retention", f"{nrr:.1f}%", f"{nrr - 120:.1f}% vs Target", delta_color="normal")

    with col3:
        st.metric("Customer LTV", f"AED {metrics['LTV']:,.0f}", f"{metrics['LTV_CAC_Ratio']:.1f}x LTV:CAC Ratio", delta_color="normal")

    with col4:
        st.metric("CAC Payback Period", f"{metrics['Payback_Period']:.1f} months", f"{12 - metrics['Payback_Period']:.1f} mo vs Target", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. MRR Growth Chart
    st.subheader("Monthly Recurring Revenue Growth")
    fig_mrr = px.line(mrr_df, x='month', y='mrr', markers=True,
                      line_shape='spline', render_mode='svg',
                      labels={'month': 'Month', 'mrr': 'MRR (AED)'})

    fig_mrr.update_traces(line_color='#00FFCC', marker_color='#FF00FF', line_width=4)
    fig_mrr.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FAFAFA'),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#333333'),
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_mrr, use_container_width=True)

    # 3. Cohort Churn Heatmap
    st.subheader("Cohort Retention Matrix")
    cohort_matrix = get_cohort_churn(engine)

    fig_cohort = go.Figure(data=go.Heatmap(
        z=cohort_matrix.values,
        x=cohort_matrix.columns,
        y=cohort_matrix.index,
        colorscale='Viridis',
        zmin=0.5, zmax=1.0,
        hoverongaps=False,
        text=np.round(cohort_matrix.values * 100, 1),
        texttemplate="%{text}%",
        showscale=True
    ))

    fig_cohort.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FAFAFA'),
        xaxis_title="Months Since Joining",
        yaxis_title="Cohort Month",
        height=500,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_cohort, use_container_width=True)


elif page == "Financial Projections":
    st.title("Monte Carlo Financial Projections (36 Months)")
    st.markdown("---")

    # Fetch Monte Carlo Data
    mc_df = get_monte_carlo_results(engine)

    # Selection
    year_select = st.selectbox("Select Projection Year", ["Year 1", "Year 2", "Year 3"])
    col_map = {"Year 1": "y1_arr", "Year 2": "y2_arr", "Year 3": "y3_arr"}
    target_col = col_map[year_select]

    # Calculate Percentiles
    p10 = np.percentile(mc_df[target_col], 10)
    p50 = np.percentile(mc_df[target_col], 50)
    p90 = np.percentile(mc_df[target_col], 90)

    # Target Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("10th Percentile (Worst Case)", f"AED {p10:,.0f}")
    with col2:
        st.metric("50th Percentile (Base Case)", f"AED {p50:,.0f}")
    with col3:
        st.metric("90th Percentile (Best Case)", f"AED {p90:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Histogram Chart
    st.subheader(f"{year_select} ARR Probability Distribution")

    fig_hist = px.histogram(
        mc_df, x=target_col,
        nbins=50,
        marginal="box", # Adds a box plot on top
        color_discrete_sequence=['#00FFCC']
    )

    # Add vertical line for Median
    fig_hist.add_vline(x=p50, line_dash="dash", line_color="#FF00FF", line_width=2,
                       annotation_text=f"Median: AED {p50:,.0f}", annotation_position="top right",
                       annotation_font=dict(color="#FF00FF", size=14))

    fig_hist.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FAFAFA'),
        xaxis_title=f"{year_select} ARR (AED)",
        yaxis_title="Frequency",
        xaxis=dict(showgrid=False, tickformat=",.0f"),
        yaxis=dict(gridcolor='#333333'),
        height=500,
        bargap=0.1
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.caption(f"Based on {len(mc_df):,} randomized simulation runs projecting acquisition, churn, and dynamic pricing models.")