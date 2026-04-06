// src/features/sales/components/AuthorPaymentsGroupList.jsx
import React from "react";
import AuthorPaymentsGroupCard from "./AuthorPaymentsGroupCard";

export default function AuthorPaymentsGroupList({ groups, onMarkAllPaid, onGoSale }) {
  return (
    <div className="space-y-4">
      {groups.map((g) => (
        <AuthorPaymentsGroupCard
          key={g.author.id}
          group={g}
          onMarkAllPaid={() => onMarkAllPaid(g.author)}
          onGoSale={onGoSale}
        />
      ))}
    </div>
  );
}
