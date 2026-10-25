# ==========================================================
# COMBINED HR ANALYTICS DASHBOARD SCRIPT
# ==========================================================



# ============================================================
# MODULE: app.py
# ============================================================


import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_data

st.set_page_config(
    page_title="HR Analytics | Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

from src.auth import load_users, create_admin, authenticate

# Login session
if "user" not in st.session_state:
    st.session_state.user = None

users = load_users()
admin_exists = any(user.get("role") == "Admin" for user in users)

st.sidebar.title("HCM Lite")

if st.session_state.user is None:
    st.title("HCM Lite — HR Management System")

    if not admin_exists:
        st.subheader("First-Time Company Setup")

        with st.form("admin_setup"):
            company = st.text_input("Company Name")
            name = st.text_input("Admin Full Name")
            email = st.text_input("Admin Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Admin Account")

            if submitted:
                if not all([company.strip(), name.strip(), email.strip(),
                            password, confirm]):
                    st.error("Saari fields fill karo.")
                elif password != confirm:
                    st.error("Passwords match nahi karte.")
                elif len(password) < 8:
                    st.error("Password kam az kam 8 characters ka rakho.")
                else:
                    success, message = create_admin(
                        company, name, email, password
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    else:
        st.subheader("Admin Login")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                user = authenticate(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Email ya password ghalat hai.")

    st.stop()

user = st.session_state.user

st.sidebar.write(f"Logged in: **{user['name']}**")
st.sidebar.write(f"Role: **{user['role']}**")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

if user["role"] != "Admin":
    st.warning("Employee dashboard abhi setup nahi hua.")
    st.stop()

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #14213d, #203a5f);
    border: 1px solid #344b69;
    padding: 18px;
    border-radius: 14px;
}
[data-testid="stMetricLabel"] {
    color: #dbeafe;
}
[data-testid="stMetricValue"] {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    return load_data()


st.title("📊 HR Analytics")
st.caption("Executive Overview | Workforce • Salary • Retention")

try:
    data = get_data().copy()
except Exception as e:
    st.error(f"Dataset load nahi hua: {e}")
    st.stop()

# Sidebar filters
st.sidebar.title("🎛️ Dashboard Filters")

filtered = data.copy()

if "Department" in filtered.columns:
    departments = sorted(filtered["Department"].dropna().unique())
    selected_departments = st.sidebar.multiselect(
        "Department",
        departments,
        default=departments
    )
    filtered = filtered[
        filtered["Department"].isin(selected_departments)
    ]

if "Gender" in filtered.columns:
    genders = sorted(filtered["Gender"].dropna().unique())
    selected_genders = st.sidebar.multiselect(
        "Gender",
        genders,
        default=genders
    )
    filtered = filtered[filtered["Gender"].isin(selected_genders)]

if "Attrition" in filtered.columns:
    statuses = sorted(filtered["Attrition"].dropna().unique())
    selected_statuses = st.sidebar.multiselect(
        "Attrition Status",
        statuses,
        default=statuses
    )
    filtered = filtered[
        filtered["Attrition"].isin(selected_statuses)
    ]

if filtered.empty:
    st.warning("In filters ke mutabiq koi employee record nahi mila.")
    st.stop()

# KPI calculations
employee_count = len(filtered)

avg_age = (
    filtered["Age"].mean()
    if "Age" in filtered.columns else None
)

avg_salary = (
    pd.to_numeric(filtered["MonthlyIncome"], errors="coerce").mean()
    if "MonthlyIncome" in filtered.columns else None
)

left_rate = (
    filtered["Attrition"]
    .astype(str).str.strip().str.lower().eq("yes").mean() * 100
    if "Attrition" in filtered.columns else None
)

# KPI cards
k1, k2, k3, k4 = st.columns(4)

k1.metric("👥 Employees", f"{employee_count:,}")
k2.metric(
    "🎂 Average Age",
    f"{avg_age:.1f}" if avg_age is not None else "N/A"
)
k3.metric(
    "💰 Average Monthly Income",
    f"{avg_salary:,.0f}" if avg_salary is not None else "N/A"
)
k4.metric(
    "📉 Attrition Rate",
    f"{left_rate:.1f}%" if left_rate is not None else "N/A"
)

st.divider()

# Main charts
st.subheader("📈 Workforce Insights")

left, right = st.columns(2)

with left:
    if "Department" in filtered.columns:
        dept_counts = (
            filtered["Department"]
            .value_counts()
            .rename_axis("Department")
            .reset_index(name="Employees")
        )

        fig = px.bar(
            dept_counts,
            x="Department",
            y="Employees",
            color="Department",
            text="Employees",
            title="Workforce by Department",
            template="plotly_dark"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with right:
    if "Attrition" in filtered.columns:
        attrition_counts = (
            filtered["Attrition"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Employees")
        )

        fig = px.pie(
            attrition_counts,
            names="Status",
            values="Employees",
            hole=0.5,
            title="Employee Retention Overview",
            color="Status",
            color_discrete_map={
                "Yes": "#ef4444",
                "No": "#22c55e"
            },
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

# Salary and overtime
st.divider()
st.subheader("💼 Salary & Work Patterns")

left, right = st.columns(2)

with left:
    if "Department" in filtered.columns and "MonthlyIncome" in filtered.columns:
        salary_data = filtered.copy()
        salary_data["MonthlyIncome"] = pd.to_numeric(
            salary_data["MonthlyIncome"], errors="coerce"
        )

        salary_summary = (
            salary_data.groupby("Department")["MonthlyIncome"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            salary_summary,
            x="Department",
            y="MonthlyIncome",
            color="Department",
            text_auto=".0f",
            title="Average Monthly Income by Department",
            template="plotly_dark"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with right:
    if "OverTime" in filtered.columns:
        overtime_data = (
            filtered["OverTime"]
            .value_counts()
            .rename_axis("Overtime")
            .reset_index(name="Employees")
        )

        fig = px.pie(
            overtime_data,
            names="Overtime",
            values="Employees",
            hole=0.45,
            title="Overtime Distribution",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

# Important insights
st.divider()
st.subheader("💡 Key Insights")

if "Department" in filtered.columns:
    largest_department = filtered["Department"].value_counts()

    if not largest_department.empty:
        st.info(
            f"Largest workforce department: **{largest_department.index[0]}** "
            f"({largest_department.iloc[0]} employees in the current selection)."
        )

if "Attrition" in filtered.columns and "Department" in filtered.columns:
    temp = filtered.copy()
    temp["_left"] = (
        temp["Attrition"].astype(str).str.lower().eq("yes")
    )

    department_attrition = (
        temp.groupby("Department")["_left"]
        .mean()
        .mul(100)
        .sort_values(ascending=False)
    )

    if not department_attrition.empty:
        st.info(
            f"Highest department attrition rate in this selection: "
            f"**{department_attrition.index[0]}** "
            f"({department_attrition.iloc[0]:.1f}%)."
        )

if "OverTime" in filtered.columns and "Attrition" in filtered.columns:
    overtime_rate = (
        filtered.groupby("OverTime")["Attrition"]
        .apply(
            lambda values:
            values.astype(str).str.lower().eq("yes").mean() * 100
        )
    )

    if "Yes" in overtime_rate.index and "No" in overtime_rate.index:
        st.info(
            f"Attrition among employees with overtime: "
            f"**{overtime_rate['Yes']:.1f}%**. "
            f"Without overtime: **{overtime_rate['No']:.1f}%**. "
            "This is an association in the dataset, not proof that overtime causes attrition."
        )

# Dataset preview
st.divider()
st.subheader("📋 Employee Dataset")

search = st.text_input(
    "🔎 Search employee records",
    placeholder="Search by department, job role, gender..."
)

table = filtered.copy()

if search.strip():
    matches = table.astype(str).apply(
        lambda col: col.str.contains(
            search.strip(), case=False, regex=False, na=False
        )
    ).any(axis=1)
    table = table[matches]

st.caption(f"{len(table):,} records found")

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=450
)

st.caption(
    "Built with Python, Pandas, Streamlit and Plotly | HR Analytics Hackathon Project"
)


# ============================================================
# MODULE: src/auth.py
# ============================================================


import json
import hashlib
import hmac
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_FILE = BASE_DIR / "data" / "users.json"


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users():
    if not AUTH_FILE.exists():
        return []

    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as file:
            users = json.load(file)

        return users if isinstance(users, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_users(users):
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(AUTH_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


def create_admin(company_name, name, email, password):
    users = load_users()

    if any(user["role"] == "Admin" for user in users):
        return False, "Admin account pehle se bana hua hai."

    if any(user["email"].lower() == email.lower() for user in users):
        return False, "Ye email pehle se registered hai."

    users.append({
        "id": 1,
        "company": company_name.strip(),
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password),
        "role": "Admin"
    })

    save_users(users)
    return True, "Admin account successfully create ho gaya!"


def authenticate(email, password):
    users = load_users()
    entered_hash = hash_password(password)

    for user in users:
        if (
            user["email"].lower() == email.strip().lower()
            and hmac.compare_digest(
                user["password_hash"],
                entered_hash
            )
        ):
            return user

    return None


# ============================================================
# MODULE: src/data_loader.py
# ============================================================


import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_data():
    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("data folder mein CSV file nahi mili.")

    df = pd.read_csv(csv_files[0])
    return df


# ============================================================
# MODULE: src/data_cleaning.py
# ============================================================



# ============================================================
# MODULE: src/charts.py
# ============================================================



# ============================================================
# MODULE: src/analysis.py
# ============================================================



# ============================================================
# MODULE: src/employee_manager.py
# ============================================================


import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EMP_FILE = DATA_DIR / "employees.json"


def load_employees():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not EMP_FILE.exists():
        save_employees([])
        return []

    try:
        with open(EMP_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            st.error("employees.json ka format invalid hai.")
            return []

        return data

    except (json.JSONDecodeError, OSError):
        st.error("employees.json read nahi ho rahi.")
        return []


def save_employees(employees):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = EMP_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(employees, file, indent=4, ensure_ascii=False)

    temp_file.replace(EMP_FILE)


def next_employee_id(employees):
    ids = []

    for employee in employees:
        try:
            ids.append(int(employee.get("id", 0)))
        except (ValueError, TypeError):
            continue

    return max(ids, default=0) + 1


def account_label(employee):
    if employee.get("password_hash") and employee.get("password_salt"):
        return "Registered"

    return "No login credentials"


def show_employee_list(employees=None):
    if employees is None:
        employees = load_employees()

    st.subheader("Employee Directory")

    active_employees = [
        employee for employee in employees
        if str(employee.get("status", "Active")).strip().lower() == "active"
    ]

    st.caption(f"Active employees: {len(active_employees)}")

    if not active_employees:
        st.info("Abhi koi approved/active employee nahi hai.")
        return

    rows = [
        {
            "Employee ID": employee.get("id", ""),
            "Name": employee.get("name", ""),
            "Email": employee.get("email", ""),
            "Department": employee.get("department", ""),
            "Job Title": employee.get("job_title", ""),
            "Status": employee.get("status", "Active"),
            "Account": account_label(employee),
        }
        for employee in active_employees
    ]

    search = st.text_input(
        "Search employees",
        placeholder="Name, email, department ya job title...",
        key="employee_directory_search",
    )

    department_options = sorted({
        str(employee.get("department", ""))
        for employee in active_employees
        if employee.get("department")
    })

    selected_department = st.selectbox(
        "Filter by department",
        ["All Departments"] + department_options,
        key="employee_directory_department",
    )

    table = pd.DataFrame(rows)

    if search.strip():
        searchable = table.astype(str).apply(
            lambda column: column.str.contains(
                search.strip(),
                case=False,
                regex=False,
                na=False,
            )
        ).any(axis=1)

        table = table[searchable]

    if selected_department != "All Departments":
        table = table[table["Department"] == selected_department]

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Showing {len(table)} employee(s).")


def show_employee_manager():
    user = st.session_state.get("user")

    if not isinstance(user, dict) or (
        str(user.get("role", "")).strip().lower() != "admin"
    ):
        st.error("Sirf Admin employee management access kar sakta hai.")
        st.stop()

    st.title("Employee Management")
    st.caption("Review registrations and manage employee records.")

    employees = load_employees()

    pending = [
        employee for employee in employees
        if str(employee.get("status", "")).strip().lower()
        == "pending approval"
    ]

    active = [
        employee for employee in employees
        if str(employee.get("status", "Active")).strip().lower() == "active"
    ]

    rejected = [
        employee for employee in employees
        if str(employee.get("status", "")).strip().lower() == "rejected"
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Pending Requests", len(pending))
    col2.metric("Active Employees", len(active))
    col3.metric("Rejected Requests", len(rejected))

    st.divider()

    # Registration approval
    st.subheader("Registration Requests")

    if not pending:
        st.info("Koi pending registration request nahi hai.")
    else:
        for employee in pending:
            employee_id = employee.get("id")
            name = employee.get("name", "Unknown")
            email = employee.get("email", "")

            with st.expander(
                f"#{employee_id} — {name} ({email})",
                expanded=True,
            ):
                st.write("**Department:**", employee.get("department", "—"))
                st.write("**Job Title:**", employee.get("job_title", "—"))
                st.write("**Registered At:**", employee.get("registered_at", "—"))

                approve_col, reject_col = st.columns(2)

                with approve_col:
                    if st.button(
                        "Approve",
                        key=f"approve_employee_{employee_id}",
                        use_container_width=True,
                    ):
                        latest = load_employees()

                        target = next(
                            (
                                item for item in latest
                                if str(item.get("id")) == str(employee_id)
                            ),
                            None,
                        )

                        if target is None:
                            st.error("Employee record nahi mila.")
                        elif str(target.get("status", "")).lower() != "pending approval":
                            st.warning("Is request par pehle hi action ho chuka hai.")
                        else:
                            target["status"] = "Active"
                            target["approved_at"] = pd.Timestamp.now().isoformat()
                            save_employees(latest)
                            st.success(f"{name} ka account approve ho gaya.")
                            st.rerun()

                with reject_col:
                    if st.button(
                        "Reject",
                        key=f"reject_employee_{employee_id}",
                        use_container_width=True,
                    ):
                        latest = load_employees()

                        target = next(
                            (
                                item for item in latest
                                if str(item.get("id")) == str(employee_id)
                            ),
                            None,
                        )

                        if target is None:
                            st.error("Employee record nahi mila.")
                        elif str(target.get("status", "")).lower() != "pending approval":
                            st.warning("Is request par pehle hi action ho chuka hai.")
                        else:
                            target["status"] = "Rejected"
                            target["rejected_at"] = pd.Timestamp.now().isoformat()
                            save_employees(latest)
                            st.warning(f"{name} ki request reject ho gayi.")
                            st.rerun()

    st.divider()

    # Admin can still add an employee manually
    with st.expander("➕ Add Employee Manually", expanded=False):
        with st.form("add_employee_form_updated"):
            name = st.text_input("Full Name")
            email = st.text_input("Company Email")
            department = st.text_input("Department")
            job_title = st.text_input("Job Title")
            salary = st.number_input(
                "Monthly Salary",
                min_value=0.0,
                step=1000.0,
            )
            joining_date = st.date_input("Joining Date")
            submit = st.form_submit_button("Add Employee")

        if submit:
            name = name.strip()
            email = email.strip().lower()
            department = department.strip()
            job_title = job_title.strip()

            if not all([name, email, department, job_title]):
                st.error("Name, email, department aur job title required hain.")
            elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
                st.error("Valid email address enter karo.")
            elif any(
                str(item.get("email", "")).strip().lower() == email
                for item in load_employees()
            ):
                st.error("Ye email pehle se registered hai.")
            else:
                latest = load_employees()

                latest.append({
                    "id": next_employee_id(latest),
                    "name": name,
                    "email": email,
                    "department": department,
                    "job_title": job_title,
                    "monthly_salary": salary,
                    "joining_date": str(joining_date),
                    "status": "Active",
                })

                save_employees(latest)
                st.success("Employee record add ho gaya.")
                st.rerun()

    st.divider()

    # Active directory
    show_employee_list(load_employees())




# ============================================================
# MODULE: src/attendance_manager.py
# ============================================================


import json
from pathlib import Path
from datetime import datetime, time

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EMPLOYEE_FILE = DATA_DIR / "employees.json"
ATTENDANCE_FILE = DATA_DIR / "attendance.json"
SETTINGS_FILE = DATA_DIR / "company_settings.json"

DEFAULT_SETTINGS = {
    "office_start": "09:00",
    "grace_minutes": 15,
}


def load_json(path, default=None):
    if default is None:
        default = []

    if not path.exists():
        return default.copy()

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, type(default)) else default.copy()

    except (json.JSONDecodeError, OSError):
        st.error(f"{path.name} file read nahi ho saki.")
        return default.copy()


def save_attendance(records):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = ATTENDANCE_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    temp_file.replace(ATTENDANCE_FILE)


def load_settings():
    saved = load_json(SETTINGS_FILE, {})
    settings = {**DEFAULT_SETTINGS, **saved}

    try:
        time.fromisoformat(settings["office_start"])
    except (ValueError, TypeError):
        settings["office_start"] = DEFAULT_SETTINGS["office_start"]

    try:
        settings["grace_minutes"] = max(
            0, int(settings["grace_minutes"])
        )
    except (ValueError, TypeError):
        settings["grace_minutes"] = DEFAULT_SETTINGS["grace_minutes"]

    return settings


def same_employee(first_id, second_id):
    return str(first_id).strip() == str(second_id).strip()


def calculate_status(check_in, office_start, grace_minutes):
    check_in_minutes = check_in.hour * 60 + check_in.minute
    office_minutes = office_start.hour * 60 + office_start.minute

    return (
        "Late"
        if check_in_minutes > office_minutes + grace_minutes
        else "Present"
    )


def show_attendance_manager():
    user = st.session_state.get("user")

    if not isinstance(user, dict):
        st.warning("Please Admin account se login karo.")
        st.stop()

    if str(user.get("role", "")).strip().lower() != "admin":
        st.error("Sirf Admin attendance manage kar sakta hai.")
        st.stop()

    st.title("📅 Attendance Management")
    st.caption("Employee aur Admin attendance records ek hi jagah manage karein.")

    employees = [
        employee
        for employee in load_json(EMPLOYEE_FILE, [])
        if isinstance(employee, dict)
        and str(employee.get("status", "Active")).strip().lower() == "active"
    ]

    records = [
        record
        for record in load_json(ATTENDANCE_FILE, [])
        if isinstance(record, dict)
    ]

    settings = load_settings()
    today = datetime.now().date().isoformat()

    if not employees:
        st.info("Abhi koi active employee available nahi hai.")
        return

    employee_map = {
        f'{employee.get("name", "Unknown")} — {employee.get("email", "")}': employee
        for employee in employees
    }

    today_records = [
        record for record in records
        if record.get("date") == today
    ]

    present_ids = {
        str(record.get("employee_id"))
        for record in today_records
        if record.get("check_in")
    }

    late_count = sum(
        record.get("status") == "Late"
        for record in today_records
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Employees", len(employees))
    col2.metric("Checked In Today", len(present_ids))
    col3.metric("Late Today", late_count)

    st.divider()
    st.subheader("Record Attendance")

    try:
        default_office_time = time.fromisoformat(settings["office_start"])
    except (ValueError, TypeError):
        default_office_time = time(9, 0)

    with st.form("attendance_record_form"):
        selected_label = st.selectbox(
            "Select Employee",
            list(employee_map.keys()),
        )

        check_in = st.time_input(
            "Check-in Time",
            value=datetime.now().time().replace(second=0, microsecond=0),
        )

        st.caption(
            f'Company office start: {default_office_time.strftime("%H:%M")} '
            f'| Grace period: {settings["grace_minutes"]} minutes'
        )

        submitted = st.form_submit_button("Save Attendance")

    if submitted:
        employee = employee_map[selected_label]

        already_recorded = any(
            same_employee(record.get("employee_id"), employee.get("id"))
            and record.get("date") == today
            for record in records
        )

        if already_recorded:
            st.error("Is employee ki attendance aaj already recorded hai.")
        else:
            status = calculate_status(
                check_in,
                default_office_time,
                settings["grace_minutes"],
            )

            records.append({
                "employee_id": employee.get("id"),
                "employee_name": employee.get("name", ""),
                "date": today,
                "check_in": check_in.strftime("%H:%M:%S"),
                "check_out": None,
                "status": status,
            })

            save_attendance(records)
            st.success(f"Attendance save ho gayi: {status}")
            st.rerun()

    st.divider()
    st.subheader("Attendance Records")

    if not records:
        st.info("Abhi koi attendance record nahi hai.")
        return

    search = st.text_input(
        "Search by employee name or ID",
        placeholder="Employee name ya ID likho...",
    )

    filtered_records = records

    if search.strip():
        query = search.strip().lower()
        filtered_records = [
            record for record in records
            if query in str(record.get("employee_name", "")).lower()
            or query in str(record.get("employee_id", "")).lower()
        ]

    df = pd.DataFrame(filtered_records)

    preferred_columns = [
        "employee_id",
        "employee_name",
        "date",
        "check_in",
        "check_out",
        "status",
    ]

    available_columns = [
        column for column in preferred_columns if column in df.columns
    ]

    if not df.empty:
        df = df[available_columns].sort_values(
            "date", ascending=False
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Attendance CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="attendance_records.csv",
            mime="text/csv",
        )
    else:
        st.info("Search se koi matching attendance record nahi mila.")


# ============================================================
# MODULE: src/leave_manager.py
# ============================================================


import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EMPLOYEE_FILE = DATA_DIR / "employees.json"
LEAVE_FILE = DATA_DIR / "leaves.json"
SETTINGS_FILE = DATA_DIR / "company_settings.json"

DEFAULT_WORKING_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
]


def load_json(path, default=None):
    if default is None:
        default = []

    if not path.exists():
        return default.copy()

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, type(default)) else default.copy()

    except (json.JSONDecodeError, OSError):
        st.error(f"File read nahi ho saki: {path.name}")
        return default.copy()


def save_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    temp_file.replace(path)


def load_employees():
    return load_json(EMPLOYEE_FILE, [])


def load_settings():
    settings = load_json(SETTINGS_FILE, {})

    if not isinstance(settings, dict):
        settings = {}

    return {
        "annual_leave_quota": int(
            settings.get("annual_leave_quota", 20)
        ),
        "working_days": settings.get(
            "working_days", DEFAULT_WORKING_DAYS
        ),
    }


def parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def normalize_leave(leave):
    """Support both old Admin and Employee Portal leave field names."""
    item = dict(leave)

    item["id"] = item.get("id", item.get("request_id", ""))
    item["request_id"] = item.get("request_id", item["id"])

    item["from_date"] = item.get(
        "from_date", item.get("start_date", "")
    )
    item["to_date"] = item.get(
        "to_date", item.get("end_date", "")
    )

    item["start_date"] = item.get("start_date", item["from_date"])
    item["end_date"] = item.get("end_date", item["to_date"])

    item.setdefault("employee_name", "Unknown")
    item.setdefault("leave_type", "Other")
    item.setdefault("reason", "")
    item.setdefault("status", "Pending")
    item.setdefault("admin_comment", "")

    return item


def load_leaves():
    raw_leaves = load_json(LEAVE_FILE, [])
    return [
        normalize_leave(item)
        for item in raw_leaves
        if isinstance(item, dict)
    ]


def save_leaves(leaves):
    # Store both field-name formats for compatibility with old records
    # and the Employee Portal.
    compatible = []

    for leave in leaves:
        item = normalize_leave(leave)
        item["start_date"] = item["from_date"]
        item["end_date"] = item["to_date"]
        compatible.append(item)

    save_json(LEAVE_FILE, compatible)


def working_days(start, end, configured_days=None):
    """Count configured company working days, inclusive."""
    configured_days = configured_days or DEFAULT_WORKING_DAYS

    day_numbers = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    allowed = {
        day_numbers[name]
        for name in configured_days
        if name in day_numbers
    }

    total = 0
    current = start

    while current <= end:
        if current.weekday() in allowed:
            total += 1

        current += timedelta(days=1)

    return total


def next_leave_id(leaves):
    ids = []

    for leave in leaves:
        try:
            ids.append(int(leave.get("id", 0)))
        except (ValueError, TypeError):
            continue

    return max(ids, default=0) + 1


def annual_leave_used(leaves, employee_id, year, company_days):
    total = 0

    for leave in leaves:
        if (
            str(leave.get("employee_id")) != str(employee_id)
            or leave.get("status") != "Approved"
            or leave.get("leave_type") != "Annual Leave"
        ):
            continue

        start = parse_date(leave.get("from_date"))
        end = parse_date(leave.get("to_date"))

        if not start or not end or end < start:
            continue

        # Count only the days within the requested calendar year.
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        clipped_start = max(start, year_start)
        clipped_end = min(end, year_end)

        if clipped_start <= clipped_end:
            total += working_days(
                clipped_start, clipped_end, company_days
            )

    return total


def has_overlapping_leave(leaves, employee_id, start, end):
    for leave in leaves:
        if (
            str(leave.get("employee_id")) != str(employee_id)
            or leave.get("status") not in ("Pending", "Approved")
        ):
            continue

        old_start = parse_date(leave.get("from_date"))
        old_end = parse_date(leave.get("to_date"))

        if old_start and old_end and old_start <= end and old_end >= start:
            return True

    return False


def show_leave_manager():
    user = st.session_state.get("user")

    if not isinstance(user, dict):
        st.warning("Please Admin account se login karo.")
        st.stop()

    if str(user.get("role", "")).strip().lower() != "admin":
        st.error("Sirf Admin leave requests manage kar sakta hai.")
        st.stop()

    st.title("🏖️ Leave Management")
    st.caption("Review employee requests, approve leave and export reports.")

    employees = [
        employee for employee in load_employees()
        if str(employee.get("status", "Active")).strip().lower() == "active"
    ]

    leaves = load_leaves()
    settings = load_settings()
    company_days = settings["working_days"]
    quota = settings["annual_leave_quota"]

    pending = sum(item.get("status") == "Pending" for item in leaves)
    approved = sum(item.get("status") == "Approved" for item in leaves)
    rejected = sum(item.get("status") == "Rejected" for item in leaves)

    c1, c2, c3 = st.columns(3)
    c1.metric("Pending Requests", pending)
    c2.metric("Approved Requests", approved)
    c3.metric("Rejected Requests", rejected)

    create_tab, review_tab, summary_tab = st.tabs(
        ["➕ Create Request", "📋 Review Requests", "📊 Leave Summary"]
    )

    with create_tab:
        if not employees:
            st.info("Abhi koi active employee available nahi hai.")
        else:
            options = {
                f'{item.get("name", "Unknown")} — {item.get("email", "")}': item
                for item in employees
            }

            with st.form("admin_create_leave_form"):
                selected = st.selectbox("Employee", list(options.keys()))
                leave_type = st.selectbox(
                    "Leave Type",
                    ["Annual Leave", "Sick Leave", "Personal Leave", "Other"],
                )
                start_date = st.date_input(
                    "From Date", value=date.today(), key="admin_leave_start"
                )
                end_date = st.date_input(
                    "To Date", value=date.today(), key="admin_leave_end"
                )
                reason = st.text_area("Reason")
                submit = st.form_submit_button("Create Leave Request")

            if submit:
                employee = options[selected]

                if end_date < start_date:
                    st.error("To Date, From Date se pehle nahi ho sakti.")
                elif not reason.strip():
                    st.error("Leave ki reason enter karo.")
                else:
                    days = working_days(
                        start_date, end_date, company_days
                    )

                    if days == 0:
                        st.error("Selected dates mein working day nahi hai.")
                    elif has_overlapping_leave(
                        leaves, employee.get("id"), start_date, end_date
                    ):
                        st.error("Is employee ki dates par leave pehle se pending ya approved hai.")
                    else:
                        used = annual_leave_used(
                            leaves,
                            employee.get("id"),
                            start_date.year,
                            company_days,
                        )

                        if (
                            leave_type == "Annual Leave"
                            and used + days > quota
                        ):
                            st.error(
                                f"Annual leave quota exceed hoga. "
                                f"Used: {used}/{quota} working days."
                            )
                        else:
                            leave_id = next_leave_id(leaves)

                            leaves.append({
                                "id": leave_id,
                                "request_id": str(leave_id),
                                "employee_id": employee.get("id"),
                                "employee_name": employee.get("name", ""),
                                "employee_email": employee.get("email", ""),
                                "leave_type": leave_type,
                                "from_date": start_date.isoformat(),
                                "to_date": end_date.isoformat(),
                                "start_date": start_date.isoformat(),
                                "end_date": end_date.isoformat(),
                                "days": days,
                                "reason": reason.strip(),
                                "status": "Pending",
                                "admin_comment": "",
                                "created_at": date.today().isoformat(),
                            })

                            save_leaves(leaves)
                            st.success("Leave request create ho gayi.")
                            st.rerun()

    with review_tab:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "Approved", "Rejected"],
            key="admin_leave_status_filter",
        )

        filtered = [
            item for item in leaves
            if status_filter == "All"
            or item.get("status") == status_filter
        ]

        if not filtered:
            st.info("Is status ke liye koi leave request nahi hai.")

        for leave in filtered:
            leave_id = leave.get("id", leave.get("request_id", ""))
            employee_id = leave.get("employee_id")
            start = leave.get("from_date", "")
            end = leave.get("to_date", "")

            with st.expander(
                f'#{leave_id} — {leave.get("employee_name", "Unknown")} '
                f'| {leave.get("leave_type", "Other")} '
                f'| {leave.get("status", "Pending")}'
            ):
                st.write("**Employee ID:**", employee_id)
                st.write("**Employee email:**", leave.get("employee_email", "—"))
                st.write(f"**Dates:** {start} to {end}")
                st.write("**Working days:**", leave.get("days", "—"))
                st.write("**Reason:**", leave.get("reason", ""))

                if leave.get("admin_comment"):
                    st.write("**Admin comment:**", leave["admin_comment"])

                if leave.get("status") == "Pending":
                    comment = st.text_input(
                        "Admin Comment",
                        key=f"leave_comment_{leave_id}",
                    )

                    approve_col, reject_col = st.columns(2)

                    with approve_col:
                        if st.button(
                            "✅ Approve",
                            key=f"approve_leave_{leave_id}",
                            use_container_width=True,
                        ):
                            latest = load_leaves()
                            target = next(
                                (
                                    item for item in latest
                                    if str(item.get("id")) == str(leave_id)
                                    or str(item.get("request_id")) == str(leave_id)
                                ),
                                None,
                            )

                            if target is None:
                                st.error("Leave request nahi mili.")
                            elif target.get("status") != "Pending":
                                st.warning("Is request par pehle action ho chuka hai.")
                            else:
                                target_start = parse_date(target.get("from_date"))
                                target_end = parse_date(target.get("to_date"))

                                if not target_start or not target_end:
                                    st.error("Leave dates invalid hain.")
                                else:
                                    used = annual_leave_used(
                                        latest,
                                        target.get("employee_id"),
                                        target_start.year,
                                        company_days,
                                    )
                                    days = working_days(
                                        target_start, target_end, company_days
                                    )

                                    if (
                                        target.get("leave_type") == "Annual Leave"
                                        and used + days > quota
                                    ):
                                        st.error(
                                            f"Quota exceed hoga. Used: {used}/{quota}."
                                        )
                                    else:
                                        target["status"] = "Approved"
                                        target["admin_comment"] = comment.strip()
                                        save_leaves(latest)
                                        st.success("Leave approve ho gayi.")
                                        st.rerun()

                    with reject_col:
                        if st.button(
                            "❌ Reject",
                            key=f"reject_leave_{leave_id}",
                            use_container_width=True,
                        ):
                            latest = load_leaves()
                            target = next(
                                (
                                    item for item in latest
                                    if str(item.get("id")) == str(leave_id)
                                    or str(item.get("request_id")) == str(leave_id)
                                ),
                                None,
                            )

                            if target is None:
                                st.error("Leave request nahi mili.")
                            elif target.get("status") != "Pending":
                                st.warning("Is request par pehle action ho chuka hai.")
                            else:
                                target["status"] = "Rejected"
                                target["admin_comment"] = comment.strip()
                                save_leaves(latest)
                                st.warning("Leave reject ho gayi.")
                                st.rerun()

    with summary_tab:
        st.caption(f"Annual leave quota configured in Company Settings: {quota} working days.")

        if leaves:
            df = pd.DataFrame(leaves)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.download_button(
                "Download Leave Report CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="leave_report.csv",
                mime="text/csv",
            )
        else:
            st.info("Leave summary ke liye abhi records nahi hain.")


# The Streamlit page should call show_leave_manager().


# ============================================================
# MODULE: src/settings_manager.py
# ============================================================


import json
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "data" / "company_settings.json"

DEFAULT_SETTINGS = {
    "company_name": "My Company",
    "office_start": "09:00",
    "grace_minutes": 15,
    "annual_leave_quota": 20,
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}


def load_settings():
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)

        return {**DEFAULT_SETTINGS, **saved}
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)


def show_settings_manager():
    user = st.session_state.get("user")

    if not user:
        st.warning("Please log in first.")
        st.stop()

    if user.get("role") != "Admin":
        st.error("Only Admin can change company settings.")
        st.stop()

    st.title("⚙️ Company Settings")
    st.caption("Configure company information and HR policies.")

    settings = load_settings()
    days = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]

    with st.form("company_settings_form"):
        company_name = st.text_input(
            "Company Name",
            value=settings["company_name"]
        )

        office_start = st.time_input(
            "Office Start Time",
            value=__import__("datetime").time.fromisoformat(
                settings["office_start"]
            )
        )

        grace_minutes = st.number_input(
            "Late Grace Period (minutes)",
            min_value=0,
            max_value=120,
            value=int(settings["grace_minutes"])
        )

        annual_quota = st.number_input(
            "Annual Leave Quota (working days)",
            min_value=0,
            max_value=365,
            value=int(settings["annual_leave_quota"])
        )

        working_days_selected = st.multiselect(
            "Company Working Days",
            options=days,
            default=settings["working_days"]
        )

        submitted = st.form_submit_button("Save Settings")

        if submitted:
            if not company_name.strip():
                st.error("Company name required hai.")
            elif not working_days_selected:
                st.error("Kam az kam ek working day select karo.")
            else:
                updated_settings = {
                    "company_name": company_name.strip(),
                    "office_start": office_start.strftime("%H:%M"),
                    "grace_minutes": int(grace_minutes),
                    "annual_leave_quota": int(annual_quota),
                    "working_days": working_days_selected
                }

                save_settings(updated_settings)
                st.success("Company settings save ho gayi!")
                st.rerun()


# Called from the Streamlit page.
