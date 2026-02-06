import { useEffect } from 'react';

/**
 * Custom hook to auto-calculate royalties per author based on royalty rate.
 * When an author's royalty is not overridden, it calculates: publisher_revenue × royalty_rate
 * 
 * @param {Object} options
 * @param {number} options.publisherRevenue - The publisher revenue for this sale
 * @param {Array} options.authors - Array of authors with { author_id, royalty_rate, name }
 * @param {Object} options.authorRoyalties - Current royalties { [authorId]: string }
 * @param {Object} options.overrides - Override flags { [authorId]: boolean }
 * @param {Function} options.onUpdate - Callback to update royalties with new values
 */
export const useRoyaltyCalculation = ({
    publisherRevenue,
    authors,
    authorRoyalties,
    overrides,
    onUpdate,
}) => {
    useEffect(() => {
        if (publisherRevenue && authors?.length) {
            const currentRoyalties = authorRoyalties || {};
            const newRoyalties = { ...currentRoyalties };
            let hasChanges = false;

            authors.forEach(author => {
                // only calculate based on the royalty rate if not overridden
                if (!overrides[author.author_id]) {
                    const rate = parseFloat(author.royalty_rate) || 0;
                    const calculated = parseFloat(publisherRevenue) * rate;
                    const formatted = calculated.toFixed(2);

                    if (newRoyalties[author.author_id] !== formatted) {
                        console.log(`Calculating royalty for ${author.name}: Revenue=${publisherRevenue}, Rate=${rate}, Result=${formatted}`);
                        newRoyalties[author.author_id] = formatted;
                        hasChanges = true;
                    }
                }
            });

            if (hasChanges) {
                onUpdate(newRoyalties);
            }
        }
    }, [publisherRevenue, authors, overrides, authorRoyalties, onUpdate]);
};
