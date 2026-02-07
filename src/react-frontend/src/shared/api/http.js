function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

async function ensureCsrf() {
  await fetch("/api/csrf", { credentials: "include" });
}

function formatSimpleErrors(data) {
  if (!data) return "";
  if (typeof data === "string") return data;
  
  if (Array.isArray(data)) {
    return data.map(item => formatSimpleErrors(item)).join("\n");
  }
  
  if (typeof data === "object") {
    return Object.entries(data)
      .map(([key, value]) => {
        const formattedValue = formatSimpleErrors(value);
        return `${formattedValue}`;
      })
      .join("\n");
  }
  
  return String(data);
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

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    let msg = "Request failed";
    

    if (data) {
        if (typeof data === "string") {
            msg = data;
        } else if (Array.isArray(data)) {
            // Check if it's the specific bulk upload error format
            if (data.length > 0 && data[0].index !== undefined && data[0].errors) {
              if (data.length > 1) {
                msg = data.map(item => {
                    const details = formatSimpleErrors(item.errors);
                    return `Entry ${item.index + 1}\n: ${details}`;
                }).join("\n");
              } else {
                // dont group by entry, just show the error if only one entry
                msg = formatSimpleErrors(data[0].errors);
              }
            } else {
                // Generic array of errors
                msg = formatSimpleErrors(data);
            }
        } else if (data.detail) {
            msg = data.detail;
        } else if (data.message) {
            msg = data.message;
        } else if (typeof data === "object") {
            msg = formatSimpleErrors(data);
        }
    }

    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}