'''
Weeks 4-5 – Data Cleaning and Preparation

Purpose:
Clean and prepare the mortgage-enriched CRMLS sold and listings datasets for
analysis. This script converts date and numeric fields to appropriate types,
removes unnecessary and highly-missing non-core columns, flags invalid values,
replaces objectively impossible numeric values with missing values, checks
transaction date consistency, and adds geographic quality flags.

Date inconsistencies are flagged rather than overwritten because the correct
source date cannot be determined from the record alone.
'''

import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

REPORTS_DIR = Path(
    r"C:\Users\khush\Desktop\IDX-Exchange\Reports"
)

CLEANING_REPORT_DIR = (
    REPORTS_DIR / "Week4_5_Cleaning"
)

CLEANING_REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD ENRICHED DATASETS
# ============================================================

sold = pd.read_csv(
    REPORTS_DIR / "sold_with_rates.csv",
    low_memory=False
)

listings = pd.read_csv(
    REPORTS_DIR / "listings_with_rates.csv",
    low_memory=False
)


print("=== Starting Shapes ===")

print(
    f"Sold: {sold.shape[0]:,} rows x "
    f"{sold.shape[1]} columns"
)

print(
    f"Listings: {listings.shape[0]:,} rows x "
    f"{listings.shape[1]} columns"
)


starting_sold_shape = sold.shape
starting_listings_shape = listings.shape


# ============================================================
# STEP 1 – CONVERT DATE FIELDS
# ============================================================

DATE_FIELDS = [
    'CloseDate',
    'PurchaseContractDate',
    'ListingContractDate',
    'ContractStatusChangeDate'
]


def convert_dates(df, dataset_name):

    rows = []

    for col in DATE_FIELDS:

        if col in df.columns:

            missing_before = (
                df[col]
                .isnull()
                .sum()
            )

            df[col] = pd.to_datetime(
                df[col],
                errors='coerce'
            )

            missing_after = (
                df[col]
                .isnull()
                .sum()
            )

            rows.append({
                'dataset': dataset_name,
                'field': col,
                'status': 'converted',
                'dtype_after': str(df[col].dtype),
                'missing_before': int(missing_before),
                'missing_after': int(missing_after)
            })

        else:

            rows.append({
                'dataset': dataset_name,
                'field': col,
                'status': 'column_not_found',
                'dtype_after': None,
                'missing_before': None,
                'missing_after': None
            })

    return pd.DataFrame(rows)


sold_date_report = convert_dates(
    sold,
    'sold'
)

listings_date_report = convert_dates(
    listings,
    'listings'
)


date_conversion_report = pd.concat(
    [
        sold_date_report,
        listings_date_report
    ],
    ignore_index=True
)


date_conversion_report.to_csv(
    CLEANING_REPORT_DIR
    / "date_conversion_report.csv",
    index=False
)


print(
    "\nDate fields converted."
)


# ============================================================
# STEP 2 – CONVERT NUMERIC FIELDS
# ============================================================

NUMERIC_FIELDS = [
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'LivingArea',
    'LotSizeAcres',
    'BedroomsTotal',
    'BathroomsTotalInteger',
    'DaysOnMarket',
    'YearBuilt',
    'Latitude',
    'Longitude',
    'AssociationFee',
    'ParkingTotal',
    'GarageSpaces',
    'rate_30yr_fixed'
]


def convert_numeric_fields(
    df,
    dataset_name
):

    rows = []

    for col in NUMERIC_FIELDS:

        if col in df.columns:

            missing_before = (
                df[col]
                .isnull()
                .sum()
            )

            df[col] = pd.to_numeric(
                df[col],
                errors='coerce'
            )

            missing_after = (
                df[col]
                .isnull()
                .sum()
            )

            rows.append({
                'dataset': dataset_name,
                'field': col,
                'status': 'converted',
                'dtype_after': str(df[col].dtype),
                'missing_before':
                    int(missing_before),
                'missing_after':
                    int(missing_after)
            })

        else:

            rows.append({
                'dataset': dataset_name,
                'field': col,
                'status': 'column_not_found',
                'dtype_after': None,
                'missing_before': None,
                'missing_after': None
            })

    return pd.DataFrame(rows)


sold_numeric_report = (
    convert_numeric_fields(
        sold,
        'sold'
    )
)

listings_numeric_report = (
    convert_numeric_fields(
        listings,
        'listings'
    )
)


