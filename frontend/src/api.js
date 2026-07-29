function resolveApiBaseUrl() {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  const baseUrl = configuredBaseUrl || "/api";
  return baseUrl.replace(/\/+$/, "");
}

const API_BASE_URL = resolveApiBaseUrl();

function normalizeErrorDetail(detail) {
  const translateDetail = (message) => {
    if (message === "String should have at least 1 character") {
      return "한 글자 이상 입력해야 합니다.";
    }

    return message;
  };

  if (typeof detail === "string" && detail.trim()) {
    return translateDetail(detail);
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const firstItem = detail[0];
    if (typeof firstItem === "string" && firstItem.trim()) {
      return translateDetail(firstItem);
    }

    if (firstItem && typeof firstItem === "object") {
      if (typeof firstItem.msg === "string" && firstItem.msg.trim()) {
        return translateDetail(firstItem.msg);
      }
    }
  }

  if (detail && typeof detail === "object") {
    if (typeof detail.msg === "string" && detail.msg.trim()) {
      return translateDetail(detail.msg);
    }
  }

  return "요청 처리에 실패했습니다.";
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "요청 처리에 실패했습니다.";

    try {
      const data = await response.json();
      detail = normalizeErrorDetail(data.detail);
    } catch {
      detail = response.statusText || detail;
    }

    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export function fetchSession() {
  return request("/auth/session");
}

export function fetchDashboard(referenceDate) {
  return request(`/dashboard?reference_date=${referenceDate}`);
}

export function lookupProduct(barcode) {
  return request(`/products/by-barcode?barcode=${encodeURIComponent(barcode)}`);
}

export function createProduct(payload) {
  return request("/products", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProduct(productId, payload) {
  return request(`/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateExpiration(productId, payload) {
  return request(`/products/${productId}/expiration`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createDiscard(payload) {
  return request("/discards", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createNoDiscard(payload) {
  return request("/expiration-checks/no-discard", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function archiveProduct(productId) {
  return request(`/products/${productId}/archive`, {
    method: "PATCH",
  });
}

export function restoreProduct(productId) {
  return request(`/products/${productId}/restore`, {
    method: "PATCH",
  });
}

export function fetchArchivedProducts(query = "") {
  const search = query.trim();
  const suffix = search ? `?query=${encodeURIComponent(search)}` : "";
  return request(`/archived-products${suffix}`);
}
