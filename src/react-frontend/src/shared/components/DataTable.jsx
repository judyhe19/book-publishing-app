import React from 'react';
import { Spinner } from "./Spinner";

export function DataTable({ 
    data, 
    columns, 
    loading = false, 
    ordering, 
    onSort, 
    onRowClick,
    emptyMessage = "No data found.",
    loadingMessage = "Loading data..."
}) {
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
                        {columns.map((col, idx) => (
                            <th
                                key={idx}
                                onClick={col.sortKey && onSort ? () => onSort(col.sortKey) : undefined}
                                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${col.sortKey && onSort ? 'cursor-pointer hover:bg-gray-100' : ''}`}
                            >
                                {col.label} {renderSortIcon(col.sortKey)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                        <tr>
                            <td colSpan={columns.length} className="px-6 py-12 text-center">
                                <div className="flex justify-center items-center gap-2 text-slate-500">
                                    <Spinner />
                                    <span>{loadingMessage}</span>
                                </div>
                            </td>
                        </tr>
                    ) : !data || data.length === 0 ? (
                        <tr>
                            <td colSpan={columns.length} className="px-6 py-4 text-center text-gray-500">
                                {emptyMessage}
                            </td>
                        </tr>
                    ) : (
                        data.map((row) => (
                            <tr 
                                key={row.id} 
                                className={`hover:bg-gray-50 ${onRowClick ? 'cursor-pointer' : ''}`}
                                onClick={onRowClick ? () => onRowClick(row) : undefined}
                            >
                                {columns.map((col, idx) => (
                                    <td key={idx} className={`px-6 py-4 text-sm text-gray-500 ${col.className !== undefined ? col.className : 'whitespace-nowrap'}`}>
                                        {col.render(row)}
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
