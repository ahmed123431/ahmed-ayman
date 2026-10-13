# 🏢 Grand Mall Reliability Centered Maintenance (RCM) Web Application

A full-stack, enterprise-grade Reliability Centered Maintenance (RCM) SaaS web platform tailored for shopping malls, facilities, and commercial real estate complexes.

Built with **Python**, **Streamlit**, **SQLite**, and **Plotly**.

---

## 🌟 Key Features

### 1. 🔐 User Authentication & Role-Based Access Control (RBAC)
- Multi-tier roles:
  - **Mall Operations Manager (`admin`)**: Complete overview, asset registration, cost accounting, user administration.
  - **Chief MEP Engineer (`engineer1`)**: FMEA risk assessment, RCM maintenance strategy formulation, PM routine creation.
  - **Maintenance Technician (`tech1`, `tech2`)**: Work order execution, labor & parts tracking, digital PM inspection checklist sign-off.
  - **Store / Tenant Representative (`tenant_zara`)**: Issue reporting, priority tracking, public equipment status.

### 2. 📊 Executive RCM Analytics Dashboard
- Live Mall Asset Availability % (uptime vs downtime)
- Mean Time To Repair (MTTR) and Mean Time Between Failures (MTBF)
- Active work orders by priority (Emergency, High, Medium, Low)
- High-risk FMEA triggers (RPN ≥ 80)
- Interactive Plotly visualizations for Asset Health, RCM strategies, Work order breakdown, and Labor vs Parts costs.

### 3. 🏢 Equipment & Asset Registry (Full CRUD)
- Mall zoning: Plant rooms, Atrium, Food Court, Parking bays, Wings, Cinema.
- Systems: HVAC Chillers, AHUs, Escalators, Elevators, Emergency Generators, Fire Pumps, Plumbing.
- RCM Criticality scoring across 4 dimensions: Life Safety, Operations, Tenant Impact, and Financial Cost.
- Live search, filtering by category/status/criticality, and instant Excel / CSV export.

### 4. 🔬 Failure Mode and Effects Analysis (FMEA / RCM)
- Quantitative Risk Priority Number calculation:  
  $$\text{RPN} = \text{Severity} \times \text{Occurrence} \times \text{Detection}$$
- Scatter matrix mapping Severity vs Occurrence.
- Maintenance strategy assignment: Predictive (CBM), Preventive (Time-based), Failure Finding, or Run-to-Failure.

### 5. 🛠️ Work Order & Incident Management (Full CRUD)
- Complete lifecycle: `New / Reported` ➔ `Under Review` ➔ `Assigned` ➔ `In Progress` ➔ `Pending Parts` ➔ `Completed`.
- Real-time logging of labor hours, hourly labor costs, spare parts, and equipment downtime minutes.
- Automatic asset status update upon ticket resolution.

### 6. 📅 Preventive Maintenance (PM) Scheduler & Digital Checklists
- Frequencies: Daily, Weekly, Monthly, Quarterly, Annual.
- Digital checklist with interactive tick-boxes for technicians.
- Automated next-due calculation and compliance auditing.

---

## 🚀 Quick Start Guide

### Option 1: Double-click to launch
Double-click `run.bat` in the project root folder.

### Option 2: Command Line (PowerShell)
```powershell
e:\AI\venv\Scripts\streamlit.exe run app.py
```

---

## 🔑 Default Demo Accounts

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Mall Operations Director** | `admin` | `admin123` | Full administrative, financial & user management |
| **Chief MEP Engineer** | `engineer1` | `eng123` | FMEA analysis, asset strategies, PM schedules |
| **Senior HVAC Technician** | `tech1` | `tech123` | Work order execution & PM checklists |
| **Escalator & Electrical Tech** | `tech2` | `tech123` | Work order execution & PM checklists |
| **Tenant Representative** | `tenant_zara` | `tenant123` | Mall issue reporting & status tracking |

---

## 📁 Project Structure

```
e:\AI\
├── app.py                     # Main Streamlit web app & page router
├── database.py                # SQLite schema, migration & realistic seed data
├── auth.py                    # Session state, authentication & RBAC logic
├── run.bat                    # Quick-start script for Windows
├── components/
│   └── ui_helpers.py          # Custom CSS, badges, KPI cards & Excel exporter
├── modules/
│   ├── dashboard.py           # Executive RCM analytics & Plotly charts
│   ├── assets.py              # Asset Registry CRUD & Criticality matrix
│   ├── fmea.py                # FMEA failure modes & RPN calculation
│   ├── work_orders.py         # Work order lifecycle, labor & parts tracking
│   ├── preventive_maint.py    # PM routines & interactive checklists
│   └── user_management.py     # Staff directory, roles & profile settings
└── mall_rcm.db                # SQLite database with seeded sample data
```
