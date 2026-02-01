import React from 'react';
import AsyncSelect from 'react-select/async';
import { Input } from '../../../shared/components/Input';

export const DateField = ({ value, onChange }) => (
    <div className="w-48">
        <label className="block text-sm font-medium text-gray-700 mb-1">Month/Year</label>
        <Input type="month" value={value || ''} onChange={(e) => onChange(e.target.value)} />
    </div>
);

export const BookSelect = ({ date, value, loadOptions, onChange }) => (
    <div className="flex-1 min-w-[200px]">
        <label className="block text-sm font-medium text-gray-700 mb-1">Book (Title or ISBN)</label>
        <AsyncSelect
            key={date || 'default'}
            cacheOptions
            loadOptions={loadOptions}
            defaultOptions
            onChange={onChange}
            value={value}
            placeholder="Search..."
            menuPortalTarget={document.body}
            styles={{
                menuPortal: base => ({ ...base, zIndex: 9999 }),
                control: base => ({
                    ...base,
                    borderRadius: '0.75rem',
                    borderColor: '#e2e8f0',
                    boxShadow: 'none',
                    '&:hover': { borderColor: '#e2e8f0' }
                })
            }}
        />
    </div>
);

export const QuantityField = ({ value, onChange }) => (
    <div className="w-32">
        <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
        <Input type="number" value={value || ''} onChange={(e) => onChange(e.target.value)} />
    </div>
);

export const RevenueField = ({ value, onChange }) => (
    <div className="w-36">
        <label className="block text-sm font-medium text-gray-700 mb-1">Revenue</label>
        <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <Input
                type="number"
                step="0.01"
                className="pl-7"
                placeholder="0.00"
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
            />
        </div>
    </div>
);

const AuthorRoyaltyRow = ({ author, royaltyValue, isPaid, isOverridden, onRoyaltyChange, onRoyaltyBlur, onPaidChange }) => (
    <div className="flex items-end gap-3">
        <div className="flex-1">
            <span className="text-xs text-gray-500 truncate mb-0.5 block">{author.name}</span>
            <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <span className="text-gray-400 text-xs">$</span>
                </div>
                <Input
                    type="number"
                    step="0.01"
                    className={`pl-6 py-1 text-sm h-8 ${isOverridden ? 'bg-yellow-50 border-yellow-400 text-yellow-800' : ''}`}
                    placeholder="0.00"
                    value={royaltyValue || ''}
                    onChange={(e) => onRoyaltyChange(e.target.value)}
                    onBlur={onRoyaltyBlur}
                />
            </div>
        </div>
        <div className="h-8 flex items-center pb-1">
            <input
                type="checkbox"
                className="form-checkbox h-4 w-4 text-slate-900 transition duration-150 ease-in-out rounded border-gray-300 focus:ring-slate-900"
                checked={isPaid}
                onChange={(e) => onPaidChange(e.target.checked)}
                title={`Mark ${author.name} as paid`}
            />
        </div>
    </div>
);

export const AuthorRoyaltiesSection = ({ book, authorRoyalties, authorPaid, overrides, onRoyaltyChange, onRoyaltyBlur, onPaidChange }) => (
    <div className="min-w-[200px] flex flex-col gap-2">
        <div className="flex justify-between items-center mb-0">
            <label className="block text-sm font-medium text-gray-700">Royalties</label>
            <label className="block text-xs font-medium text-gray-500 mr-1">Paid?</label>
        </div>
        {!book ? (
            <div className="text-sm text-gray-400 italic mt-1">Select a book</div>
        ) : (book.authors || []).length === 0 ? (
            <div className="text-sm text-gray-400 italic mt-1">No authors found</div>
        ) : (
            (book.authors || []).map(author => (
                <AuthorRoyaltyRow
                    key={author.author_id}
                    author={author}
                    royaltyValue={authorRoyalties?.[author.author_id]}
                    isPaid={authorPaid?.[author.author_id] || false}
                    isOverridden={overrides[author.author_id]}
                    onRoyaltyChange={(val) => onRoyaltyChange(author.author_id, val)}
                    onRoyaltyBlur={() => onRoyaltyBlur(author.author_id)}
                    onPaidChange={(val) => onPaidChange(author.author_id, val)}
                />
            ))
        )}
    </div>
);

export const RemoveRowButton = ({ onClick }) => (
    <button
        onClick={onClick}
        className="text-red-500 hover:text-red-700 p-2 absolute right-0 top-0 mt-2 mr-2"
        title="Remove row"
    >
        ✕
    </button>
);