numeric_conversion_report = pd.concat(
    [
        sold_numeric_report,
        listings_numeric_report
    ],
    ignore_index=True
)


numeric_conversion_report.to_csv(
    CLEANING_REPORT_DIR
    / "numeric_conversion_report.csv",
    index=False
)


print(
    "Numeric fields converted."
)


# ============================================================
# STEP 3 – ADD MONTH / YEAR FIELDS
# ============================================================

# Sold analysis uses CloseDate.
if 'CloseDate' in sold.columns:

    sold['Month'] = (
        sold['CloseDate']
        .dt.month
    )

    sold['Year'] = (
        sold['CloseDate']
        .dt.year
    )


# Listings analysis uses ListingContractDate.
if 'ListingContractDate' in listings.columns:

    listings['Month'] = (
        listings[
            'ListingContractDate'
        ]
        .dt.month
    )

    listings['Year'] = (
        listings[
            'ListingContractDate'
        ]
        .dt.year
    )


# ============================================================
# STEP 4 – SAFELY REMOVE VERIFIED .1 DUPLICATE COLUMNS
# ============================================================

def remove_duplicate_dot1_columns(df, dataset_name):

    dropped = []

    for col in df.columns:

        if not col.endswith('.1'):
            continue

        original_col = col[:-2]

        if original_col not in df.columns:
            print(
                f"WARNING: {dataset_name} has {col}, "
                f"but original column {original_col} was not found."
            )
            continue

        # Compare values while treating missing values
        # in the same positions as equal.
        original = df[original_col]
        duplicate = df[col]

        same_values = (
            original.eq(duplicate)
            | (original.isna() & duplicate.isna())
        ).all()

        if same_values:
            dropped.append(col)

        else:
            differing_rows = ~(
                original.eq(duplicate)
                | (original.isna() & duplicate.isna())
            )

            print(
                f"WARNING: {dataset_name} column {col} "
                f"differs from {original_col} in "
                f"{differing_rows.sum():,} rows. "
                f"It was NOT dropped."
            )

    df = df.drop(
        columns=dropped,
        errors='ignore'
    )

    return df, dropped


sold, sold_dot1 = (
    remove_duplicate_dot1_columns(
        sold,
        'sold'
    )
)


listings, listings_dot1 = (
    remove_duplicate_dot1_columns(
        listings,
        'listings'
    )
)


print(
    f"\nVerified .1 duplicates "
    f"removed from sold: "
    f"{len(sold_dot1)}"
)

print(
    f"Verified .1 duplicates "
    f"removed from listings: "
    f"{len(listings_dot1)}"
)


# ============================================================
# STEP 5 – HIGH-MISSING COLUMN REVIEW
# ============================================================

# Core analytical fields should not be removed
# automatically solely due to missingness.

PROTECTED_FIELDS = {
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
    'PurchaseContractDate',
    'ListingContractDate',
    'ContractStatusChangeDate',

    'ListingKey',

    'rate_30yr_fixed',

    # Possible later feature engineering
    'ElementarySchool',
    'MiddleOrJuniorSchool',
    'HighSchool',
    'HighSchoolDistrict'
}


def build_missing_report(
    df,
    dataset_name
):

    missing_count = (
        df.isnull()
        .sum()
    )

    missing_pct = (
        missing_count
        / len(df)
        * 100
    )


    report = pd.DataFrame({
        'dataset': dataset_name,
        'column': df.columns,
        'missing_count':
            missing_count.values,
        'missing_pct':
            missing_pct.values
    })


    report[
        'over_90_pct_missing'
    ] = (
        report[
            'missing_pct'
        ] > 90
    )


    report[
        'protected_field'
    ] = (
        report[
            'column'
        ]
        .isin(
            PROTECTED_FIELDS
        )
    )


    def recommendation(row):

        if (
            row[
                'over_90_pct_missing'
            ]
            and row[
                'protected_field'
            ]
        ):

            return 'retain_core'

        if row[
            'over_90_pct_missing'
        ]:

            return 'drop'

        return 'retain'


    report[
        'recommendation'
    ] = (
        report.apply(
            recommendation,
            axis=1
        )
    )


    return (
        report.sort_values(
            'missing_pct',
            ascending=False
        )
    )


sold_missing_report = (
    build_missing_report(
        sold,
        'sold'
    )
)

listings_missing_report = (
    build_missing_report(
        listings,
        'listings'
    )
)


combined_missing_report = pd.concat(
    [
        sold_missing_report,
        listings_missing_report
    ],
    ignore_index=True
)


