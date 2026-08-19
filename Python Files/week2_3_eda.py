'''
Weeks 2-3 – Dataset Structuring, Validation, and EDA

Purpose:
Inspect the combined CRMLS sold dataset, review property types and filtering,
analyze missing values and numeric distributions, identify extreme outliers,
answer key EDA questions, and save the filtered Residential dataset.
'''

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------
# Paths
# -----------------------------
RAW_DIR = Path(
    r"C:\Users\khush\idx files"
)

REPORTS_DIR = Path(
    r"C:\Users\khush\Desktop\IDX-Exchange\Reports"
)

VIZ_DIR = (
    REPORTS_DIR
    / "Visualizations"
)


REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

VIZ_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# -----------------------------
# Load Unfiltered Sold Dataset
# -----------------------------
sold_all = pd.read_csv(
    RAW_DIR / "sold_all_combined.csv",
    low_memory=False
)


print(
    "Loaded unfiltered combined sold dataset."
)


# -----------------------------
# Dataset Structure
# -----------------------------
print("\nDataset shape:")

print(
    "Rows:",
    sold_all.shape[0]
)

print(
    "Columns:",
    sold_all.shape[1]
)


print("\nColumn names:")
print(
    sold_all.columns.tolist()
)


print("\nFirst 5 rows:")
print(
    sold_all.head()
)


print("\nData type summary:")
print(
    sold_all.dtypes.value_counts()
)


# Save detailed data type report
dtype_summary = (
    sold_all.dtypes
    .astype(str)
    .reset_index()
)

dtype_summary.columns = [
    'column',
    'dtype'
]


dtype_summary.to_csv(
    REPORTS_DIR
    / "data_types_summary.csv",
    index=False
)


# -----------------------------
# Property Type Review
# -----------------------------
if 'PropertyType' not in sold_all.columns:
    raise ValueError(
        "PropertyType column is missing."
    )


property_types = (
    sold_all['PropertyType']
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)


print("\nUnique property types found:")
print(property_types)


property_type_counts = (
    sold_all['PropertyType']
    .fillna('Missing')
    .astype(str)
    .str.strip()
    .value_counts()
    .reset_index()
)


property_type_counts.columns = [
    'PropertyType',
    'row_count'
]


property_type_counts.to_csv(
    REPORTS_DIR
    / "property_type_counts.csv",
    index=False
)


# -----------------------------
# Residential Filtering
# -----------------------------
sold = sold_all[
    sold_all['PropertyType']
    .astype(str)
    .str.strip()
    .eq('Residential')
].copy()


print("\nFiltering logic:")
print(
    "Keeping rows where PropertyType = Residential"
)


print(
    f"Rows before filter: "
    f"{len(sold_all):,}"
)

print(
    f"Residential rows after filter: "
    f"{len(sold):,}"
)


residential_share = (
    len(sold)
    / len(sold_all)
    * 100
)

other_share = (
    100
    - residential_share
)


print(
    f"Residential share: "
    f"{residential_share:.2f}%"
)

print(
    f"Other property type share: "
    f"{other_share:.2f}%"
)


# -----------------------------
# Save Filtered Dataset
# -----------------------------
filtered_output = (
    REPORTS_DIR
    / "sold_eda_filtered.csv"
)


sold.to_csv(
    filtered_output,
    index=False
)


print(
    f"\nFiltered dataset saved to: "
    f"{filtered_output}"
)


# -----------------------------
# Field Classification
# -----------------------------
CORE_FIELDS = {
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'LivingArea',
    'LotSizeAcres',
    'BedroomsTotal',
    'BathroomsTotalInteger',
    'DaysOnMarket',
    'YearBuilt',
    'PropertyType',
    'PropertySubType',
    'CountyOrParish',
    'City',
    'PostalCode',
    'Latitude',
    'Longitude',
    'CloseDate',
    'ListingContractDate',
    'PurchaseContractDate',
    'ContractStatusChangeDate',
    'ListingKey',
    'ListingId'
}


METADATA_FIELDS = {
    'ListAgentFirstName',
    'ListAgentLastName',
    'ListAgentFullName',
    'ListAgentEmail',
    'CoListAgentFirstName',
    'CoListAgentLastName',
    'BuyerAgentFirstName',
    'BuyerAgentLastName',
    'BuyerAgentMlsId',
    'CoBuyerAgentFirstName',
    'ListOfficeName',
    'BuyerOfficeName',
    'CoListOfficeName',
    'BuyerOfficeAOR',
    'BuyerAgentAOR',
    'ListAgentAOR',
    'OriginatingSystemName',
    'OriginatingSystemSubName',
    'ListingKeyNumeric',
    'MlsStatus',
    'StreetNumberNumeric'
}


def classify_fields(columns):

    rows = []

    for col in columns:

        if col in METADATA_FIELDS:
            category = 'metadata'

        elif col in CORE_FIELDS:
            category = 'market_analysis_core'

        else:
            category = 'market_analysis_other'

        rows.append({
            'column': col,
            'category': category
        })

    return pd.DataFrame(rows)


