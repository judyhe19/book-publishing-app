/**
 * Shared quarter-range utilities.
 * Extracted from AuthorRoyaltyReportPage for reuse across report pages.
 */

/** Quarter options for dropdown selects. */
export const QUARTER_OPTIONS = [1, 2, 3, 4];

/**
 * Return the current default range: four quarters ending at current quarter.
 * @returns {{ startYear: number, startQ: number, endYear: number, endQ: number }}
 */
export function getDefaultQuarterRange() {
  const now = new Date();
  const curYear = now.getFullYear();
  const curMonth = now.getMonth() + 1; // 1-indexed
  const curQ = Math.ceil(curMonth / 3);

  // End = current quarter
  let endYear = curYear;
  let endQ = curQ;

  // Start = 3 quarters before current → 4 quarters total
  let startYear = curYear;
  let startQ = curQ - 3;
  if (startQ <= 0) {
    startQ += 4;
    startYear -= 1;
  }

  return { startYear, startQ, endYear, endQ };
}
