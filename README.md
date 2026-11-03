# Where and when did the GDR invent?

#### Author: Like He

#### Supervisor：Marta Bernardi

#### Start Date:27.10.2026

## I. Work Completed So Far

### 1. Basic Data Cleaning

Created `clean_data.py` to perform basic cleaning of the original dataset, `DDR Patente_Regionaldaten GESIS_final.csv`.

Main operations:

- Preserved missing values and duplicate records without directly deleting them.

- Saved the cleaned results separately while keeping the original dataset unchanged.

- Processed 286,478 records and removed 394,411 instances of leading and trailing whitespace.

### 2. Generation and Analysis of Data Audit Tables

Generated and analyzed 9 CSV audit tables using the data auditing script to examine the completeness and consistency of the original dataset.

Main findings:

- No missing values, formatting errors, or duplicates were found in the complete publication document identifiers (`veroeffentlichungsnummer`).

- Identified 403 records with abnormal links.

### 3. Filtering by Patent Application Date

Modified `01_audit_patent_csv_enhanced.py` to group patent records according to their application dates (`anmeldedatum`).

The selected period is 1950-01-01 to 1990-10-02, including both start and end dates.

| Data Category                   | Number of Records |
|---------------------------------|-------------------|
| Original dataset                | 286,478           |
| Within the selected date range  | 281,852           |
| Outside the selected date range | 4,625             |
| Invalid application date        | 1                 |

Records outside the selected range and records with invalid application dates were saved separately rather than deleted.

The subsequent analysis uses the 281,852 records within the selected period.

### 4. Examination of Date-Related Data Issues

Further examined patent application dates (`anmeldedatum`) and publication dates (`veroeffentlichungsdatum`).

The following issues were identified:

| Issue | Count | Status |
|----|----|----|
| Invalid application date | 1 | the original scan is folded and the date cannot be identified |
| NULL publication dates | 18 | some source documents are missing, while others can be identified and require manual correction |
| Publication date earlier than application date | 23 | Pending individual verification |
| Application date within the selected range but publication date after the cutoff date | 21,943 | Retained because filtering is based on application dates |

### 5. Correction of Abnormal Patent Links

Examined the abnormal links identified during the audit and corrected 4 patent document records and 6 link fields.

| Patent Publication Number (`veroeffentlichungsnummer`) | Correction |
|----|----|
| `DD000000030198A1` | Corrected a PDF link pointing to the wrong patent |
| `DD000000075030A5` | Corrected a PDF link pointing to the wrong patent |
| `DD000000287026A5` | Replaced both the PDF and text links |
| `DD000000287125A5` | Completed the missing PDF and text links |

### 6. Splitting Inventor and Applicant Names and Addresses

Generated separate name and address fields for the 281,852 patent document records within the selected date range.

Main operations:

- Preserved the original fields.

- Split inventor information (`erfinder`) into separate name and address fields, with a maximum of 30 inventor entries.

- Split applicant information (`anmelderinhaber`) into separate name and address fields, with a maximum of 25 applicant entries.

- Preserved the original order of entries without automatically merging individuals with identical names.

For example, patent `DD000000138481A3` contains 30 inventor entries, none of which provides an address.

Some errors have been identified in the automated splitting results, such as personal names being incorrectly recognized as addresses. These issues have been flagged but have not yet been fully corrected.

### 7. Preliminary Classification of Individuals and Organizations

Automatically classified inventor and applicant information and generated detailed classification and summary tables.

The classification results contain 281,852 records and 366 columns.

Final verification has not yet been completed.

### 8. Full-Scale Textual and Structural Error Detection for Names and Organizations

Conducted textual and structural checks on all inventor and applicant entries within the selected date range.

The scope of the examination was as follows:

| Examined Item           | Count     |
|-------------------------|-----------|
| Patent document records | 281,852   |
| Inventor entries        | 744,424   |
| Applicant entries       | 466,126   |
| Total entries           | 1,210,550 |

After grouping entries by their original category and name string, 339,586 unique name combinations were identified.

Results:

| Classification Result | Number of Name Combinations |
|----|----|
| Confirmed spelling, splitting, missing-value, or classification issues | 117 |
| Suspected issues requiring further verification | 21,622 |
| No issues detected by the applied rules | 317,847 |

A total of 91,884 detailed records of confirmed or suspected issues were generated.

The main issues include:

- Incomplete personal or organization names.

- Personal names incorrectly assigned to address fields.

- Organizations incorrectly classified as individuals.

- Names containing unusual numbers, symbols, or parentheses.

- Suspected spelling errors based on similarities to frequently occurring names.

This part may require applying OCR again to the original source documents.

### 9. Confirmation of Spelling Errors in Selected Organization Names

The corrections have not yet been written back uniformly to the original dataset in order to avoid affecting other records that have not yet been verified.

## II. Next Steps

### 1. Verification of Individual and Organization Information

Further verify inventor and applicant information based on the existing classification results and detected anomalies.

### 2. Verification of Anomalous Information Using Original Patent Documents

For records containing spelling errors, splitting errors, or other suspected problems in personal names, addresses, or organization names, trace the information back to the corresponding original patent documents.

### 3. Correction of Remaining Data Issues and Regeneration of Results
