'''
Week 7 – Outlier Detection and Final Data Quality

Purpose:
Identify statistically extreme records using the Interquartile Range (IQR)
method while preserving the full dataset for auditability.

This script:
- loads the Week 6 feature-engineered sold dataset
- compares 1.5x and 3.0x IQR thresholds
- applies 3.0x IQR flags to ClosePrice, LivingArea, and DaysOnMarket
- creates a combined IQR outlier flag
- audits engineered metrics such as price_per_sqft and price ratios
- identifies suspicious low ClosePrice records
- standardizes ZIP codes for Tableau
- identifies geography inconsistencies using coordinates
- preserves all records in a full flagged dataset
- creates a separate Tableau-ready filtered dataset
- compares dataset size and summary statistics before vs. after filtering

The 3.0x multiplier is used for final IQR filtering because California
housing data is strongly right-skewed and the standard 1.5x rule may classify
legitimate luxury properties as outliers.

Final Tableau exclusions:
1. 3.0x IQR outliers in ClosePrice, LivingArea, or DaysOnMarket
2. suspicious extremely low ClosePrice / OriginalListPrice combinations
3. records with coordinates clearly outside California

Rows are NOT removed simply because:
- StateOrProvince is incorrect
- coordinates are missing
- PostalCode is malformed

Those issues are instead flagged so potentially valid California transactions
are not unnecessarily discarded.
'''

import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

REPORTS_DIR = Path(
    r"C:\Users\khush\Desktop\IDX-Exchange\Reports"
)

WEEK7_REPORT_DIR = (
    REPORTS_DIR / "Week7_Outlier_Detection"
)

WEEK7_REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


INPUT_FILE = (
    REPORTS_DIR / "sold_features.csv"
)

FLAGGED_FILE = (
    REPORTS_DIR / "sold_flagged.csv"
)

FILTERED_FILE = (
    REPORTS_DIR / "sold_filtered.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# Handbook-required IQR fields
IQR_FIELDS = [
    'ClosePrice',
    'LivingArea',
    'DaysOnMarket'
]


# Final IQR multiplier selected after comparing 1.5x vs 3.0x
FINAL_IQR_MULTIPLIER = 3.0


# Engineered fields reviewed for extreme values,
# but NOT automatically included in the IQR removal union
AUDIT_FIELDS = [
    'price_per_sqft',
    'sale_to_list_ratio',
    'close_to_original_list_ratio'
]


# Suspicious price review rule
LOW_CLOSE_PRICE_REVIEW_THRESHOLD = 50_000
LOW_RATIO_REVIEW_THRESHOLD = 0.10


# Broad California bounding box used only as a final
# geographic quality screen for Tableau.
CA_MIN_LAT = 32
CA_MAX_LAT = 42
CA_MIN_LON = -125
CA_MAX_LON = -114


# ============================================================
# LOAD WEEK 6 DATA
# ============================================================

sold = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)


print("=== Starting Dataset ===")

print(
    f"Sold: {sold.shape[0]:,} rows x "
    f"{sold.shape[1]} columns"
)


# ============================================================
# STEP 1 – VALIDATE / CONVERT REQUIRED NUMERIC FIELDS
# ============================================================

required_numeric_fields = (
    IQR_FIELDS
    + AUDIT_FIELDS
    + [
        'Latitude',
        'Longitude'
    ]
)


for col in required_numeric_fields:

    if col not in sold.columns:

        raise ValueError(
            f"Required Week 7 column missing: {col}"
        )

    sold[col] = pd.to_numeric(
        sold[col],
        errors='coerce'
    )


# ============================================================
# STEP 2 – BASELINE DISTRIBUTIONS
# ============================================================

print(
    "\n=== Baseline Distribution "
    "(Before Outlier Filtering) ==="
)


baseline_summary = (
    sold[
        IQR_FIELDS
        + AUDIT_FIELDS
    ]
    .describe(
        percentiles=[
            .01,
            .05,
            .25,
            .50,
            .75,
            .95,
            .99
        ]
    )
    .T
)


print(
    baseline_summary
)


baseline_summary.to_csv(
    WEEK7_REPORT_DIR
    / "baseline_distribution.csv"
)


# ============================================================
# STEP 3 – IQR BOUNDS FUNCTION
# ============================================================

