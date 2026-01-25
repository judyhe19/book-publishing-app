function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

async function ensureCsrf() {
  await fetch("/api/csrf", { credentials: "include" });
}

export async function apiFetch(path, { method = "GET", headers, body } = {}) {
  const isUnsafe = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method.toUpperCase());

  if (isUnsafe) {
    await ensureCsrf();
  }

  const csrfToken = getCookie("csrftoken");

  const res = await fetch(path, {
    method,
    credentials: "include",
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(isUnsafe && csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  // Optional: nice error handling
  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    const msg = (data && data.detail) || (data && data.message) || (typeof data === "string" ? data : "Request failed");
    throw new Error(msg);
  }

  return data;
}