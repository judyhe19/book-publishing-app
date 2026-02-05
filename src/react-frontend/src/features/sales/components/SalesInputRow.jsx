import React from 'react';
import { Card } from '../../../shared/components/Card';
import {
    DateField,
    BookSelect,
    QuantityField,
    RevenueField,
    AuthorRoyaltiesSection,
    RemoveRowButton
} from './SalesInputFields';
import { useSalesInputRow } from '../hooks/useSalesInputRow';

const SalesInputRow = ({ index, data, onChange, onRemove, isFirst }) => {
    const {
        overrides,
        loadOptions,
        handleBookChange,
        handleRoyaltyChange,
        handleRoyaltyBlur,
        handlePaidChange
    } = useSalesInputRow({ index, data, onChange });

    return (
        <Card>
            <div className="flex flex-wrap gap-4 items-start p-4 pr-12 bg-white rounded-2xl relative">
                <DateField value={data.date} onChange={(val) => onChange(index, 'date', val)} />
                <BookSelect date={data.date} value={data.book} loadOptions={loadOptions} onChange={handleBookChange} />
                <QuantityField value={data.quantity} onChange={(val) => onChange(index, 'quantity', val)} />
                <RevenueField value={data.publisher_revenue} onChange={(val) => onChange(index, 'publisher_revenue', val)} />
                <AuthorRoyaltiesSection
                    book={data.book}
                    authorRoyalties={data.author_royalties}
                    authorPaid={data.author_paid}
                    overrides={overrides}
                    isEdit={data.isEdit}
                    onRoyaltyChange={handleRoyaltyChange}
                    onRoyaltyBlur={handleRoyaltyBlur}
                    onPaidChange={handlePaidChange}
                />
                {!isFirst && <RemoveRowButton onClick={() => onRemove(index)} />}
            </div>
        </Card>
    );
};

export default SalesInputRow;
