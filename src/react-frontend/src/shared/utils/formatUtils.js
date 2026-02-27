/**
 * Shared formatting utilities
 */

/**
 * Formats a number or string as a US dollar currency string.
 *
 * @param {string|number} x - The value to format
 * @param {string} fallback - The string to return if the value is missing/invalid
 * @param {boolean} allowZero - If false, a value of 0 will return the fallback
 * @returns {string} The formatted string, e.g., "$12.34"
 */
export function formatMoney(x, fallback = "—", allowZero = true) {
  if (x === null || x === undefined || x === "") return fallback;
  
  const n = Number(x);
  if (Number.isNaN(n)) return fallback;
  if (n === 0 && !allowZero) return fallback;
  
  return `$${n.toFixed(2)}`;
}
