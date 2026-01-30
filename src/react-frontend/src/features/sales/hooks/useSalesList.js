import { useState, useEffect, useMemo } from "react";
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

    // fetch from backend only when date filters change
    useEffect(() => {
        fetchSales();
    }, [filters.start_date, filters.end_date]);

    const fetchSales = async () => {
        setLoading(true);
        try {
            const activeFilters = {};
            if (filters.start_date) activeFilters.start_date = filters.start_date;
            if (filters.end_date) activeFilters.end_date = filters.end_date;

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

    // client side sorting 
    const sortedSales = useMemo(() => {
        if (!sales) return [];
        const sorted = [...sales];
        const { ordering } = filters;
        if (!ordering) return sorted;

        const isDesc = ordering.startsWith('-');
        const field = isDesc ? ordering.substring(1) : ordering;

        const columnConfig = TABLE_COLUMNS.find(col => col.sortKey === field);
        const isNumeric = columnConfig?.type === 'number';

        sorted.sort((a, b) => {
            let valA = columnConfig?.sortValue ? columnConfig.sortValue(a) : a[field];
            let valB = columnConfig?.sortValue ? columnConfig.sortValue(b) : b[field];

            if (isNumeric) {
                valA = Number(valA);
                valB = Number(valB);
            }

            if (valA < valB) return isDesc ? 1 : -1;
            if (valA > valB) return isDesc ? -1 : 1;
            return 0;
        });
        return sorted;
    }, [sales, filters.ordering]);

    return {
        sales: sortedSales, // Return the processed/sorted list
        loading,
        filters,
        handleSort,
        handleDateChange,
        refresh: fetchSales,
    };
}
