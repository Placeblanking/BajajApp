import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bajaj Dashboard", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Home"


def go_to(page_name: str):
    st.session_state.page = page_name


st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Historic Rates", "Blacklist Companies"],
    index=["Home", "Historic Rates", "Blacklist Companies"].index(
        st.session_state.page
    ),
)

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
                pharma = st.selectbox(
                    "Pharmaceutical Content",
                    ["All"] + sorted(df["Pharmaceutical Content"].dropna().unique().tolist()),
                )
            with col2:
                zone = st.selectbox(
                    "Zone", ["All"] + sorted(df["Zone"].dropna().unique().tolist())
                )

            df_filtered = df.copy()
            if pharma != "All":
                df_filtered = df_filtered[df_filtered["Pharmaceutical Content"] == pharma]
            if zone != "All":
                df_filtered = df_filtered[df_filtered["Zone"] == zone]

            if not df_filtered.empty:
                # ---- Bid Rank + Status calculation ----
                df_filtered["Bid Rank"] = (
                    df_filtered.groupby(["Pharmaceutical Content", "Zone", "Tender Due Date"])["Quoted Rate"]
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

                # ---- Sorting fix (L1, L2, L3...) ----
                df_filtered["RankOrder"] = df_filtered["Status"].str.extract(r"(\d+)").astype(float)
                df_filtered = df_filtered.sort_values(
                    by=["Tender Due Date", "RankOrder"], ascending=[False, True]
                )

                # ---- Conditional Formatting ----
                def highlight_row(row):
                    style = ""
                    if row["Status"] == "L1":
                        style += "background-color: lightgreen; "
                    elif row["Status"] == "L2":   # Fixed L2 color
                        style += "background-color: lightblue; "
                    elif row["Status"] == "L3":
                        style += "background-color: lightsalmon; "
                    return [style] * len(row)

                st.dataframe(
                    df_filtered.drop(columns=["RankOrder"]).style.apply(highlight_row, axis=1),
                    use_container_width=True,
                )
            else:
                st.warning("⚠️ No records found for selected filters.")

        # ---------------- ACCOUNTS ----------------
        else:
            df = pd.read_excel("SampleData.xlsx")

            # ---- Filters ----
            st.subheader("🔍 Filters (Accounts)")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                state = st.selectbox(
                    "Accounts (Region)",
                    ["All"] + sorted(df["Region"].dropna().unique().tolist()),
                )
            with col2:
                product = st.selectbox(
                    "Product", ["All"] + sorted(df["Product Name"].dropna().unique().tolist())
                )
            with col3:
                company = st.selectbox(
                    "Company Name",
                    ["All"] + sorted(df["Company Name"].dropna().unique().tolist()),
                )
            with col4:
                start_date = st.date_input("Start Date", value=None)
            with col5:
                end_date = st.date_input("End Date", value=None)

            df_filtered = df.copy()
            if state != "All":
                df_filtered = df_filtered[df_filtered["Region"] == state]
            if product != "All":
                df_filtered = df_filtered[df_filtered["Product Name"] == product]
            if company != "All":
                df_filtered = df_filtered[df_filtered["Company Name"] == company]
            if start_date and end_date:
                df_filtered = df_filtered[
                    (df_filtered["Publish Date"] >= pd.to_datetime(start_date))
                    & (df_filtered["Publish Date"] <= pd.to_datetime(end_date))
                ]

            if not df_filtered.empty:
                # ---- Bid Rank + Status calculation ----
                df_filtered["Bid Rank"] = (
                    df_filtered.groupby(["Product Name", "Region", "Publish Date"])["Rate Quoted"]
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
                        (df_filtered["Status"].isin(["L1", "L2", "L3", "L4", "L5"]))
                        & (df_filtered["Company Name"].str.upper().str.strip() != "BAJAJ HEALTHCARE LIMITED")
                    ]
                    .groupby("Company Name")
                    .size()
                )
                competitor_companies = competitor_counts[competitor_counts >= 2].index.tolist()

                # ---- Sorting fix ----
                df_filtered["RankOrder"] = df_filtered["Status"].str.extract(r"(\d+)").astype(float)
                df_filtered = df_filtered.sort_values(
                    by=["Publish Date", "RankOrder"], ascending=[False, True]
                )

                # ---- Conditional Formatting ----
                def highlight_row(row):
                    style = ""
                    if row["Status"] == "L1":
                        style += "background-color: lightgreen; "
                    elif row["Status"] == "L2":
                        style += "background-color: lightblue; "
                    elif row["Status"] == "L3":
                        style += "background-color: lightsalmon; "
                    if row["Company Name"] in competitor_companies:
                        style += "color: red; font-weight: bold;"
                    return [style] * len(row)

                st.dataframe(
                    df_filtered.drop(columns=["RankOrder"]).style.apply(highlight_row, axis=1),
                    use_container_width=True,
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
