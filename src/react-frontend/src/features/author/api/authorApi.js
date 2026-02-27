import { apiFetch } from "../../../shared/api/http";

export function getAllAuthors(queryParams = "") {
    const qs = queryParams ? `?${queryParams}` : "";
    return apiFetch(`/api/authors/${qs}`);
}

export function createAuthor(authorData) {
    return apiFetch("/api/authors/", {
        method: "POST",
        body: authorData,
    });
}

export function updateAuthor(authorId, data) {
    return apiFetch(`/api/authors/${authorId}/`, {
        method: "PATCH",
        body: data,
    });
}

export function deleteAuthor(authorId) {
    return apiFetch(`/api/authors/${authorId}/`, {
        method: "DELETE",
    });
}

export function getAuthor(authorId) {
    return apiFetch(`/api/authors/${authorId}/`);
}