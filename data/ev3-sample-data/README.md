## Evolution 3 Pre-seed Data

Please take note of the following details for the files provided

### books.csv

This file contains all the books expected for the review session. All
fields are requirements-accurate. An optional field with no value is blank.
The ISBN and ASIN values are accurate to the title. 

Book covers are in an `img/` directory with their name as the value in the
CSV column.

A note for authors. Given that authors are a first class system with only the
names and emails, like last evolution, please create a sample email with an 
@example.com or equivalent domain. The test plan does not require knowing the 
authors' email addresses. The test only requires the authors of the books in
the `books.csv` record

### records.csv

This file contains all the records expected for the review session. The
records are requirements-accurate for optional fields. Fields that are not
applicable for a given record type are blank (i.e. a KENP value for a print
edition). These records may be in currencies other than USD. It is expected
that your input method does the conversion based on the conversion rate at
the time of input, as converted values are not supplied in these pre-seed 
records.

#### Revisions
- A: Original release
- B: Corrected ISBN and ASIN for "The Galaxy, and the Ground Within", corrected
  missing leading zeroes in ISBN-10
- C: corrected unintentional fractional Yen, Corrected ISBN for "Rouge Protocol"
- D: corrected multiple records that contained old ISBN from previous
corrections
