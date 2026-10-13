"""
Main application file for Grand Mall Reliability Centered Maintenance (RCM) SaaS Platform.
"""
import streamlit as st
from database import init_database, seed_sample_data
from auth import login_ui, logout, get_current_user
from components.ui_helpers import inject_custom_css
from modules.dashboard import render_dashboard
from modules.assets import render_assets_page
from modules.fmea import render_fmea_page
from modules.work_orders import render_work_orders_page
from modules.preventive_maint import render_pm_page
from modules.user_management import render_users_page

# Set page configuration
st.set_page_config(
    page_title="RCM System - Reliability Centered Maintenance",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database is initialized and seeded
init_database()
seed_sample_data()

# Inject styling
inject_custom_css()

# Session State & Authentication
user = get_current_user()

if not user:
    login_ui()
else:
    # Sidebar Navigation & User Info
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 15px 0; border-bottom: 1px solid #334155; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 32px;">🏢</span>
                    <div>
                        <h3 style="margin: 0; color: #38BDF8; font-size: 18px; font-weight: 700;">RCM SYSTEM</h3>
                        <p style="margin: 0; color: #94A3B8; font-size: 12px; letter-spacing: 0.5px;">RELIABILITY OPERATIONS PORTAL</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # User profile chip
        role_colors = {
            'Manager': '#EF4444',
            'Engineer': '#3B82F6',
            'Technician': '#10B981',
            'Tenant': '#F59E0B'
        }
        r_color = role_colors.get(user['role'], '#64748B')
        
        st.markdown(
            f"""
            <div style="background: #1E293B; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;">
                <div style="color: #F8FAFC; font-weight: 600; font-size: 14px;">👤 {user['full_name']}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                    <span style="background: {r_color}22; color: {r_color}; border: 1px solid {r_color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{user['role']}</span>
                    <span style="color: #64748B; font-size: 11px;">{user['department']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Role-based menu options
        if user['role'] == 'Tenant':
            nav_options = [
                "🛠️ Report & Track Issues",
                "🏢 Mall Public Equipment Status",
                "👤 My Profile"
            ]
        else:
            nav_options = [
                "📊 Executive Dashboard",
                "🏢 Equipment & Asset Registry",
                "🔬 FMEA & Reliability Analysis",
                "🛠️ Work Orders & Incidents",
                "📅 Preventive Maintenance (PM)",
                "👥 Personnel & Users"
            ]

        selected_page = st.radio("Navigation Menu", nav_options, index=0)

        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            logout()

    # Route Page
    if user['role'] == 'Tenant':
        if selected_page == "🛠️ Report & Track Issues":
            render_work_orders_page(user)
        elif selected_page == "🏢 Mall Public Equipment Status":
            render_assets_page(user)
        elif selected_page == "👤 My Profile":
            render_users_page(user)
    else:
        if selected_page == "📊 Executive Dashboard":
            render_dashboard(user)
        elif selected_page == "🏢 Equipment & Asset Registry":
            render_assets_page(user)
        elif selected_page == "🔬 FMEA & Reliability Analysis":
            render_fmea_page(user)
        elif selected_page == "🛠️ Work Orders & Incidents":
            render_work_orders_page(user)
        elif selected_page == "📅 Preventive Maintenance (PM)":
            render_pm_page(user)
        elif selected_page == "👥 Personnel & Users":
            render_users_page(user)
