// src/features/author/pages/AuthorModifyPage.jsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button,
  ErrorAlert,
  LoadingState,
  PageHeader,
  Card,
  CardContent,
} from "../../../shared/components";
import { useAuthorModify } from "../hooks/useAuthorModify";
import { useAuthorBooks } from "../hooks/useAuthorBooks";
import DeleteAuthorDialog from "../components/DeleteAuthorDialog";

export default function AuthorModifyPage() {
  const { authorId } = useParams();
  const navigate = useNavigate();

  const { author, loading, saving, error, save, remove } = useAuthorModify(authorId);
  const { books, hasSales, loadingBooks } = useAuthorBooks(authorId);

  const [form, setForm] = useState({ name: "", email: "" });
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    if (!author) return;
    setForm({
      name: author.name || "",
      email: author.email || "",
    });
  }, [author]);

  const payload = useMemo(() => {
    const name = form.name?.trim();
    const email = form.email?.trim();

    if (!name) return null;

    return {
      name,
      email: email || "",
    };
  }, [form]);

  async function onSave() {
    if (!payload) return;
    const updated = await save(payload);
    if (updated) navigate(-1);
  }

  async function onConfirmDelete() {
    const res = await remove();
    if (res !== null) navigate("/authors");
  }

  if (loading) {
    return <LoadingState message="Loading author..." fullPage />;
  }

  if (!author) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorAlert>{error || "Author not found."}</ErrorAlert>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title="Modify Author" subtitle="Update author information.">
        <Button variant="danger" onClick={() => setDeleteOpen(true)} disabled={saving}>
          Delete
        </Button>
        <Button onClick={onSave} disabled={saving || !payload}>
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </PageHeader>

      {error && (
        <ErrorAlert variant="leftBorder" className="mb-4">
          {error}
        </ErrorAlert>
      )}

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
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                disabled={saving}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                disabled={saving}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <DeleteAuthorDialog
        open={deleteOpen}
        onConfirm={onConfirmDelete}
        onCancel={() => setDeleteOpen(false)}
        disabled={saving || loadingBooks}
        authorName={author.name}
        authorEmail={author.email}
        books={books}
        hasSales={hasSales}
        deletionBehaviorText={
          author.deletion_behavior ||
          "This will delete the author. Any existing books/sales with this author will also be deleted."
        }
      />
    </div>
  );
}