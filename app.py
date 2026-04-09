import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("🚀 CX Health Command Center")

uploaded_file = st.file_uploader("Upload your client CSV", type=["csv"])

# --------------------------
# 📂 Load existing actions
# --------------------------
if os.path.exists("actions.csv"):
    actions_df = pd.read_csv("actions.csv")
else:
    actions_df = pd.DataFrame(columns=["client_name", "user", "owner", "status", "notes"])

# --------------------------
# 👤 USER SELECTION
# --------------------------
st.sidebar.header("User")
user = st.sidebar.selectbox("Select User", ["Ronjone", "CSM 1", "CSM 2"])

# --------------------------
# 🚨 WAR ROOM MODE
# --------------------------
war_room = st.sidebar.checkbox("🚨 War Room Mode (Critical Only)")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # --------------------------
    # 🧹 Clean columns
    # --------------------------
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("(", "").str.replace(")", "").str.replace("-", "_")

    # --------------------------
    # 🧠 Scoring
    # --------------------------
    df['raw_score'] = (
        df['sentiment_score_1_10'] +
        df['usage_score_1_10'] +
        df['engagement_score_1_10'] +
        df['support_score_1_10']
    ) / 4

    df['health_score'] = df['raw_score'].round(1)

    df['priority'] = pd.qcut(
        df['raw_score'],
        q=[0, 0.2, 0.5, 0.8, 1],
        labels=["Critical", "High", "Medium", "Low"]
    )

    df['churn_risk'] = df['priority'].map({
        "Critical": "High",
        "High": "Medium",
        "Medium": "Low",
        "Low": "Low"
    })

    def get_risk_type(row):
        if row['usage_score_1_10'] < 4:
            return "Usage"
        elif row['support_score_1_10'] < 4:
            return "Support"
        elif row['sentiment_score_1_10'] < 4:
            return "Sentiment"
        else:
            return "Engagement"

    df['risk_type'] = df.apply(get_risk_type, axis=1)

    def get_action(priority):
        if priority == "Critical":
            return "🚨 Immediate escalation + exec call"
        elif priority == "High":
            return "⚠️ Schedule intervention within 7 days"
        elif priority == "Medium":
            return "📈 Drive feature adoption"
        else:
            return "💰 Expansion opportunity"

    df['recommended_action'] = df['priority'].apply(get_action)
    df['heal_desk'] = df['priority'].apply(lambda x: "Yes" if x == "Critical" else "No")

    # --------------------------
    # 📊 METRICS
    # --------------------------
    st.subheader("📊 Portfolio Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚨 Critical", (df['priority'] == "Critical").sum())
    col2.metric("⚠️ High", (df['priority'] == "High").sum())
    col3.metric("🟡 Medium", (df['priority'] == "Medium").sum())
    col4.metric("🟢 Low", (df['priority'] == "Low").sum())

    # --------------------------
    # 🎛 FILTER + WAR ROOM
    # --------------------------
    st.sidebar.header("Filters")

    selected_priority = st.sidebar.selectbox(
        "Select Priority",
        ["All", "Critical", "High", "Medium", "Low"]
    )

    if war_room:
        filtered_df = df[df['priority'] == "Critical"]
    elif selected_priority != "All":
        filtered_df = df[df['priority'] == selected_priority]
    else:
        filtered_df = df

    # Sort worst first
    filtered_df = filtered_df.sort_values(by="health_score")

    # --------------------------
    # 🚨 WAR ROOM ALERT
    # --------------------------
    if war_room:
        st.error("🚨 WAR ROOM MODE ACTIVE: Showing Critical Accounts Only")

    # --------------------------
    # 📌 MY TASKS
    # --------------------------
    st.sidebar.subheader("📌 My Tasks")

    if not actions_df.empty and 'user' in actions_df.columns:
        my_tasks = actions_df[
            (actions_df['user'] == user) &
            (actions_df['status'] != "Completed")
        ]

        if not my_tasks.empty:
            st.sidebar.write(my_tasks[['client_name', 'status']])
        else:
            st.sidebar.write("No pending tasks 🎉")

    # --------------------------
    # 📋 TABLE
    # --------------------------
    st.subheader("📋 Client List")
    st.dataframe(filtered_df, use_container_width=True)

    # --------------------------
    # 🔍 DRILLDOWN
    # --------------------------
    st.subheader("🔍 Client Drilldown")

    client_name = st.selectbox("Select Client", df['client_name'])
    client_data = df[df['client_name'] == client_name].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Health Score", client_data['health_score'])
        st.metric("Priority", client_data['priority'])
        st.metric("Churn Risk", client_data['churn_risk'])

    with col2:
        st.metric("Risk Type", client_data['risk_type'])
        st.metric("Heal Desk", client_data['heal_desk'])

    st.subheader("🧠 Recommended Action")
    st.info(client_data['recommended_action'])

    # --------------------------
    # ✍️ ACTION TRACKING
    # --------------------------
    st.subheader("✍️ Action Tracking")

    existing = actions_df[actions_df['client_name'] == client_name]

    default_owner = existing['owner'].values[0] if not existing.empty else ""
    default_status = existing['status'].values[0] if not existing.empty else "Not Started"
    default_notes = existing['notes'].values[0] if not existing.empty else ""

    owner = st.text_input("Owner", value=default_owner)
    status = st.selectbox(
        "Status",
        ["Not Started", "In Progress", "Completed"],
        index=["Not Started", "In Progress", "Completed"].index(default_status)
    )
    notes = st.text_area("Notes", value=default_notes)

    if st.button("Save Action"):
        new_row = pd.DataFrame([{
            "client_name": client_name,
            "user": user,
            "owner": owner,
            "status": status,
            "notes": notes
        }])

        actions_df = actions_df[actions_df['client_name'] != client_name]
        actions_df = pd.concat([actions_df, new_row], ignore_index=True)

        actions_df.to_csv("actions.csv", index=False)

        st.success(f"Saved for {client_name} ✅")