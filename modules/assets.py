"""
Asset Registry & RCM Criticality Assessment Module.
Provides full CRUD capabilities, criticality scoring, and location mapping.
"""
import streamlit as st
import pandas as pd
from database import get_connection
from components.ui_helpers import status_badge_html, download_df_as_excel_or_csv

CATEGORIES = [
    'HVAC',
    'Vertical Transport',
    'Electrical & Power',
    'Plumbing & Drainage',
    'Fire & Safety',
    'Access & Security',
    'Mall Architecture & Facade'
]

STATUS_CHOICES = ['Operational', 'Degraded', 'Under Maintenance', 'Out of Service']
CRITICALITY_TIERS = ['Critical (Tier 1)', 'High (Tier 2)', 'Medium (Tier 3)', 'Low (Tier 4)']
RCM_STRATEGIES = [
    'Predictive (CBM)',
    'Preventive (Time-based)',
    'Condition-based Monitoring',
    'Periodic Inspection & Testing',
    'Failure Finding',
    'Run-to-Failure'
]

def render_assets_page(user):
    """Render Asset Management interface with CRUD and Criticality Evaluation."""
    st.markdown("## 🏢 Mall Equipment & Asset Registry")
    st.caption("Manage physical equipment, assess RCM criticality scores, and map assets to mall zones.")

    tab_list, tab_add, tab_matrix = st.tabs(["📋 Asset Directory", "➕ Register New Asset", "🎯 Criticality Scoring Matrix"])

    conn = get_connection()
    locations = pd.read_sql_query("SELECT id, name, zone_type FROM locations ORDER BY name", conn)
    loc_dict = {row['id']: f"{row['name']} ({row['zone_type']})" for _, row in locations.iterrows()}

    with tab_list:
        # Filter controls
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1.5, 1.5, 1.5])
        with f_col1:
            search_query = st.text_input("🔍 Search Asset Tag or Name", placeholder="e.g. Chiller, Escalator, HVAC...")
        with f_col2:
            cat_filter = st.selectbox("Category", ["All Categories"] + CATEGORIES)
        with f_col3:
            status_filter = st.selectbox("Status", ["All Statuses"] + STATUS_CHOICES)
        with f_col4:
            crit_filter = st.selectbox("Criticality", ["All Criticality"] + CRITICALITY_TIERS)

        # Build Query
        query = """
            SELECT a.*, l.name as location_name 
            FROM assets a 
            LEFT JOIN locations l ON a.location_id = l.id
            WHERE 1=1
        """
        params = []

        if search_query:
            query += " AND (a.name LIKE ? OR a.asset_tag LIKE ? OR a.manufacturer LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])

        if cat_filter != "All Categories":
            query += " AND a.category = ?"
            params.append(cat_filter)

        if status_filter != "All Statuses":
            query += " AND a.status = ?"
            params.append(status_filter)

        if crit_filter != "All Criticality":
            query += " AND a.criticality = ?"
            params.append(crit_filter)

        query += " ORDER BY a.criticality ASC, a.asset_tag ASC"
        df = pd.read_sql_query(query, conn, params=params)

        st.markdown(f"**Found {len(df)} matching assets:**")

        if df.empty:
            st.info("No assets match the chosen criteria.")
        else:
            # Display interactive table
            display_df = df[['asset_tag', 'name', 'category', 'location_name', 'status', 'criticality', 'rcm_strategy']].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            download_df_as_excel_or_csv(df, filename="mall_assets_export")

            # Selected Asset Inspector & Editor
            st.markdown("### 🔍 Asset Details & Quick Update")
            selected_tag = st.selectbox("Select Asset to Inspect or Update", df['asset_tag'].tolist())
            
            selected_asset = df[df['asset_tag'] == selected_tag].iloc[0]

            with st.expander(f"⚙️ Edit Details for {selected_asset['name']} ({selected_tag})", expanded=True):
                with st.form(f"edit_asset_{selected_asset['id']}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_name = st.text_input("Asset Name", value=selected_asset['name'])
                        new_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(selected_asset['category']) if selected_asset['category'] in CATEGORIES else 0)
                        
                        current_loc_idx = list(loc_dict.keys()).index(selected_asset['location_id']) if selected_asset['location_id'] in loc_dict else 0
                        new_loc = st.selectbox("Location", options=list(loc_dict.keys()), format_func=lambda x: loc_dict[x], index=current_loc_idx)
                        new_status = st.selectbox("Current Status", STATUS_CHOICES, index=STATUS_CHOICES.index(selected_asset['status']) if selected_asset['status'] in STATUS_CHOICES else 0)

                    with ec2:
                        new_crit = st.selectbox("Criticality Tier", CRITICALITY_TIERS, index=CRITICALITY_TIERS.index(selected_asset['criticality']) if selected_asset['criticality'] in CRITICALITY_TIERS else 0)
                        new_strategy = st.selectbox("RCM Strategy", RCM_STRATEGIES, index=RCM_STRATEGIES.index(selected_asset['rcm_strategy']) if selected_asset['rcm_strategy'] in RCM_STRATEGIES else 0)
                        new_mfg = st.text_input("Manufacturer", value=selected_asset['manufacturer'] or '')
                        new_model = st.text_input("Model Number", value=selected_asset['model'] or '')

                    save_changes = st.form_submit_button("💾 Save Asset Changes", type="primary")
                    if save_changes:
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE assets 
                            SET name = ?, category = ?, location_id = ?, status = ?, criticality = ?, rcm_strategy = ?, manufacturer = ?, model = ?
                            WHERE id = ?
                        """, (new_name, new_cat, new_loc, new_status, new_crit, new_strategy, new_mfg, new_model, int(selected_asset['id'])))
                        conn.commit()
                        st.success(f"Successfully updated {selected_tag}!")
                        st.rerun()

    with tab_add:
        st.markdown("### ➕ Register New Physical Asset")
        if user['role'] in ['Tenant']:
            st.warning("⚠️ Only Operations Managers and Engineers can register new assets.")
        else:
            with st.form("new_asset_form"):
                ac1, ac2 = st.columns(2)
                with ac1:
                    new_tag = st.text_input("Asset Tag / Code *", placeholder="e.g. ESC-EW-03, CHL-03, GEN-02")
                    new_name = st.text_input("Asset Descriptive Name *", placeholder="e.g. East Wing Travelator Level 1")
                    new_category = st.selectbox("Asset Category *", CATEGORIES)
                    new_loc = st.selectbox("Mall Location *", options=list(loc_dict.keys()), format_func=lambda x: loc_dict[x])
                    new_status = st.selectbox("Initial Status", STATUS_CHOICES)

                with ac2:
                    new_crit = st.selectbox("Criticality Tier", CRITICALITY_TIERS)
                    new_strategy = st.selectbox("RCM Strategy", RCM_STRATEGIES)
                    new_mfg = st.text_input("Manufacturer / Brand", placeholder="e.g. Schindler, Daikin, Siemens")
                    new_model = st.text_input("Model / Serial Number", placeholder="e.g. MOD-5000 / SN-2026-X")
                    new_life = st.number_input("Design Lifespan (Years)", min_value=1, max_value=50, value=15)

                st.markdown("#### Impact Weights (1 = Minimal, 5 = Critical Catastrophe)")
                ic1, ic2, ic3, ic4 = st.columns(4)
                with ic1:
                    safety_score = st.slider("Life Safety Impact", 1, 5, 3)
                with ic2:
                    ops_score = st.slider("Mall Operations Impact", 1, 5, 3)
                with ic3:
                    tenant_score = st.slider("Tenant Business Impact", 1, 5, 3)
                with ic4:
                    cost_score = st.slider("Repair / Replacement Cost", 1, 5, 3)

                submit_new = st.form_submit_button("Register Asset", type="primary")
                if submit_new:
                    if not new_tag or not new_name:
                        st.error("Please provide both an Asset Tag and Asset Name.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO assets (
                                    asset_tag, name, category, location_id, status, manufacturer, model,
                                    criticality, safety_impact, operational_impact, tenant_impact, cost_impact,
                                    rcm_strategy, expected_lifespan_years
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                new_tag.strip().upper(), new_name.strip(), new_category, new_loc, new_status,
                                new_mfg.strip(), new_model.strip(), new_crit, safety_score, ops_score,
                                tenant_score, cost_score, new_strategy, new_life
                            ))
                            conn.commit()
                            st.success(f"Asset '{new_tag.upper()}' registered successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating asset: {e}")

    with tab_matrix:
        st.markdown("### 🎯 RCM Asset Criticality Decision Matrix")
        st.info("""
        **Reliability Centered Maintenance (RCM) Principles:**
        Assets are tiered according to their consequence of failure across 4 dimensions:
        1. **Safety & Regulatory**: Risk of injury to mall patrons, fire code violation.
        2. **Operational Continuity**: Disruption to major shopping corridors, HVAC comfort, power.
        3. **Tenant Revenue Impact**: Closure of retail units, loss of footfall, merchandise damage.
        4. **Asset Replacement Cost**: Financial burden of catastrophic breakdown.
        """)

        matrix_df = pd.read_sql_query("""
            SELECT asset_tag, name, category, safety_impact, operational_impact, tenant_impact, cost_impact,
                   (safety_impact * 0.35 + operational_impact * 0.30 + tenant_impact * 0.20 + cost_impact * 0.15) as weighted_rcm_score,
                   criticality, rcm_strategy
            FROM assets
            ORDER BY weighted_rcm_score DESC
        """, conn)

        matrix_df['weighted_rcm_score'] = matrix_df['weighted_rcm_score'].round(2)
        st.dataframe(matrix_df, use_container_width=True)

    conn.close()
