// src/shared/components/DataTable.jsx
import React from "react";
import { Link } from "react-router-dom";
import { Spinner } from "./Spinner";
import { Button } from "./Button";

export function DataTable({
  data,
  columns,
  loading = false,
  ordering,
  onSort,
  onRowClick,
  rowClassName,
  emptyMessage = "No data found.",
  loadingMessage = "Loading data...",
  fixedLayout = false,
}) {
  // Parse comma-separated multi-sort string into [{field, desc, position}]
  const sortParts = (ordering || "")
    .split(",")
    .filter(Boolean)
    .map((p, i) => ({
      field: p.startsWith("-") ? p.slice(1) : p,
      desc: p.startsWith("-"),
      position: i + 1,
    }));
  const multiSort = sortParts.length > 1;

  const renderSortIcon = (field) => {
    if (!field) return null;
    const entry = sortParts.find((p) => p.field === field);
    if (!entry) return null;
    const arrow = entry.desc ? " ↓" : " ↑";
    return multiSort ? (
      <span className="text-blue-500 text-xs">
        {arrow}<sup>{entry.position}</sup>
      </span>
    ) : (
      <span className="text-blue-500">{arrow}</span>
    );
  };

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <table className={`w-full ${fixedLayout ? "table-fixed" : "table-auto"} divide-y divide-gray-200`}>
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, idx) => {
              const alignClass = col.className?.includes("text-right")
                ? "text-right"
                : col.className?.includes("text-center")
                ? "text-center"
                : "text-left";
              return (
                <th
                  key={idx}
                  onClick={col.sortKey && onSort ? () => onSort(col.sortKey) : undefined}
                  className={`px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider ${alignClass} ${
                    col.sortKey && onSort ? "cursor-pointer hover:bg-gray-100" : ""
                  } ${col.className || ""}`}
                >
                  {col.label} {!col.hideSortIcon && renderSortIcon(col.sortKey)}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-12 text-center">
                <div className="flex justify-center items-center gap-2 text-slate-500">
                  <Spinner />
                  <span>{loadingMessage}</span>
                </div>
              </td>
            </tr>
          ) : !data || data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-4 text-center text-gray-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={row.id}
                className={`hover:bg-gray-50 ${onRowClick ? "cursor-pointer" : ""} ${rowClassName ? rowClassName(row) : ""}`}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((col, idx) => (
                  <td
                    key={idx}
                    className={`px-3 py-3 text-sm text-gray-500 ${
                      col.className !== undefined ? col.className : "whitespace-nowrap"
                    }`}
                  >
                    {col.type === "actions" && col.getActions ? (
                      <div
                        className={`flex gap-2 ${
                          col.className?.includes("text-right") ? "justify-end" : ""
                        }`}
                      >
                        {col.getActions(row).map((action, aIdx) => {
                          const btn = (
                            <Button
                              variant={action.variant || "primary"}
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (action.onClick) action.onClick(row);
                              }}
                            >
                              {action.label}
                            </Button>
                          );
                          return action.to ? (
                            <Link key={aIdx} to={action.to} onClick={(e) => e.stopPropagation()}>
                              {btn}
                            </Link>
                          ) : (
                            <React.Fragment key={aIdx}>{btn}</React.Fragment>
                          );
                        })}
                      </div>
                    ) : (
                      col.render(row)
                    )}
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

export default DataTable;
