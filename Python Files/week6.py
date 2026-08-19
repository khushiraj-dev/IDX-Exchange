'''
Week 6 – Feature Engineering and Market Metrics

Purpose:
Engineer market metrics from the cleaned sold dataset, assign California school
districts using property latitude and longitude, create segmented market
summaries, and save the final feature-engineered dataset.

Key engineered metrics:
- sale_to_list_ratio
- close_to_original_list_ratio
- price_per_sqft
- DaysOnMarket
- Year
- Month
- YrMo
- listing_to_contract_days
- contract_to_close_days

School district fields:
- school_district_unified
- school_district_elementary
- school_district_high
- school_district

Date inconsistencies from Weeks 4-5 are preserved through the existing flags.
Impossible negative derived timeline values are set to missing so they do not
distort later analytics.
'''

import pandas as pd
import geopandas as gpd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

REPORTS_DIR = Path(
    r"C:\Users\khush\Desktop\IDX-Exchange\Reports"
)

WEEK6_REPORT_DIR = (
    REPORTS_DIR / "Week6_Feature_Engineering"
)

WEEK6_REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


SCHOOL_DISTRICT_FILE = Path(
    r"C:\Users\khush\Desktop\IDX-Exchange\data\DistrictAreas2526_-284845464123469011.geojson"
)


INPUT_FILE = (
    REPORTS_DIR / "sold_cleaned.csv"
)

OUTPUT_FILE = (
    REPORTS_DIR / "sold_features.csv"
)


# ============================================================
# LOAD CLEANED SOLD DATA
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
# STEP 1 – CONFIRM DATE TYPES
# ============================================================

DATE_FIELDS = [
    'CloseDate',
    'PurchaseContractDate',
    'ListingContractDate'
]


for col in DATE_FIELDS:

    if col in sold.columns:

        sold[col] = pd.to_datetime(
            sold[col],
            errors='coerce'
        )


print("\nDate dtypes:")

print(
    sold[
        [
            col
            for col in DATE_FIELDS
            if col in sold.columns
        ]
    ].dtypes
)


# ============================================================
# STEP 2 – CONFIRM NUMERIC TYPES
# ============================================================

NUMERIC_FIELDS = [
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'LivingArea',
    'DaysOnMarket',
    'Latitude',
    'Longitude'
]


for col in NUMERIC_FIELDS:

    if col in sold.columns:

        sold[col] = pd.to_numeric(
            sold[col],
            errors='coerce'
        )


# ============================================================
# STEP 3 – MARKET METRICS
# ============================================================

# ------------------------------------------------------------
# Sale-to-List Ratio
#
# The handbook repeats ClosePrice / OriginalListPrice for both
# "Price Ratio" and "Close to Original List Ratio."
#
# To keep the two measures analytically distinct:
#
# sale_to_list_ratio =
# ClosePrice / current ListPrice
#
# close_to_original_list_ratio =
# ClosePrice / OriginalListPrice
# ------------------------------------------------------------

valid_list_price = (
    sold['ListPrice']
    .notna()
    &
    sold['ListPrice']
    .gt(0)
)


sold['sale_to_list_ratio'] = pd.NA


sold.loc[
    valid_list_price,
    'sale_to_list_ratio'
] = (
    sold.loc[
        valid_list_price,
        'ClosePrice'
    ]
    /
    sold.loc[
        valid_list_price,
        'ListPrice'
    ]
)


sold[
    'sale_to_list_ratio'
] = pd.to_numeric(
    sold[
        'sale_to_list_ratio'
    ],
    errors='coerce'
)


# ------------------------------------------------------------
# Close to Original List Ratio
# ------------------------------------------------------------

valid_original_price = (
    sold[
        'OriginalListPrice'
    ]
    .notna()
    &
    sold[
        'OriginalListPrice'
    ]
    .gt(0)
)


sold[
    'close_to_original_list_ratio'
] = pd.NA


sold.loc[
    valid_original_price,
    'close_to_original_list_ratio'
] = (
    sold.loc[
        valid_original_price,
        'ClosePrice'
    ]
    /
    sold.loc[
        valid_original_price,
        'OriginalListPrice'
    ]
)


sold[
    'close_to_original_list_ratio'
] = pd.to_numeric(
    sold[
        'close_to_original_list_ratio'
    ],
    errors='coerce'
)


# ------------------------------------------------------------
# Price Per Square Foot
# ------------------------------------------------------------

valid_living_area = (
    sold['LivingArea']
    .notna()
    &
    sold['LivingArea']
    .gt(0)
)


sold['price_per_sqft'] = pd.NA


