// src/shared/components/Navbar.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "./Button";
import { useAuth } from "../../features/auth/hooks/useAuth";
import * as authApi from "../../features/auth/api/authApi";

export function Navbar({ branding }) {
  const { user, setUser } = useAuth();
  const nav = useNavigate();

  async function onLogout() {
    await authApi.logout();
    setUser(null);
    nav("/login");
  }

  return (
    <div className="sticky top-0 z-10 border-b border-slate-100 bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          {branding?.publisher_logo_url && (
            <img
              src={branding.publisher_logo_url}
              alt={branding.publisher_name}
              className="h-8 w-8 object-contain"
            />
          )}
          <span className="font-semibold text-slate-900">
            {branding?.publisher_name || "Loading..."}
          </span>
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/books">
                Books
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/sales">
                Sales
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/authors">
                Authors
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/series">
                Series
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/reports">
                Reports
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/changepassword">
                Password
              </Link>
              <Button variant="secondary" onClick={onLogout}>
                Logout
              </Button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default Navbar;
