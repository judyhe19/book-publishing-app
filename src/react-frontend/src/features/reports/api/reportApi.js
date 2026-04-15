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

// ---------------------------------------------------------------------------
// Shared XLSX blob download helper
// ---------------------------------------------------------------------------

/**
 * Fetch an XLSX blob from the given URL and trigger a browser download.
 * Extracts the filename from the Content-Disposition header if available.
 */
async function downloadXlsxBlob(url, fallbackFilename) {
    const res = await fetch(url, { credentials: "include" });

    if (!res.ok) {
        const err = new Error("Failed to export report");
        err.status = res.status;
        throw err;
    }

    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);

    // Extract filename from Content-Disposition header, fallback to default
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?(.+?)"?$/);
    const filename = match ? match[1] : fallbackFilename;

    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(blobUrl);
}

// ---------------------------------------------------------------------------
// Financial report exports
// ---------------------------------------------------------------------------

export async function exportAllAuthorsRoyaltyReport(startYear, startQuarter, endYear, endQuarter) {
    const params = new URLSearchParams({
        start_year: startYear,
        start_quarter: startQuarter,
        end_year: endYear,
        end_quarter: endQuarter,
    });
    return downloadXlsxBlob(
        `/api/reports/all-authors-royalty/?${params}`,
        "All_Authors_Royalty_Report.xlsx"
    );
}

export async function exportPublisherProfitReport(startYear, startQuarter, endYear, endQuarter) {
    const params = new URLSearchParams({
        start_year: startYear,
        start_quarter: startQuarter,
        end_year: endYear,
        end_quarter: endQuarter,
    });
    return downloadXlsxBlob(
        `/api/reports/publisher-profit/?${params}`,
        "Publisher_Profit_Report.xlsx"
    );
}

export async function exportAmazonSalesReport() {
    return downloadXlsxBlob(
        "/api/reports/amazon-sales/",
        "Amazon_Sale_Report.xlsx"
    );
}
