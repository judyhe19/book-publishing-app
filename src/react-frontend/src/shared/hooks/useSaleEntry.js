// src/shared/hooks/useSaleEntry.js
import { useState, useCallback, useEffect } from 'react';
import { useBookSearch } from './useBookSearch';
import { useRoyaltyCalculation } from './useRoyaltyCalculation';

/**
 * Custom hook to manage sale entry row logic
 * Handles book search, royalty calculations, and author payment tracking
 * 
 * Note: With the single-author model, book.authors will have at most one entry.
 * The royalty rate comes from the book's distributor_author_royalty_rate.
 * 
 * @param {Object} options
 * @param {number} options.index - Row index
 * @param {Object} options.data - Row data
 * @param {Function} options.onChange - Change handler
 * @param {Object} [options.fixedBook] - Optional pre-selected book (skips book selector)
 */
export const useSaleEntry = ({ index, data, onChange, fixedBook }) => {
    // track which author's royalty is overridden: { [authorId]: boolean }
    const [overrides, setOverrides] = useState(() => data.overrides || {});

    // Use shared book search hook
    const { loadOptions } = useBookSearch({ date: data.date });

    // When fixedBook is provided, set it on mount
    useEffect(() => {
        if (fixedBook && !data.book) {
            onChange(index, 'book', fixedBook);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fixedBook]);

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
        // Clear royalties when book changes - they'll be recalculated
        onChange(index, 'author_royalties', {});
        onChange(index, 'author_paid', {});
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
