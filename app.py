"""
Amazon Product Analysis Dashboard
Run: streamlit run app.py
"""

from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Amazon Product Analysis",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Amazon Product Analysis Dashboard")
st.caption("Explore product prices, discounts, ratings, categories, and review activity.")

REQUIRED_HINT_COLUMNS = ["product_id", "product_name", "category"]


def clean_numeric(series, kind="number"):
    """Convert common Amazon CSV text formats to numeric values safely."""
    # Work with text first so symbols and commas can be removed consistently.
    values = series.astype("string").str.strip()
    values = values.str.replace(",", "", regex=False)
    values = values.str.replace("₹", "", regex=False)
    if kind == "percent":
        values = values.str.replace("%", "", regex=False)
    # Invalid text becomes NaN instead of crashing the dashboard.
    return pd.to_numeric(values, errors="coerce")


def prepare_data(raw_df):
    """Clean supported columns and create category/savings fields when possible."""
    # Normalize column labels to avoid issues caused by extra spaces.
    df = raw_df.copy()
    df.columns = [str(column).strip() for column in df.columns]

    # Convert numeric columns only when they exist in the uploaded dataset.
    numeric_columns = {
        "discounted_price": "number",
        "actual_price": "number",
        "discount_percentage": "percent",
        "rating": "number",
        "rating_count": "number",
    }
    for column, kind in numeric_columns.items():
        if column in df.columns:
            df[column] = clean_numeric(df[column], kind)

    # Split the pipe-separated category path into broad and sub-category labels.
    if "category" in df.columns:
        category_path = df["category"].fillna("Unknown").astype(str).str.split("|")
        df["main_category"] = category_path.str[0].str.strip()
        df["sub_category"] = category_path.str[1].fillna("Not specified").str.strip()
    elif "main_category" not in df.columns:
        df["main_category"] = "Unknown"

    # Calculate savings only when both price columns are available.
    if {"actual_price", "discounted_price"}.issubset(df.columns):
        df["savings_amount"] = df["actual_price"] - df["discounted_price"]

    return df


def money(value):
    """Format a number as Indian rupees; show N/A for unavailable values."""
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.2f}"


# Let the user upload the dataset because the notebook upload did not include the CSV.
uploaded_file = st.sidebar.file_uploader("Upload Amazon CSV dataset", type=["csv"])
default_candidates = [
    Path("data/amazon (2).csv"),
    Path("data/amazon.csv"),
    Path("amazon (2).csv"),
    Path("amazon.csv"),
]

raw_df = None
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        st.stop()
else:
    # Try common local dataset locations for users who keep the CSV in the project folder.
    for candidate in default_candidates:
        if candidate.exists():
            try:
                raw_df = pd.read_csv(candidate)
                st.sidebar.success(f"Loaded: {candidate}")
                break
            except Exception:
                continue

if raw_df is None:
    st.info(
        "Upload your Amazon product CSV using the control in the left sidebar. "
        "The ZIP includes the notebook and dashboard code, but not the original CSV dataset."
    )
    st.markdown(
        """
        **Expected columns for the full dashboard:** `product_id`, `product_name`,
        `category`, `discounted_price`, `actual_price`, `discount_percentage`,
        `rating`, and `rating_count`.

        The app will still try to work if some optional columns are missing.
        """
    )
    st.stop()

df = prepare_data(raw_df)
analysis_df = df.drop_duplicates().copy()

st.sidebar.header("Filters")
if "main_category" in analysis_df.columns:
    categories = sorted(analysis_df["main_category"].dropna().astype(str).unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Main category",
        categories,
        default=categories,
    )
    if selected_categories:
        analysis_df = analysis_df[
            analysis_df["main_category"].astype(str).isin(selected_categories)
        ]
    else:
        analysis_df = analysis_df.iloc[0:0]

if "rating" in analysis_df.columns and analysis_df["rating"].notna().any():
    min_rating = float(analysis_df["rating"].dropna().min())
    max_rating = float(analysis_df["rating"].dropna().max())
    if min_rating < max_rating:
        rating_range = st.sidebar.slider(
            "Rating range",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
        )
        analysis_df = analysis_df[
            analysis_df["rating"].between(rating_range[0], rating_range[1], inclusive="both")
            | analysis_df["rating"].isna()
        ]

if analysis_df.empty:
    st.warning("No rows match the selected filters. Change the filters in the sidebar.")
    st.stop()

# KPIs use only the available columns and valid values.
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
product_count = (
    analysis_df["product_id"].nunique()
    if "product_id" in analysis_df.columns
    else len(analysis_df)
)
kpi1.metric("Unique products", f"{product_count:,}")

avg_rating = analysis_df["rating"].mean() if "rating" in analysis_df.columns else float("nan")
kpi2.metric("Average rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A")

avg_discount = (
    analysis_df["discount_percentage"].mean()
    if "discount_percentage" in analysis_df.columns
    else float("nan")
)
kpi3.metric("Average discount", f"{avg_discount:.2f}%" if pd.notna(avg_discount) else "N/A")

avg_price = (
    analysis_df["discounted_price"].mean()
    if "discounted_price" in analysis_df.columns
    else float("nan")
)
kpi4.metric("Average discounted price", money(avg_price))

st.divider()
overview_tab, category_tab, relationship_tab, text_tab, data_tab = st.tabs(
    ["Overview", "Categories", "Relationships", "Review Text", "Data Quality & Table"]
)