sold.loc[
    valid_living_area,
    'price_per_sqft'
] = (
    sold.loc[
        valid_living_area,
        'ClosePrice'
    ]
    /
    sold.loc[
        valid_living_area,
        'LivingArea'
    ]
)


sold[
    'price_per_sqft'
] = pd.to_numeric(
    sold[
        'price_per_sqft'
    ],
    errors='coerce'
)


# ------------------------------------------------------------
# Days on Market
#
# Already supplied as a raw MLS field.
# Weeks 4-5 cleaned negative values to missing.
# ------------------------------------------------------------

sold[
    'days_on_market'
] = sold[
    'DaysOnMarket'
]


# ============================================================
# STEP 4 – TIME-SERIES FEATURES
# ============================================================

sold['Year'] = (
    sold['CloseDate']
    .dt.year
)


sold['Month'] = (
    sold['CloseDate']
    .dt.month
)


sold['YrMo'] = (
    sold['CloseDate']
    .dt.to_period('M')
    .astype(str)
)


# ============================================================
# STEP 5 – TRANSACTION TIMELINE FEATURES
# ============================================================

sold[
    'listing_to_contract_days'
] = (
    sold[
        'PurchaseContractDate'
    ]
    -
    sold[
        'ListingContractDate'
    ]
).dt.days


sold[
    'contract_to_close_days'
] = (
    sold[
        'CloseDate'
    ]
    -
    sold[
        'PurchaseContractDate'
    ]
).dt.days


# ------------------------------------------------------------
# Derived durations cannot logically be negative.
#
# Keep the original date fields and Week 4-5 flags,
# but set impossible engineered durations to missing.
# ------------------------------------------------------------

negative_listing_to_contract = (
    sold[
        'listing_to_contract_days'
    ]
    .lt(0)
    .fillna(False)
)


negative_contract_to_close = (
    sold[
        'contract_to_close_days'
    ]
    .lt(0)
    .fillna(False)
)


print(
    "\nNegative listing-to-contract values "
    f"set to missing: "
    f"{int(negative_listing_to_contract.sum()):,}"
)


print(
    "Negative contract-to-close values "
    f"set to missing: "
    f"{int(negative_contract_to_close.sum()):,}"
)


sold.loc[
    negative_listing_to_contract,
    'listing_to_contract_days'
] = pd.NA


sold.loc[
    negative_contract_to_close,
    'contract_to_close_days'
] = pd.NA


# ============================================================
# STEP 6 – ENGINEERED METRIC SUMMARY
# ============================================================

metric_cols = [
    'sale_to_list_ratio',
    'close_to_original_list_ratio',
    'price_per_sqft',
    'days_on_market',
    'listing_to_contract_days',
    'contract_to_close_days'
]


metric_summary = (
    sold[
        metric_cols
    ]
    .describe(
        percentiles=[
            .05,
            .25,
            .50,
            .75,
            .95
        ]
    )
    .T
)


metric_summary.to_csv(
    WEEK6_REPORT_DIR
    / "engineered_metric_summary.csv"
)


print(
    "\n=== Engineered Metric Summary ==="
)

print(
    metric_summary
)


# ============================================================
# STEP 7 – SCHOOL DISTRICT SPATIAL JOIN
# ============================================================

print(
    "\n=== School District Mapping ==="
)


if not SCHOOL_DISTRICT_FILE.exists():

    raise FileNotFoundError(
        f"School district file not found: "
        f"{SCHOOL_DISTRICT_FILE}"
    )


school_districts = gpd.read_file(
    SCHOOL_DISTRICT_FILE
)


print(
    "School district rows:",
    len(
        school_districts
    )
)


print(
    "School district columns:"
)

print(
    school_districts
    .columns
    .tolist()
)


print(
    "School district CRS:",
    school_districts.crs
)


# ------------------------------------------------------------
# Identify district-name and district-type fields.
#
# The GeoJSON you previously used contained:
# DistrictName
# DistrictType
# ------------------------------------------------------------

DISTRICT_NAME_COL = (
    'DistrictName'
)

DISTRICT_TYPE_COL = (
    'DistrictType'
)


if (
    DISTRICT_NAME_COL
    not in school_districts.columns
):

    raise ValueError(
        f"{DISTRICT_NAME_COL} not found "
        "in school district dataset."
    )


if (
    DISTRICT_TYPE_COL
    not in school_districts.columns
):

    raise ValueError(
        f"{DISTRICT_TYPE_COL} not found "
        "in school district dataset."
    )


# ------------------------------------------------------------
# Reproject district polygons to property lat/lon CRS.
# ------------------------------------------------------------

school_districts = (
    school_districts
    .to_crs(
        "EPSG:4326"
    )
)


