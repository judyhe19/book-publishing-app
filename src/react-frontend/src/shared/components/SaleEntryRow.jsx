import React from 'react';
import { Card } from './Card';
import {
    DateField,
    BookSelect,
    QuantityField,
    RevenueField,
    AuthorRoyaltiesSection,
    RemoveRowButton
} from './SaleEntryFields';
import { useSaleEntry } from '../hooks/useSaleEntry';

const SaleEntryRow = ({ index, data, onChange, onRemove, isFirst }) => {
    const {
        overrides,
        loadOptions,
        handleDateChange,
        handleBookChange,
        handleRoyaltyChange,
        handleRoyaltyBlur,
        handlePaidChange
    } = useSaleEntry({ index, data, onChange });

    return (
        <Card>
            <div className="flex flex-wrap gap-4 items-start p-4 pr-12 bg-white rounded-2xl relative">
                <DateField value={data.date} onChange={handleDateChange} />
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

export default SaleEntryRow;