def calculate_iqr_bounds(
    series,
    multiplier
):

    clean_series = (
        pd.to_numeric(
            series,
            errors='coerce'
        )
        .dropna()
    )


    q1 = clean_series.quantile(
        0.25
    )

    q3 = clean_series.quantile(
        0.75
    )

    iqr = (
        q3
        - q1
    )


    lower_bound = (
        q1
        - multiplier * iqr
    )

    upper_bound = (
        q3
        + multiplier * iqr
    )


    return (
        q1,
        q3,
        iqr,
        lower_bound,
        upper_bound
    )


# ============================================================
# STEP 4 – COMPARE 1.5x VS 3.0x IQR
# ============================================================

print(
    "\n=== Comparison: "
    "1.5x vs 3.0x IQR ==="
)


comparison_rows = []


for col in IQR_FIELDS:

    for multiplier in [
        1.5,
        3.0
    ]:

        (
            q1,
            q3,
            iqr,
            lower,
            upper
        ) = calculate_iqr_bounds(
            sold[col],
            multiplier
        )


        flagged = (
            (
                sold[col]
                < lower
            )
            |
            (
                sold[col]
                > upper
            )
        ).fillna(False)


        flagged_count = int(
            flagged.sum()
        )


        flagged_pct = (
            flagged_count
            / len(sold)
            * 100
        )


        comparison_rows.append({
            'field':
                col,

            'multiplier':
                multiplier,

            'q1':
                q1,

            'q3':
                q3,

            'iqr':
                iqr,

            'lower_bound':
                lower,

            'upper_bound':
                upper,

            'flagged_count':
                flagged_count,

            'flagged_pct':
                flagged_pct
        })


        print(
            f"{col} ({multiplier}x): "
            f"lower={lower:,.2f}, "
            f"upper={upper:,.2f}, "
            f"flagged={flagged_count:,} "
            f"({flagged_pct:.2f}%)"
        )


    print()


iqr_multiplier_comparison = pd.DataFrame(
    comparison_rows
)


iqr_multiplier_comparison.to_csv(
    WEEK7_REPORT_DIR
    / "iqr_multiplier_comparison.csv",
    index=False
)


# ============================================================
# STEP 5 – APPLY FINAL 3.0x IQR FLAGS
# ============================================================

print(
    "\n=== Final IQR Flags "
    f"({FINAL_IQR_MULTIPLIER}x) ==="
)


final_iqr_rows = []
iqr_flag_columns = []


for col in IQR_FIELDS:

    (
        q1,
        q3,
        iqr,
        lower,
        upper
    ) = calculate_iqr_bounds(
        sold[col],
        FINAL_IQR_MULTIPLIER
    )


    flag_col = (
        f"{col.lower()}_iqr_outlier_flag"
    )


    sold[
        flag_col
    ] = (
        (
            sold[col]
            < lower
        )
        |
        (
            sold[col]
            > upper
        )
    ).fillna(False)


    iqr_flag_columns.append(
        flag_col
    )


    flagged_count = int(
        sold[
            flag_col
        ].sum()
    )


    flagged_pct = (
        flagged_count
        / len(sold)
        * 100
    )


    final_iqr_rows.append({
        'field':
            col,

        'multiplier':
            FINAL_IQR_MULTIPLIER,

        'q1':
            q1,

        'q3':
            q3,

        'iqr':
            iqr,

        'lower_bound':
            lower,

        'upper_bound':
            upper,

        'flagged_count':
            flagged_count,

        'flagged_pct':
            flagged_pct
    })


    print(
        f"{col}: "
        f"lower={lower:,.2f}, "
        f"upper={upper:,.2f}, "
        f"flagged={flagged_count:,} "
        f"({flagged_pct:.2f}%)"
    )


# Combined IQR flag
sold[
    'iqr_outlier_any_flag'
] = (
    sold[
        iqr_flag_columns
    ]
    .any(
        axis=1
    )
)


combined_iqr_count = int(
    sold[
        'iqr_outlier_any_flag'
    ].sum()
)


combined_iqr_pct = (
    combined_iqr_count
    / len(sold)
    * 100
)


print(
    "\nRecords flagged by at least "
    "one required IQR field:"
)

print(
    f"{combined_iqr_count:,} "
    f"({combined_iqr_pct:.2f}%)"
)


