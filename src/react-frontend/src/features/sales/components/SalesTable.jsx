// src/features/sales/components/SalesTable.jsx
import React from "react";
import { TABLE_COLUMNS } from "../config/salesTableConfig";
import { DataTable } from "../../../shared/components";

export default function SalesTable({ data, loading, ordering, onSort, columns, onRowClick, rowTo }) {
  const baseColumns = columns || TABLE_COLUMNS;

  const enhancedColumns = baseColumns.map((col) => {
    if (col.sortKey === 'publisher_revenue' || col.sortKey === 'publisher_revenue_original') {
      const isOrigSort = ordering === 'publisher_revenue_original' || ordering === '-publisher_revenue_original';
      const isOrigDesc = ordering === '-publisher_revenue_original';
      const origArrow = isOrigDesc ? '↓' : '↑';

      const isUsdSort = ordering === 'publisher_revenue' || ordering === '-publisher_revenue';
      const isUsdDesc = ordering === '-publisher_revenue';
      const usdArrow = isUsdDesc ? '↓' : '↑';
      
      return {
        ...col,
        sortKey: isOrigSort ? 'publisher_revenue_original' : 'publisher_revenue',
        hideSortIcon: true,
        label: (
          <div className="flex flex-col gap-1 items-start w-full">
            <span className="leading-tight">Pub Rev</span>
            <div className="flex bg-gray-200 rounded p-[2px] w-full max-w-[80px]" onClick={(e) => e.stopPropagation()}>
               <button 
                 type="button"
                 title="Sort by Original Currency"
                 className={`flex-1 flex items-center justify-center px-1 py-0.5 text-[9px] uppercase rounded font-bold transition-all ${isOrigSort ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-800'}`}
                 onClick={() => onSort('publisher_revenue_original')}
               >
                 Orig{isOrigSort && <span className="ml-[1px]">{origArrow}</span>}
               </button>
               <button 
                 type="button"
                 title="Sort by USD Value"
                 className={`flex-1 flex items-center justify-center px-1 py-0.5 text-[9px] uppercase rounded font-bold transition-all ${isUsdSort ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-800'}`}
                 onClick={() => onSort('publisher_revenue')}
               >
                 USD{isUsdSort && <span className="ml-[1px]">{usdArrow}</span>}
               </button>
            </div>
          </div>
        )
      };
    }
    return col;
  });

  return (
    <>
      <div className="mb-1 flex items-center gap-2 text-xs text-gray-400">
        <span className="inline-block w-4 h-0.5 bg-gray-300 rounded opacity-50"></span>
        <span className="italic">Greyed-out rows are projected sales (pre-orders for unreleased books).</span>
      </div>
      <DataTable
        data={data}
        columns={enhancedColumns}
        loading={loading}
        ordering={ordering}
        onSort={onSort}
        onRowClick={onRowClick}
        rowTo={rowTo}
        rowClassName={(row) => row.is_projected ? "opacity-50 italic" : ""}
        emptyMessage="No sales found."
        loadingMessage="Loading sales data..."
        fixedLayout
      />
    </>
  );
}
