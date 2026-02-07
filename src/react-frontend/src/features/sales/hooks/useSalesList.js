import { useState, useEffect } from "react";
import { getAllSales } from "../api/salesApi";
import { SORT_CONFIG } from "../config/salesTableConfig";

export function useSalesList() {
    const [sales, setSales] = useState([]);
    const [loading, setLoading] = useState(true);

    // ✅ pagination state
    const [page, setPage] = useState(1);
    const [pageSize] = useState(50);
    const [count, setCount] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    // ✅ show-all toggle
    const [showAll, setShowAll] = useState(false);

    const [filters, setFilters] = useState({
        start_date: "",
        end_date: "",
        ordering: SORT_CONFIG.DEFAULT_ORDER,
    });

    // fetch from backend when date filters OR ordering OR page OR showAll changes
    useEffect(() => {
        fetchSales();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters.start_date, filters.end_date, filters.ordering, page, pageSize, showAll]);

    const fetchSales = async () => {
        setLoading(true);
        try {
            const activeFilters = {};
            if (filters.start_date) activeFilters.start_date = filters.start_date;
            if (filters.end_date) activeFilters.end_date = filters.end_date;
            if (filters.ordering) activeFilters.ordering = filters.ordering;

            // ✅ show-all param mirrors Books: all=1
            if (showAll) {
                activeFilters.all = "1";
            } else {
                // ✅ normal pagination params
                activeFilters.page = String(page);
                activeFilters.page_size = String(pageSize);
            }

            const queryParams = new URLSearchParams(activeFilters).toString();

            const data = await getAllSales(queryParams);

            setSales(data.results || []);
            setCount(data.count ?? 0);
            setTotalPages(data.total_pages ?? 1);
        } catch (error) {
            console.error("Error fetching sales:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (field) => {
        // reset page when sorting changes
        setPage(1);

        setFilters((prev) => {
            if (prev.ordering === `-${field}`) return { ...prev, ordering: field };
            if (prev.ordering === field) return { ...prev, ordering: `-${field}` };
            if (SORT_CONFIG.DESC_FIELDS.includes(field)) {
                return { ...prev, ordering: `-${field}` };
            }
            return { ...prev, ordering: field };
        });
    };

    const handleDateChange = (e) => {
        const { name, value } = e.target;
        setPage(1);
        setFilters((prev) => ({ ...prev, [name]: value }));
    };

    // ✅ toggle showAll and reset page safely
    const toggleShowAll = () => {
        setPage(1);
        setShowAll((prev) => !prev);
    };

    return {
        sales,
        loading,
        filters,
        handleSort,
        handleDateChange,
        refresh: fetchSales,

        page,
        pageSize,
        count,
        totalPages,
        setPage,

        showAll,
        toggleShowAll,
    };
}