combined_missing_report.to_csv(
    CLEANING_REPORT_DIR
    / "missing_value_report.csv",
    index=False
)


sold_high_missing_drop = (
    sold_missing_report.loc[
        (
            sold_missing_report[
                'over_90_pct_missing'
            ]
        )
        &
        (
            ~sold_missing_report[
                'protected_field'
            ]
        ),
        'column'
    ]
    .tolist()
)


listings_high_missing_drop = (
    listings_missing_report.loc[
        (
            listings_missing_report[
                'over_90_pct_missing'
            ]
        )
        &
        (
            ~listings_missing_report[
                'protected_field'
            ]
        ),
        'column'
    ]
    .tolist()
)


sold = sold.drop(
    columns=sold_high_missing_drop,
    errors='ignore'
)

listings = listings.drop(
    columns=listings_high_missing_drop,
    errors='ignore'
)


print(
    f"\nSold >90% missing columns dropped: "
    f"{len(sold_high_missing_drop)}"
)

print(
    f"Listings >90% missing columns dropped: "
    f"{len(listings_high_missing_drop)}"
)


# ============================================================
# STEP 6 – DROP REDUNDANT / UNNECESSARY COLUMNS
# ============================================================

REDUNDANT_COLUMNS = [
    'ListingKeyNumeric',
    'ListingId',

    # Keep LotSizeAcres as standardized lot-size field
    'LotSizeArea',
    'LotSizeSquareFeet',

    # Administrative/system metadata
    'OriginatingSystemName',
    'OriginatingSystemSubName',

    'StreetNumberNumeric',

    # Compensation fields
    'BuyerAgencyCompensationType',
    'BuyerAgencyCompensation',

    # Co-agent fields not needed for current analysis
    'CoListAgentFirstName',
    'CoListAgentLastName',
    'CoBuyerAgentFirstName',

    # Already filtered to Residential
    'PropertyType'
]


def drop_redundant_columns(df):

    existing = [
        col
        for col in REDUNDANT_COLUMNS
        if col in df.columns
    ]

    df = df.drop(
        columns=existing,
        errors='ignore'
    )

    return df, existing


sold, sold_redundant = (
    drop_redundant_columns(
        sold
    )
)

listings, listings_redundant = (
    drop_redundant_columns(
        listings
    )
)


print(
    f"\nRedundant columns removed "
    f"from sold: "
    f"{len(sold_redundant)}"
)

print(
    f"Redundant columns removed "
    f"from listings: "
    f"{len(listings_redundant)}"
)


# ============================================================
# STEP 7 – FLAG + CLEAN INVALID NUMERIC VALUES
# ============================================================

# Required cleaning rules:
#
# ClosePrice <= 0
# LivingArea <= 0
# DaysOnMarket < 0
# BedroomsTotal < 0
# BathroomsTotalInteger < 0
#
# We first preserve a boolean flag showing that the original
# value was invalid. The impossible numeric value is then
# replaced with NaN so it cannot distort later calculations.


