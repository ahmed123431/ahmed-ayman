"""
Preventive Maintenance (PM) Scheduler & Checklist Execution Module.
Automates recurring reliability tasks, audits, and compliance schedules.
"""
import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta
from database import get_connection
from components.ui_helpers import download_df_as_excel_or_csv

FREQUENCY_DAYS = {
    'Daily': 1,
    'Weekly': 7,
    'Monthly': 30,
    'Quarterly': 90,
    'Semi-Annual': 180,
    'Annual': 365
}

def render_pm_page(user):
    """Render Preventive Maintenance Scheduler and Technician Checklist."""
    st.markdown("## 📅 Preventive Maintenance (PM) & Compliance Scheduler")
    st.caption("Manage scheduled inspection rounds, execute digital maintenance checklists, and track compliance due dates.")

    conn = get_connection()
    tab_list, tab_execute, tab_new = st.tabs(["📋 PM Schedules", "✅ Execute PM Checklist", "➕ Create PM Routine"])

    with tab_list:
        pm_df = pd.read_sql_query("""
            SELECT p.id, p.code, p.title, a.asset_tag, a.name as asset_name,
                   p.frequency, p.last_executed, p.next_due, p.assigned_role,
                   p.estimated_hours, p.status, p.checklist_json
            FROM preventive_schedules p
            JOIN assets a ON p.asset_id = a.id
            ORDER BY p.next_due ASC
        """, conn)

        # Overview cards
        c1, c2, c3 = st.columns(3)
        today = date.today().isoformat()
        with c1:
            overdue_count = len(pm_df[pm_df['next_due'] < today])
            st.metric("🚨 Overdue PM Routines", overdue_count)
        with c2:
            active_routines = len(pm_df[pm_df['status'] == 'Active'])
            st.metric("🔄 Active PM Routines", active_routines)
        with c3:
            due_soon = len(pm_df[(pm_df['next_due'] >= today) & (pm_df['next_due'] <= (date.today() + timedelta(days=7)).isoformat())])
            st.metric("⏳ Due within 7 Days", due_soon)

        st.markdown("### 📋 Scheduled PM Library")
        display_df = pm_df[['code', 'title', 'asset_tag', 'frequency', 'last_executed', 'next_due', 'assigned_role', 'status']].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        download_df_as_excel_or_csv(display_df, filename="preventive_maintenance_schedules")

    with tab_execute:
        st.markdown("### ✅ Technician Digital Checklist Execution")
        st.info("Select a routine to run inspection checks, verify safety conditions, and sign off execution.")

        active_pms = pm_df[pm_df['status'] == 'Active']
        if active_pms.empty:
            st.warning("No active routines found.")
        else:
            selected_pm_code = st.selectbox("Select Scheduled Routine to Execute", active_pms['code'].tolist(), format_func=lambda x: f"{x} - {active_pms.loc[active_pms['code'] == x, 'title'].values[0]}")
            selected_routine = active_pms[active_pms['code'] == selected_pm_code].iloc[0]

            st.markdown(f"**Asset:** `{selected_routine['asset_tag']}` - **Frequency:** `{selected_routine['frequency']}` | **Due:** `{selected_routine['next_due']}`")

            # Parse Checklist JSON
            try:
                checklist = json.loads(selected_routine['checklist_json'])
            except Exception:
                checklist = []

            with st.form(f"run_pm_{selected_routine['id']}"):
                st.markdown("#### Inspection Steps & Checkpoints:")
                checked_states = []
                for idx, item in enumerate(checklist):
                    task_text = item.get("task", f"Task {idx+1}")
                    checked = st.checkbox(f"✔️ {task_text}", key=f"chk_{selected_routine['id']}_{idx}")
                    checked_states.append(checked)

                technician_notes = st.text_area("Technician Field Remarks / Findings", placeholder="e.g. Operating pressures normal. Minor dust cleaned on condenser coils.")
                actual_hours = st.number_input("Actual Execution Time (Hours)", min_value=0.25, max_value=24.0, value=float(selected_routine['estimated_hours']), step=0.25)

                complete_pm = st.form_submit_button("Sign Off & Complete PM Routine", type="primary")
                if complete_pm:
                    all_passed = all(checked_states)
                    if not all_passed:
                        st.warning("⚠️ Note: Some checklist items were left unchecked. Please confirm all inspection points.")
                    
                    cur = conn.cursor()
                    today_date = date.today()
                    freq_days = FREQUENCY_DAYS.get(selected_routine['frequency'], 30)
                    next_due_date = today_date + timedelta(days=freq_days)

                    cur.execute("""
                        UPDATE preventive_schedules
                        SET last_executed = ?, next_due = ?
                        WHERE id = ?
                    """, (today_date.isoformat(), next_due_date.isoformat(), int(selected_routine['id'])))

                    # Log a completed work order record for accountability and maintenance history
                    cur.execute("SELECT COUNT(*) FROM work_orders")
                    wo_count = cur.fetchone()[0] + 1
                    wo_code = f"PM-WO-{today_date.strftime('%Y%m')}-{wo_count:03d}"
                    labor_cost = actual_hours * 60.0

                    cur.execute("""
                        INSERT INTO work_orders (
                            wo_number, title, description, asset_id, priority, status,
                            assigned_to, reported_by, due_date, completed_at, labor_hours, labor_cost, resolution_summary
                        ) VALUES (?, ?, ?, ?, 'Medium', 'Completed', ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        wo_code,
                        f"Routine PM Execution: {selected_routine['title']}",
                        f"Checklist executed by {user['full_name']}. Findings: {technician_notes or 'Routine inspection passed nominal parameters.'}",
                        int(selected_routine['asset_id']) if 'asset_id' in selected_routine else 1,
                        user['id'],
                        user['id'],
                        today_date.isoformat(),
                        today_date.isoformat(),
                        actual_hours,
                        labor_cost,
                        f"All steps completed. Next due on {next_due_date.isoformat()}."
                    ))

                    conn.commit()
                    st.success(f"PM Routine '{selected_pm_code}' signed off! Next execution scheduled for {next_due_date.isoformat()}.")
                    st.rerun()

    with tab_new:
        st.markdown("### ➕ Create New Preventive Maintenance Routine")
        if user['role'] in ['Tenant', 'Technician']:
            st.warning("⚠️ Only Operations Managers and Engineers can configure PM routines.")
        else:
            assets = pd.read_sql_query("SELECT id, asset_tag, name FROM assets ORDER BY asset_tag", conn)
            asset_opts = {row['id']: f"{row['asset_tag']} - {row['name']}" for _, row in assets.iterrows()}

            with st.form("new_pm_routine_form"):
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    new_code = st.text_input("Routine Code *", placeholder="e.g. PM-ELEV-Q01, PM-GEN-W02")
                    new_title = st.text_input("Routine Title *", placeholder="e.g. Quarterly Elevator Governor & Brake Test")
                    chosen_asset = st.selectbox("Asset *", options=list(asset_opts.keys()), format_func=lambda x: asset_opts[x])

                with p_c2:
                    new_freq = st.selectbox("Frequency", list(FREQUENCY_DAYS.keys()), index=2)
                    assigned_role = st.selectbox("Assigned Role", ['Technician', 'Engineer', 'Specialist Contractor'])
                    est_hrs = st.number_input("Estimated Labor Hours", min_value=0.5, max_value=40.0, value=2.0, step=0.5)

                st.markdown("#### Inspection Checklist Items (one per line):")
                tasks_raw = st.text_area("Checklist Tasks", value="Inspect mechanical drive belts for wear\nCheck oil level and clear oil filter\nMeasure motor vibration and thermal temperature\nVerify emergency shut-off operation")

                save_routine = st.form_submit_button("Create PM Routine", type="primary")
                if save_routine:
                    if not new_code or not new_title:
                        st.error("Please provide both Routine Code and Title.")
                    else:
                        task_lines = [t.strip() for t in tasks_raw.strip().split("\n") if t.strip()]
                        checklist_data = [{"task": t, "done": False} for t in task_lines]
                        checklist_json = json.dumps(checklist_data)
                        
                        next_date = date.today() + timedelta(days=FREQUENCY_DAYS.get(new_freq, 30))

                        cur = conn.cursor()
                        try:
                            cur.execute("""
                                INSERT INTO preventive_schedules (
                                    code, title, asset_id, frequency, checklist_json,
                                    last_executed, next_due, assigned_role, estimated_hours, status
                                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, 'Active')
                            """, (
                                new_code.strip().upper(), new_title.strip(), chosen_asset,
                                new_freq, checklist_json, next_date.isoformat(), assigned_role, est_hrs
                            ))
                            conn.commit()
                            st.success(f"Preventive Routine '{new_code.upper()}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating routine: {e}")

    conn.close()