# ------------------------------------------------------------
# Only use coordinates that are present.
#
# Many properties may share the same coordinates,
# especially condos. Spatially join unique coordinates
# once, then merge the district results back.
# ------------------------------------------------------------

valid_coordinate_rows = (
    sold[
        'Latitude'
    ].notna()
    &
    sold[
        'Longitude'
    ].notna()
)


coords = (
    sold.loc[
        valid_coordinate_rows,
        [
            'Latitude',
            'Longitude'
        ]
    ]
    .drop_duplicates()
)


points = gpd.GeoDataFrame(
    coords,
    geometry=gpd.points_from_xy(
        coords[
            'Longitude'
        ],
        coords[
            'Latitude'
        ]
    ),
    crs="EPSG:4326"
)


# ------------------------------------------------------------
# Spatial join against ALL district types.
# ------------------------------------------------------------

district_matches = gpd.sjoin(
    points,
    school_districts[
        [
            DISTRICT_NAME_COL,
            DISTRICT_TYPE_COL,
            'geometry'
        ]
    ],
    how='left',
    predicate='within'
)


# ------------------------------------------------------------
# Review district types found before pivoting.
# ------------------------------------------------------------

print(
    "\nDistrict types found:"
)

print(
    district_matches[
        DISTRICT_TYPE_COL
    ]
    .value_counts(
        dropna=False
    )
)


# ------------------------------------------------------------
# Pivot district type into separate columns.
#
# A property can fall in:
#
# - one Unified district
#
# OR
#
# - one Elementary district
# - one High district
#
# Pivoting keeps one row per property coordinate.
# ------------------------------------------------------------

district_lookup = (
    district_matches
    .pivot_table(
        index=[
            'Latitude',
            'Longitude'
        ],
        columns=
            DISTRICT_TYPE_COL,
        values=
            DISTRICT_NAME_COL,
        aggfunc='first'
    )
    .reset_index()
)


# ------------------------------------------------------------
# Normalize district column names.
# ------------------------------------------------------------

rename_map = {
    'Unified':
        'school_district_unified',

    'Elementary':
        'school_district_elementary',

    'High':
        'school_district_high'
}


district_lookup = (
    district_lookup.rename(
        columns=rename_map
    )
)


# Ensure expected columns exist even if
# a district type is absent from the data.
expected_district_cols = [
    'school_district_unified',
    'school_district_elementary',
    'school_district_high'
]


for col in expected_district_cols:

    if col not in district_lookup.columns:

        district_lookup[col] = pd.NA


# ------------------------------------------------------------
# Merge district information back to sold dataset.
# ------------------------------------------------------------

sold = sold.merge(
    district_lookup[
        [
            'Latitude',
            'Longitude',
            'school_district_unified',
            'school_district_elementary',
            'school_district_high'
        ]
    ],
    on=[
        'Latitude',
        'Longitude'
    ],
    how='left'
)


# ------------------------------------------------------------
# Single simplified district field for Tableau.
#
# If Unified exists, use it.
# Otherwise use Elementary.
#
# High-school district remains available separately.
# ------------------------------------------------------------

sold[
    'school_district'
] = (
    sold[
        'school_district_unified'
    ]
    .fillna(
        sold[
            'school_district_elementary'
        ]
    )
)


district_cols = [
    'school_district_unified',
    'school_district_elementary',
    'school_district_high'
]


matched_any_district = (
    sold[
        district_cols
    ]
    .notna()
    .any(
        axis=1
    )
)


print(
    "\nProperties matched to at least "
    "one school district:"
)

print(
    f"{matched_any_district.sum():,} "
    f"/ {len(sold):,} "
    f"({matched_any_district.mean() * 100:.2f}%)"
)


print(
    "Simplified school_district populated:"
)

print(
    f"{sold['school_district'].notna().sum():,} "
    f"/ {len(sold):,} "
    f"({sold['school_district'].notna().mean() * 100:.2f}%)"
)


# ============================================================
# STEP 8 – SAMPLE ENGINEERED OUTPUT
# ============================================================

sample_columns = [
    'ListingKey',
    'ClosePrice',
    'ListPrice',
    'OriginalListPrice',
    'LivingArea',
    'sale_to_list_ratio',
    'close_to_original_list_ratio',
    'price_per_sqft',
    'DaysOnMarket',
    'Year',
    'Month',
    'YrMo',
    'listing_to_contract_days',
    'contract_to_close_days',
    'school_district',
    'school_district_unified',
    'school_district_elementary',
    'school_district_high'
]


sample_columns = [
    col
    for col in sample_columns
    if col in sold.columns
]


sample_output = (
    sold[
        sample_columns
    ]
    .head(20)
)


print(
    "\n=== Sample Engineered Output ==="
)

print(
    sample_output.to_string(
        index=False
    )
)


