// src/features/sales/components/SalesFilters.jsx
import React, { useState, useEffect } from "react";
import { MonthPicker } from "../../../shared/components";
import { listAuthors } from "../../books/api/booksApi";

export default function SalesFilters({ filters, onDateChange, onFilterChange }) {
  const [authors, setAuthors] = useState([]);

  useEffect(() => {
    listAuthors()
      .then((data) => setAuthors(data))
      .catch(() => setAuthors([]));
  }, []);

  const inputClass =
    "w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent bg-white";

  return (
    <div className="mb-6 flex gap-4 items-end flex-wrap">
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
      <div className="flex-1 max-w-sm">
        <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
        <input
          type="text"
          list="author-options"
          placeholder="Any"
          value={filters.author_name}
          onChange={(e) => onFilterChange("author_name", e.target.value)}
          className={inputClass}
        />
        <datalist id="author-options">
          {authors.map((a) => (
            <option key={a.id} value={a.name} />
          ))}
        </datalist>
      </div>
      <div className="flex-1 max-w-sm">
        <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
        <select
          value={filters.sale_source}
          onChange={(e) => onFilterChange("sale_source", e.target.value)}
          className={inputClass}
        >
          <option value="">All Sources</option>
          <option value="Distributor">Distributor</option>
          <option value="Handsold">Handsold</option>
        </select>
      </div>
      <div className="flex-1 max-w-sm">
        <label className="block text-sm font-medium text-gray-700 mb-1">Distributor</label>
        <select
          value={filters.distributor}
          onChange={(e) => onFilterChange("distributor", e.target.value)}
          className={inputClass}
        >
          <option value="">All Distributors</option>
          <option value="Ingram Spark">Ingram Spark</option>
          <option value="Amazon">Amazon</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <div className="flex-1 max-w-sm">
        <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
        <select
          value={filters.format}
          onChange={(e) => onFilterChange("format", e.target.value)}
          className={inputClass}
        >
          <option value="">All Formats</option>
          <option value="print">Print</option>
          <option value="ebook">eBook</option>
          <option value="kindle unlimited">Kindle Unlimited</option>
        </select>
      </div>
    </div>
  );
}