def flag_and_clean_invalid_numeric(
    df,
    include_close_price=False
):

    cleaning_counts = {}


    # -----------------------------
    # ClosePrice
    # -----------------------------
    if (
        include_close_price
        and 'ClosePrice' in df.columns
    ):

        df[
            'invalid_close_price_flag'
        ] = (
            df[
                'ClosePrice'
            ]
            .le(0)
            .fillna(False)
        )


        count = int(
            df[
                'invalid_close_price_flag'
            ]
            .sum()
        )


        cleaning_counts[
            'invalid_close_price_flag'
        ] = count


        df.loc[
            df[
                'invalid_close_price_flag'
            ],
            'ClosePrice'
        ] = pd.NA


    # -----------------------------
    # LivingArea
    # -----------------------------
    if 'LivingArea' in df.columns:

        df[
            'invalid_living_area_flag'
        ] = (
            df[
                'LivingArea'
            ]
            .le(0)
            .fillna(False)
        )


        count = int(
            df[
                'invalid_living_area_flag'
            ]
            .sum()
        )


        cleaning_counts[
            'invalid_living_area_flag'
        ] = count


        df.loc[
            df[
                'invalid_living_area_flag'
            ],
            'LivingArea'
        ] = pd.NA


    # -----------------------------
    # DaysOnMarket
    # -----------------------------
    if 'DaysOnMarket' in df.columns:

        df[
            'negative_days_on_market_flag'
        ] = (
            df[
                'DaysOnMarket'
            ]
            .lt(0)
            .fillna(False)
        )


        count = int(
            df[
                'negative_days_on_market_flag'
            ]
            .sum()
        )


        cleaning_counts[
            'negative_days_on_market_flag'
        ] = count


        df.loc[
            df[
                'negative_days_on_market_flag'
            ],
            'DaysOnMarket'
        ] = pd.NA


    # -----------------------------
    # Bedrooms
    # -----------------------------
    if 'BedroomsTotal' in df.columns:

        df[
            'negative_bedrooms_flag'
        ] = (
            df[
                'BedroomsTotal'
            ]
            .lt(0)
            .fillna(False)
        )


        count = int(
            df[
                'negative_bedrooms_flag'
            ]
            .sum()
        )


        cleaning_counts[
            'negative_bedrooms_flag'
        ] = count


        df.loc[
            df[
                'negative_bedrooms_flag'
            ],
            'BedroomsTotal'
        ] = pd.NA


    # -----------------------------
    # Bathrooms
    # -----------------------------
    if (
        'BathroomsTotalInteger'
        in df.columns
    ):

        df[
            'negative_bathrooms_flag'
        ] = (
            df[
                'BathroomsTotalInteger'
            ]
            .lt(0)
            .fillna(False)
        )


        count = int(
            df[
                'negative_bathrooms_flag'
            ]
            .sum()
        )


        cleaning_counts[
            'negative_bathrooms_flag'
        ] = count


        df.loc[
            df[
                'negative_bathrooms_flag'
            ],
            'BathroomsTotalInteger'
        ] = pd.NA


    return cleaning_counts


sold_numeric_cleaning = (
    flag_and_clean_invalid_numeric(
        sold,
        include_close_price=True
    )
)


listings_numeric_cleaning = (
    flag_and_clean_invalid_numeric(
        listings,
        include_close_price=False
    )
)


print(
    "\n=== Invalid Numeric Cleaning (Sold) ==="
)

for flag, count in (
    sold_numeric_cleaning.items()
):

    print(
        f"{flag}: {count:,}"
    )


print(
    "\n=== Invalid Numeric Cleaning (Listings) ==="
)

for flag, count in (
    listings_numeric_cleaning.items()
):

    print(
        f"{flag}: {count:,}"
    )


# ============================================================
# STEP 8 – DATE CONSISTENCY FLAGS
# ============================================================

# Expected sequence:
#
# ListingContractDate
#        <=
# PurchaseContractDate
#        <=
# CloseDate
#
# Dates are NOT overwritten because an inconsistency tells us
# a problem exists but does not tell us which source date is
# incorrect.


if {
    'ListingContractDate',
    'CloseDate'
}.issubset(
    sold.columns
):

    sold[
        'listing_after_close_flag'
    ] = (
        sold[
            'ListingContractDate'
        ].notna()
        &
        sold[
            'CloseDate'
        ].notna()
        &
        (
            sold[
                'ListingContractDate'
            ]
            >
            sold[
                'CloseDate'
            ]
        )
    )

else:

    sold[
        'listing_after_close_flag'
    ] = False


if {
    'PurchaseContractDate',
    'CloseDate'
}.issubset(
    sold.columns
):

    sold[
        'purchase_after_close_flag'
    ] = (
        sold[
            'PurchaseContractDate'
        ].notna()
        &
        sold[
            'CloseDate'
        ].notna()
        &
        (
            sold[
                'PurchaseContractDate'
            ]
            >
            sold[
                'CloseDate'
            ]
        )
    )

else:

    sold[
        'purchase_after_close_flag'
    ] = False


if {
    'ListingContractDate',
    'PurchaseContractDate'
}.issubset(
    sold.columns
):

    purchase_before_listing = (
        sold[
            'ListingContractDate'
        ].notna()
        &
        sold[
            'PurchaseContractDate'
        ].notna()
        &
        (
            sold[
                'PurchaseContractDate'
            ]
            <
            sold[
                'ListingContractDate'
            ]
        )
    )

else:

    purchase_before_listing = (
        pd.Series(
            False,
            index=sold.index
        )
    )


# Overall timeline violation flag
sold[
    'negative_timeline_flag'
] = (
    sold[
        'listing_after_close_flag'
    ]
    |
    sold[
        'purchase_after_close_flag'
    ]
    |
    purchase_before_listing
)


print(
    "\n=== Date Consistency Flags (Sold) ==="
)

