import React from "react";
import AuthorPaymentsGroupCard from "./AuthorPaymentsGroupCard";

export default function AuthorPaymentsGroupList({ groups, onMarkAllPaid, onGoBook, onGoSale }) {
  return (
    <div className="space-y-4">
      {groups.map((g) => (
        <AuthorPaymentsGroupCard
          key={g.author.id}
          group={g}
          onMarkAllPaid={() => onMarkAllPaid(g.author)}
          onGoBook={onGoBook}
          onGoSale={onGoSale}
        />
      ))}
    </div>
  );
}
