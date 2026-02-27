import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createManySales } from '../api/salesApi';
import {
    EMPTY_ROW,
    transformRowToSaleData,
    isRowStarted,
    computeAuthorRoyalty,
} from '../../../shared/utils/salesUtils';

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

            // Auto-compute author_royalty whenever revenue or book changes
            const row = newRows[index];
            const royalty = computeAuthorRoyalty(row.sale_source, row.publisher_revenue, row.book);
            newRows[index] = { ...newRows[index], author_royalty: royalty };

            // If editing the last row, append a new empty one inheriting date, book, and sale_source
            if (index === prevRows.length - 1) {
                newRows.push({
                    ...EMPTY_ROW,
                    date: newRows[index].date,
                    book: newRows[index].book,
                    sale_source: newRows[index].sale_source,
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

        // Drop the trailing auto-generated row if the user hasn't entered
        // any unique data into it (quantity / publisher_revenue / comment).
        let rowsToSubmit = [...rows];
        if (rowsToSubmit.length > 1) {
            const last = rowsToSubmit[rowsToSubmit.length - 1];
            if (!last.quantity && !last.publisher_revenue && !last.comment) {
                rowsToSubmit = rowsToSubmit.slice(0, -1);
            }
        }

        // Get rows that have been started (have any data)
        const startedRows = rowsToSubmit.filter(isRowStarted);

        if (startedRows.length === 0) {
            setError("Please fill in at least one sale record.");
            setIsSubmitting(false);
            return;
        }

        try {
            const salesData = startedRows.map(transformRowToSaleData);
            await createManySales(salesData);
            navigate(-1);
        } catch (err) {
            console.error("Error creating sales:", err);
            setError(err.message || "Failed to create sales. Please check your data.");
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
