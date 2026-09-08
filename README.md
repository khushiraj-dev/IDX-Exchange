# IDX Exchange – Data Analyst Internship

**Intern:** Khushi
**Program:** MLS Analytics & Tableau Dashboard (12-Week)

## Overview

This project is part of the IDX Exchange Data Analyst Internship Program. The objective is to analyze California residential real estate market trends using CRMLS transaction data, build automated data preparation workflows in Python, and develop interactive Tableau dashboards for market intelligence reporting.

Raw CRMLS data files are confidential and are not included in this repository.

## Tech Stack

- **Python** — primary programming language
- **pandas** — data processing and CSV handling
- **GeoPandas** — spatial join of properties to California school district boundaries
- **Matplotlib** — histograms and boxplots
- **Jupyter Notebook** — interactive EDA and exploration
- **CRMLS data** — monthly MLS listing and sold transaction source data
- **FRED MORTGAGE30US** — weekly U.S. 30-year fixed mortgage rate data
- **Tableau Desktop Public** — dashboard development (Weeks 8–12)

## Repository Structure
```
IDX-Exchange/
├── Python Files/
│   ├── week1.py
│   ├── week2_3_eda.py
│   ├── week2_3_mortgage_rates.py
│   ├── week4_5.py
│   ├── week6.py
│   ├── week7.py
│   └── final_cleaning.py
├── Notebooks/
│   ├── mortgageRates.ipynb
│   ├── week2-3.ipynb
│   ├── week4-5.ipynb
│   ├── week_6.ipynb
│   ├── week_7.ipynb
│   └── week11.ipynb
├── Reports/
│   ├── Visualizations/
│   ├── Week4_5_Cleaning/
│   ├── Week6_Feature_Engineering/
│   ├── Week7_Outlier_Detection/
│   └── Map_Checks/
├── data/
│   └── CA school district boundary GeoJSON
├── market_analysis.twbx        (Tableau workbook, Weeks 8–10)
└── README.md
```

Raw and derived CSV outputs are excluded via `.gitignore` (confidential and too large for GitHub).

## Key Files

| Week | File | Purpose |
|---|---|---|
| Week 1 | `week1.py` | Combine monthly CRMLS CSVs, filter to Residential, save combined datasets |
| Weeks 2–3 | `week2_3_eda.py` | Dataset structuring, missing value analysis, EDA questions, visualizations |
| Weeks 2–3 | `week2_3_mortgage_rates.py` | Fetch FRED mortgage rates and merge onto MLS datasets by month |
| Weeks 4–5 | `week4_5.py` | Data cleaning, date conversions, invalid value flags, geographic checks |
| Week 6 | `week6.py` | Engineer market metrics, join school districts, build segment summaries |
| Week 7 | `week7.py` | IQR outlier detection, suspicious price review, ZIP and geography quality checks |
| Final Cleaning | `final_cleaning.py` | Resolve flagged data quality issues into the final analysis-ready dataset |

## Data Pipeline

| Stage | Output | Sold Rows |
|---|---|---|
| Week 1 – Combine | `sold_combined.csv` | 448,253 |
| Weeks 2–3 – Enrich | `sold_with_rates.csv` | 448,253 |
| Weeks 4–5 – Clean | `sold_cleaned.csv` | 465,313 |
| Week 6 – Feature Engineering | `sold_features.csv` | 465,313 |
| Week 7 – Outlier Flagging | `sold_flagged.csv` | 465,313 |
| Week 7 – Outlier Filtering | `sold_filtered.csv` | 437,456 |
| Final Cleaning | `sold_final_cleaned.csv` | 465,282 |

Listing dataset counts follow the same Weeks 1–3 stages (607,724 rows after the Residential filter).

## Weekly Progress

### Week 0 – Orientation

- Downloaded all CRMLS CSV files from FTP server (`CRMLSListing` and `CRMLSSold` files)
- Obtained February through June 2026 files from teammates who ran the extraction scripts
- Reviewed Trestle Property Metadata for field definitions and data types

### Week 1 – Monthly Dataset Aggregation

- Loaded all monthly CSV files from January 2024 through June 2026
- Preferred `_filled` files when available and dropped extra `latfilled` and `lonfilled` columns
- Concatenated into two combined datasets and filtered to `PropertyType == 'Residential'`

| Dataset | Before Filter | After Filter |
|---|---|---|
| Sold | 666,037 | 448,253 |
| Listings | 955,190 | 607,724 |

### Weeks 2–3 – Dataset Structuring, Validation, and EDA

- Classified all columns into core, metadata, and market analysis categories
- Performed missing value analysis — flagged 8 columns at 100% missing in the sold dataset
- Generated numeric distribution summaries and IQR-filtered visualizations for 9 key fields
- Enriched both datasets with FRED 30-year fixed mortgage rates via monthly join

