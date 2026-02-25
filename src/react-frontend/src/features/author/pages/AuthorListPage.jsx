// src/features/authors/pages/AuthorListPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuthorsList } from "../hooks/useAuthorsList";
import { AuthorsTable } from "../components";
import {
  Button,
  Card,
  CardContent,
  Pagination,
  ShowAllToggle,
  DualScrollContainer,
} from "../../../shared/components";

export default function AuthorListPage() {
  const navigate = useNavigate();
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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Authors</h1>
          <p className="text-slate-500 mt-1">Manage and view your authors.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate("/authors/create")}>New Author</Button>
        </div>
      </div>

      <Card>
        <CardContent>
          {/* Filters + Show All toggle */}
          <div className="flex items-center justify-between gap-3">
            <ShowAllToggle showAll={showAll} onToggle={toggleShowAll} />
          </div>

          <DualScrollContainer contentWidth={1400} className="mt-4">
            <AuthorsTable
              data={authors}
              loading={loading}
              ordering={filters.ordering}
              onSort={handleSort}
            />
          </DualScrollContainer>

          {/* Pagination */}
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