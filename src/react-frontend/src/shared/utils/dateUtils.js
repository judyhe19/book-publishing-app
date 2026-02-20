/**
 * Shared date display utilities.
 *
 * All dates in this application are month/year granularity (YYYY-MM).
 * These helpers format and parse that representation consistently.
 *
 * NOTE: Year 0 is unsupported. On the backend, Python's datetime.date
 * requires year >= 1 and rejects "0000-MM".  On the frontend, JS treats
 * year 0 as falsy (!0 === true), so formatMonthYear returns the raw
 * string.  This is correct — there is no year 0 in the Gregorian calendar.
 *
 * IMPORTANT: Do NOT use new Date() for formatting — JS maps years 0-99
 * to 1900-1999, which causes display bugs (e.g. year 0 → "1900").
 * Always use the string-based approach below.
 */

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

/**
 * Formats a YYYY-MM string as "Month Year", e.g. "2023-01" → "January 2023".
 * Returns fallback for falsy or unparseable input.
 */
export function formatMonthYear(dateStr, fallback = "") {
  if (!dateStr) return fallback;
  const [y, m] = dateStr.split("-").map(Number);
  if (!y || !m || m < 1 || m > 12) return dateStr;
  return `${MONTH_NAMES[m - 1]} ${y}`;
}
