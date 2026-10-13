"""
UI helper functions, badges, custom CSS styling, and export utilities.
"""
import streamlit as st
import pandas as pd
import io

def inject_custom_css():
    """Inject modern, high-contrast, professional styling for the Mall RCM interface."""
    st.markdown("""
    <style>
        /* Main application container */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 96%;
        }

        /* Metric cards styling */
        .rcm-metric-card {
            background: linear-gradient(145deg, #1E293B, #0F172A);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 18px 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .rcm-metric-card:hover {
            transform: translateY(-2px);
            border-color: #38BDF8;
        }
        .rcm-metric-title {
            color: #94A3B8;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .rcm-metric-value {
            color: #F8FAFC;
            font-size: 28px;
            font-weight: 700;
            line-height: 1.2;
        }
        .rcm-metric-subtitle {
            color: #64748B;
            font-size: 12px;
            margin-top: 5px;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-align: center;
        }
        .badge-operational { background-color: #064E3B; color: #34D399; border: 1px solid #059669; }
        .badge-degraded { background-color: #78350F; color: #FBBF24; border: 1px solid #D97706; }
        .badge-maintenance { background-color: #1E3A8A; color: #60A5FA; border: 1px solid #2563EB; }
        .badge-outofservice { background-color: #7F1D1D; color: #F87171; border: 1px solid #DC2626; }

        /* Priority Badges */
        .badge-priority-critical { background-color: #991B1B; color: #FCA5A5; font-weight: 700; }
        .badge-priority-high { background-color: #9A3412; color: #FDBA74; }
        .badge-priority-medium { background-color: #854D0E; color: #FEF08A; }
        .badge-priority-low { background-color: #065F46; color: #A7F3D0; }

        /* General Section Header */
        .section-header {
            border-left: 4px solid #38BDF8;
            padding-left: 12px;
            margin: 20px 0 15px 0;
            font-size: 19px;
            font-weight: 600;
            color: #F1F5F9;
        }
    </style>
    """, unsafe_allow_html=True)

def status_badge_html(status: str) -> str:
    """Return colored HTML badge for asset or work order status."""
    st_lower = status.lower()
    if 'operat' in st_lower or 'completed' in st_lower or 'active' in st_lower:
        cls = 'badge-operational'
    elif 'degrad' in st_lower or 'pending' in st_lower or 'review' in st_lower:
        cls = 'badge-degraded'
    elif 'maint' in st_lower or 'progress' in st_lower or 'assigned' in st_lower:
        cls = 'badge-maintenance'
    else:
        cls = 'badge-outofservice'
    return f'<span class="badge {cls}">{status}</span>'

def priority_badge_html(priority: str) -> str:
    """Return colored HTML badge for priority levels."""
    p_lower = priority.lower()
    if 'critical' in p_lower or 'emergency' in p_lower:
        cls = 'badge-priority-critical'
    elif 'high' in p_lower:
        cls = 'badge-priority-high'
    elif 'medium' in p_lower:
        cls = 'badge-priority-medium'
    else:
        cls = 'badge-priority-low'
    return f'<span class="badge {cls}">{priority}</span>'

def render_kpi_card(title: str, value: str, subtitle: str = "", icon: str = ""):
    """Render a clean metric KPI box."""
    html = f"""
    <div class="rcm-metric-card">
        <div class="rcm-metric-title">{icon} {title}</div>
        <div class="rcm-metric-value">{value}</div>
        <div class="rcm-metric-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def download_df_as_excel_or_csv(df: pd.DataFrame, filename: str = "export"):
    """Render download buttons for DataFrame in CSV and Excel formats."""
    col1, col2 = st.columns([1, 1])
    with col1:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            excel_data = output.getvalue()
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"{filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception:
            pass
