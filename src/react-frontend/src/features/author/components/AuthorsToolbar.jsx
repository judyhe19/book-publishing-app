import React from "react";
import { useNavigate } from "react-router-dom";
import { Button, Input } from "../../../shared/components";

export default function AuthorsToolbar({ q, onChangeQ }) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Authors</h1>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="w-full sm:w-[320px]">
          <Input
            value={q}
            onChange={(e) => onChangeQ(e.target.value)}
            placeholder="Search name or email…"
          />
        </div>

        <Button onClick={() => navigate("/authors/new")}>Create Author</Button>
      </div>
    </div>
  );
}