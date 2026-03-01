import { apiFetch } from "../../../shared/api/http";

export function getAuthorRoyaltyReport(authorId, startYear, startQuarter, endYear, endQuarter) {
    const params = new URLSearchParams({
        start_year: startYear,
        start_quarter: startQuarter,
        end_year: endYear,
        end_quarter: endQuarter,
    });
    return apiFetch(`/api/authors/${authorId}/royalty-report/?${params}`);
}
