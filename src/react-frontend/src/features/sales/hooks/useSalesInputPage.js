import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createManySales } from '../api/salesApi';

const EMPTY_ROW = {
    date: '',
    book: null,
    quantity: '',
    publisher_revenue: '',
    author_royalties: {},
    author_paid: {}
};

/**
 * Transforms a row from UI format to API format
 */
const transformRowToSaleData = (row) => {
    const sale = {
        book: row.book.value,
        date: `${row.date}-01`,
        quantity: parseInt(row.quantity),
        publisher_revenue: parseFloat(row.publisher_revenue),
        author_royalties: {},
        author_paid: {}
    };

    const royaltyInput = row.author_royalties || {};
    const paidInput = row.author_paid || {};
    const authors = row.book.authors || [];

    authors.forEach(author => {
        const amount = royaltyInput[author.author_id];
        if (amount !== undefined && amount !== '') {
            sale.author_royalties[author.author_id] = parseFloat(amount);
        }
        if (paidInput[author.author_id]) {
            sale.author_paid[author.author_id] = true;
        }
    });

    return sale;
};

/**
 * Checks if a row has any data entered (partially or fully filled)
 */
const isRowStarted = (row) => {
    return row.date || row.book || row.quantity || row.publisher_revenue;
};

/**
 * Checks if a row has all required fields filled
 */
const isRowComplete = (row) => {
    return row.book && row.quantity && row.publisher_revenue && row.date;
};

/**
 * Custom hook to manage sales input page state and logic
 */
export const useSalesInputPage = () => {
    const navigate = useNavigate();
    const [rows, setRows] = useState([{ ...EMPTY_ROW }]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleRowChange = (index, field, value) => {
        setRows(prevRows => {
            const newRows = [...prevRows];
            if (typeof field === 'object' && field !== null) {
                newRows[index] = { ...newRows[index], ...field };
            } else {
                newRows[index] = { ...newRows[index], [field]: value };
            }

            // if editing the last row, append a new empty one with the date/book from current row
            if (index === prevRows.length - 1) {
                newRows.push({
                    ...EMPTY_ROW,
                    date: newRows[index].date,
                    book: newRows[index].book
                });
            }
            return newRows;
        });
    };

    const handleRemoveRow = (index) => {
        if (rows.length <= 1) return;
        setRows(prevRows => prevRows.filter((_, i) => i !== index));
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        setError(null);

        // Get rows that have been started (have any data)
        const startedRows = rows.filter(isRowStarted);

        if (startedRows.length === 0) {
            setError("Please fill in at least one sale record.");
            setIsSubmitting(false);
            return;
        }

        // Check if any started row is incomplete
        const incompleteRows = startedRows.filter(row => !isRowComplete(row));
        if (incompleteRows.length > 0) {
            setError("Please complete all fields for each sale entry before submitting.");
            setIsSubmitting(false);
            return;
        }

        try {
            const salesData = startedRows.map(transformRowToSaleData);
            await createManySales(salesData);
            navigate('/sales');
        } catch (err) {
            console.error("Error creating sales:", err);
            setError("Failed to create sales. Please check your data.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return {
        rows,
        isSubmitting,
        error,
        handleRowChange,
        handleRemoveRow,
        handleSubmit
    };
};