sample_output.to_csv(
    WEEK6_REPORT_DIR
    / "sample_engineered_output.csv",
    index=False
)


# ============================================================
# STEP 9 – SEGMENT ANALYSIS
# ============================================================

def build_segment_summary(
    df,
    group_col,
    min_sales=10
):

    if group_col not in df.columns:

        print(
            f"Skipping {group_col}: "
            "column not found."
        )

        return pd.DataFrame()


    summary = (
        df
        .dropna(
            subset=[
                group_col
            ]
        )
        .groupby(
            group_col
        )
        .agg(
            total_sales=(
                'ClosePrice',
                'count'
            ),

            median_close_price=(
                'ClosePrice',
                'median'
            ),

            average_close_price=(
                'ClosePrice',
                'mean'
            ),

            median_days_on_market=(
                'DaysOnMarket',
                'median'
            ),

            median_price_per_sqft=(
                'price_per_sqft',
                'median'
            ),

            median_sale_to_list_ratio=(
                'sale_to_list_ratio',
                'median'
            ),

            median_close_to_original_ratio=(
                'close_to_original_list_ratio',
                'median'
            ),

            median_listing_to_contract_days=(
                'listing_to_contract_days',
                'median'
            ),

            median_contract_to_close_days=(
                'contract_to_close_days',
                'median'
            )
        )
        .reset_index()
    )


    summary = summary[
        summary[
            'total_sales'
        ] >= min_sales
    ]


    return (
        summary
        .sort_values(
            'total_sales',
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


# ------------------------------------------------------------
# Property Subtype
# ------------------------------------------------------------

property_subtype_summary = (
    build_segment_summary(
        sold,
        'PropertySubType',
        min_sales=10
    )
)


# ------------------------------------------------------------
# County
# Require 50 sales for more reliable comparisons.
# ------------------------------------------------------------

county_summary = (
    build_segment_summary(
        sold,
        'CountyOrParish',
        min_sales=50
    )
)


# ------------------------------------------------------------
# MLS Area Major
# ------------------------------------------------------------

mls_area_summary = (
    build_segment_summary(
        sold,
        'MLSAreaMajor',
        min_sales=50
    )
)


# ------------------------------------------------------------
# Listing Office
# ------------------------------------------------------------

list_office_summary = (
    build_segment_summary(
        sold,
        'ListOfficeName',
        min_sales=50
    )
)


# ------------------------------------------------------------
# Buyer Office
# ------------------------------------------------------------

buyer_office_summary = (
    build_segment_summary(
        sold,
        'BuyerOfficeName',
        min_sales=50
    )
)


# ------------------------------------------------------------
# PropertyType
#
# Week 1 already filtered to Residential,
# so this should normally contain only one group.
# Still included because it is listed in the handbook.
# ------------------------------------------------------------

property_type_summary = (
    build_segment_summary(
        sold,
        'PropertyType',
        min_sales=1
    )
)


# ============================================================
# STEP 10 – PRINT KEY SEGMENT RESULTS
# ============================================================

print(
    "\n=== County Summary "
    "(Top 15 by Sales Volume) ==="
)

print(
    county_summary
    .head(15)
    .to_string(
        index=False
    )
)


print(
    "\n=== Property Subtype Summary ==="
)

print(
    property_subtype_summary
    .head(20)
    .to_string(
        index=False
    )
)


print(
    "\n=== Listing Office Summary "
    "(Top 20) ==="
)

print(
    list_office_summary
    .head(20)
    .to_string(
        index=False
    )
)


print(
    "\n=== Buyer Office Summary "
    "(Top 20) ==="
)

print(
    buyer_office_summary
    .head(20)
    .to_string(
        index=False
    )
)


# ============================================================
# STEP 11 – SAVE SEGMENT SUMMARIES
# ============================================================

property_subtype_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_property_subtype.csv",
    index=False
)


county_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_county.csv",
    index=False
)


mls_area_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_mls_area.csv",
    index=False
)


list_office_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_listing_office.csv",
    index=False
)


buyer_office_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_buyer_office.csv",
    index=False
)


property_type_summary.to_csv(
    WEEK6_REPORT_DIR
    / "summary_by_property_type.csv",
    index=False
)


# ============================================================
# STEP 12 – SAVE FINAL FEATURE DATASET
# ============================================================

sold.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\n=== Week 6 Complete ==="
)


print(
    f"Final dataset: "
    f"{sold.shape[0]:,} rows x "
    f"{sold.shape[1]} columns"
)


print(
    "\nSaved feature dataset:"
)

print(
    OUTPUT_FILE
)


print(
    "\nSaved Week 6 reports:"
)

print(
    WEEK6_REPORT_DIR
)