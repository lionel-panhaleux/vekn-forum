import { apiInitializer } from "discourse/lib/api";

// `[[Card Name]]` in a post shows the card's scan: on hover where there is one, on tap otherwise.
// krcg resolves the name (English or translated, fuzzy) — card knowledge stays upstream.
const CARD = /\[\[([^[\]\n]{2,80})\]\]/g;
const cards = new Map();

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

async function decorate(text) {
  const parts = text.data.split(CARD);
  if (parts.length === 1) {
    return;
  }
  const found = await Promise.all(
    parts.map((part, i) => (i % 2 ? lookup(part.trim()) : null))
  );
  const nodes = parts.map((part, i) => {
    if (!(i % 2)) {
      return part;
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
        node.parentElement.closest("code, pre, a, .vekn-card")
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT,
    });
    const texts = [];
    while (walker.nextNode()) {
      if (walker.currentNode.data.includes("[[")) {
        texts.push(walker.currentNode);
      }
    }
    texts.forEach(decorate);
  });
});
