# IDX Exchange – Data Analyst Internship

**Intern:** Khushi  
**Program:** MLS Analytics & Tableau Dashboard (12-Week)

## Overview

This project is part of the IDX Exchange Data Analyst Internship Program. The objective is to analyze California residential real estate market trends using CRMLS transaction data, build automated data preparation workflows in Python, and develop interactive Tableau dashboards for market intelligence reporting.

Raw CRMLS data files are confidential and are not included in this repository.

## Tech Stack

- **Python** — primary programming language
- **pandas** — data processing and CSV handling
- **Matplotlib** — histograms and boxplots
- **Jupyter Notebook** — interactive EDA and exploration
- **CRMLS data** — monthly MLS listing and sold transaction source data
- **FRED MORTGAGE30US** — weekly U.S. 30-year fixed mortgage rate data
- **Tableau Desktop Public** — dashboard development (Weeks 8–12)

## Repository Structure
```
IDX-Exchange/
├── Python Files/
├── Notebooks/
├── Reports/
│   └── Visualizations/
└── README.md
```
## Key Files

| Week | File | Purpose |
|---|---|---|
| Week 1 | `week1.py` | Combine monthly CRMLS CSVs, filter to Residential, save combined datasets |
| Weeks 2–3 | `week2_3_eda.py` | Dataset structuring, missing value analysis, EDA questions, visualizations |
| Weeks 2–3 | `week2_3_mortgage.py` | Fetch FRED mortgage rates and merge onto MLS datasets by month |
| Weeks 4–5 | `week4_cleaning.ipynb` | Data cleaning, date conversions, invalid value flags, geographic checks |

## Data Pipeline

| Stage | Output | Sold Rows | Listing Rows |
|---|---|---|---|
| Week 1 – Combine | `sold_combined.csv` | 448,253 | 607,724 |
| Weeks 2–3 – Enrich | `sold_with_rates.csv` | 448,253 | 607,724 |
| Weeks 4–5 – Clean | `sold_cleaned.csv` | TBD | TBD |

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
- Date inconsistencies flagged: some close dates precede purchase contract dates, to be resolved in Weeks 4–5

### Weeks 4–5 – Data Cleaning and Preparation

- Converted date fields to datetime format
- Dropped 8 columns with 100% missing values and redundant metadata columns
- Flagged invalid numeric values: ClosePrice at or below zero, LivingArea at or below zero, negative DaysOnMarket
- Created date consistency flags: listing_after_close_flag, purchase_after_close_flag, negative_timeline_flag
- Created geographic quality flags: missing coordinates, zero coordinates, invalid longitude, out-of-state records

### Week 6 – Feature Engineering

Planned.

### Week 7 – Outlier Detection

Planned.

### Weeks 8–10 – Tableau Dashboard Development

Planned.

### Weeks 11–12 – Final Presentation and Market Intelligence Report

Planned.

## Key Metrics

- Median Sales Price
- Days on Market
- Price per Square Foot
- Sale-to-List Price Ratio
- New Listings vs. Closed Sales
- Top Agents and Brokerages by Volume
- Regional Market Trends by County and ZIP Code