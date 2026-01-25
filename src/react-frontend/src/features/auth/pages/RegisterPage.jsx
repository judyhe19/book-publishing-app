import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { Input } from "../../../shared/components/Input";
import { Button } from "../../../shared/components/Button";
import { errorMessage } from "../../../shared/utils/errors";
import * as authApi from "../api/authApi";

export default function RegisterPage() {
  const nav = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);
    try {
      await authApi.register({ username, email, password, password2 });
      nav("/login");
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <Card>
        <CardHeader title="Create account" subtitle="Start managing titles and royalties." />
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-700">Username</label>
              <div className="mt-1">
                <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">Email</label>
              <div className="mt-1">
                <Input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">Password</label>
              <div className="mt-1">
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">Confirm password</label>
              <div className="mt-1">
                <Input type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} autoComplete="new-password" />
              </div>
            </div>

            {err && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {err}
              </div>
            )}

            <Button disabled={submitting} className="w-full">
              {submitting ? "Creating..." : "Create account"}
            </Button>

            <div className="text-sm text-slate-600">
              Already have an account?{" "}
              <Link className="text-slate-900 underline" to="/login">
                Login
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}