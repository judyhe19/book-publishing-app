import React, { useState } from "react";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { Input } from "../../../shared/components/Input";
import { Button } from "../../../shared/components/Button";
import { errorMessage } from "../../../shared/utils/errors";
import * as authApi from "../api/authApi";

export default function ChangePasswordPage() {
  const [old_password, setOld] = useState("");
  const [new_password, setNew] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [ok, setOk] = useState(null);
  const [err, setErr] = useState(null);

  async function onSubmit(e) {
    e.preventDefault();
    setOk(null);
    setErr(null);
    setSubmitting(true);
    try {
      const res = await authApi.changePassword({ old_password, new_password });
      setOk(res.message);
      setOld("");
      setNew("");
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="max-w-xl">
        <Card>
          <CardHeader title="Change password" subtitle="Update your password for this account." />
          <CardContent>
            <form className="space-y-4" onSubmit={onSubmit}>
              <div>
                <label className="text-sm font-medium text-slate-700">Old password</label>
                <div className="mt-1">
                  <Input type="password" value={old_password} onChange={(e) => setOld(e.target.value)} />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">New password</label>
                <div className="mt-1">
                  <Input type="password" value={new_password} onChange={(e) => setNew(e.target.value)} />
                </div>
              </div>

              {ok && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                  {ok}
                </div>
              )}
              {err && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {err}
                </div>
              )}

              <Button disabled={submitting} className="w-full">
                {submitting ? "Updating..." : "Update password"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}