final_iqr_report = pd.DataFrame(
    final_iqr_rows
)


final_iqr_report.to_csv(
    WEEK7_REPORT_DIR
    / "final_iqr_thresholds.csv",
    index=False
)


# ============================================================
# STEP 6 – AUDIT ENGINEERED METRICS
# ============================================================

print(
    "\n=== Engineered Metric Outlier Audit ==="
)


audit_rows = []


for col in AUDIT_FIELDS:

    (
        q1,
        q3,
        iqr,
        lower,
        upper
    ) = calculate_iqr_bounds(
        sold[col],
        FINAL_IQR_MULTIPLIER
    )


    flagged = (
        (
            sold[col]
            < lower
        )
        |
        (
            sold[col]
            > upper
        )
    ).fillna(False)


    flagged_count = int(
        flagged.sum()
    )


    flagged_pct = (
        flagged_count
        / len(sold)
        * 100
    )


    audit_rows.append({
        'field':
            col,

        'multiplier':
            FINAL_IQR_MULTIPLIER,

        'lower_bound':
            lower,

        'upper_bound':
            upper,

        'flagged_count':
            flagged_count,

        'flagged_pct':
            flagged_pct,

        'minimum':
            sold[col].min(),

        'maximum':
            sold[col].max()
    })


    print(
        f"{col}: "
        f"lower={lower:,.4f}, "
        f"upper={upper:,.4f}, "
        f"flagged={flagged_count:,} "
        f"({flagged_pct:.2f}%)"
    )


engineered_metric_audit = pd.DataFrame(
    audit_rows
)


engineered_metric_audit.to_csv(
    WEEK7_REPORT_DIR
    / "engineered_metric_outlier_audit.csv",
    index=False
)


# ============================================================
# STEP 7 – SUSPICIOUS LOW CLOSE PRICE FLAG
# ============================================================

# These records were reviewed separately.
#
# Very low absolute ClosePrice +
# very low ClosePrice / OriginalListPrice ratio
# strongly suggests a corrupted sale price.
#
# We do NOT guess the correct ClosePrice.
# The row remains in sold_flagged.csv but is excluded from
# the Tableau-ready sold_filtered.csv.

sold[
    'suspicious_low_close_price_flag'
] = (
    (
        sold[
            'ClosePrice'
        ]
        <
        LOW_CLOSE_PRICE_REVIEW_THRESHOLD
    )
    &
    (
        sold[
            'close_to_original_list_ratio'
        ]
        <
        LOW_RATIO_REVIEW_THRESHOLD
    )
).fillna(False)


low_price_review_count = int(
    sold[
        'suspicious_low_close_price_flag'
    ].sum()
)


print(
    "\n=== Suspicious Low Price Review ==="
)


print(
    f"Rows with ClosePrice < "
    f"${LOW_CLOSE_PRICE_REVIEW_THRESHOLD:,} "
    f"and close/original ratio < "
    f"{LOW_RATIO_REVIEW_THRESHOLD:.0%}: "
    f"{low_price_review_count:,}"
)


suspicious_low_price_rows = sold[
    sold[
        'suspicious_low_close_price_flag'
    ]
].copy()


suspicious_review_columns = [
    'ListingKey',
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'sale_to_list_ratio',
    'close_to_original_list_ratio',
    'PropertySubType',
    'CountyOrParish',
    'City',
    'PostalCode',
    'Latitude',
    'Longitude'
]


suspicious_review_columns = [
    col
    for col in suspicious_review_columns
    if col
    in suspicious_low_price_rows.columns
]


suspicious_low_price_rows[
    suspicious_review_columns
].to_csv(
    WEEK7_REPORT_DIR
    / "suspicious_low_price_review.csv",
    index=False
)


# ============================================================
# STEP 8 – STANDARDIZE POSTAL CODE
# ============================================================

print(
    "\n=== Postal Code Quality ==="
)


