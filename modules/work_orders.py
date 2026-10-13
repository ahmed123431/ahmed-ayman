"""
Work Order & Incident Management Module (Full CRUD & Lifecycle Tracking).
Handles tenant issue reporting, technician job tracking, parts/labor costing, and resolution.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import get_connection
from components.ui_helpers import status_badge_html, priority_badge_html, download_df_as_excel_or_csv

PRIORITIES = ['Critical / Emergency', 'High', 'Medium', 'Low']
STATUSES = ['New / Reported', 'Under Review', 'Assigned', 'In Progress', 'Pending Parts', 'Completed', 'Cancelled']

def render_work_orders_page(user):
    """Render Work Orders & Incident Management UI."""
    st.markdown("## 🛠️ Work Orders & Maintenance Operations")
    st.caption("Manage scheduled repairs, emergency breakdown calls, technician assignments, and cost accounting.")

    conn = get_connection()
    techs = pd.read_sql_query("SELECT id, full_name FROM users WHERE role IN ('Engineer', 'Technician') ORDER BY full_name", conn)
    tech_map = {row['id']: row['full_name'] for _, row in techs.iterrows()}
    tech_map[0] = "Unassigned"

    assets = pd.read_sql_query("SELECT id, asset_tag, name FROM assets ORDER BY asset_tag", conn)
    asset_map = {row['id']: f"{row['asset_tag']} - {row['name']}" for _, row in assets.iterrows()}

    tab_active, tab_create, tab_history = st.tabs(["📋 Active Work Orders", "➕ Issue New Work Order", "📜 Completed History"])

    with tab_active:
        # Filter Bar
        fc1, fc2, fc3 = st.columns([1.5, 1.5, 1.5])
        with fc1:
            p_filter = st.selectbox("Filter Priority", ["All Priorities"] + PRIORITIES)
        with fc2:
            s_filter = st.selectbox("Filter Status", ["All Active Statuses", "New / Reported", "Under Review", "Assigned", "In Progress", "Pending Parts"])
        with fc3:
            t_filter = st.selectbox("Assigned Technician", ["All Personnel"] + list(tech_map.values()))

        # Query active WOs
        query = """
            SELECT w.*, a.asset_tag, a.name as asset_name, u.full_name as assigned_name, r.full_name as reporter_name
            FROM work_orders w
            JOIN assets a ON w.asset_id = a.id
            LEFT JOIN users u ON w.assigned_to = u.id
            LEFT JOIN users r ON w.reported_by = r.id
            WHERE w.status NOT IN ('Completed', 'Cancelled')
        """
        params = []

        if p_filter != "All Priorities":
            query += " AND w.priority = ?"
            params.append(p_filter)

        if s_filter != "All Active Statuses":
            query += " AND w.status = ?"
            params.append(s_filter)

        if t_filter != "All Personnel":
            query += " AND (u.full_name = ? OR (? = 'Unassigned' AND w.assigned_to IS NULL))"
            params.extend([t_filter, t_filter])

        query += " ORDER BY CASE w.priority WHEN 'Critical / Emergency' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END ASC, w.due_date ASC"
        df_active = pd.read_sql_query(query, conn, params=params)

        st.markdown(f"**{len(df_active)} Open Work Orders In Progress:**")
        if df_active.empty:
            st.success("No active work orders currently open!")
        else:
            display_cols = df_active[['wo_number', 'title', 'asset_tag', 'priority', 'status', 'assigned_name', 'due_date']].copy()
            st.dataframe(display_cols, use_container_width=True, hide_index=True)

            # Interactive Inspector and Action Panel
            st.markdown("### 📝 Work Order Action & Execution Panel")
            selected_wo_num = st.selectbox("Select Work Order to View or Update", df_active['wo_number'].tolist())
            wo_data = df_active[df_active['wo_number'] == selected_wo_num].iloc[0]

            with st.expander(f"🔧 Details for {selected_wo_num}: {wo_data['title']}", expanded=True):
                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    st.write(f"**Asset:** {wo_data['asset_tag']} - {wo_data['asset_name']}")
                    st.write(f"**Reported By:** {wo_data['reporter_name'] or 'Facility System'} on {wo_data['created_at']}")
                    st.write(f"**Description:** {wo_data['description']}")
                with c_info2:
                    st.write(f"**Target Due Date:** `{wo_data['due_date']}`")
                    st.write(f"**Current Status:** {status_badge_html(wo_data['status'])}", unsafe_allow_html=True)
                    st.write(f"**Priority:** {priority_badge_html(wo_data['priority'])}", unsafe_allow_html=True)

                st.markdown("---")
                # Form to update status, technician, labor, and parts
                with st.form(f"update_wo_{wo_data['id']}"):
                    u_c1, u_c2 = st.columns(2)
                    with u_c1:
                        new_status = st.selectbox("Update Status", STATUSES, index=STATUSES.index(wo_data['status']))
                        
                        # Technicians can be assigned
                        assigned_idx = 0
                        if wo_data['assigned_to'] in tech_map:
                            assigned_idx = list(tech_map.keys()).index(wo_data['assigned_to'])
                        new_tech_id = st.selectbox("Assign Lead Technician", options=list(tech_map.keys()), format_func=lambda x: tech_map[x], index=assigned_idx)

                    with u_c2:
                        labor_hrs = st.number_input("Logged Labor Hours", min_value=0.0, max_value=200.0, value=float(wo_data['labor_hours'] or 0.0), step=0.5)
                        parts_cost = st.number_input("Spare Parts Cost ($)", min_value=0.0, max_value=50000.0, value=float(wo_data['parts_cost'] or 0.0), step=10.0)
                        labor_rate = 60.0  # Standard facility technician rate per hour
                        calculated_labor_cost = labor_hrs * labor_rate
                        st.caption(f"Calculated Labor Cost: **${calculated_labor_cost:,.2f}** (@ $60/hr)")

                    resolution_text = st.text_area("Resolution Notes / Technician Actions Taken", value=wo_data['resolution_summary'] or '')
                    downtime = st.number_input("Asset Downtime Minutes", min_value=0, max_value=10000, value=int(wo_data['downtime_minutes'] or 0))

                    update_btn = st.form_submit_button("💾 Save Progress & Update Work Order", type="primary")
                    if update_btn:
                        cur = conn.cursor()
                        completed_time = date.today().isoformat() if new_status == 'Completed' else None
                        assigned_val = None if new_tech_id == 0 else new_tech_id

                        cur.execute("""
                            UPDATE work_orders
                            SET status = ?, assigned_to = ?, labor_hours = ?, parts_cost = ?,
                                labor_cost = ?, resolution_summary = ?, downtime_minutes = ?,
                                completed_at = COALESCE(?, completed_at)
                            WHERE id = ?
                        """, (
                            new_status, assigned_val, labor_hrs, parts_cost,
                            calculated_labor_cost, resolution_text.strip(), downtime,
                            completed_time, int(wo_data['id'])
                        ))

                        # If status is completed and asset was degraded or down, restore asset status to Operational
                        if new_status == 'Completed':
                            cur.execute("UPDATE assets SET status = 'Operational' WHERE id = ?", (int(wo_data['asset_id']),))

                        conn.commit()
                        st.success(f"Work order {selected_wo_num} updated successfully!")
                        st.rerun()

    with tab_create:
        st.markdown("### ➕ Issue New Work Order / Report Breakdown")
        with st.form("new_wo_form"):
            w_c1, w_c2 = st.columns(2)
            with w_c1:
                wo_title = st.text_input("Incident Title *", placeholder="e.g. Unusual grinding noise on Escalator 2")
                sel_asset = st.selectbox("Equipment / Asset Involved *", options=list(asset_map.keys()), format_func=lambda x: asset_map[x])
                wo_desc = st.text_area("Detailed Issue Description *", placeholder="Describe observable symptoms, abnormal sounds, leaks, error codes...")

            with w_c2:
                wo_priority = st.selectbox("Priority Level", PRIORITIES)
                due_in_days = 1 if 'Critical' in wo_priority else (3 if 'High' in wo_priority else 7)
                target_due = st.date_input("Target Resolution Date", value=date.today() + timedelta(days=due_in_days))
                
                initial_tech = 0
                if user['role'] != 'Tenant':
                    initial_tech = st.selectbox("Assign Lead Technician", options=list(tech_map.keys()), format_func=lambda x: tech_map[x])

            create_submit = st.form_submit_button("Submit Work Order", type="primary")
            if create_submit:
                if not wo_title or not wo_desc:
                    st.error("Please provide both a Title and Detailed Description.")
                else:
                    cur = conn.cursor()
                    # Generate unique WO number
                    cur.execute("SELECT COUNT(*) FROM work_orders")
                    wo_count = cur.fetchone()[0] + 1
                    wo_code = f"WO-2026-{wo_count:03d}"
                    assigned_person = None if initial_tech == 0 else initial_tech

                    cur.execute("""
                        INSERT INTO work_orders (
                            wo_number, title, description, asset_id, priority, status,
                            assigned_to, reported_by, due_date
                        ) VALUES (?, ?, ?, ?, ?, 'New / Reported', ?, ?, ?)
                    """, (
                        wo_code, wo_title.strip(), wo_desc.strip(), sel_asset,
                        wo_priority, assigned_person, user['id'], target_due.isoformat()
                    ))

                    # If emergency, update asset status to Degraded or Under Maintenance
                    if 'Critical' in wo_priority:
                        cur.execute("UPDATE assets SET status = 'Under Maintenance' WHERE id = ?", (sel_asset,))

                    conn.commit()
                    st.success(f"Work order '{wo_code}' successfully generated!")
                    st.rerun()

    with tab_history:
        st.markdown("### 📜 Work Order Completion Archive & Audit Log")
        history_df = pd.read_sql_query("""
            SELECT w.wo_number, w.title, a.asset_tag, w.priority, w.status,
                   u.full_name as technician, w.labor_hours, (w.labor_cost + w.parts_cost) as total_cost,
                   w.completed_at, w.resolution_summary
            FROM work_orders w
            JOIN assets a ON w.asset_id = a.id
            LEFT JOIN users u ON w.assigned_to = u.id
            WHERE w.status IN ('Completed', 'Cancelled')
            ORDER BY w.completed_at DESC
        """, conn)

        if history_df.empty:
            st.info("No completed work orders yet.")
        else:
            st.dataframe(history_df, use_container_width=True, hide_index=True)
            download_df_as_excel_or_csv(history_df, filename="completed_work_orders_archive")

    conn.close()
