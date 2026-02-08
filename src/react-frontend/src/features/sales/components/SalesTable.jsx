import React from 'react';
import { TABLE_COLUMNS } from "../config/salesTableConfig";
import { Spinner } from "../../../shared/components/Spinner";

export default function SalesTable({ data, loading, ordering, onSort }) {

    const renderSortIcon = (field) => {
        if (!field) return null;
        if (ordering === field) return " ↑";
        if (ordering === `-${field}`) return " ↓";
        return "";
    };

    return (
        <div className="rounded-lg border border-slate-200">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        {TABLE_COLUMNS.map((col, idx) => (
                            <th
                                key={idx}
                                onClick={col.sortKey ? () => onSort(col.sortKey) : undefined}
                                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${col.sortKey ? 'cursor-pointer hover:bg-gray-100' : ''}`}
                            >
                                {col.label} {renderSortIcon(col.sortKey)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                        <tr>
                            <td colSpan={TABLE_COLUMNS.length} className="px-6 py-12 text-center">
                                <div className="flex justify-center items-center gap-2 text-slate-500">
                                    <Spinner />
                                    <span>Loading sales data...</span>
                                </div>
                            </td>
                        </tr>
                    ) : data.length === 0 ? (
                        <tr>
                            <td colSpan={TABLE_COLUMNS.length} className="px-6 py-4 text-center">
                                No sales found.
                            </td>
                        </tr>
                    ) : (
                        data.map((sale) => (
                            <tr key={sale.id} className="hover:bg-gray-50">
                                {TABLE_COLUMNS.map((col, idx) => (
                                    <td key={idx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {col.render(sale)}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}