print(
    "Listing after close:",
    int(
        sold[
            'listing_after_close_flag'
        ]
        .sum()
    )
)

print(
    "Purchase after close:",
    int(
        sold[
            'purchase_after_close_flag'
        ]
        .sum()
    )
)

print(
    "Purchase before listing:",
    int(
        purchase_before_listing.sum()
    )
)

print(
    "Any negative timeline:",
    int(
        sold[
            'negative_timeline_flag'
        ]
        .sum()
    )
)


# ============================================================
# STEP 9 – GEOGRAPHIC QUALITY FLAGS
# ============================================================

CA_MIN_LAT = 32
CA_MAX_LAT = 42

CA_MIN_LON = -125
CA_MAX_LON = -114


def add_geographic_flags(df):

    if (
        'Latitude' not in df.columns
        or
        'Longitude' not in df.columns
    ):

        return


    latitude = (
        df[
            'Latitude'
        ]
    )

    longitude = (
        df[
            'Longitude'
        ]
    )


    # Missing either coordinate
    df[
        'missing_coordinate_flag'
    ] = (
        latitude.isna()
        |
        longitude.isna()
    )


    # Placeholder zero values
    df[
        'zero_coordinate_flag'
    ] = (
        latitude.eq(0)
        |
        longitude.eq(0)
    )


    # California longitude should be negative
    df[
        'positive_longitude_flag'
    ] = (
        longitude.gt(0)
        .fillna(False)
    )


    # Only evaluate geographic bounds
    # when both coordinates exist.
    df[
        'out_of_bounds_flag'
    ] = (
        latitude.notna()
        &
        longitude.notna()
        &
        (
            ~latitude.between(
                CA_MIN_LAT,
                CA_MAX_LAT,
                inclusive='both'
            )
            |
            ~longitude.between(
                CA_MIN_LON,
                CA_MAX_LON,
                inclusive='both'
            )
        )
    )


    if (
        'StateOrProvince'
        in df.columns
    ):

        state = (
            df[
                'StateOrProvince'
            ]
            .fillna('')
            .astype(str)
            .str.strip()
            .str.upper()
        )


        # Missing state is kept for review.
        # Only explicit non-California states
        # are marked out-of-state.
        df[
            'out_of_state_flag'
        ] = (
            ~state.isin(
                [
                    '',
                    'CA',
                    'CALIFORNIA'
                ]
            )
        )


add_geographic_flags(
    sold
)

add_geographic_flags(
    listings
)


# ============================================================
# STEP 10 – DATA QUALITY FLAG SUMMARY
# ============================================================

def create_flag_summary(
    df,
    dataset_name
):

    flag_cols = [
        col
        for col in df.columns
        if col.endswith(
            '_flag'
        )
    ]


    rows = []


    for col in flag_cols:

        flagged_count = int(
            df[col]
            .sum()
        )


        flagged_pct = (
            flagged_count
            / len(df)
            * 100
        )


        rows.append({
            'dataset':
                dataset_name,
            'flag':
                col,
            'flagged_count':
                flagged_count,
            'flagged_pct':
                flagged_pct
        })


    return pd.DataFrame(
        rows
    )


sold_flag_summary = (
    create_flag_summary(
        sold,
        'sold'
    )
)


listings_flag_summary = (
    create_flag_summary(
        listings,
        'listings'
    )
)


flag_summary = pd.concat(
    [
        sold_flag_summary,
        listings_flag_summary
    ],
    ignore_index=True
)


flag_summary.to_csv(
    CLEANING_REPORT_DIR
    / "flag_summary.csv",
    index=False
)


print(
    "\n=== Data Quality Flag Summary ==="
)

print(
    flag_summary
)


# ============================================================
# STEP 11 – DROPPED COLUMN REPORT
# ============================================================

dropped_rows = []


for col in sold_dot1:

    dropped_rows.append({
        'dataset':
            'sold',
        'column':
            col,
        'reason':
            'verified_duplicate_dot1'
    })


for col in listings_dot1:

    dropped_rows.append({
        'dataset':
            'listings',
        'column':
            col,
        'reason':
            'verified_duplicate_dot1'
    })


for col in sold_high_missing_drop:

    dropped_rows.append({
        'dataset':
            'sold',
        'column':
            col,
        'reason':
            'over_90_pct_missing'
    })


for col in listings_high_missing_drop:

    dropped_rows.append({
        'dataset':
            'listings',
        'column':
            col,
        'reason':
            'over_90_pct_missing'
    })