Key EDA findings:

- Median close price: $825,000 | Mean: $1.18M (skewed by extreme outliers)
- Median days on market: 18 days (right-skewed; max of 12,430 flagged as a data error)
- 40.1% of homes sold above list price, 42.5% below, 17.4% at list price
- Top counties by median close price: San Mateo ($1.7M), Santa Clara ($1.6M), San Francisco ($1.2M)
- Date inconsistencies flagged: some close dates precede purchase contract dates, resolved in Weeks 4–5

### Weeks 4–5 – Data Cleaning and Preparation

- Converted date fields to datetime format and added Month and Year columns for Tableau grouping
- Dropped 8 columns with 100% missing values and redundant metadata columns
- Dropped duplicate `.1` suffix columns from the listings dataset
- Flagged invalid numeric values: ClosePrice at or below zero, LivingArea at or below zero, negative DaysOnMarket
- Created date consistency flags: `listing_after_close_flag`, `purchase_after_close_flag`, `negative_timeline_flag`
- Resolved date flags by setting impossible dates to null — sales are real, only the dates were corrupted
- Created geographic quality flags: missing coordinates, zero coordinates, invalid longitude, out-of-state records

### Week 6 – Feature Engineering

- Engineered market metrics: `sale_to_list_ratio`, `close_to_original_list_ratio`, `price_per_sqft`
- Built time-series fields (`Year`, `Month`, `YrMo`) and transaction timeline fields (`listing_to_contract_days`, `contract_to_close_days`)
- Spatially joined properties to California Unified School District boundaries using GeoPandas (74.9% coverage)
- Built segmented market summaries by property subtype, county, MLS area, listing office, and buyer office

### Week 7 – Outlier Detection and Data Quality Audit

- Compared 1.5x vs. 3.0x IQR thresholds on ClosePrice, LivingArea, and DaysOnMarket
- Selected 3.0x multiplier — California housing is strongly right-skewed and 1.5x misclassifies legitimate luxury properties
- Removing the 6% flagged records moved the median close price by only 2% but the mean by 17%, confirming medians resist outliers and justifying their use throughout this project
- Produced a full flagged dataset (`sold_flagged.csv`, all rows preserved) and a filtered Tableau-ready dataset (`sold_filtered.csv`)

### Final Data Cleaning

- Removed 31 confirmed non-California and foreign-country records
- Fixed 28 ZIP code typos and repaired 28 positive-longitude coordinate errors (dropped minus signs)
- Nulled zero coordinates, invalid LivingArea placeholder values, and negative DaysOnMarket
- Nulled OriginalListPrice for 275 extreme sale-to-list ratio records caused by bad source data
- Flagged 624 year-built anomalies and nulled 2 impossible future-dated values
- Recalculated all engineered metrics after fixes to produce `sold_final_cleaned.csv` (465,282 rows)

### Weeks 8–10 – Tableau Dashboard Development

Built two Tableau workbooks published to Tableau Public:

**market_analysis.twbx** — California residential market intelligence:
- Dashboard 1 (Market Overview): KPI cards, monthly median close price, new listings, average days on market, close-to-original-list ratio
- Dashboard 2 (Market Trends & Rate Impact): Closed sales by month, mortgage rate vs. median close price (custom dual-axis chart)

**competitive_analysis.twbx** — Agent and geographic competitive intelligence:
- Dashboard 1 (Agent & Office Performance): Top 100 listing agents by volume and units, top 100 listing offices by volume and units, agent performance scatter plot (volume vs. median price)
- Dashboard 2 (Geographic Market Intelligence): Zip code heat map of median close prices, zip code heat map of homes sold

All dashboards filterable by city, county, zip code, and property subtype.

### Weeks 11–12 – Market Intelligence Report and Final Presentation

- Conducted city-level deep dive on Fremont, CA — chosen for its Bay Area tech market dynamics and personal familiarity
- Key findings: $1.526M median close price (85% above statewide median), 10-day median DOM, 62.3% of homes sold above asking price, mild 4.2% price softening from 2024–2026
- Produced 1-page Fremont Market Intelligence Report covering market overview, pricing trends, market activity, competitive landscape, and key takeaways
- Delivered 5-minute live presentation walking through Tableau dashboards and Fremont findings

## Key Metrics Analyzed

- Median Sales Price
- Days on Market
- Price per Square Foot
- Sale-to-List Price Ratio
- New Listings vs. Closed Sales
- Top Agents and Brokerages by Volume and Units
- Regional Market Trends by County and ZIP Code
- School District Impact on Home Prices
- Mortgage Rate vs. Median Close Price Relationship