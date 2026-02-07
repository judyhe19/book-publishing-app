import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createManySales } from '../api/salesApi';
import { EMPTY_ROW, transformRowToSaleData, isRowStarted } from '../../../shared/utils/salesUtils';

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

        try {
            const salesData = startedRows.map(transformRowToSaleData);
            await createManySales(salesData);
            navigate(-1);
        } catch (err) {
            console.error("Error creating sales:", err);
            // apiFetch throws an Error with a formatted message now
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
