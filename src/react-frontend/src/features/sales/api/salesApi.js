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