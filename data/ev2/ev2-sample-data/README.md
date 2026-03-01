# Evolution 2 Sample Data

This is a set of pre-seed data for EV2.

## books.csv

This is a set of 16 real Sci-Fi and Fantasy books with matching ISBN data and supplied royalty rates for distributor and handsold. Some book records include the name of an image that should be used as the book cover.

NOTE: There is one book that has a JPG-XL image which may be used as an alternative to the JPG image. This is not required and there is a JPG fallback if JXL is not supported.

## sales_records.csv
This is a table of 20 sales records spanning across some of the books from the included books.csv dataset. This list is **NOT** in an Ingram Spark CSV format, rather is just a set of records that should be added to the application manually or via backend directly.

As the application should be calculating your revenues for handsold copies, that cell is blank for the appropriate rows. Some records have comments that are expected to be included in your records importing. Some records use ISBN-10 and others use ISBN-13 as the identifier.
