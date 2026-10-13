"""
User Management and Administration Module.
Handles staff directory, role assignments, password updates, and user registration.
"""
import streamlit as st
import pandas as pd
from database import get_connection, hash_password
from components.ui_helpers import download_df_as_excel_or_csv

ROLES = ['Manager', 'Engineer', 'Technician', 'Tenant']

def render_users_page(user):
    """Render User Directory & Account Settings."""
    st.markdown("## 👥 User Directory & Access Management")
    st.caption("Manage facility personnel roles, tenant access permissions, and staff credentials.")

    conn = get_connection()
    tab_list, tab_add, tab_profile = st.tabs(["📋 Personnel Directory", "➕ Register New User", "👤 My Profile"])

    with tab_list:
        users_df = pd.read_sql_query("""
            SELECT id, username, full_name, email, role, department, created_at
            FROM users
            ORDER BY id ASC
        """, conn)

        st.dataframe(users_df[['id', 'username', 'full_name', 'email', 'role', 'department']], use_container_width=True, hide_index=True)
        download_df_as_excel_or_csv(users_df, filename="users_directory")

        if user['role'] == 'Manager':
            st.markdown("### 🔑 Admin Role Management")
            selected_uid = st.selectbox("Select User to Modify Role", users_df['id'].tolist(), format_func=lambda x: f"{x} - {users_df.loc[users_df['id'] == x, 'full_name'].values[0]} ({users_df.loc[users_df['id'] == x, 'username'].values[0]})")
            u_row = users_df[users_df['id'] == selected_uid].iloc[0]

            with st.form(f"admin_edit_user_{selected_uid}"):
                c1, c2 = st.columns(2)
                with c1:
                    new_role = st.selectbox("Assign System Role", ROLES, index=ROLES.index(u_row['role']))
                    new_dept = st.text_input("Department", value=u_row['department'])
                with c2:
                    reset_pwd = st.text_input("Reset Password (leave blank to keep current)", type="password")

                save_user = st.form_submit_button("Update User Credentials", type="primary")
                if save_user:
                    cur = conn.cursor()
                    if reset_pwd.strip():
                        pwd_hash = hash_password(reset_pwd.strip())
                        cur.execute("UPDATE users SET role = ?, department = ?, password_hash = ? WHERE id = ?", (new_role, new_dept, pwd_hash, int(selected_uid)))
                    else:
                        cur.execute("UPDATE users SET role = ?, department = ? WHERE id = ?", (new_role, new_dept, int(selected_uid)))
                    conn.commit()
                    st.success(f"User '{u_row['username']}' updated successfully!")
                    st.rerun()

    with tab_add:
        st.markdown("### ➕ Register New Mall Personnel or Tenant")
        if user['role'] != 'Manager':
            st.warning("⚠️ Only Operations Managers can register new system accounts.")
        else:
            with st.form("new_user_form"):
                u1, u2 = st.columns(2)
                with u1:
                    new_uname = st.text_input("Username *", placeholder="e.g. tech_alex")
                    new_fname = st.text_input("Full Name *", placeholder="e.g. Alex Henderson")
                    new_pwd = st.text_input("Password *", type="password")

                with u2:
                    new_email = st.text_input("Email Address *", placeholder="e.g. alex.h@grandmall.com")
                    new_role = st.selectbox("Role *", ROLES)
                    new_dept = st.text_input("Department", placeholder="e.g. HVAC Maintenance or Store Tenant")

                create_u = st.form_submit_button("Create User Account", type="primary")
                if create_u:
                    if not new_uname or not new_pwd or not new_fname or not new_email:
                        st.error("Please fill in all required fields.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO users (username, password_hash, full_name, email, role, department)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                new_uname.strip().lower(),
                                hash_password(new_pwd.strip()),
                                new_fname.strip(),
                                new_email.strip(),
                                new_role,
                                new_dept.strip()
                            ))
                            conn.commit()
                            st.success(f"Account for '{new_uname}' successfully created!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating account: {e}")

    with tab_profile:
        st.markdown("### 👤 My Account Profile")
        st.write(f"**Full Name:** {user['full_name']}")
        st.write(f"**Username:** `{user['username']}`")
        st.write(f"**System Role:** `{user['role']}`")
        st.write(f"**Department:** {user['department']}")
        st.write(f"**Email:** {user['email']}")

        with st.form("change_my_password_form"):
            st.markdown("#### Change My Password")
            old_pwd = st.text_input("Current Password", type="password")
            new_p1 = st.text_input("New Password", type="password")
            new_p2 = st.text_input("Confirm New Password", type="password")
            change_submit = st.form_submit_button("Update Password")

            if change_submit:
                if new_p1 != new_p2:
                    st.error("New passwords do not match.")
                elif len(new_p1) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    cur = conn.cursor()
                    cur.execute("SELECT password_hash FROM users WHERE id = ?", (user['id'],))
                    current_hash = cur.fetchone()[0]
                    if hash_password(old_pwd) != current_hash:
                        st.error("Current password incorrect.")
                    else:
                        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_p1), user['id']))
                        conn.commit()
                        st.success("Password updated successfully!")

    conn.close()
