import React from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../features/auth/store/authStore";
import { Navbar } from "../shared/components/Navbar";

export function Providers({ children }) {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        {children}
      </BrowserRouter>
    </AuthProvider>
  );
}