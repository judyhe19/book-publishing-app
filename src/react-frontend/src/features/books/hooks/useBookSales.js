import { useState, useEffect } from "react";
import { getAllSales } from "../../sales/api/salesApi";

// Sort configuration for book sales table
export const BOOK_SALES_SORT_CONFIG = {
    DEFAULT_FIELD: 'date',
    DEFAULT_ORDER: '-date',
    DESC_FIELDS: ['date', 'quantity', 'publisher_revenue', 'total_royalties'],
};

export function useBookSales(bookId) {
    const [sales, setSales] = useState([]);
    const [loading, setLoading] = useState(true);
    const [ordering, setOrdering] = useState(BOOK_SALES_SORT_CONFIG.DEFAULT_ORDER);

    useEffect(() => {
        if (!bookId) return;
        fetchSales();
    }, [bookId, ordering]);

    const fetchSales = async () => {
        setLoading(true);
        try {
            const queryParams = new URLSearchParams({
                book_id: bookId,
                ordering: ordering,
            }).toString();

            const data = await getAllSales(queryParams);
            setSales(data);
        } catch (error) {
            console.error("Error fetching book sales:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (field) => {
        setOrdering((prev) => {
            if (prev === `-${field}`) return field;
            if (prev === field) return `-${field}`;
            // First time sorting: default to descending for specified fields
            if (BOOK_SALES_SORT_CONFIG.DESC_FIELDS.includes(field)) {
                return `-${field}`;
            }
            return field;
        });
    };

    return {
        sales,
        loading,
        ordering,
        handleSort,
        refresh: fetchSales,
    };
}
