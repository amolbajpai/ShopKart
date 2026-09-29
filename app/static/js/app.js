const api = {
  async request(url, options = {}, retry = true) {
    const res = await fetch(url, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (res.status === 401 && retry && !url.includes("/api/auth/")) {
      const refreshed = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (refreshed.ok) return api.request(url, options, false);
    }
    let data = null;
    const text = await res.text();
    if (text) {
      try { data = JSON.parse(text); } catch { data = { detail: text }; }
    }
    if (!res.ok) {
      const detail = data && data.detail;
      const msg = Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : (detail || res.statusText);
      throw new Error(msg);
    }
    return data;
  },
  get(url) { return this.request(url); },
  post(url, body) { return this.request(url, { method: "POST", body: JSON.stringify(body || {}) }); },
  put(url, body) { return this.request(url, { method: "PUT", body: JSON.stringify(body || {}) }); },
  patch(url, body) { return this.request(url, { method: "PATCH", body: JSON.stringify(body || {}) }); },
  del(url) { return this.request(url, { method: "DELETE" }); },
};

function money(n) {
  return "₹" + Number(n).toLocaleString("en-IN");
}

function stars(n) {
  const full = Math.round(n);
  return "★".repeat(full) + "☆".repeat(5 - full) + ` ${Number(n).toFixed(1)}`;
}

function productCard(p) {
  return `
    <article class="card">
      <a href="/product/${p.id}"><img src="${p.image_url}" alt="${p.name}" /></a>
      <div class="brand">${p.brand}</div>
      <h3><a href="/product/${p.id}">${p.name}</a></h3>
      <div class="stars">${stars(p.rating)} (${p.review_count})</div>
      <div><span class="price">${money(p.price)}</span><span class="mrp">${money(p.mrp)}</span></div>
      <div class="btn-row">
        <button class="btn" onclick="addCart(${p.id})">Add to Cart</button>
        <button class="btn-ghost" onclick="toggleWish(${p.id})">♡</button>
      </div>
    </article>`;
}

async function addCart(productId, quantity = 1) {
  try {
    await api.post("/api/cart", { product_id: productId, quantity });
    await refreshCartCount();
    toast("Added to cart");
  } catch (err) {
    if (String(err.message).toLowerCase().includes("not authenticated")) {
      location.href = "/login";
      return;
    }
    toast(err.message, true);
  }
}

async function toggleWish(productId) {
  try {
    await api.post("/api/wishlist", { product_id: productId });
    toast("Saved to wishlist");
  } catch (err) {
    if (String(err.message).toLowerCase().includes("not authenticated")) {
      location.href = "/login";
      return;
    }
    toast(err.message, true);
  }
}

function toast(msg, isError) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.style.cssText = "position:fixed;bottom:20px;right:20px;background:#232f3e;color:#fff;padding:10px 14px;border-radius:8px;z-index:9";
    document.body.appendChild(el);
  }
  el.style.background = isError ? "#b12704" : "#232f3e";
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2200);
}

async function refreshCartCount() {
  try {
    const cart = await api.get("/api/cart");
    document.getElementById("cart-count").textContent = cart.count;
  } catch {
    document.getElementById("cart-count").textContent = "0";
  }
}

async function bootHeader() {
  const params = new URLSearchParams(location.search);
  const q = document.getElementById("search-q");
  if (q) q.value = params.get("q") || "";

  try {
    const cats = await api.get("/api/categories");
    const bar = document.getElementById("catbar");
    const select = document.getElementById("search-cat");
    if (bar) {
      bar.innerHTML = `<a href="/">All</a>` + cats.map((c) => `<a href="/?category=${c.slug}">${c.name}</a>`).join("");
    }
    if (select) {
      select.innerHTML = `<option value="">All</option>` + cats.map((c) =>
        `<option value="${c.slug}" ${params.get("category") === c.slug ? "selected" : ""}>${c.name}</option>`
      ).join("");
    }
  } catch { /* catalog optional on first paint */ }

  try {
    const me = await api.get("/api/auth/me");
    document.getElementById("nav-hello").innerHTML = `Hello, ${me.full_name.split(" ")[0]}<br><strong>Account</strong>`;
    document.getElementById("nav-hello").href = "/profile";
    document.getElementById("nav-logout").classList.remove("hidden");
    if (me.is_admin) document.getElementById("nav-admin").classList.remove("hidden");
    await refreshCartCount();
  } catch {
    document.getElementById("nav-hello").href = "/login";
  }

  document.getElementById("nav-logout").addEventListener("click", async () => {
    await api.post("/api/auth/logout", {});
    location.href = "/";
  });
}

document.addEventListener("DOMContentLoaded", bootHeader);
