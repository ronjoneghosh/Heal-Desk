import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("🚀 CX Health Command Center")
st.caption("Customer Success Intelligence Platform")

uploaded_file = st.file_uploader("Upload your client CSV", type=["csv"])

# --------------------------
# 📂 Load actions
# --------------------------
if os.path.exists("actions.csv"):
    actions_df = pd.read_csv("actions.csv")
else:
    actions_df = pd.DataFrame(columns=["client_name", "user", "owner", "status", "notes"])

# --------------------------
# 👤 USER
# --------------------------
st.sidebar.header("👤 User")
user = st.sidebar.selectbox("Select User", ["Ronjone", "CSM 1", "CSM 2"])

# --------------------------
# 🚨 WAR ROOM
# --------------------------
war_room = st.sidebar.checkbox("🚨 War Room Mode")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean columns
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("(", "").str.replace(")", "").str.replace("-", "_")

    # --------------------------
    # 🧠 SCORING
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

    # --------------------------
    # 📊 SMART METRICS
    # --------------------------
    arr_column = next((c for c in df.columns if "arr" in c and "risk" not in c), None)
    renewal_column = next((c for c in df.columns if "renewal" in c), None)

    total_customers = len(df)
    critical_count = (df['priority'] == "Critical").sum()
    high_count = (df['priority'] == "High").sum()

    percent_critical = round((critical_count / total_customers) * 100, 1)

    if arr_column:
        arr_at_risk = df[df['priority'].isin(["Critical", "High"])][arr_column].sum()
        total_arr = df[arr_column].sum()
    else:
        arr_at_risk = 0
        total_arr = 0

    if renewal_column:
        urgent_renewals = (df[renewal_column] < 90).sum()
    else:
        urgent_renewals = 0

    avg_sentiment = round(df['sentiment_score_1_10'].mean(), 2)

    # --------------------------
    # 🧠 EXECUTIVE SUMMARY
    # --------------------------
    st.subheader("🧠 Executive Summary")

    summary = []

    if percent_critical > 25:
        summary.append("🚨 High portfolio risk")
    elif percent_critical > 10:
        summary.append("⚠️ Moderate risk")
    else:
        summary.append("✅ Healthy portfolio")

    if arr_at_risk > 0:
        summary.append(f"💰 ${arr_at_risk:,.0f} ARR at risk")

    if urgent_renewals > 0:
        summary.append(f"⏳ {urgent_renewals} renewals < 90 days")

    for line in summary:
        st.write(f"- {line}")

    # --------------------------
    # 📊 METRICS
    # --------------------------
    st.subheader("📊 Portfolio Overview")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🚨 Critical", critical_count)
    col2.metric("⚠️ High", high_count)
    col3.metric("🟡 Medium", (df['priority'] == "Medium").sum())
    col4.metric("🟢 Low", (df['priority'] == "Low").sum())
    col5.metric("% Critical", f"{percent_critical}%")

    st.subheader("💰 Business Risk")

    col1, col2, col3 = st.columns(3)
    col1.metric("ARR at Risk", f"${arr_at_risk:,.0f}")
    col2.metric("Total ARR", f"${total_arr:,.0f}")
    col3.metric("Renewals < 90 Days", urgent_renewals)

    # --------------------------
    # 📊 CHARTS (FIXED ONLY)
    # --------------------------
    st.subheader("📊 Visual Dashboard")

    # Dropdown for chart data
    chart_mode = st.selectbox(
        "View Charts Based On:",
        ["All Customers", "Filtered Customers"]
    )

    # Filter logic reused
    if war_room:
        filtered_df = df[df['priority'] == "Critical"]
    else:
        filtered_df = df

    chart_df = df if chart_mode == "All Customers" else filtered_df

    # 3 aligned charts
    col1, col2, col3 = st.columns(3)

    # Priority Distribution
    with col1:
        st.write("### Priority Distribution")

        fig, ax = plt.subplots(figsize=(4,3))
        chart_df['priority'].value_counts().plot(kind='bar', ax=ax)

        ax.set_xlabel("Priority Level")
        ax.set_ylabel("Number of Customers")
        ax.set_title("Customer Count")

        st.pyplot(fig)
        st.caption("Y = customers | X = priority category")

    # ARR by Priority
    with col2:
        if arr_column:
            st.write("### ARR by Priority")

            fig, ax = plt.subplots(figsize=(4,3))
            chart_df.groupby('priority')[arr_column].sum().plot(kind='bar', ax=ax)

            ax.set_xlabel("Priority Level")
            ax.set_ylabel("Total ARR ($)")

            ax.get_yaxis().set_major_formatter(
                plt.FuncFormatter(lambda x, _: f'${int(x):,}')
            )

            st.pyplot(fig)
            st.caption("Y = revenue ($) | X = priority")

    # Health Score Distribution
    with col3:
        st.write("### Health Score Distribution")

        fig, ax = plt.subplots(figsize=(4,3))
        chart_df['health_score'].hist(ax=ax, bins=8)

        ax.set_xlabel("Health Score (1–10)")
        ax.set_ylabel("Number of Customers")

        st.pyplot(fig)
        st.caption("Distribution of customer health scores")

    # --------------------------
    # 🚨 ATTENTION
    # --------------------------
    st.subheader("🚨 What Needs Attention Today")

    critical_df = df[df['priority'] == "Critical"]

    if not critical_df.empty:
        st.error(f"{len(critical_df)} Critical accounts need action")
        st.dataframe(critical_df[['client_name', 'health_score']])

    if urgent_renewals > 0:
        st.warning(f"{urgent_renewals} renewals < 90 days")

    # --------------------------
    # FILTER
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

    filtered_df = filtered_df.sort_values(by="health_score")

    if war_room:
        st.error("🚨 WAR ROOM MODE ACTIVE")

    # --------------------------
    # TABLE
    # --------------------------
    st.subheader("📋 Client Portfolio")
    st.dataframe(filtered_df, use_container_width=True)

    # --------------------------
    # DRILLDOWN
    # --------------------------
    st.subheader("🔍 Client Drilldown")

    client_name = st.selectbox("Select Client", df['client_name'])
    client_data = df[df['client_name'] == client_name].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Health Score", client_data['health_score'])
        st.metric("Priority", client_data['priority'])

    with col2:
        st.metric("Sentiment", client_data['sentiment_score_1_10'])
        st.metric("Usage", client_data['usage_score_1_10'])

    # --------------------------
    # ACTION TRACKING
    # --------------------------
    st.subheader("✍️ Action Tracking")

    existing = actions_df[actions_df['client_name'] == client_name]

    owner = st.text_input("Owner", value=existing['owner'].values[0] if not existing.empty else "")
    status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
    notes = st.text_area("Notes", value=existing['notes'].values[0] if not existing.empty else "")

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

        st.success("Saved ✅")