import { useState, useCallback } from 'react';
import { useBookSearch } from './useBookSearch';
import { useRoyaltyCalculation } from './useRoyaltyCalculation';

/**
 * Custom hook to manage sale entry row logic
 * Handles book search, royalty calculations, and author payment tracking
 */
export const useSaleEntry = ({ index, data, onChange }) => {
    // track which author's royalty is overridden: { [authorId]: boolean }
    const [overrides, setOverrides] = useState(() => data.overrides || {});

    // Use shared book search hook
    const { loadOptions } = useBookSearch({ date: data.date });

    const handleDateChange = (newDate) => {
        onChange(index, 'date', newDate);
        
        // Check if selected book's publication date is after the new sale date
        // If so, clear the book to prevent invalid entry
        if (data.book?.publication_date && newDate) {
            const [saleYear, saleMonth] = newDate.split('-').map(Number);
            const [pubYear, pubMonth] = data.book.publication_date.split('-').map(Number);
            
            // Compare at month/year granularity: clear book if published after sale month
            const saleYearMonth = saleYear * 100 + saleMonth;
            const pubYearMonth = pubYear * 100 + pubMonth;
            
            if (pubYearMonth > saleYearMonth) {
                onChange(index, 'book', null);
                onChange(index, 'author_royalties', {});
                onChange(index, 'author_paid', {});
                setOverrides({});
            }
        }
    };

    const handleBookChange = (selectedOption) => {
        onChange(index, 'book', selectedOption);
        setOverrides({});
        if (selectedOption?.authors) {
            onChange(index, 'author_royalties', {});
        }
    };

    // Callback for royalty calculation updates
    const handleRoyaltyUpdate = useCallback((newRoyalties) => {
        onChange(index, 'author_royalties', newRoyalties);
    }, [index, onChange]);

    // Use shared royalty calculation hook
    useRoyaltyCalculation({
        publisherRevenue: data.publisher_revenue,
        authors: data.book?.authors,
        authorRoyalties: data.author_royalties,
        overrides,
        onUpdate: handleRoyaltyUpdate,
    });

    const handleRoyaltyChange = (authorId, value) => {
        setOverrides(prev => ({ ...prev, [authorId]: true }));
        const newRoyalties = { ...(data.author_royalties || {}) };
        newRoyalties[authorId] = value;
        onChange(index, 'author_royalties', newRoyalties);
    };

    // handles case where the user manually left a royalty field blank after editing (we revert override to allow auto-calculated royalties)
    const handleRoyaltyBlur = (authorId) => {
        const value = data.author_royalties ? data.author_royalties[authorId] : '';
        if (value === '' || value === null) {
            setOverrides(prev => ({ ...prev, [authorId]: false }));
        }
    };

    const handlePaidChange = (authorId, checked) => {
        const newPaid = { ...(data.author_paid || {}) };
        newPaid[authorId] = checked;
        onChange(index, 'author_paid', newPaid);
    };

    return {
        overrides,
        loadOptions,
        handleDateChange,
        handleBookChange,
        handleRoyaltyChange,
        handleRoyaltyBlur,
        handlePaidChange
    };
};