if 'PostalCode' in sold.columns:

    postal_raw = (
        sold[
            'PostalCode'
        ]
        .astype('string')
        .str.strip()
    )


    # Valid formats:
    # 94538
    # 94538-1234
    #
    # PostalCode5 retains only the five-digit ZIP.
    sold[
        'PostalCode5'
    ] = (
        postal_raw
        .str.extract(
            r'^(\d{5})(?:-\d{4})?$',
            expand=False
        )
    )


    # Flag non-null ZIP values that cannot be standardized.
    sold[
        'malformed_postal_code_flag'
    ] = (
        postal_raw.notna()
        &
        sold[
            'PostalCode5'
        ].isna()
    )


    malformed_zip_count = int(
        sold[
            'malformed_postal_code_flag'
        ].sum()
    )


    print(
        f"Malformed PostalCode values: "
        f"{malformed_zip_count:,}"
    )


else:

    sold[
        'PostalCode5'
    ] = pd.NA

    sold[
        'malformed_postal_code_flag'
    ] = False


# Save malformed ZIP records for audit
postal_review_columns = [
    'ListingKey',
    'PostalCode',
    'PostalCode5',
    'City',
    'CountyOrParish',
    'StateOrProvince',
    'Latitude',
    'Longitude'
]


postal_review_columns = [
    col
    for col in postal_review_columns
    if col in sold.columns
]


sold.loc[
    sold[
        'malformed_postal_code_flag'
    ],
    postal_review_columns
].to_csv(
    WEEK7_REPORT_DIR
    / "malformed_postal_code_review.csv",
    index=False
)


# ============================================================
# STEP 9 – FINAL CALIFORNIA GEOGRAPHY QUALITY
# ============================================================

print(
    "\n=== California Geography Quality ==="
)


latitude = sold[
    'Latitude'
]

longitude = sold[
    'Longitude'
]


coords_present = (
    latitude.notna()
    &
    longitude.notna()
)


coordinates_inside_california = (
    coords_present
    &
    latitude.between(
        CA_MIN_LAT,
        CA_MAX_LAT,
        inclusive='both'
    )
    &
    longitude.between(
        CA_MIN_LON,
        CA_MAX_LON,
        inclusive='both'
    )
)


# A row is confirmed outside California only when
# BOTH coordinates are available and those coordinates
# clearly fall outside the broad California bounds.
#
# Missing coordinates alone do NOT cause exclusion.
sold[
    'confirmed_outside_california_flag'
] = (
    coords_present
    &
    ~coordinates_inside_california
)


# ------------------------------------------------------------
# State / Coordinate mismatch
# ------------------------------------------------------------

if 'StateOrProvince' in sold.columns:

    normalized_state = (
        sold[
            'StateOrProvince'
        ]
        .astype('string')
        .str.strip()
        .str.upper()
    )


    explicit_non_ca_state = (
        normalized_state.notna()
        &
        ~normalized_state.isin(
            [
                '',
                'CA',
                'CALIFORNIA'
            ]
        )
    )


    # Keep these rows if coordinates clearly place
    # the property inside California.
    sold[
        'state_coordinate_mismatch_flag'
    ] = (
        coordinates_inside_california
        &
        explicit_non_ca_state
    )


else:

    sold[
        'state_coordinate_mismatch_flag'
    ] = False


confirmed_outside_count = int(
    sold[
        'confirmed_outside_california_flag'
    ].sum()
)


state_mismatch_count = int(
    sold[
        'state_coordinate_mismatch_flag'
    ].sum()
)


print(
    f"Confirmed outside California "
    f"by coordinates: "
    f"{confirmed_outside_count:,}"
)


print(
    f"Non-CA state label but "
    f"California coordinates: "
    f"{state_mismatch_count:,}"
)


# ------------------------------------------------------------
# Create a clean Tableau state field
# ------------------------------------------------------------

# If coordinates confirm the property is in California,
# use CA for analysis even if StateOrProvince was miscoded.
#
# Otherwise retain the normalized source value.

if 'StateOrProvince' in sold.columns:

    normalized_state = (
        sold[
            'StateOrProvince'
        ]
        .astype('string')
        .str.strip()
        .str.upper()
    )


    sold[
        'StateForAnalysis'
    ] = normalized_state


    sold.loc[
        coordinates_inside_california,
        'StateForAnalysis'
    ] = 'CA'


else:

    sold[
        'StateForAnalysis'
    ] = pd.NA