field_classification = classify_fields(
    sold.columns
)


field_classification.to_csv(
    REPORTS_DIR
    / "field_classification.csv",
    index=False
)


print(
    "\nField classification saved."
)


# -----------------------------
# Missing Value Analysis
# -----------------------------
missing_count = (
    sold.isnull().sum()
)


missing_pct = (
    missing_count
    / len(sold)
    * 100
)


missing_summary = pd.DataFrame({
    'column': sold.columns,
    'missing_count': missing_count.values,
    'missing_pct': missing_pct.values
})


missing_summary[
    'over_90_pct_missing'
] = (
    missing_summary[
        'missing_pct'
    ] > 90
)


def missing_recommendation(row):

    if row['missing_pct'] > 90:

        if row['column'] in CORE_FIELDS:
            return 'retain_core_review'

        return 'drop_candidate'

    return 'retain'


missing_summary[
    'recommendation'
] = (
    missing_summary.apply(
        missing_recommendation,
        axis=1
    )
)


missing_summary = (
    missing_summary
    .sort_values(
        'missing_pct',
        ascending=False
    )
)


print("\nNull-count summary:")

print(
    missing_summary[
        [
            'column',
            'missing_count',
            'missing_pct'
        ]
    ]
)


print(
    "\nColumns with more than "
    "90% missing:"
)

print(
    missing_summary[
        missing_summary[
            'over_90_pct_missing'
        ]
    ]
)


missing_summary.to_csv(
    REPORTS_DIR
    / "missing_value_report_sold.csv",
    index=False
)


print(
    "\nMissing value report saved."
)


# -----------------------------
# Numeric Distribution Review
# -----------------------------
numeric_cols = [
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'LivingArea',
    'LotSizeAcres',
    'BedroomsTotal',
    'BathroomsTotalInteger',
    'DaysOnMarket',
    'YearBuilt'
]


# Convert safely to numeric
for col in numeric_cols:

    if col in sold.columns:

        sold[col] = pd.to_numeric(
            sold[col],
            errors='coerce'
        )


distribution_rows = []


for col in numeric_cols:

    if col not in sold.columns:
        continue

    series = (
        sold[col]
        .dropna()
    )

    if series.empty:
        continue


    distribution_rows.append({
        'field': col,
        'count': int(series.count()),
        'missing_count':
            int(sold[col].isnull().sum()),
        'min': series.min(),
        'max': series.max(),
        'mean': series.mean(),
        'median': series.median(),
        'p05': series.quantile(.05),
        'p25': series.quantile(.25),
        'p50': series.quantile(.50),
        'p75': series.quantile(.75),
        'p95': series.quantile(.95)
    })


distribution_summary = pd.DataFrame(
    distribution_rows
)


print(
    "\nNumeric distribution summary:"
)

print(
    distribution_summary
)


distribution_summary.to_csv(
    REPORTS_DIR
    / "numeric_distribution_summary.csv",
    index=False
)


# -----------------------------
# Outlier Review and Visualizations
# -----------------------------
outlier_rows = []


for col in numeric_cols:

    if col not in sold.columns:
        continue

    series = (
        sold[col]
        .dropna()
    )

    if series.empty:
        continue


    q1 = (
        series.quantile(.25)
    )

    q3 = (
        series.quantile(.75)
    )

    iqr = (
        q3
        - q1
    )


    lower_bound = (
        q1
        - 1.5 * iqr
    )

    upper_bound = (
        q3
        + 1.5 * iqr
    )


    low_outliers = (
        series
        < lower_bound
    ).sum()


    high_outliers = (
        series
        > upper_bound
    ).sum()


    total_outliers = (
        low_outliers
        + high_outliers
    )


    outlier_rows.append({
        'field': col,
        'iqr_lower_bound':
            lower_bound,
        'iqr_upper_bound':
            upper_bound,
        'low_outlier_count':
            int(low_outliers),
        'high_outlier_count':
            int(high_outliers),
        'total_outlier_count':
            int(total_outliers),
        'outlier_pct':
            total_outliers
            / len(series)
            * 100,
        'minimum_value':
            series.min(),
        'maximum_value':
            series.max()
    })


    # Remove IQR outliers from plots only
    # Original data remains unchanged
    filtered = series[
        (series >= lower_bound)
        & (series <= upper_bound)
    ]


    # Histogram
    plt.figure(
        figsize=(9, 5)
    )

    plt.hist(
        filtered,
        bins=50
    )

    plt.title(
        f'Histogram - {col}\n'
        '(IQR outliers excluded from visualization)'
    )

    plt.xlabel(col)

    plt.ylabel(
        'Count'
    )

    plt.tight_layout()


    plt.savefig(
        VIZ_DIR
        / f"{col}_histogram.png"
    )


    plt.close()


    # Boxplot
    plt.figure(
        figsize=(9, 4)
    )


    plt.boxplot(
        filtered,
        orientation='horizontal'
    )


    plt.title(
        f'Boxplot - {col}\n'
        '(IQR outliers excluded from visualization)'
    )


    plt.xlabel(col)

    plt.tight_layout()


    plt.savefig(
        VIZ_DIR
        / f"{col}_boxplot.png"
    )


    plt.close()


