IDX Exchange – Data Analyst Internship
Intern: Khushi | Program: MLS Analytics & Tableau Dashboard (12-Week)
Progress Tracker

✅ Week 0 – Orientation

Downloaded all CRMLS CSV files from FTP server (CRMLSListing and CRMLSSold files)
Obtained Feb–May 2026 files (202602–202605) from teammates who ran the extraction scripts
Reviewed Trestle Property Metadata for field definitions and data types


✅ Week 1 – Monthly Dataset Aggregation

Loaded all monthly CSV files from January 2024 through May 2026
Handled duplicate _filled files by preferring the filled version per month
Dropped extra columns (latfilled, lonfilled) from _filled files
Concatenated into two combined datasets (sold and listings)
Filtered both datasets to PropertyType == 'Residential' only
Saved as sold_combined.csv and listings_combined.csv

Row counts:
DatasetBefore FilterAfter FilterSold640,526430,716Listings917,740583,650

🔄 Weeks 2–3 – Dataset Structuring and Validation

Inspected dataset shape, column data types, and structure
Identified date columns stored as strings (to be converted in Weeks 4–5)
Performed missing value analysis for both sold and listings datasets
Flagged columns with >90% missing values (15 in sold, 13 in listings)
Decided which columns to drop vs. retain based on analytical importance
Generated numeric distribution summary (min, max, mean, median, percentiles) for key fields
Saved histograms and boxplots for 9 key numeric fields to Reports/ folder

EDA findings:

Median close price: $825,000 | Average: $1.18M (skewed by outliers)
Median days on market: 18 days
40.1% of homes sold above list price, 42.5% below, 17.4% at list price
Top counties by median price: San Mateo ($1.7M), Santa Clara ($1.6M), San Francisco ($1.2M)
Date issues flagged: some CloseDate precedes PurchaseContractDate — to be addressed in Weeks 4–5
Missing dates: PurchaseContractDate has 196 nulls, CloseDate has 0

Still in progress:

Mortgage rate enrichment (FRED API merge) — Week 2–3 continued