for col in sold_redundant:

    dropped_rows.append({
        'dataset':
            'sold',
        'column':
            col,
        'reason':
            'redundant_or_unnecessary'
    })


for col in listings_redundant:

    dropped_rows.append({
        'dataset':
            'listings',
        'column':
            col,
        'reason':
            'redundant_or_unnecessary'
    })


dropped_columns_report = pd.DataFrame(
    dropped_rows
)


dropped_columns_report.to_csv(
    CLEANING_REPORT_DIR
    / "dropped_columns.csv",
    index=False
)


# ============================================================
# STEP 12 – INVALID NUMERIC CLEANING REPORT
# ============================================================

numeric_cleaning_rows = []


for flag, count in (
    sold_numeric_cleaning.items()
):

    numeric_cleaning_rows.append({
        'dataset':
            'sold',
        'flag':
            flag,
        'values_replaced_with_null':
            count
    })


for flag, count in (
    listings_numeric_cleaning.items()
):

    numeric_cleaning_rows.append({
        'dataset':
            'listings',
        'flag':
            flag,
        'values_replaced_with_null':
            count
    })


numeric_cleaning_report = pd.DataFrame(
    numeric_cleaning_rows
)


numeric_cleaning_report.to_csv(
    CLEANING_REPORT_DIR
    / "invalid_numeric_cleaning.csv",
    index=False
)


# ============================================================
# STEP 13 – FINAL DTYPE CONFIRMATION
# ============================================================

fields_to_confirm = (
    DATE_FIELDS
    + NUMERIC_FIELDS
)


dtype_rows = []


for dataset_name, df in [
    ('sold', sold),
    ('listings', listings)
]:

    for col in fields_to_confirm:

        if col in df.columns:

            dtype_rows.append({
                'dataset':
                    dataset_name,
                'field':
                    col,
                'dtype_after_cleaning':
                    str(
                        df[col].dtype
                    )
            })


dtype_confirmation = pd.DataFrame(
    dtype_rows
)


dtype_confirmation.to_csv(
    CLEANING_REPORT_DIR
    / "dtype_confirmation.csv",
    index=False
)


# ============================================================
# STEP 14 – CLEANING SUMMARY
# ============================================================

cleaning_summary = pd.DataFrame({
    'dataset': [
        'sold',
        'listings'
    ],

    'rows_before': [
        starting_sold_shape[0],
        starting_listings_shape[0]
    ],

    'rows_after': [
        len(sold),
        len(listings)
    ],

    'columns_before': [
        starting_sold_shape[1],
        starting_listings_shape[1]
    ],

    'columns_after': [
        sold.shape[1],
        listings.shape[1]
    ],

    'rows_removed': [
        starting_sold_shape[0]
        - len(sold),

        starting_listings_shape[0]
        - len(listings)
    ],

    'high_missing_columns_dropped': [
        len(
            sold_high_missing_drop
        ),

        len(
            listings_high_missing_drop
        )
    ],

    'redundant_columns_dropped': [
        len(
            sold_redundant
        )
        + len(
            sold_dot1
        ),

        len(
            listings_redundant
        )
        + len(
            listings_dot1
        )
    ]
})


cleaning_summary.to_csv(
    CLEANING_REPORT_DIR
    / "cleaning_summary.csv",
    index=False
)


# ============================================================
# STEP 15 – SAVE CLEANED DATASETS
# ============================================================

sold_output = (
    REPORTS_DIR
    / "sold_cleaned.csv"
)


listings_output = (
    REPORTS_DIR
    / "listings_cleaned.csv"
)


sold.to_csv(
    sold_output,
    index=False
)


listings.to_csv(
    listings_output,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n=== Final Shapes ==="
)

print(
    f"Sold: "
    f"{sold.shape[0]:,} rows x "
    f"{sold.shape[1]} columns"
)

print(
    f"Listings: "
    f"{listings.shape[0]:,} rows x "
    f"{listings.shape[1]} columns"
)


print(
    "\nRows removed: 0"
)

print(
    "Objectively impossible numeric "
    "values were replaced with NaN."
)

print(
    "Original invalid-value flags were "
    "retained for documentation."
)

print(
    "Date inconsistencies were flagged "
    "but dates were not overwritten."
)


print(
    "\nCleaned datasets saved:"
)

print(
    sold_output
)

print(
    listings_output
)


print(
    "\nCleaning reports saved to:"
)

print(
    CLEANING_REPORT_DIR
)