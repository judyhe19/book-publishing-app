import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "./Button";
import { useAuth } from "../../features/auth/hooks/useAuth";
import * as authApi from "../../features/auth/api/authApi";

export function Navbar() {
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
        <Link to="/" className="font-semibold text-slate-900">
          Publisher Portal
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/account">
                Account
              </Link>
              <Link className="text-sm text-slate-700 hover:text-slate-900" to="/changepassword">
                Password
              </Link>
              <Button variant="secondary" onClick={onLogout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              {/* <Link className="text-sm text-slate-700 hover:text-slate-900" to="/login">
                Login
              </Link>
              <Button onClick={() => nav("/register")}>Register</Button> */}
            </>
          )}
        </div>
      </div>
    </div>
  );
}