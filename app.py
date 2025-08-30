import streamlit as st
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Bajaj Dashboard", layout="wide")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"


def go_to(page_name: str):
    st.session_state.page = page_name


# ---------------- NAVIGATION ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Historic Rates", "Blacklist Companies"], index=["Home", "Historic Rates", "Blacklist Companies"].index(st.session_state.page))

# Sync sidebar navigation
if page != st.session_state.page:
    st.session_state.page = page


# ---------------- HOME ----------------
if st.session_state.page == "Home":
    st.title("🏠 Home - Procurement Dashboard")
    st.write("Welcome! Please choose an option below:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 See Historic Rates", use_container_width=True):
            go_to("Historic Rates")
    with col2:
        if st.button("🚫 See Blacklisted Companies", use_container_width=True):
            go_to("Blacklist Companies")


# ---------------- HISTORIC RATES ----------------
elif st.session_state.page == "Historic Rates":
    st.sidebar.button("⬅️ Back to Home", on_click=lambda: go_to("Home"))
    st.title("📊 Historic Rates Dashboard")

    sub_choice = st.radio("Choose dataset:", ["Railways", "Accounts"], horizontal=True)

    try:
        # ---------------- RAILWAYS ----------------
        if sub_choice == "Railways":
            df = pd.read_excel("Railways sheet record final.xlsx")

            # ---- Filters ----
            st.subheader("🔍 Filters (Railways)")
            col1, col2 = st.columns(2)

            with col1:
                pharma = st.selectbox("Pharmaceutical Content", ["All"] + sorted(df["Pharmaceutical Content"].dropna().unique().tolist()))
            with col2:
                zone = st.selectbox("Zone", ["All"] + sorted(df["Zone"].dropna().unique().tolist()))

            df_filtered = df.copy()
            if pharma != "All":
                df_filtered = df_filtered[df_filtered["Pharmaceutical Content"] == pharma]
            if zone != "All":
                df_filtered = df_filtered[df_filtered["Zone"] == zone]

            if not df_filtered.empty:
                # ---- Bid Rank + Status calculation ----
                df_filtered["Bid Rank"] = (
                    df_filtered
                    .groupby(["Pharmaceutical Content", "Zone", "Tender Due Date"])["Quoted Rate"]
                    .rank(method="dense", ascending=True)
                )

                # Assign 99 for zero rates
                df_filtered.loc[df_filtered["Quoted Rate"] == 0, "Bid Rank"] = 99

                # Blank for missing rates
                df_filtered.loc[df_filtered["Quoted Rate"].isna(), "Bid Rank"] = None

                # Status column (L + Rank)
                df_filtered["Status"] = df_filtered["Bid Rank"].apply(
                    lambda x: None if pd.isna(x) else f"L{int(x)}"
                )

                # ---- Conditional Formatting ----
                def highlight_row(row):
                    style = ""
                    if row["Status"] == "L1":
                        style += "background-color: lightgreen; "
                    elif row["Status"] == "L2":
                        style += "background-color: orange; "  # FIXED color
                    elif row["Status"] == "L3":
                        style += "background-color: lightsalmon; "
                    return [style] * len(row)

                # ---- Sorting ----
                df_filtered = df_filtered.sort_values(by=["Tender Due Date", "Status"], ascending=[False, True])

                st.dataframe(
                    df_filtered.style.apply(highlight_row, axis=1),
                    use_container_width=True
                )
            else:
                st.warning("⚠️ No records found for selected filters.")

        # ---------------- ACCOUNTS ----------------
        else:
            df = pd.read_excel("SampleData.xlsx")

            # ---- Filters ----
            st.subheader("🔍 Filters (Accounts)")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                state = st.selectbox("Accounts (Region)", ["All"] + sorted(df["Region"].dropna().unique().tolist()))
            with col2:
                product = st.selectbox("Product", ["All"] + sorted(df["Product Name"].dropna().unique().tolist()))
            with col3:
                company = st.selectbox("Company Name", ["All"] + sorted(df["Company Name"].dropna().unique().tolist()))
            with col4:
                date_range = st.date_input("Publish Date Range", [])

            df_filtered = df.copy()
            if state != "All":
                df_filtered = df_filtered[df_filtered["Region"] == state]
            if product != "All":
                df_filtered = df_filtered[df_filtered["Product Name"] == product]
            if company != "All":
                df_filtered = df_filtered[df_filtered["Company Name"] == company]
            if len(date_range) == 2:
                start, end = date_range
                df_filtered = df_filtered[
                    (df_filtered["Publish Date"] >= pd.to_datetime(start))
                    & (df_filtered["Publish Date"] <= pd.to_datetime(end))
                ]

            if not df_filtered.empty:
                # ---- Bid Rank + Status calculation ----
                df_filtered["Bid Rank"] = (
                    df_filtered
                    .groupby(["Product Name", "Region", "Publish Date"])["Rate Quoted"]
                    .rank(method="dense", ascending=True)
                )

                # Assign 99 for zero rates
                df_filtered.loc[df_filtered["Rate Quoted"] == 0, "Bid Rank"] = 99

                # Blank for missing rates
                df_filtered.loc[df_filtered["Rate Quoted"].isna(), "Bid Rank"] = None

                # Status column (L + Rank)
                df_filtered["Status"] = df_filtered["Bid Rank"].apply(
                    lambda x: None if pd.isna(x) else f"L{int(x)}"
                )

                # ---- Competitor Logic ----
                competitor_counts = (
                    df_filtered[
                        (df_filtered["Status"].isin(["L1", "L2", "L3", "L4", "L5"])) &
                        (df_filtered["Company Name"].str.upper().str.strip() != "BAJAJ HEALTHCARE LIMITED")
                    ]
                    .groupby("Company Name")
                    .size()
                )
                competitor_companies = competitor_counts[competitor_counts >= 2].index.tolist()

                # ---- Conditional Formatting ----
                def highlight_row(row):
                    style = ""
                    if row["Status"] == "L1":
                        style += "background-color: lightgreen; "
                    elif row["Status"] == "L2":
                        style += "background-color: orange; "  # FIXED color
                    elif row["Status"] == "L3":
                        style += "background-color: lightsalmon; "
                    if row["Company Name"] in competitor_companies:
                        style += "color: red; font-weight: bold;"
                    return [style] * len(row)

                # ---- Sorting ----
                df_filtered = df_filtered.sort_values(by=["Publish Date", "Status"], ascending=[False, True])

                st.dataframe(
                    df_filtered.style.apply(highlight_row, axis=1),
                    use_container_width=True
                )
            else:
                st.warning("⚠️ No records found for selected filters.")

    except Exception as e:
        st.error(f"Error loading file: {e}")


# ---------------- BLACKLIST COMPANIES ----------------
elif st.session_state.page == "Blacklist Companies":
    st.sidebar.button("⬅️ Back to Home", on_click=lambda: go_to("Home"))
    st.title("🚫 Blacklist Companies Dashboard")

    try:
        df_blacklist = pd.read_excel("blacklist_clean.xlsx")
        st.dataframe(df_blacklist, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading blacklist file: {e}")
