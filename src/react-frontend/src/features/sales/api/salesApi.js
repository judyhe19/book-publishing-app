import { apiFetch, apiFormFetch } from "../../../shared/api/http";

export function getAllSales(queryParams = "") {
    const qs = queryParams ? `?${queryParams}` : "";
    return apiFetch(`/api/sales/${qs}`)
}

export function createManySales(salesData) {
    return apiFetch("/api/sales/create-many/", {
        method: "POST",
        body: salesData,
    })
}

export function payUnpaidSalesForAuthor(authorId) {
  return apiFetch(`/api/authors/${authorId}/pay-unpaid-sales/`, { method: "POST" });
}

export function updateSalesRecord(saleId, data) {
  return apiFetch(`/api/sales/${saleId}/`, {
    method: "PATCH",
    body: data,
  });
}

export function deleteSalesRecord(saleId) {
  return apiFetch(`/api/sales/${saleId}/`, {
    method: "DELETE",
  });
}

export function getSalesRecord(saleId) {
    return apiFetch(`/api/sales/${saleId}/`);
}

export function getAuthorPaymentsGrouped(queryParams = "") {
  const qs = queryParams ? `?${queryParams}` : "";
  return apiFetch(`/api/author/payments/grouped${qs}`);
}

/**
 * Upload an Ingram Spark CSV for validation + preview.
 */
export async function validateIngramCSV(file, month, year) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("month", month);
  formData.append("year", year);
  return apiFormFetch("/api/sales/import-ingram-csv/", formData);
}

/**
 * Upload an Amazon XLSX for validation + preview.
 * Month/year are embedded in the file itself, so no extra params are needed.
 */
export async function importAmazonXLSX(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFormFetch("/api/sales/import-amazon-xlsx/", formData);
}

/**
 * Upload a Backerkit XLSX for validation + preview.
 * Rows are rolled up into aggregate kickstarter sales records.
 */
export async function importBackerkitXLSX(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFormFetch("/api/sales/import-backerkit-xlsx/", formData);
}

/**
 * Convert a given amount and currency to USD.
 */
export function convertCurrency(amount, currency) {
  return apiFetch(`/api/sales/convert-currency/?amount=${encodeURIComponent(amount)}&currency=${encodeURIComponent(currency)}`);
}

/**
 * Export filtered sales as CSV. Triggers a file download in the browser.
 */
export async function exportSalesCSV(queryParams = "") {
  const qs = queryParams ? `?${queryParams}` : "";
  const res = await fetch(`/api/sales/export-csv/${qs}`, {
    credentials: "include",
  });

  if (!res.ok) {
    const err = new Error("Failed to export CSV");
    err.status = res.status;
    throw err;
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  // Extract filename from Content-Disposition header, fallback to default
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?(.+?)"?$/);
  const filename = match ? match[1] : "hp-sales-export.csv";

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
