## Evolution 4 Pre-seed Data

Please take note of the following details for the files provided

### authors.csv

This file contains all authors necessary to populate the books below. They
may contain none of, one of, or both of the payment portal account information.
Optional fields with no value are blank.

### books.csv

This file contains all the books expected for the review session. All
fields are requirements-accurate. An optional field with no value is blank.
The ISBN and ASIN values are accurate to the title.

Book covers are in an `img/` directory with their name as the value in the
CSV column.

New columns from the previous evolution are as followed:
- kickstarter_ebook: The tag for ebooks found in Backerkit imports
- kickstarter_paperback: The tag for paperback books found in Backerkit imports
- is_released: a y/n field that specifies if the book is released to market

### records.csv

This file contains all the records expected for the review session. The
records are requirements-accurate for optional fields. Fields that are not
applicable for a given record type are blank (i.e. a KENP value for a print
edition or distributor for Kickstarter). These records may be in currencies 
other than USD. It is expected that your input method does the conversion 
based on the conversion rate at the time of input, as converted values are 
not supplied in these pre-seed records.
