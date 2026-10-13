"""
Mall Executive RCM Analytics Dashboard:
Real-time equipment availability, MTBF, MTTR, critical asset health, and maintenance cost metrics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_connection
from components.ui_helpers import render_kpi_card, status_badge_html, priority_badge_html

def render_dashboard(user):
    """Render the full Reliability Centered Maintenance Executive Dashboard."""
    st.markdown("## 📊 Executive Reliability & Mall Operations Dashboard")
    st.caption("Live monitoring of physical assets, uptime performance, critical FMEA risks, and maintenance workflows.")

    conn = get_connection()
    assets_df = pd.read_sql_query("""
        SELECT a.*, l.name as location_name, l.zone_type 
        FROM assets a 
        LEFT JOIN locations l ON a.location_id = l.id
    """, conn)

    wo_df = pd.read_sql_query("""
        SELECT w.*, a.name as asset_name, a.asset_tag, u.full_name as tech_name
        FROM work_orders w
        LEFT JOIN assets a ON w.asset_id = a.id
        LEFT JOIN users u ON w.assigned_to = u.id
    """, conn)

    fmea_df = pd.read_sql_query("""
        SELECT f.*, a.name as asset_name, a.asset_tag
        FROM fmea_records f
        LEFT JOIN assets a ON f.asset_id = a.id
    """, conn)
    conn.close()

    # Calculate Top KPIs
    total_assets = len(assets_df)
    operational_assets = len(assets_df[assets_df['status'] == 'Operational'])
    availability_pct = round((operational_assets / total_assets * 100), 1) if total_assets > 0 else 100.0

    active_wos = len(wo_df[~wo_df['status'].isin(['Completed', 'Cancelled'])])
    critical_wos = len(wo_df[(wo_df['priority'] == 'Critical / Emergency') & (~wo_df['status'].isin(['Completed', 'Cancelled']))])

    # MTTR Calculation (completed work orders with labor_hours)
    completed_wos = wo_df[wo_df['status'] == 'Completed']
    avg_mttr_hrs = round(completed_wos['labor_hours'].mean(), 1) if len(completed_wos) > 0 else 2.5
    total_costs = round((wo_df['labor_cost'].sum() + wo_df['parts_cost'].sum()), 2)
    high_rpn_risks = len(fmea_df[fmea_df['rpn'] >= 80])

    # Render KPI Cards in a grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color_sub = "🟢 Target: ≥ 98%" if availability_pct >= 95 else "🔴 Below Threshold"
        render_kpi_card("Mall Asset Availability", f"{availability_pct}%", f"{operational_assets}/{total_assets} online ({color_sub})", "🏢")
    with c2:
        render_kpi_card("Mean Time To Repair (MTTR)", f"{avg_mttr_hrs} hrs", "Average turnaround per incident", "⏱️")
    with c3:
        status_note = f"⚠️ {critical_wos} Emergency" if critical_wos > 0 else "🟢 Zero emergencies"
        render_kpi_card("Active Work Orders", f"{active_wos}", status_note, "🛠️")
    with c4:
        render_kpi_card("High FMEA Risks (RPN ≥ 80)", f"{high_rpn_risks}", "Requires predictive mitigation", "⚠️")

    st.markdown("---")

    # Layout: Visual Charts
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### ⚙️ Asset Health Status Distribution")
        status_counts = assets_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        color_map = {
            'Operational': '#10B981',
            'Degraded': '#F59E0B',
            'Under Maintenance': '#3B82F6',
            'Out of Service': '#EF4444'
        }
        fig_status = px.pie(
            status_counts,
            names='Status',
            values='Count',
            hole=0.45,
            color='Status',
            color_discrete_map=color_map
        )
        fig_status.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_status, use_container_width=True)

    with col_right:
        st.markdown("### 🎯 Criticality vs RCM Maintenance Strategy")
        strategy_counts = assets_df.groupby(['criticality', 'rcm_strategy']).size().reset_index(name='Count')
        fig_strategy = px.bar(
            strategy_counts,
            x='criticality',
            y='Count',
            color='rcm_strategy',
            barmode='stack',
            labels={'criticality': 'Asset Criticality', 'Count': 'Number of Assets', 'rcm_strategy': 'RCM Strategy'},
            color_discrete_sequence=['#38BDF8', '#818CF8', '#F472B6', '#34D399']
        )
        fig_strategy.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_strategy, use_container_width=True)

    # Work Order Backlog & Costs
    c_w1, c_w2 = st.columns([1, 1])
    with c_w1:
        st.markdown("### 📋 Work Orders by Priority & Lifecycle")
        fig_wo = px.histogram(
            wo_df,
            x='status',
            color='priority',
            barmode='group',
            color_discrete_map={
                'Critical / Emergency': '#EF4444',
                'High': '#F97316',
                'Medium': '#EAB308',
                'Low': '#10B981'
            }
        )
        fig_wo.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
        st.plotly_chart(fig_wo, use_container_width=True)

    with c_w2:
        st.markdown("### 💰 Maintenance Cost Breakdown (YTD)")
        cost_df = pd.DataFrame({
            'Category': ['Labor Expenses', 'Spare Parts & Materials'],
            'Cost ($)': [wo_df['labor_cost'].sum(), wo_df['parts_cost'].sum()]
        })
        fig_cost = px.pie(
            cost_df,
            names='Category',
            values='Cost ($)',
            hole=0.4,
            color_discrete_sequence=['#6366F1', '#EC4899']
        )
        fig_cost.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
        st.plotly_chart(fig_cost, use_container_width=True)

    # Attention & Alert List (Degraded or Out of Service Assets)
    st.markdown("### 🚨 Critical Attention Items (Degraded or Requiring Intervention)")
    troubled_assets = assets_df[assets_df['status'] != 'Operational']
    if troubled_assets.empty:
        st.success("🎉 All mall assets are currently operating at 100% nominal capacity!")
    else:
        for _, row in troubled_assets.iterrows():
            with st.container():
                cols = st.columns([1.5, 3, 2, 2])
                with cols[0]:
                    st.markdown(f"**{row['asset_tag']}**")
                with cols[1]:
                    st.markdown(f"{row['name']} *(Location: {row['location_name']})*")
                with cols[2]:
                    st.markdown(status_badge_html(row['status']), unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(f"Criticality: `{row['criticality']}`")
                st.divider()
