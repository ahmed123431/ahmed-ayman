"""
Failure Mode and Effects Analysis (FMEA) & RCM Decision Module.
Calculates Risk Priority Number (RPN = Severity * Occurrence * Detection)
and maps equipment maintenance strategies.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
from components.ui_helpers import download_df_as_excel_or_csv

RCM_MAINT_STRATEGIES = [
    'Predictive (CBM)',
    'Preventive (Time-based)',
    'Condition-based Monitoring',
    'Periodic Inspection & Testing',
    'Failure Finding',
    'Run-to-Failure'
]

def render_fmea_page(user):
    """Render FMEA Analysis and Strategy configuration."""
    st.markdown("## 🔬 Failure Mode and Effects Analysis (FMEA / RCM)")
    st.caption("Identify equipment failure mechanisms, calculate RPN risk scores, and establish optimal maintenance strategies.")

    tab_view, tab_add = st.tabs(["📊 FMEA Risk Register", "➕ Conduct New FMEA Analysis"])

    conn = get_connection()

    with tab_view:
        fmea_df = pd.read_sql_query("""
            SELECT f.id, a.asset_tag, a.name as asset_name, a.category,
                   f.failure_mode, f.failure_cause, f.failure_effect,
                   f.severity, f.occurrence, f.detection, f.rpn,
                   f.recommended_action, f.maintenance_strategy
            FROM fmea_records f
            JOIN assets a ON f.asset_id = a.id
            ORDER BY f.rpn DESC
        """, conn)

        # High-level RPN summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            high_risk_count = len(fmea_df[fmea_df['rpn'] >= 80])
            st.metric("🚨 Critical RPN (≥ 80)", high_risk_count, "Urgent predictive action")
        with col2:
            med_risk_count = len(fmea_df[(fmea_df['rpn'] >= 40) & (fmea_df['rpn'] < 80)])
            st.metric("⚠️ Medium RPN (40 - 79)", med_risk_count, "Preventive servicing")
        with col3:
            low_risk_count = len(fmea_df[fmea_df['rpn'] < 40])
            st.metric("🟢 Low RPN (< 40)", low_risk_count, "Condition monitoring")

        # Visual Scatter Chart: Severity vs Occurrence colored by RPN
        if not fmea_df.empty:
            st.markdown("### 📈 Risk Severity vs Occurrence Matrix")
            fig = px.scatter(
                fmea_df,
                x='occurrence',
                y='severity',
                size='rpn',
                color='rpn',
                hover_name='failure_mode',
                hover_data=['asset_tag', 'maintenance_strategy'],
                color_continuous_scale='Turbo',
                labels={'occurrence': 'Occurrence (1=Rare, 10=Frequent)', 'severity': 'Severity (1=Minor, 10=Hazardous)'}
            )
            fig.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📋 Active FMEA Risk Register")
        if fmea_df.empty:
            st.info("No FMEA records logged yet.")
        else:
            st.dataframe(fmea_df, use_container_width=True, hide_index=True)
            download_df_as_excel_or_csv(fmea_df, filename="fmea_analysis_export")

            # Quick update mitigation action
            st.markdown("### ✏️ Update Mitigation & Maintenance Strategy")
            rec_id = st.selectbox("Select FMEA Item to Edit", fmea_df['id'].tolist(), format_func=lambda x: f"Item #{x}: {fmea_df.loc[fmea_df['id'] == x, 'failure_mode'].values[0]}")
            curr_row = fmea_df[fmea_df['id'] == rec_id].iloc[0]

            with st.form(f"update_fmea_{rec_id}"):
                c1, c2 = st.columns(2)
                with c1:
                    new_action = st.text_area("Recommended Action / Countermeasure", value=curr_row['recommended_action'])
                with c2:
                    current_idx = RCM_MAINT_STRATEGIES.index(curr_row['maintenance_strategy']) if curr_row['maintenance_strategy'] in RCM_MAINT_STRATEGIES else 0
                    new_strat = st.selectbox("Assigned RCM Strategy", RCM_MAINT_STRATEGIES, index=current_idx)
                
                update_btn = st.form_submit_button("Update FMEA Record", type="primary")
                if update_btn:
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE fmea_records
                        SET recommended_action = ?, maintenance_strategy = ?
                        WHERE id = ?
                    """, (new_action.strip(), new_strat, int(rec_id)))
                    conn.commit()
                    st.success("FMEA record updated successfully!")
                    st.rerun()

    with tab_add:
        st.markdown("### ➕ Perform FMEA on an Asset")
        if user['role'] in ['Tenant']:
            st.warning("⚠️ Only Operations Managers and Engineers can create FMEA studies.")
        else:
            assets = pd.read_sql_query("SELECT id, asset_tag, name FROM assets ORDER BY asset_tag", conn)
            asset_options = {row['id']: f"{row['asset_tag']} - {row['name']}" for _, row in assets.iterrows()}

            with st.form("new_fmea_form"):
                target_asset_id = st.selectbox("Target Equipment *", options=list(asset_options.keys()), format_func=lambda x: asset_options[x])
                
                f_mode = st.text_input("Potential Failure Mode *", placeholder="e.g. Chilled water pump mechanical seal leak")
                f_cause = st.text_area("Root Cause of Failure *", placeholder="e.g. Dry running or abrasive particle erosion")
                f_effect = st.text_area("Operational & Mall Impact *", placeholder="e.g. Flooding in basement plant room, loss of HVAC cooling to cinema")

                st.markdown("#### RPN Scoring Matrix (1 to 10 Scale)")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    sev = st.slider("Severity (S) [1=None, 10=Life Hazard]", 1, 10, 5)
                with sc2:
                    occ = st.slider("Occurrence (O) [1=Extremely Rare, 10=Almost Inevitable]", 1, 10, 3)
                with sc3:
                    det = st.slider("Detection (D) [1=Instant Auto-Alarm, 10=Undetectable until Failure]", 1, 10, 4)

                calc_rpn = sev * occ * det
                st.info(f"**Calculated Risk Priority Number (RPN): {calc_rpn}**")

                rec_action = st.text_area("Mitigation Action / Preventive Task", placeholder="e.g. Install dual sensor differential pressure switch and auto-grease canister")
                strategy = st.selectbox("Recommended RCM Maintenance Strategy", RCM_MAINT_STRATEGIES)

                create_fmea = st.form_submit_button("Save FMEA Analysis", type="primary")
                if create_fmea:
                    if not f_mode or not f_cause or not f_effect:
                        st.error("Please fill in the Failure Mode, Cause, and Effect fields.")
                    else:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO fmea_records (
                                asset_id, failure_mode, failure_cause, failure_effect,
                                severity, occurrence, detection, rpn, recommended_action, maintenance_strategy
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            target_asset_id, f_mode.strip(), f_cause.strip(), f_effect.strip(),
                            sev, occ, det, calc_rpn, rec_action.strip(), strategy
                        ))
                        conn.commit()
                        st.success("New FMEA study saved successfully!")
                        st.rerun()

    conn.close()
