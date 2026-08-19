import pandas as pd
import os
import re


folder = r"C:\Users\khush\idx files"


# Function to choose one file per month
# Prefers the _filled version if both regular and _filled exist
def get_monthly_files(folder, prefix):
    all_files = [
        f for f in os.listdir(folder)
        if f.startswith(prefix) and f.endswith('.csv')
    ]

    monthly_files = {}

    for f in all_files:
        match = re.search(rf'{prefix}(\d{{6}})', f)

        if match:
            month = match.group(1)

            if month not in monthly_files:
                monthly_files[month] = f

            # Prefer _filled version if available
            elif '_filled' in f:
                monthly_files[month] = f

    return sorted(monthly_files.values())


# Getting one file per month
listing_files = get_monthly_files(
    folder,
    'CRMLSListing'
)

sold_files = get_monthly_files(
    folder,
    'CRMLSSold'
)


print(f"Listing files found: {len(listing_files)}")
print(f"Sold files found: {len(sold_files)}")


# -----------------------------
# Load Sold Files
# -----------------------------
sold_dfs = []

for f in sold_files:

    file_path = os.path.join(
        folder,
        f
    )

    df = pd.read_csv(
        file_path,
        low_memory=False
    )

    # _filled files contain additional latitude/longitude fields
    df = df.drop(
        columns=[
            'latfilled',
            'lonfilled'
        ],
        errors='ignore'
    )

    print(
        f"Loaded {f}: "
        f"{len(df):,} rows"
    )

    sold_dfs.append(df)


if not sold_dfs:
    raise ValueError(
        "No sold files were found."
    )


sold = pd.concat(
    sold_dfs,
    ignore_index=True,
    sort=False
)


print(
    f"\nTotal sold rows before filter: "
    f"{len(sold):,}"
)


# -----------------------------
# Load Listing Files
# -----------------------------
listing_dfs = []

for f in listing_files:

    file_path = os.path.join(
        folder,
        f
    )

    df = pd.read_csv(
        file_path,
        low_memory=False
    )

    df = df.drop(
        columns=[
            'latfilled',
            'lonfilled'
        ],
        errors='ignore'
    )

    print(
        f"Loaded {f}: "
        f"{len(df):,} rows"
    )

    listing_dfs.append(df)


if not listing_dfs:
    raise ValueError(
        "No listing files were found."
    )


listings = pd.concat(
    listing_dfs,
    ignore_index=True,
    sort=False
)


print(
    f"\nTotal listing rows before filter: "
    f"{len(listings):,}"
)


# -----------------------------
# Save Unfiltered Combined Files
# -----------------------------
# These are useful for Weeks 2-3 so we can examine
# all property types before filtering to Residential.

sold_all_output = os.path.join(
    folder,
    'sold_all_combined.csv'
)

listings_all_output = os.path.join(
    folder,
    'listings_all_combined.csv'
)


sold.to_csv(
    sold_all_output,
    index=False
)

listings.to_csv(
    listings_all_output,
    index=False
)


print("\nSaved unfiltered combined files:")
print(sold_all_output)
print(listings_all_output)


# -----------------------------
# Validate PropertyType
# -----------------------------
if 'PropertyType' not in sold.columns:
    raise ValueError(
        "PropertyType column missing from sold data."
    )


if 'PropertyType' not in listings.columns:
    raise ValueError(
        "PropertyType column missing from listing data."
    )


# -----------------------------
# Filter Residential
# -----------------------------
sold_residential = sold[
    sold['PropertyType']
    .astype(str)
    .str.strip()
    .eq('Residential')
].copy()


listings_residential = listings[
    listings['PropertyType']
    .astype(str)
    .str.strip()
    .eq('Residential')
].copy()


print(
    f"\nTotal sold rows after Residential filter: "
    f"{len(sold_residential):,}"
)

print(
    f"Total listing rows after Residential filter: "
    f"{len(listings_residential):,}"
)


print(
    f"Sold rows removed: "
    f"{len(sold) - len(sold_residential):,}"
)

print(
    f"Listing rows removed: "
    f"{len(listings) - len(listings_residential):,}"
)


# -----------------------------
# Save Residential Files
# -----------------------------
sold_output = os.path.join(
    folder,
    'sold_combined.csv'
)

listings_output = os.path.join(
    folder,
    'listings_combined.csv'
)


sold_residential.to_csv(
    sold_output,
    index=False
)

listings_residential.to_csv(
    listings_output,
    index=False
)


print("\nSaved Residential files:")
print(sold_output)
print(listings_output)