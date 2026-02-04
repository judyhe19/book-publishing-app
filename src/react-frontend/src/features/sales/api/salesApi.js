import { apiFetch } from "../../../shared/api/http";

export function getAllSales(queryParams) {
    return apiFetch(`/api/sale/get_all?${queryParams}`)
}

export function createManySales(salesData) {
    return apiFetch("/api/sale/createmany", {
        method: "POST",
        body: salesData,
    })
}

export function payUnpaidSalesForAuthor(authorId) {
  return apiFetch(`/api/author/${authorId}/pay_unpaid_sales`, { method: "POST" });
}

export function updateSalesRecord(saleId, data) {
  return apiFetch(`/api/sale/${saleId}/edit`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteSalesRecord(saleId) {
  return apiFetch(`/api/sale/${saleId}`, {
    method: "DELETE",
  });
}

export function getSalesRecord(saleId) {
    return apiFetch(`/api/sale/${saleId}/get`);
}