outlier_report = pd.DataFrame(
    outlier_rows
)


outlier_report.to_csv(
    REPORTS_DIR
    / "numeric_outlier_report.csv",
    index=False
)


print(
    "\nOutlier report and visualizations saved."
)


# -----------------------------
# Suggested EDA Questions
# -----------------------------
print(
    "\n--- EDA Questions ---"
)


# 1. Residential vs other property types
print(
    f"\nResidential property share: "
    f"{residential_share:.2f}%"
)


print(
    f"Other property type share: "
    f"{other_share:.2f}%"
)


# 2. Median and average close price
median_close_price = (
    sold[
        'ClosePrice'
    ].median()
)


average_close_price = (
    sold[
        'ClosePrice'
    ].mean()
)


print(
    f"\nMedian close price: "
    f"${median_close_price:,.2f}"
)


print(
    f"Average close price: "
    f"${average_close_price:,.2f}"
)


# -----------------------------
# 3. Days on Market
# -----------------------------
print(
    "\nDays on Market summary:"
)


print(
    sold[
        'DaysOnMarket'
    ].describe(
        percentiles=[
            .05,
            .25,
            .50,
            .75,
            .95
        ]
    )
)


# -----------------------------
# 4. Above vs Below List Price
# -----------------------------
valid_prices = sold.dropna(
    subset=[
        'ClosePrice',
        'ListPrice'
    ]
).copy()


valid_prices[
    'priceDiff'
] = (
    valid_prices[
        'ClosePrice'
    ]
    - valid_prices[
        'ListPrice'
    ]
)


valid_total = len(
    valid_prices
)


if valid_total > 0:

    above = (
        valid_prices[
            'priceDiff'
        ] > 0
    ).sum()


    below = (
        valid_prices[
            'priceDiff'
        ] < 0
    ).sum()


    equal = (
        valid_prices[
            'priceDiff'
        ] == 0
    ).sum()


    print(
        f"\nSold above list price: "
        f"{above / valid_total * 100:.2f}%"
    )


    print(
        f"Sold below list price: "
        f"{below / valid_total * 100:.2f}%"
    )


    print(
        f"Sold at list price: "
        f"{equal / valid_total * 100:.2f}%"
    )


else:

    print(
        "\nNo valid ClosePrice/ListPrice "
        "pairs available."
    )


# -----------------------------
# 5. Date Consistency
# -----------------------------
date_cols = [
    'ListingContractDate',
    'PurchaseContractDate',
    'CloseDate'
]


print(
    "\nSample date values:"
)


print(
    sold[
        date_cols
    ].head(10)
)


listing_date = pd.to_datetime(
    sold[
        'ListingContractDate'
    ],
    errors='coerce'
)


purchase_date = pd.to_datetime(
    sold[
        'PurchaseContractDate'
    ],
    errors='coerce'
)


close_date = pd.to_datetime(
    sold[
        'CloseDate'
    ],
    errors='coerce'
)


date_missing_summary = pd.DataFrame({
    'date_field': [
        'ListingContractDate',
        'PurchaseContractDate',
        'CloseDate'
    ],

    'missing_or_invalid': [
        listing_date.isnull().sum(),
        purchase_date.isnull().sum(),
        close_date.isnull().sum()
    ]
})


print(
    "\nMissing or invalid dates:"
)

print(
    date_missing_summary
)


close_before_listing = (
    close_date
    < listing_date
).sum()


close_before_purchase = (
    close_date
    < purchase_date
).sum()


print(
    f"\nCloseDate before "
    f"ListingContractDate: "
    f"{close_before_listing:,}"
)


print(
    f"CloseDate before "
    f"PurchaseContractDate: "
    f"{close_before_purchase:,}"
)


# -----------------------------
# 6. Counties With Highest Median Prices
# -----------------------------
county_summary = (
    sold
    .dropna(
        subset=[
            'CountyOrParish',
            'ClosePrice'
        ]
    )
    .groupby(
        'CountyOrParish',
        as_index=False
    )
    .agg(
        count=(
            'ClosePrice',
            'count'
        ),
        median=(
            'ClosePrice',
            'median'
        )
    )
)


# Require at least 50 sales
county_summary = (
    county_summary[
        county_summary[
            'count'
        ] >= 50
    ]
    .sort_values(
        'median',
        ascending=False
    )
)


print(
    "\nTop 10 counties by median "
    "close price (minimum 50 sales):"
)


print(
    county_summary.head(10)
)


county_summary.to_csv(
    REPORTS_DIR
    / "county_price_summary.csv",
    index=False
)


print(
    "\nWeeks 2-3 EDA complete."
)


print(
    "Reports saved to:",
    REPORTS_DIR
)