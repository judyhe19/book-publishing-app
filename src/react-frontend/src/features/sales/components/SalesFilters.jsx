import React from 'react';
import { Input } from "../../../shared/components/Input";

export default function SalesFilters({ filters, onDateChange }) {
    return (
        <div className="mb-6 flex gap-4 items-end">
            <div className="flex-1 max-w-sm">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                </label>
                <Input
                    type="date"
                    name="start_date"
                    value={filters.start_date}
                    onChange={onDateChange}
                />
            </div>
            <div className="flex-1 max-w-sm">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                </label>
                <Input
                    type="date"
                    name="end_date"
                    value={filters.end_date}
                    onChange={onDateChange}
                />
            </div>
        </div>
    );
}