# Save geography problems for review
geography_review_columns = [
    'ListingKey',
    'StateOrProvince',
    'StateForAnalysis',
    'PostalCode',
    'PostalCode5',
    'City',
    'CountyOrParish',
    'Latitude',
    'Longitude',
    'confirmed_outside_california_flag',
    'state_coordinate_mismatch_flag'
]


geography_review_columns = [
    col
    for col in geography_review_columns
    if col in sold.columns
]


sold.loc[
    (
        sold[
            'confirmed_outside_california_flag'
        ]
        |
        sold[
            'state_coordinate_mismatch_flag'
        ]
    ),
    geography_review_columns
].to_csv(
    WEEK7_REPORT_DIR
    / "geography_quality_review.csv",
    index=False
)


# ============================================================
# STEP 10 – SAVE FULL FLAGGED DATASET
# ============================================================

# Every row is preserved here.
sold.to_csv(
    FLAGGED_FILE,
    index=False
)


print(
    "\nFull flagged dataset saved:"
)

print(
    FLAGGED_FILE
)

print(
    f"{sold.shape[0]:,} rows x "
    f"{sold.shape[1]} columns"
)


# ============================================================
# STEP 11 – CREATE FINAL TABLEAU-READY DATASET
# ============================================================

# Exclude only records that have a strong reason
# not to represent typical California market behavior:
#
# 1. required-field IQR outlier
# 2. reviewed suspicious low ClosePrice
# 3. coordinates clearly outside California
#
# DO NOT exclude:
#
# - state-coordinate mismatch where coordinates are in CA
# - malformed ZIP alone
# - missing coordinates
#
# Those rows may still contain valid California sales data.

tableau_exclude = (
    sold[
        'iqr_outlier_any_flag'
    ]
    |
    sold[
        'suspicious_low_close_price_flag'
    ]
    |
    sold[
        'confirmed_outside_california_flag'
    ]
)


sold_filtered = sold[
    ~tableau_exclude
].copy()


sold_filtered.to_csv(
    FILTERED_FILE,
    index=False
)


print(
    "\n=== Final Tableau Filtering ==="
)


print(
    f"IQR outliers: "
    f"{sold['iqr_outlier_any_flag'].sum():,}"
)


print(
    f"Suspicious low ClosePrice: "
    f"{sold['suspicious_low_close_price_flag'].sum():,}"
)


print(
    f"Confirmed outside California: "
    f"{sold['confirmed_outside_california_flag'].sum():,}"
)


print(
    "Total excluded after overlap: "
    f"{tableau_exclude.sum():,}"
)


print(
    "\nClean Tableau-ready dataset saved:"
)

print(
    FILTERED_FILE
)

print(
    f"{sold_filtered.shape[0]:,} rows x "
    f"{sold_filtered.shape[1]} columns"
)


# ============================================================
# STEP 12 – BEFORE VS AFTER COMPARISON
# ============================================================

comparison_metrics = [
    'ClosePrice',
    'LivingArea',
    'DaysOnMarket',
    'price_per_sqft',
    'sale_to_list_ratio',
    'close_to_original_list_ratio'
]


comparison_output = []


for col in comparison_metrics:

    before_median = (
        sold[col]
        .median()
    )

    after_median = (
        sold_filtered[col]
        .median()
    )


    before_mean = (
        sold[col]
        .mean()
    )

    after_mean = (
        sold_filtered[col]
        .mean()
    )


    comparison_output.append({
        'metric':
            col,

        'before_median':
            before_median,

        'after_median':
            after_median,

        'median_change':
            (
                after_median
                - before_median
            ),

        'before_mean':
            before_mean,

        'after_mean':
            after_mean,

        'mean_change':
            (
                after_mean
                - before_mean
            )
    })


before_after_metrics = pd.DataFrame(
    comparison_output
)


row_comparison = pd.DataFrame({
    'metric': [
        'row_count'
    ],

    'before_median': [
        len(sold)
    ],

    'after_median': [
        len(sold_filtered)
    ],

    'median_change': [
        len(sold_filtered)
        - len(sold)
    ],

    'before_mean': [
        pd.NA
    ],

    'after_mean': [
        pd.NA
    ],

    'mean_change': [
        pd.NA
    ]
})


before_after_report = pd.concat(
    [
        row_comparison,
        before_after_metrics
    ],
    ignore_index=True
)


before_after_report.to_csv(
    WEEK7_REPORT_DIR
    / "before_after_comparison.csv",
    index=False
)


