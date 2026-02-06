import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { Input } from "../../../shared/components/Input";
import { Button } from "../../../shared/components/Button";
import { errorMessage } from "../../../shared/utils/errors";
import * as authApi from "../api/authApi";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);
  const [success, setSuccess] = useState(null);

  const nav = useNavigate();
  const loc = useLocation();
  const { refresh } = useAuth();

  const redirectTo = loc.state?.from || "/books";

  useEffect(() => {
    const msg = loc.state?.success;
    if (msg) {
      setSuccess(msg);
      window.history.replaceState({}, document.title);
    }
  }, [loc.state]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);
    try {
      await authApi.login({ username, password });
      await refresh();
      nav(redirectTo, { replace: true });
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <Card>
        <CardHeader title="Welcome back" subtitle="Log in to your publisher account." />
        <CardContent>
          {/* ✅ show success ABOVE the form */}
          {success && (
            <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {success}
            </div>
          )}

          {err && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {err}
            </div>
          )}

          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-700">Username</label>
              <div className="mt-1">
                <Input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">Password</label>
              <div className="mt-1">
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
            </div>

            <Button disabled={submitting} className="w-full">
              {submitting ? "Logging in..." : "Login"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}
