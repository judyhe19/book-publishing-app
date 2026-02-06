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
    let msg = "Request failed";

    if (data) {
        if (typeof data === "string") {
            msg = data;
        } else if (Array.isArray(data)) {
            // Handle lists of errors (e.g. from bulk create)
            msg = data.map(item => {
                if (item.index !== undefined && item.errors) {
                    const details = Object.entries(item.errors)
                        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
                        .join("; ");
                    return `Entry ${item.index + 1}: ${details}`;
                }
                return typeof item === 'string' ? item : JSON.stringify(item);
            }).join("\n");
        } else if (data.detail) {
            msg = data.detail;
        } else if (data.message) {
            msg = data.message;
        } else if (typeof data === "object") {
            // Handle DRF-style generic validation errors { field: [errors] }
            msg = Object.entries(data)
                .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(", ") : val}`)
                .join("\n");
        }
    }
    
    throw new Error(msg);
  }

  return data;
}