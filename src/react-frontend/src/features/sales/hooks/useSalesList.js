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
        author_name: "",
        sale_source: "",
        distributor: "",
        format: "",
        projected: "",
        ordering: SORT_CONFIG.DEFAULT_ORDER,
    });

    // fetch from backend when date filters OR ordering OR page OR showAll changes
    useEffect(() => {
        fetchSales();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters.start_date, filters.end_date, filters.author_name, filters.sale_source, filters.distributor, filters.format, filters.projected, filters.ordering, page, pageSize, showAll]);

    const fetchSales = async () => {
        setLoading(true);
        try {
            const activeFilters = {};
            if (filters.start_date) activeFilters.start_date = filters.start_date;
            if (filters.end_date) activeFilters.end_date = filters.end_date;
            if (filters.author_name) activeFilters.author_name = filters.author_name;
            if (filters.sale_source) activeFilters.sale_source = filters.sale_source.toLowerCase();
            if (filters.distributor) activeFilters.distributor = filters.distributor;
            if (filters.format) activeFilters.sale_format = filters.format;
            if (filters.projected) activeFilters.projected = filters.projected;
            if (filters.ordering) activeFilters.ordering = filters.ordering;

            if (showAll) {
                activeFilters.all = "1";
            } else {
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

    const handleFilterChange = (name, value) => {
        setPage(1);
        setFilters((prev) => ({ ...prev, [name]: value }));
    };

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
        handleFilterChange,
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
