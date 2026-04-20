// src/features/authors/pages/AuthorListPage.jsx
import React from "react";
import { useLocation } from "react-router-dom";
import { useAuthorsList } from "../hooks/useAuthorsList";
import { AuthorsTable } from "../components";
import {
  Button,
  Card,
  CardContent,
  Pagination,
  ShowAllToggle,
  DualScrollContainer,
  Input,
} from "../../../shared/components";

export default function AuthorListPage() {
  const location = useLocation();
  const returnToParam = encodeURIComponent(location.pathname + location.search);
  const {
    authors,
    loading,
    filters,
    handleSort,
    handleSearchChange,
    page,
    totalPages,
    setPage,
    count,
    showAll,
    toggleShowAll,
  } = useAuthorsList();

  return (
    <div className="p-6 max-w-full mx-auto">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Authors</h1>
          <p className="text-slate-500 mt-1">Manage and view your authors.</p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="w-full sm:w-[320px]">
            <Input
              value={filters.q}
              onChange={handleSearchChange}
              placeholder="Search name or email…"
            />
          </div>
          <Button
            className="bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-400"
            to="/sales/authors"
          >
            💰 Author Payments
          </Button>
          <Button to="/authors/create">New Author</Button>
        </div>
      </div>

      <Card>
        <CardContent>
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-slate-600">
              {loading ? "Loading…" : `${count ?? 0} author${count === 1 ? "" : "s"}`}
              {showAll && count != null ? " (showing all)" : ""}
            </div>
            <ShowAllToggle showAll={showAll} onToggle={toggleShowAll} />
          </div>

          <DualScrollContainer contentWidth={1400} className="mt-4">
            <AuthorsTable
              data={authors}
              loading={loading}
              ordering={filters.ordering}
              onSort={handleSort}
              rowTo={(author) => `/authors/${author.id}?returnTo=${returnToParam}`}
            />
          </DualScrollContainer>

          <div className="mt-4">
            {!showAll && (
              <Pagination
                page={page}
                totalPages={totalPages}
                onPrev={() => setPage((p) => Math.max(1, p - 1))}
                onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}