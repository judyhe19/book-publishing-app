import { useState, useEffect } from "react";
import { getAllSales } from "../api/salesApi";
import { SORT_CONFIG, TABLE_COLUMNS } from "../config/salesTableConfig";

export function useSalesList() {
    const [sales, setSales] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        start_date: "",
        end_date: "",
        ordering: SORT_CONFIG.DEFAULT_ORDER,
    });

    // fetch from backend when date filters OR ordering changes
    useEffect(() => {
        fetchSales();
    }, [filters.start_date, filters.end_date, filters.ordering]);

    const fetchSales = async () => {
        setLoading(true);
        try {
            const activeFilters = {};
            if (filters.start_date) activeFilters.start_date = filters.start_date;
            if (filters.end_date) activeFilters.end_date = filters.end_date;
            if (filters.ordering) activeFilters.ordering = filters.ordering;

            const queryParams = new URLSearchParams(activeFilters).toString();

            const data = await getAllSales(queryParams);
            setSales(data);
        } catch (error) {
            console.error("Error fetching sales:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (field) => {
        setFilters((prev) => {
            if (prev.ordering === `-${field}`) return { ...prev, ordering: field };
            if (prev.ordering === field) return { ...prev, ordering: `-${field}` };
            // first time sorting:
            // default to descending for specified fields
            if (SORT_CONFIG.DESC_FIELDS.includes(field)) {
                return { ...prev, ordering: `-${field}` };
            }
            // default to ascending for other fields
            return { ...prev, ordering: field };
        });
    };

    const handleDateChange = (e) => {
        const { name, value } = e.target;
        setFilters((prev) => ({ ...prev, [name]: value }));
    };

    return {
        sales, // Return the list directly (sorting is now server-side)
        loading,
        filters,
        handleSort,
        handleDateChange,
        refresh: fetchSales,
    };
}

