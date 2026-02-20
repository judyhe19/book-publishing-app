import React from 'react';
import MonthPicker from "../../../shared/components/MonthPicker";

export default function SalesFilters({ filters, onDateChange }) {
    return (
        <div className="mb-6 flex gap-4 items-end">
            <MonthPicker
                label="Start Month"
                value={filters.start_date}
                onChange={(val) => onDateChange({ target: { name: "start_date", value: val } })}
                className="flex-1 max-w-sm"
            />
            <MonthPicker
                label="End Month"
                value={filters.end_date}
                onChange={(val) => onDateChange({ target: { name: "end_date", value: val } })}
                className="flex-1 max-w-sm"
            />
        </div>
    );
}
