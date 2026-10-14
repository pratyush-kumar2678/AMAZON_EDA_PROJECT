# Amazon EDA Portfolio Project

## Project Overview
This project performs Exploratory Data Analysis (EDA) on Amazon product data using Python. It explores product prices, discounts, ratings, customer reviews, and categories to identify useful business insights.

## Objectives
- Clean and prepare the dataset.
- Calculate Key Performance Indicators (KPIs).
- Perform Univariate, Bivariate, and Multivariate Analysis.
- Create meaningful data visualizations.
- Build an interactive dashboard using Streamlit.

## Tools and Technologies
- Python
- Pandas and NumPy
- Matplotlib and Seaborn
- Plotly
- Streamlit
- Jupyter Notebook

## Project Files
- `AMAZON_EDA_PROJECT.ipynb` — Data cleaning, EDA, visualizations, and insights.
- `app.py` — Interactive Streamlit dashboard.
- `requirements.txt` — Required Python libraries.
- `amazon (2).csv` — Amazon product dataset.
- `.gitignore` — Files excluded from version control.

## EDA Analysis
1. **KPI Analysis:** Summary metrics for product data.
2. **Univariate Analysis:** Distribution of individual variables.
3. **Bivariate Analysis:** Relationships between two variables.
4. **Multivariate Analysis:** Patterns involving multiple variables.

## Run the Project Locally

Install the required libraries:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

Make sure the dataset is available at the file path expected by the notebook and dashboard.

## Disclaimer
This project is intended for educational and portfolio purposes. Findings depend on the dataset and do not necessarily represent all Amazon products or customers.
