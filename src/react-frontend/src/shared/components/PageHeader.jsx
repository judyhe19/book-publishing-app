// src/shared/components/PageHeader.jsx
import React from "react";

/**
 * Consistent page header with title, optional subtitle, and action buttons.
 * Extracts the repeated pattern from SalesListPage, AuthorPaymentsPage, SalesDetailPage, etc.
 */
export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex justify-between items-center mb-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="text-slate-500 mt-1">{subtitle}</p>}
      </div>

      {children && (
        <div className="flex gap-2">
          {children}
        </div>
      )}
    </div>
  );
}

export default PageHeader;
