import { apiFetch } from "../../../shared/api/http";

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
