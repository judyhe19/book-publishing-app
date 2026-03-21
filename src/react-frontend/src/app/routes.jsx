import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "../features/auth/pages/LoginPage";
import RegisterPage from "../features/auth/pages/RegisterPage";
import AccountPage from "../features/auth/pages/AccountPage";
import ChangePasswordPage from "../features/auth/pages/ChangePasswordPage";
import SalesListPage from "../features/sales/pages/SalesListPage";
import SalesInputPage from "../features/sales/pages/SalesInputPage";
import IngramCSVImportPage from "../features/sales/pages/IngramCSVImportPage";
import AmazonXLSXImportPage from "../features/sales/pages/AmazonXLSXImportPage";
import AuthorPaymentsPage from "../features/sales/pages/AuthorPaymentsPage";
import SalesDetailPage from "../features/sales/pages/SalesDetailPage";
import { RequireAuth } from "../features/auth/routes/RequireAuth";
import BooksListPage from "../features/books/pages/BooksListPage";
import CreateBookPage from "../features/books/pages/CreateBookPage";
import BookDetailPage from "../features/books/pages/BookDetailPage";
import AuthorListPage from "../features/author/pages/AuthorListPage";
import AuthorCreatePage from "../features/author/pages/AuthorCreatePage";
import AuthorModifyPage from "../features/author/pages/AuthorModifyPage";
import SeriesEditorPage from "../features/books/pages/SeriesEditorPage";
import AuthorRoyaltyReportPage from "../features/reports/pages/AuthorRoyaltyReportPage";
import AuthorDetailPage from "../features/author/pages/AuthorDetailPage";


export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/books" replace />} />

      <Route path="/login" element={<LoginPage />} />
      {/* <Route path="/register" element={<RegisterPage />} /> */}

      <Route
        path="/books/input"
        element={
          <RequireAuth>
            <CreateBookPage />
          </RequireAuth>
        }
      />

      <Route
        path="/books/:bookId"
        element={
          <RequireAuth>
            <BookDetailPage />
          </RequireAuth>
        }
      />

      
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

      <Route 
        path="/sales/authors" 
        element={
          <RequireAuth>
            <AuthorPaymentsPage />
          </RequireAuth>
        } 
      />

      <Route 
        path="/sale/:saleId" 
        element={
          <RequireAuth>
            <SalesDetailPage />
          </RequireAuth>
        } 
      />

      <Route
        path="/sales/input"
        element={
          <RequireAuth>
            <SalesInputPage />
          </RequireAuth>
        }
      />

      <Route
        path="/sales/import-csv"
        element={
          <RequireAuth>
            <IngramCSVImportPage />
          </RequireAuth>
        }
      />

      <Route
        path="/sales/import-xlsx"
        element={
          <RequireAuth>
            <AmazonXLSXImportPage />
          </RequireAuth>
        }
      />

      <Route
        path="/series"
        element={
          <RequireAuth>
            <SeriesEditorPage />
          </RequireAuth>
        }
      />

      <Route
        path="/authors"
        element={
          <RequireAuth>
            <AuthorListPage />
          </RequireAuth>
        }
      />

      <Route
        path="/authors/:authorId/modify"
        element={
          <RequireAuth>
            <AuthorModifyPage />
          </RequireAuth>
        }
      />

      <Route
        path="/authors/create"
        element={
          <RequireAuth>
            <AuthorCreatePage />
          </RequireAuth>
        }
      />

      <Route
        path="/authors/:authorId"
        element={
          <RequireAuth>
            <AuthorDetailPage />
          </RequireAuth>
        }
      />

      <Route
        path="/reports/royalty"
        element={
          <RequireAuth>
            <AuthorRoyaltyReportPage />
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