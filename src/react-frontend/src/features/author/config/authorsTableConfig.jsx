import { Link, useNavigate } from "react-router-dom";
import React from "react";
import { Button } from "../../../shared/components/Button";

// Sort configuration
// IMPORTANT: Keep sortKeys in sync with backend: bookapp/views/authors.py (FIELD_MAP)
export const SORT_CONFIG = {
  DEFAULT_FIELD: "name",
  DEFAULT_ORDER: "name",
  // Fields that should default to descending on first click
  DESC_FIELDS: [
    "authored_books_count",
    "total_author_royalty",
    "paid_author_royalty",
    "unpaid_author_royalty",
  ],
};

export const TABLE_COLUMNS = [
  {
    label: "Name",
    sortKey: "name",
    render: (author) => (
      <span className="font-medium text-gray-900">{author.name}</span>
    ),
  },
  {
    label: "Email",
    sortKey: "email",
    render: (author) =>
      author.email ? (
        <span className="text-gray-700">{author.email}</span>
      ) : (
        <span className="text-gray-400">-</span>
      ),
  },
  {
    label: "Books",
    sortKey: "authored_books_count",
    type: "number",
    sortValue: (author) => Number(author.authored_books_count ?? 0),
    render: (author) => Number(author.authored_books_count ?? 0),
  },
  {
    label: "Total Royalty",
    sortKey: "total_author_royalty",
    type: "number",
    sortValue: (author) => Number(author.total_author_royalty ?? 0),
    render: (author) => {
      const total = Number(author.total_author_royalty ?? 0);
      return <span className="font-medium">${total.toFixed(2)}</span>;
    },
  },
  {
    label: "Paid Royalty",
    sortKey: "paid_author_royalty",
    type: "number",
    sortValue: (author) => Number(author.paid_author_royalty ?? 0),
    render: (author) => {
      const paid = Number(author.paid_author_royalty ?? 0);
      return <span className="text-green-700">${paid.toFixed(2)}</span>;
    },
  },
  {
    label: "Unpaid Royalty",
    sortKey: "unpaid_author_royalty",
    type: "number",
    sortValue: (author) => Number(author.unpaid_author_royalty ?? 0),
    render: (author) => {
      const unpaid = Number(author.unpaid_author_royalty ?? 0);
      return <span className="text-red-700">${unpaid.toFixed(2)}</span>;
    },
  },
  {
    label: "Actions",
    type: "actions",
    getActions: (author) => [
      { label: "Author Details", to: `/authors/${author.id}`, variant: "secondary" },
      { label: 'Modify Author', to: `/authors/${author.id}/modify?returnTo=${encodeURIComponent(window.location.pathname + window.location.search)}`, variant: 'primary' }
    ],
  },
];