import { useState, useEffect } from 'react';
import { apiFetch } from '../../../shared/api/http';

/**
 * Custom hook to manage sales input row logic
 * Handles book search, royalty calculations, and author payment tracking
 */
export const useSalesInputRow = ({ index, data, onChange }) => {
    // track which author's royalty is overridden: { [authorId]: boolean }
    const [overrides, setOverrides] = useState(() => data.overrides || {});


    // book search function for AsyncSelect
    const loadOptions = async (inputValue) => {
        try {
            const params = new URLSearchParams({ q: inputValue || '' });

            // Filter by publication date if date is selected
            if (data.date) {
                const [year, month] = data.date.split('-').map(Number);
                if (year && month) {
                    const lastDay = new Date(year, month, 0).getDate();
                    params.set('published_before', `${year}-${String(month).padStart(2, '0')}-${lastDay}`);
                }
            }

            const json = await apiFetch(`/api/books/?${params}`); // TODO: refactor this into smth like bookApi.js

            if (!json.results) return [];

            return json.results.map(book => ({
                label: `${book.title} (ISBN-13: ${book.isbn_13})`,
                value: book.id,
                authors: book.authors,
                ...book
            }));
        } catch (error) {
            console.error("Error searching books:", error);
            return [];
        }
    };

    const handleBookChange = (selectedOption) => {
        onChange(index, 'book', selectedOption);
        setOverrides({});
        if (selectedOption?.authors) {
            onChange(index, 'author_royalties', {});
        }
    };

    // auto-calculate royalties per author based on royalty rate
    useEffect(() => {
        if (data.isEdit) return;
        
        if (data.publisher_revenue && data.book?.authors) {
            const currentRoyalties = data.author_royalties || {};
            const newRoyalties = { ...currentRoyalties };
            let hasChanges = false;

            data.book.authors.forEach(author => {
                // only calculate based on the royalty rate if not overridden
                if (!overrides[author.author_id]) {
                    const rate = parseFloat(author.royalty_rate) || 0;
                    const calculated = parseFloat(data.publisher_revenue) * rate;
                    const formatted = calculated.toFixed(2);

                    if (newRoyalties[author.author_id] !== formatted) {
                        console.log(`Calculating royalty for ${author.name}: Revenue=${data.publisher_revenue}, Rate=${rate}, Result=${formatted}`);
                        newRoyalties[author.author_id] = formatted;
                        hasChanges = true;
                    }
                }
            });

            if (hasChanges) {
                onChange(index, 'author_royalties', newRoyalties);
            }
        }
    }, [data.publisher_revenue, data.book, overrides, index, onChange]);

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
        handleBookChange,
        handleRoyaltyChange,
        handleRoyaltyBlur,
        handlePaidChange
    };
};
