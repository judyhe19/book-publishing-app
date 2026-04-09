// src/features/author/pages/AuthorCreatePage.jsx
import { useNavigate, useLocation } from "react-router-dom";
import { Button, Card, CardContent, ErrorAlert } from "../../../shared/components";
import { useCreateAuthor } from "../hooks/useCreateAuthor";

export default function AuthorCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = location.state?.returnTo ?? "/authors";
  const { form, isSubmitting, error, handleChange, handleSubmit } = useCreateAuthor();

  const onSubmit = async () => {
    const created = await handleSubmit();
    if (created) {
      navigate(returnTo);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Create New Author</h1>
        <p className="text-slate-500 mt-1">
          Enter the author’s name, email, and optional payment accounts.
        </p>
      </div>

      {error && (
        <ErrorAlert variant="leftBorder" className="mb-4">
          {error}
        </ErrorAlert>
      )}

      <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }}>
        <Card>
          <CardContent>
            <div className="space-y-4">

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Name
                </label>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
                  value={form.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                  placeholder="e.g., Douglas Adams"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
                  value={form.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  placeholder="e.g., douglasadams@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  PayPal Username
                </label>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
                  value={form.paypal}
                  onChange={(e) => handleChange("paypal", e.target.value)}
                  placeholder="e.g., douglasadams"
                />
                <p className="text-xs text-slate-500 mt-1">
                  PayPal.me username (not email)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Venmo Username
                </label>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
                  value={form.venmo}
                  onChange={(e) => handleChange("venmo", e.target.value)}
                  placeholder="e.g., douglasadams"
                />
              </div>

            </div>

            <div className="mt-8 flex justify-end gap-4">
              <Button type="button" variant="secondary" onClick={() => navigate(returnTo)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || !form.name.trim()}>
                {isSubmitting ? "Creating..." : "Create Author"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}