/**
 * Shared navigation bar, injected into every page.
 *
 * Renders a top navbar into <div id="app-nav"></div> and highlights
 * the link matching the current page. Centralizing this in one file
 * means adding/renaming a page only requires editing here, not every
 * HTML file.
 */

const NAV_LINKS = [
  { href: "/index.html", label: "Home", match: ["/", "/index.html"] },
  { href: "/pages/vehicle.html", label: "Vehicle", match: ["/pages/vehicle.html"] },
  { href: "/pages/simulation.html", label: "Simulation", match: ["/pages/simulation.html"] },
  { href: "/pages/analysis.html", label: "Analysis", match: ["/pages/analysis.html"] },
  { href: "/pages/validation.html", label: "Validation", match: ["/pages/validation.html"] },
  { href: "/pages/comparison.html", label: "Comparison", match: ["/pages/comparison.html"] },
];

function resolveNavHref(href) {
  // index.html/pages links are absolute from the frontend root, but
  // pages are served from different depths (root vs /pages/), so
  // resolve relative to the current document location.
  return new URL(href.replace(/^\//, ""), document.baseURI.replace(/pages\/?$/, "")).pathname;
}

function isActive(link) {
  const currentPath = window.location.pathname;
  return link.match.some((m) => currentPath.endsWith(m) || (m === "/" && currentPath.endsWith("/index.html")));
}

function renderNav() {
  const container = document.getElementById("app-nav");
  if (!container) return;

  const nav = document.createElement("nav");
  nav.className = "app-navbar";

  const brand = document.createElement("a");
  brand.className = "app-navbar-brand";
  brand.href = resolveNavHrefSafe("/index.html");
  brand.textContent = "Vehicle Digital Twin";
  nav.appendChild(brand);

  const linksWrap = document.createElement("div");
  linksWrap.className = "app-navbar-links";

  NAV_LINKS.forEach((link) => {
    const a = document.createElement("a");
    a.textContent = link.label;
    a.className = "app-navbar-link";

    if (link.disabled) {
      a.classList.add("app-navbar-link-disabled");
      a.href = "#";
      a.addEventListener("click", (e) => e.preventDefault());
    } else {
      a.href = resolveNavHrefSafe(link.href);
      if (isActive(link)) {
        a.classList.add("app-navbar-link-active");
      }
    }

    linksWrap.appendChild(a);
  });

  nav.appendChild(linksWrap);

  const statusWrap = document.createElement("span");
  statusWrap.className = "app-navbar-status";
  statusWrap.id = "navApiStatus";
  statusWrap.textContent = "checking...";
  nav.appendChild(statusWrap);

  container.appendChild(nav);
}

function resolveNavHrefSafe(href) {
  // Pages live either at the root (index.html) or under /pages/.
  // Build the correct relative path based on current depth.
  const inPagesDir = window.location.pathname.includes("/pages/");
  if (href === "/index.html") {
    return inPagesDir ? "../index.html" : "index.html";
  }
  const fileName = href.replace("/pages/", "");
  return inPagesDir ? fileName : `pages/${fileName}`;
}

async function updateNavApiStatus() {
  const el = document.getElementById("navApiStatus");
  if (!el || typeof apiGet !== "function") return;

  try {
    await apiGet("/api/health");
    el.textContent = "API online";
    el.classList.add("status-ok");
    el.classList.remove("status-error");
  } catch (err) {
    el.textContent = "API offline";
    el.classList.add("status-error");
    el.classList.remove("status-ok");
  }
}

renderNav();
updateNavApiStatus();