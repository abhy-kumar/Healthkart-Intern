import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="HealthKart Influencer ROI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLING ---
st.markdown("""
<style>
    /* Base Styles */
    .stApp {
        background-color: #F0F2F6;
    }
    .block-container {
        padding: 1.5rem 2.5rem 2rem;
    }

    /* Typography */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 32px;
        color: #1a1a1a;
    }
    h2 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 24px;
        color: #2a2a2a;
        padding-top: 1rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 18px;
        color: #3a3a3a;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }
    .stMetricValue {
        font-size: 28px !important;
        font-weight: 600 !important;
    }
    .stMetricLabel {
        font-size: 14px !important;
        color: #6e6e73;
    }
    
    /* Sidebar Navigation */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    .stRadio [role="radiogroup"] {
        gap: 0.5rem;
    }
    .stRadio [role="radio"] {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        transition: background-color 0.2s ease;
    }
    .stRadio [aria-checked="true"] {
        background-color: #e6f1fc;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA LOADING AND PROCESSING ---

# Chart & Color Constants
HK_BLUE = '#0079d3'
HK_ORANGE = '#ff4500'
GRAY = '#6e6e73'

@st.cache_data
def load_and_process_data():
    """Loads, merges, and calculates key metrics for all datasets."""
    try:
        # Load data from the user-provided CSV files
        df_influencers = pd.read_csv('influencers.csv')
        df_posts = pd.read_csv('posts.csv')
        df_tracking = pd.read_csv('tracking_data.csv')
        df_payouts = pd.read_csv('payouts.csv')
    except FileNotFoundError as e:
        st.error(f"File not found: {e.filename}. Make sure all CSVs are in the same directory.", icon="🚨")
        return None, None, None

    # --- CORRECTION 1: Handle duplicate 'platform' column before merging ---
    # Merge posts with influencers, dropping the redundant platform column from influencers
    df_merged = df_posts.merge(
        df_influencers.drop('platform', axis=1), 
        left_on='influencer_id', right_on='ID', how='left'
    )
    df_merged = df_merged.merge(df_payouts, on='influencer_id', how='left')
    
    # --- CORRECTION 2: Aggregate revenue, orders, AND campaign at the post level ---
    # This ensures the 'campaign' column is available in the master dataframe.
    post_performance = df_tracking.groupby('source').agg(
        post_orders=('orders', 'sum'),
        post_revenue=('revenue', 'sum'),
        campaign=('campaign', 'first')  # Assume a post belongs to one primary campaign
    ).reset_index()
    
    df_merged = df_merged.merge(post_performance, left_on='post_id', right_on='source', how='left')
    df_merged[['post_orders', 'post_revenue']] = df_merged[['post_orders', 'post_revenue']].fillna(0)
    
    # Calculate advanced metrics
    df_merged['engagement_rate'] = ((df_merged['likes'] + df_merged['comments']) / df_merged['reach']).fillna(0)
    df_merged['cpm'] = np.where(df_merged['reach'] > 0, (df_merged['total_payout'] / (df_merged['reach'] / 1000)), 0)
    total_engagement = df_merged['likes'] + df_merged['comments']
    df_merged['cpe'] = np.where(total_engagement > 0, df_merged['total_payout'] / total_engagement, 0)
    
    # --- Aggregate Data for Analysis ---
    
    # Influencer Level Aggregation (Now groups by the single 'platform' column)
    influencer_agg = df_merged.groupby(['influencer_id', 'name', 'category', 'follower_count', 'platform', 'total_payout']).agg(
        total_revenue=('post_revenue', 'sum'),
        total_orders=('post_orders', 'sum'),
        total_reach=('reach', 'sum'),
        total_likes=('likes', 'sum'),
        total_comments=('comments', 'sum'),
        avg_engagement_rate=('engagement_rate', 'mean')
    ).reset_index()
    
    influencer_agg = calculate_metrics(influencer_agg, 'total_revenue', 'total_payout')
    
    # Campaign Level Aggregation
    campaign_agg = df_merged.groupby('campaign').agg(
        revenue=('post_revenue', 'sum'),
        total_payout=('total_payout', 'sum'),
        unique_influencers=('influencer_id', 'nunique')
    ).reset_index()
    campaign_agg = calculate_metrics(campaign_agg, 'revenue', 'total_payout')
    
    # Calculate Baseline for iROAS
    baseline_roas = campaign_agg['revenue'].sum() / campaign_agg['total_payout'].sum() if campaign_agg['total_payout'].sum() > 0 else 0
    campaign_agg['iroas'] = campaign_agg['roas'] - baseline_roas
    influencer_agg['iroas'] = influencer_agg['roas'] - baseline_roas

    return df_merged, influencer_agg, campaign_agg

def calculate_metrics(df, revenue_col, payout_col):
    """Calculates ROI and ROAS on a dataframe."""
    df['roas'] = np.where(df[payout_col] > 0, df[revenue_col] / df[payout_col], 0)
    df['roi'] = np.where(df[payout_col] > 0, (df[revenue_col] - df[payout_col]) / df[payout_col], 0)
    return df

# Load all data
df_merged, df_influencer_agg, df_campaign_agg = load_and_process_data()
if df_merged is None:
    st.stop()
    
baseline_roas = df_campaign_agg['roas'].mean()

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.title("HealthKart")
    
    page = st.radio("Navigation", 
                    ['🏠 Overview', '📊 Campaign Analysis', '✨ Influencer Analysis', '📝 Content & Engagement', '💰 Financials & Review'],
                    label_visibility="hidden")
    
    st.markdown("---")
    st.header("Filters")
    
    # Ensure campaign list is not empty before passing to multiselect
    campaign_options = df_campaign_agg['campaign'].dropna().unique()
    selected_campaigns = st.multiselect(
        "Campaigns", 
        options=campaign_options,
        default=campaign_options
    )
    
    selected_categories = st.multiselect(
        "Influencer Categories",
        options=df_influencer_agg['category'].unique(),
        default=df_influencer_agg['category'].unique()
    )
    
    min_followers, max_followers = int(df_influencer_agg['follower_count'].min()), int(df_influencer_agg['follower_count'].max())
    follower_range = st.slider(
        "Follower Count",
        min_value=min_followers,
        max_value=max_followers,
        value=(min_followers, max_followers)
    )

# --- Filter Application ---
filtered_influencers = df_influencer_agg[
    (df_influencer_agg['category'].isin(selected_categories)) &
    (df_influencer_agg['follower_count'].between(follower_range[0], follower_range[1]))
]

filtered_campaigns = df_campaign_agg[df_campaign_agg['campaign'].isin(selected_campaigns)]

filtered_posts = df_merged[
    (df_merged['influencer_id'].isin(filtered_influencers['influencer_id'])) &
    (df_merged['campaign'].isin(selected_campaigns))
]

# --- 5. PAGE DEFINITIONS ---

def render_overview_page():
    st.title("🏠 Executive Overview")
    st.markdown("A high-level summary of influencer marketing performance based on selected filters.")

    total_revenue = filtered_influencers['total_revenue'].sum()
    total_payout = filtered_influencers['total_payout'].sum()
    roas = total_revenue / total_payout if total_payout > 0 else 0
    roi = (total_revenue - total_payout) / total_payout if total_payout > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Total Payout", f"₹{total_payout:,.0f}")
    col3.metric("Overall ROAS", f"{roas:.2f}x")
    col4.metric("Overall ROI", f"{roi:.2%}")
    
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 Campaigns by ROAS")
        st.dataframe(filtered_campaigns.nlargest(5, 'roas')[['campaign', 'revenue', 'roas']], 
                     use_container_width=True, hide_index=True,
                     column_config={
                         "campaign": "Campaign",
                         "revenue": st.column_config.NumberColumn("Revenue", format="₹%.0f"),
                         "roas": st.column_config.ProgressColumn("ROAS", format="%.2fx", min_value=0, max_value=int(filtered_campaigns['roas'].max()+1))
                     })
    with col2:
        st.subheader("Top 5 Influencers by Revenue")
        st.dataframe(filtered_influencers.nlargest(5, 'total_revenue')[['name', 'total_revenue', 'roas']], 
                     use_container_width=True, hide_index=True,
                     column_config={
                         "name": "Influencer",
                         "total_revenue": st.column_config.NumberColumn("Revenue", format="₹%.0f"),
                         "roas": st.column_config.NumberColumn("ROAS", format="%.2fx")
                     })

def render_campaign_analysis_page():
    st.title("📊 Campaign Analysis")
    st.markdown("Deep dive into the performance of individual campaigns.")
    
    st.header("Campaign Financials")
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Revenue', x=filtered_campaigns['campaign'], y=filtered_campaigns['revenue'], marker_color=HK_BLUE))
    fig.add_trace(go.Bar(name='Payout', x=filtered_campaigns['campaign'], y=filtered_campaigns['total_payout'], marker_color=HK_ORANGE))
    fig.update_layout(title_text="Campaign Revenue vs. Payout", barmode='group', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    
    st.header("Incremental ROAS (iROAS)")
    st.info(f"iROAS measures performance against the baseline ROAS of **{baseline_roas:.2f}x**. A positive value indicates above-average performance.", icon="💡")
    df_sorted_iroas = filtered_campaigns.sort_values(by='iroas', ascending=False)
    colors = [HK_BLUE if x >= 0 else HK_ORANGE for x in df_sorted_iroas['iroas']]
    fig_iroas = px.bar(df_sorted_iroas, x='campaign', y='iroas', title="iROAS by Campaign", text_auto='.2f')
    fig_iroas.update_traces(marker_color=colors)
    fig_iroas.update_layout(template='plotly_white', yaxis_title="iROAS Value", xaxis_title=None)
    fig_iroas.add_hline(y=0, line_dash="dot", line_color=GRAY)
    st.plotly_chart(fig_iroas, use_container_width=True)

def render_influencer_analysis_page():
    st.title("✨ Influencer Analysis")
    st.markdown("Evaluate individual influencer effectiveness and identify top performers.")
    
    st.header("ROAS vs. Follower Count")
    fig = px.scatter(
        filtered_influencers, x='follower_count', y='roas',
        size='total_revenue', color='category', hover_name='name',
        title='ROAS vs. Follower Count (Bubble Size = Revenue)',
        labels={'follower_count': 'Follower Count', 'roas': 'Return on Ad Spend (ROAS)'},
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.header("Influencer Performance Metrics")
    st.dataframe(filtered_influencers[[
        'name', 'category', 'follower_count', 'roas', 'iroas', 'total_revenue', 'total_payout', 'avg_engagement_rate'
    ]], use_container_width=True, hide_index=True, column_config={
        "name": "Influencer", "roas": "ROAS", "iroas": "iROAS",
        "total_revenue": st.column_config.NumberColumn("Revenue", format="₹%.0f"),
        "total_payout": st.column_config.NumberColumn("Payout", format="₹%.0f"),
        "avg_engagement_rate": st.column_config.ProgressColumn("Avg. Engagement", format="%.2f%%", min_value=0, max_value=1)
    })

def render_content_page():
    st.title("📝 Content & Engagement Analysis")
    st.markdown("Analyze which posts and captions drive the best results.")
    
    sort_by = st.selectbox("Sort Top Posts By:", ['post_revenue', 'likes', 'engagement_rate'])
    
    top_posts = filtered_posts.nlargest(5, sort_by)
    
    for _, row in top_posts.iterrows():
        st.subheader(f"{row['name']} on {row['platform']}")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"*{row['caption']}*")
        with col2:
            st.metric("Post Revenue", f"₹{row['post_revenue']:,.0f}")
            st.metric("Engagement Rate", f"{row['engagement_rate']:.2%}")
            st.metric("Likes", f"{row['likes']:,}")
        st.markdown("---")

def render_financials_page():
    st.title("💰 Financials & Performance Review")
    st.markdown("Analyze payout structures and identify underperforming assets.")
    
    st.header("Payout Details")
    payouts_to_show = filtered_influencers[['name', 'total_payout']].drop_duplicates()
    st.dataframe(payouts_to_show, hide_index=True, use_container_width=True, column_config={
        "name": "Influencer", "total_payout": st.column_config.NumberColumn("Total Payout", format="₹%.2f")
    })

    st.header("Performance Review Tool")
    roas_threshold = st.slider("Identify Influencers with ROAS below:", 0.0, 3.0, 1.0, 0.1)
    underperformers = filtered_influencers[
        (filtered_influencers['roas'] < roas_threshold) & (filtered_influencers['total_payout'] > 0)
    ]
    st.dataframe(underperformers[[
        'name', 'category', 'roas', 'total_revenue', 'total_payout'
    ]], hide_index=True, use_container_width=True, column_config={
        "name": "Influencer", "roas": st.column_config.NumberColumn("ROAS", format="%.2fx"),
        "total_revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
        "total_payout": st.column_config.NumberColumn("Payout", format="₹%d")
    })

# --- 6. PAGE ROUTING ---
if page == '🏠 Overview':
    render_overview_page()
elif page == '📊 Campaign Analysis':
    render_campaign_analysis_page()
elif page == '✨ Influencer Analysis':
    render_influencer_analysis_page()
elif page == '📝 Content & Engagement':
    render_content_page()
elif page == '💰 Financials & Review':
    render_financials_page()