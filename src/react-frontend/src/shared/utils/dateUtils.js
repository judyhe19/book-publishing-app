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

const MONTH_NAMES_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/**
 * Formats a YYYY-MM string as "Month Year", e.g. "2023-01" → "January 2023".
 * If `short` is true, returns "Jan 2023".
 * Returns fallback for falsy or unparseable input.
 */
export function formatMonthYear(dateStr, fallback = "", short = false) {
  if (!dateStr) return fallback;
  const parts = dateStr.split("-");
  if (parts.length !== 2) return dateStr;
  const y = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(y) || isNaN(m) || m < 1 || m > 12) return dateStr;
  const monthName = short ? MONTH_NAMES_SHORT[m - 1] : MONTH_NAMES[m - 1];
  return `${monthName} ${y}`;
}
