'''
Weeks 2-3 – Mortgage Rate Enrichment

Purpose:
Fetch the national 30-year fixed mortgage rate from FRED,
resample weekly observations to monthly averages, and merge
the monthly mortgage rate onto both sold and listings datasets.
'''

import pandas as pd
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


REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# -----------------------------
# Load Combined Residential Datasets
# -----------------------------
sold = pd.read_csv(
    RAW_DIR
    / "sold_combined.csv",
    low_memory=False
)


listings = pd.read_csv(
    RAW_DIR
    / "listings_combined.csv",
    low_memory=False
)


print(
    "Sold shape:",
    sold.shape
)

print(
    "Listings shape:",
    listings.shape
)


# -----------------------------
# Step 1 – Fetch Mortgage Rate Data
# -----------------------------
url = (
    "https://fred.stlouisfed.org/"
    "graph/fredgraph.csv?id=MORTGAGE30US"
)


mortgage = pd.read_csv(
    url,
    parse_dates=[
        'observation_date'
    ]
)


mortgage.columns = [
    'date',
    'rate_30yr_fixed'
]


# Ensure rates are numeric
mortgage[
    'rate_30yr_fixed'
] = pd.to_numeric(
    mortgage[
        'rate_30yr_fixed'
    ],
    errors='coerce'
)


print(
    f"\nMortgage data fetched: "
    f"{len(mortgage):,} weekly records"
)


print(
    mortgage.tail()
)


# -----------------------------
# Step 2 – Weekly to Monthly Average
# -----------------------------
mortgage[
    'year_month'
] = (
    mortgage[
        'date'
    ]
    .dt
    .to_period('M')
)


mortgage_monthly = (
    mortgage
    .groupby(
        'year_month'
    )[
        'rate_30yr_fixed'
    ]
    .mean()
    .reset_index()
)


print(
    f"\nMortgage data resampled to "
    f"{len(mortgage_monthly):,} "
    f"monthly records"
)


print(
    mortgage_monthly.tail()
)


# -----------------------------
# Step 3 – Create Matching Keys
# -----------------------------

# Sold dataset uses CloseDate
sold[
    'CloseDate'
] = pd.to_datetime(
    sold[
        'CloseDate'
    ],
    errors='coerce'
)


sold[
    'year_month'
] = (
    sold[
        'CloseDate'
    ]
    .dt
    .to_period('M')
)


# Listings dataset uses ListingContractDate
listings[
    'ListingContractDate'
] = pd.to_datetime(
    listings[
        'ListingContractDate'
    ],
    errors='coerce'
)


listings[
    'year_month'
] = (
    listings[
        'ListingContractDate'
    ]
    .dt
    .to_period('M')
)


print(
    "\nMissing/invalid sold CloseDate values:",
    sold[
        'CloseDate'
    ]
    .isnull()
    .sum()
)


print(
    "Missing/invalid listing "
    "ListingContractDate values:",
    listings[
        'ListingContractDate'
    ]
    .isnull()
    .sum()
)


# -----------------------------
# Step 4 – Merge Mortgage Rates
# -----------------------------
sold_with_rates = sold.merge(
    mortgage_monthly,
    on='year_month',
    how='left'
)


listings_with_rates = listings.merge(
    mortgage_monthly,
    on='year_month',
    how='left'
)


# -----------------------------
# Step 5 – Validate Merge
# -----------------------------
sold_null_rates = (
    sold_with_rates[
        'rate_30yr_fixed'
    ]
    .isnull()
    .sum()
)


listings_null_rates = (
    listings_with_rates[
        'rate_30yr_fixed'
    ]
    .isnull()
    .sum()
)


print(
    f"\nNull mortgage rate values "
    f"after merge (Sold): "
    f"{sold_null_rates:,}"
)


print(
    f"Null mortgage rate values "
    f"after merge (Listings): "
    f"{listings_null_rates:,}"
)


if (
    sold_null_rates == 0
    and listings_null_rates == 0
):

    print(
        "\nValidation passed — "
        "no null mortgage rate values!"
    )


else:

    print(
        "\nWarning — some rows did not "
        "match a mortgage rate."
    )


    if sold_null_rates > 0:

        print(
            "\nSold year_month values "
            "with missing mortgage rates:"
        )


        print(
            sold_with_rates.loc[
                sold_with_rates[
                    'rate_30yr_fixed'
                ].isnull(),
                'year_month'
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
        )


    if listings_null_rates > 0:

        print(
            "\nListing year_month values "
            "with missing mortgage rates:"
        )


        print(
            listings_with_rates.loc[
                listings_with_rates[
                    'rate_30yr_fixed'
                ].isnull(),
                'year_month'
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
        )


# -----------------------------
# Preview Merged Data
# -----------------------------
print(
    "\nPreview of merged sold dataset:"
)


print(
    sold_with_rates[
        [
            'CloseDate',
            'year_month',
            'ClosePrice',
            'rate_30yr_fixed'
        ]
    ]
    .head()
)


print(
    "\nPreview of merged listings dataset:"
)


print(
    listings_with_rates[
        [
            'ListingContractDate',
            'year_month',
            'ListPrice',
            'rate_30yr_fixed'
        ]
    ]
    .head()
)


# -----------------------------
# Save Enriched Datasets
# -----------------------------
sold_output = (
    REPORTS_DIR
    / "sold_with_rates.csv"
)


listings_output = (
    REPORTS_DIR
    / "listings_with_rates.csv"
)


sold_with_rates.to_csv(
    sold_output,
    index=False
)


listings_with_rates.to_csv(
    listings_output,
    index=False
)


print(
    "\nEnriched datasets saved:"
)


print(
    sold_output
)

print(
    listings_output
)