# ============================================================
# STEP 13 – PRINT WRITTEN COMPARISON
# ============================================================

rows_removed = (
    len(sold)
    - len(sold_filtered)
)


rows_removed_pct = (
    rows_removed
    / len(sold)
    * 100
)


print(
    "\n=== Before vs After Filtering ==="
)


print(
    f"Rows before: "
    f"{len(sold):,}"
)


print(
    f"Rows after: "
    f"{len(sold_filtered):,}"
)


print(
    f"Rows removed: "
    f"{rows_removed:,} "
    f"({rows_removed_pct:.2f}%)"
)


print(
    "\nMedian ClosePrice:"
)

print(
    f"Before: "
    f"${sold['ClosePrice'].median():,.0f}"
)

print(
    f"After: "
    f"${sold_filtered['ClosePrice'].median():,.0f}"
)


print(
    "\nMedian LivingArea:"
)

print(
    f"Before: "
    f"{sold['LivingArea'].median():,.0f}"
)

print(
    f"After: "
    f"{sold_filtered['LivingArea'].median():,.0f}"
)


print(
    "\nMedian DaysOnMarket:"
)

print(
    f"Before: "
    f"{sold['DaysOnMarket'].median():,.0f}"
)

print(
    f"After: "
    f"{sold_filtered['DaysOnMarket'].median():,.0f}"
)


print(
    "\nMean ClosePrice:"
)

print(
    f"Before: "
    f"${sold['ClosePrice'].mean():,.0f}"
)

print(
    f"After: "
    f"${sold_filtered['ClosePrice'].mean():,.0f}"
)


# ============================================================
# STEP 14 – FINAL FLAG SUMMARY
# ============================================================

flag_columns_to_report = (
    iqr_flag_columns
    + [
        'iqr_outlier_any_flag',
        'suspicious_low_close_price_flag',
        'malformed_postal_code_flag',
        'confirmed_outside_california_flag',
        'state_coordinate_mismatch_flag'
    ]
)


flag_summary_rows = []


for flag_col in flag_columns_to_report:

    flagged_count = int(
        sold[
            flag_col
        ].sum()
    )


    flag_summary_rows.append({
        'flag':
            flag_col,

        'flagged_count':
            flagged_count,

        'flagged_pct':
            (
                flagged_count
                / len(sold)
                * 100
            )
    })


flag_summary = pd.DataFrame(
    flag_summary_rows
)


flag_summary.to_csv(
    WEEK7_REPORT_DIR
    / "outlier_and_quality_flag_summary.csv",
    index=False
)


# ============================================================
# STEP 15 – FINAL QUALITY SUMMARY
# ============================================================

quality_summary = pd.DataFrame({
    'metric': [
        'starting_rows',
        'final_tableau_rows',
        'rows_excluded_total',
        'iqr_outlier_rows',
        'suspicious_low_price_rows',
        'confirmed_outside_california_rows',
        'malformed_postal_code_rows',
        'state_coordinate_mismatch_rows',
        'rows_with_missing_coordinates'
    ],

    'count': [
        len(sold),
        len(sold_filtered),
        int(
            tableau_exclude.sum()
        ),
        int(
            sold[
                'iqr_outlier_any_flag'
            ].sum()
        ),
        int(
            sold[
                'suspicious_low_close_price_flag'
            ].sum()
        ),
        int(
            sold[
                'confirmed_outside_california_flag'
            ].sum()
        ),
        int(
            sold[
                'malformed_postal_code_flag'
            ].sum()
        ),
        int(
            sold[
                'state_coordinate_mismatch_flag'
            ].sum()
        ),
        int(
            (
                sold[
                    'Latitude'
                ].isna()
                |
                sold[
                    'Longitude'
                ].isna()
            ).sum()
        )
    ]
})


quality_summary.to_csv(
    WEEK7_REPORT_DIR
    / "final_quality_summary.csv",
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print(
    "\n=== Week 7 Complete ==="
)


print(
    "\nFull audit dataset:"
)

print(
    FLAGGED_FILE
)


print(
    "\nFinal Tableau dataset:"
)

print(
    FILTERED_FILE
)


print(
    "\nReports saved to:"
)

print(
    WEEK7_REPORT_DIR
)