import { useCallback } from 'react';
import { apiFetch } from '../api/http';
import { formatBookLabel } from '../utils/bookUtils';

/**
 * Custom hook to search for books by title or ISBN
 * Provides a loadOptions function compatible with react-select/async
 * 
 * @param {Object} options
 * @param {string} options.date - Optional date filter in "YYYY-MM" format to filter books published before this month
 * @returns {Object} - { loadOptions }
 */
export const useBookSearch = ({ date } = {}) => {
    const loadOptions = useCallback(async (inputValue) => {
        try {
            const params = new URLSearchParams({ q: inputValue || '' });

            // Filter by publication date if date is selected
            if (date) {
                const [year, month] = date.split('-').map(Number);
                if (year && month) {
                    const lastDay = new Date(year, month, 0).getDate();
                    params.set('published_before', `${year}-${String(month).padStart(2, '0')}-${lastDay}`);
                }
            }

            const json = await apiFetch(`/api/books/?${params}`);

            if (!json.results) return [];

            return json.results.map(book => ({
                label: formatBookLabel(book.title, book.isbn_13),
                value: book.id,
                authors: book.authors,
                publication_date: book.publication_date,
                ...book
            }));
        } catch (error) {
            console.error("Error searching books:", error);
            return [];
        }
    }, [date]);

    return { loadOptions };
};
