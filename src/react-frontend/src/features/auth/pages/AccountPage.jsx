import React from "react";
import { Card, CardContent, CardHeader } from "../../../shared/components/Card";
import { useAuth } from "../hooks/useAuth";

export default function AccountPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <Card>
        <CardHeader title="Account" subtitle="Your current session details." />
        <CardContent>
          <div className="grid gap-2 text-sm text-slate-700">
            <div><span className="font-medium text-slate-900">ID:</span> {user?.id}</div>
            <div><span className="font-medium text-slate-900">Username:</span> {user?.username}</div>
            <div><span className="font-medium text-slate-900">Email:</span> {user?.email}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}