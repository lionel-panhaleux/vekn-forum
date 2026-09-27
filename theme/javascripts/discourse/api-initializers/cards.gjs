import { apiInitializer } from "discourse/lib/api";

// `[[Card Name]]` in a post shows the card's scan: on hover where there is one, on tap otherwise.
// krcg resolves the name (English or translated, fuzzy) — card knowledge stays upstream.
// `[pot]`, `[POT]`, `[Banu Haqim]`, `[action]` show krcg's discipline, clan or card-type icon.
const MARK = /\[\[([^[\]\n]{2,80})\]\]|\[([A-Za-z][A-Za-z '-]{1,30})\]/g;
const cards = new Map();
const icons = new Map();

function lookup(name) {
  const key = name.toLowerCase();
  if (!cards.has(key)) {
    cards.set(
      key,
      fetch(`https://api.krcg.org/card/${encodeURIComponent(name)}`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null)
    );
  }
  return cards.get(key);
}

// Whatever krcg serves is an icon, so the list stays krcg's: all caps asks for the superior discipline
// first, and a tag krcg has no icon for (`[sic]`, `[edit]`) stays as typed.
function icon(tag) {
  const name = tag.toLowerCase().replace(/[^a-z]/g, "");
  const sup = tag === tag.toUpperCase();
  const key = (sup ? "^" : "") + name;
  if (!icons.has(key)) {
    const paths = [
      ...(sup ? [`disc/sup/${name}`] : []),
      `disc/inf/${name}`,
      `clan/${name}`,
      `icon/${name}`,
    ].map((p) => `https://static.krcg.org/svg/${p}.svg`);
    icons.set(
      key,
      Promise.all(
        paths.map((url) =>
          fetch(url, { method: "HEAD" })
            .then((r) => r.ok)
            .catch(() => false)
        )
      ).then((ok) => paths[ok.indexOf(true)] ?? null)
    );
  }
  return icons.get(key);
}

function scan(card) {
  const lang = document.documentElement.lang.slice(0, 2);
  return card._i18n?.[lang]?.url || card.url;
}

let overlay;
function show(src, pinned, x = 0) {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "vekn-card-overlay";
    overlay.append(document.createElement("img"));
    overlay.addEventListener("click", hide);
    document.body.append(overlay);
  }
  overlay.querySelector("img").src = src;
  overlay.classList.toggle("--pinned", pinned);
  overlay.classList.toggle("--left", x > innerWidth / 2);
  overlay.hidden = false;
}

function hide() {
  if (overlay) {
    overlay.hidden = true;
  }
}

function iconNode(tag, src) {
  const el = document.createElement("span");
  el.className = "vekn-icon";
  el.style.setProperty("--vekn-icon", `url("${src}")`);
  el.setAttribute("role", "img");
  el.setAttribute("aria-label", tag);
  el.title = tag;
  return el;
}

// split() with MARK's two groups yields [text, card, tag, text, card, tag, …], the unmatched one undefined.
async function decorate(text) {
  const parts = text.data.split(MARK);
  if (parts.length === 1) {
    return;
  }
  const found = await Promise.all(
    parts.map((part, i) =>
      part === undefined || i % 3 === 0
        ? null
        : i % 3 === 1
          ? lookup(part.trim())
          : icon(part)
    )
  );
  const nodes = parts.map((part, i) => {
    if (part === undefined) {
      return "";
    }
    if (i % 3 === 0) {
      return part;
    }
    if (i % 3 === 2) {
      return found[i] ? iconNode(part, found[i]) : `[${part}]`;
    }
    if (!found[i]) {
      return `[[${part}]]`;
    }
    const src = scan(found[i]);
    const el = document.createElement("span");
    el.className = "vekn-card";
    el.textContent = part.trim();
    el.tabIndex = 0;
    el.setAttribute("role", "button");
    el.addEventListener("mouseenter", (e) => {
      if (matchMedia("(hover: hover)").matches) {
        show(src, false, e.clientX);
      }
    });
    el.addEventListener("mouseleave", () => {
      if (!overlay?.classList.contains("--pinned")) {
        hide();
      }
    });
    el.addEventListener("click", () => show(src, true));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        show(src, true);
      }
    });
    return el;
  });
  text.replaceWith(...nodes);
}

export default apiInitializer((api) => {
  document.addEventListener("keydown", (e) => e.key === "Escape" && hide());
  api.onPageChange(hide);
  api.decorateCookedElement((element) => {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) =>
        node.parentElement.closest("code, pre, a, .vekn-card, .vekn-icon")
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT,
    });
    const texts = [];
    while (walker.nextNode()) {
      if (walker.currentNode.data.includes("[")) {
        texts.push(walker.currentNode);
      }
    }
    texts.forEach(decorate);
  });
});