with overview_tab:
    st.subheader("Numeric distributions")
    available_numeric = [
        column for column in
        ["discounted_price", "actual_price", "discount_percentage", "rating", "rating_count", "savings_amount"]
        if column in analysis_df.columns and analysis_df[column].notna().any()
    ]
    if available_numeric:
        selected_numeric = st.selectbox("Choose a numeric field", available_numeric)
        chart_df = analysis_df[[selected_numeric]].dropna()
        fig = px.histogram(
            chart_df,
            x=selected_numeric,
            nbins=30,
            marginal="box",
            title=f"Distribution of {selected_numeric.replace('_', ' ').title()}",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("A histogram shows the distribution; the box plot helps reveal spread and potential outliers.")
    else:
        st.info("No supported numeric columns were found after cleaning.")

with category_tab:
    st.subheader("Products by category")
    if "main_category" in analysis_df.columns:
        counts = (
            analysis_df["main_category"].fillna("Unknown").astype(str)
            .value_counts().rename_axis("main_category").reset_index(name="product_rows")
        )
        fig = px.bar(
            counts,
            x="main_category",
            y="product_rows",
            title="Product Rows by Main Category",
            labels={"main_category": "Main category", "product_rows": "Rows"},
        )
        st.plotly_chart(fig, use_container_width=True)

        if {"main_category", "rating"}.issubset(analysis_df.columns):
            rating_summary = (
                analysis_df.groupby("main_category", dropna=False)
                .agg(average_rating=("rating", "mean"), product_rows=("rating", "count"))
                .reset_index()
                .sort_values("average_rating", ascending=False)
            )
            st.subheader("Average rating by category")
            st.dataframe(rating_summary, use_container_width=True, hide_index=True)
    else:
        st.info("The dataset has no category column to chart.")

with relationship_tab:
    st.subheader("Explore relationships")
    possible_pairs = [
        ("discounted_price", "rating"),
        ("discount_percentage", "rating"),
        ("actual_price", "discounted_price"),
        ("discounted_price", "rating_count"),
    ]
    valid_pairs = [
        (x, y) for x, y in possible_pairs
        if x in analysis_df.columns and y in analysis_df.columns
        and analysis_df[x].notna().any() and analysis_df[y].notna().any()
    ]
    if valid_pairs:
        pair = st.selectbox(
            "Choose fields",
            valid_pairs,
            format_func=lambda item: f"{item[0]} vs {item[1]}",
        )
        scatter_df = analysis_df[[pair[0], pair[1]] + (["main_category"] if "main_category" in analysis_df.columns else [])].dropna(subset=list(pair))
        fig = px.scatter(
            scatter_df,
            x=pair[0],
            y=pair[1],
            color="main_category" if "main_category" in scatter_df.columns else None,
            opacity=0.65,
            title=f"{pair[0].replace('_', ' ').title()} vs {pair[1].replace('_', ' ').title()}",
        )
        st.plotly_chart(fig, use_container_width=True)

        corr_df = analysis_df[[pair[0], pair[1]]].corr(numeric_only=True)
        if corr_df.shape == (2, 2):
            correlation = corr_df.iloc[0, 1]
            st.metric("Pearson correlation", f"{correlation:.3f}" if pd.notna(correlation) else "N/A")
            st.caption("Correlation describes linear association; it does not prove causation.")
    else:
        st.info("Not enough supported numeric column pairs are available for relationship charts.")

with text_tab:
    st.subheader("Review text overview")
    if "review_content" in analysis_df.columns:
        text_series = analysis_df["review_content"].fillna("").astype(str)
        text_lengths = text_series.str.len()
        text_df = pd.DataFrame({"review_length": text_lengths})
        fig = px.histogram(
            text_df,
            x="review_length",
            nbins=30,
            title="Review Length (Characters)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # A simple word-frequency view; this is exploratory, not sentiment analysis.
        words = re.findall(r"\b[a-z]{4,}\b", " ".join(text_series.str.lower().tolist()))
        stopwords = {
            "this", "that", "with", "from", "have", "were", "they", "them", "very",
            "when", "what", "your", "would", "could", "which", "there", "their",
            "been", "will", "also", "just", "only", "than", "into", "good", "product",
        }
        frequencies = pd.Series([word for word in words if word not in stopwords]).value_counts().head(15)
        if not frequencies.empty:
            word_df = frequencies.rename_axis("word").reset_index(name="frequency")
            fig = px.bar(word_df, x="frequency", y="word", orientation="h", title="Frequent Review Words")
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Word frequency is not sentiment analysis; words are counted without understanding context.")
    else:
        st.info("No review_content column was found in the uploaded CSV.")

with data_tab:
    st.subheader("Data quality summary")
    quality = pd.DataFrame({
        "missing_values": df.isna().sum(),
        "data_type": df.dtypes.astype(str),
        "unique_values": df.nunique(dropna=True),
    }).sort_values("missing_values", ascending=False)
    st.dataframe(quality, use_container_width=True)

    st.write(f"Raw rows: **{len(df):,}** | Exact duplicate rows removed for analysis: **{len(df) - len(df.drop_duplicates()):,}** | Rows after filters: **{len(analysis_df):,}**")
    st.subheader("Filtered data preview")
    st.dataframe(analysis_df.head(100), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        data=analysis_df.to_csv(index=False).encode("utf-8"),
        file_name="amazon_products_filtered.csv",
        mime="text/csv",
    )

st.divider()
st.caption("Portfolio learning project. Findings describe the uploaded dataset and should not be interpreted as causal claims.")
