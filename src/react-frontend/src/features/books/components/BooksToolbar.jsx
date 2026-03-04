// src/features/books/components/BooksToolbar.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { Button, Input } from "../../../shared/components";

export default function BooksToolbar({ q, onChangeQ }) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Books</h1>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="w-full sm:w-[320px]">
          <Input
            value={q}
            onChange={(e) => onChangeQ(e.target.value)}
            placeholder="Search title, author, series, ISBN…"
          />
        </div>

        <Button onClick={() => navigate("/books/input")}>Create Book</Button>
      </div>
    </div>
  );
}
