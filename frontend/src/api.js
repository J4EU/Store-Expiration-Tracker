const API_BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "request failed";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }

    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
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
