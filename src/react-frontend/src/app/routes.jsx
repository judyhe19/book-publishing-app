import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "../features/auth/pages/LoginPage";
import RegisterPage from "../features/auth/pages/RegisterPage";
import AccountPage from "../features/auth/pages/AccountPage";
import ChangePasswordPage from "../features/auth/pages/ChangePasswordPage";
import SalesListPage from "../features/sales/pages/SalesListPage";
import SalesInputPage from "../features/sales/pages/SalesInputPage";
import AuthorPaymentsPage from "../features/sales/pages/AuthorPaymentsPage";
import SalesDetailPage from "../features/sales/pages/SalesDetailPage";
import { RequireAuth } from "../features/auth/routes/RequireAuth";
import BooksListPage from "../features/books/pages/BooksListPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/books" replace />} />

      <Route path="/login" element={<LoginPage />} />
      {/* <Route path="/register" element={<RegisterPage />} /> */}

      <Route
        path="/books"
        element={
          <RequireAuth>
            <BooksListPage />
          </RequireAuth>
        }
      />

      <Route
        path="/sales"
        element={
          <RequireAuth>
            <SalesListPage />
          </RequireAuth>
        }
      />

      <Route path="/sales/authors" element={<AuthorPaymentsPage />} />

      <Route path="/sale/:saleId" element={<SalesDetailPage />} />

      <Route
        path="/sales/input"
        element={
          <RequireAuth>
            <SalesInputPage />
          </RequireAuth>
        }
      />

      <Route
        path="/account"
        element={
          <RequireAuth>
            <AccountPage />
          </RequireAuth>
        }
      />

      <Route
        path="/changepassword"
        element={
          <RequireAuth>
            <ChangePasswordPage />
          </RequireAuth>
        }
      />

      <Route path="*" element={<div className="p-6">Not found</div>} />
    </Routes>
  );
}