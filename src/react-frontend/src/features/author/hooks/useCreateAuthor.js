// src/features/author/hooks/useCreateAuthor.js
import { useState } from "react";
import { createAuthor } from "../api/authorApi";

export function useCreateAuthor() {
  const [form, setForm] = useState({ name: "", email: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setError("");
    setIsSubmitting(true);
    try {
      const payload = {
        name: form.name?.trim(),
        email: form.email?.trim(),
        paypal: form.paypal?.trim() || null,
        venmo: form.venmo?.trim() || null,
      };
      const created = await createAuthor(payload);
      return created; // caller can navigate
    } catch (e) {
      console.error("Error creating author:", e);
      setError(e?.message || "Failed to create author.");
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { form, isSubmitting, error, handleChange, handleSubmit };
}