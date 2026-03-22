// src/shared/hooks/useBookSearch.js
import { useCallback } from 'react';
import { apiFetch } from '../api/http';
import { formatBookLabel } from '../utils/bookUtils';

/**
 * Custom hook to search for books by title or ISBN
 * Provides a loadOptions function compatible with react-select/async
 * 
 * Transforms the single-author book model into an authors array for
 * backward compatibility with sale entry components.
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

            return json.results.map(book => {
                // Transform single author to authors array for backward compatibility
                // Use distributor_author_royalty_rate as the default royalty rate
                const authors = book.author_id
                    ? [{
                        author_id: book.author_id,
                        name: book.author_name,
                        royalty_rate: book.distributor_author_royalty_rate,
                    }]
                    : [];

                return {
                    label: formatBookLabel(book.title, book.isbn_13, book.amazon_asin_ebook),
                    value: book.id,
                    authors,
                    publication_date: book.publication_date,
                    // Include book-level royalty rates for reference
                    distributor_author_royalty_rate: book.distributor_author_royalty_rate,
                    hand_sold_author_royalty_rate: book.hand_sold_author_royalty_rate,
                    // Spread remaining book fields
                    title: book.title,
                    isbn_13: book.isbn_13,
                    isbn_10: book.isbn_10,
                    amazon_asin_ebook: book.amazon_asin_ebook,
                    author_id: book.author_id,
                    author_name: book.author_name,
                    cover_price: book.cover_price,
                    print_cost: book.print_cost,
                };
            });
        } catch (error) {
            console.error("Error searching books:", error);
            return [];
        }
    }, [date]);

    return { loadOptions };
};
