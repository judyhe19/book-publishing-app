import React from "react";

export function AuthLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="grid gap-6 md:grid-cols-2 items-start">
          <div className="hidden md:block">
            <h2 className="text-3xl font-semibold text-slate-900">
              Publisher accounting, simplified.
            </h2>
            <p className="mt-3 text-slate-600">
              Track titles, sales, royalties, and payouts in one place.
            </p>
          </div>

          <div>{children}</div>
        </div>
      </div>
    </div>
  );
}