import { apiInitializer } from "discourse/lib/api";

// Every section sits in the sidebar, unfolded, for visitors and members alike, while a site has few
// enough to show at once (wiki/design.md#sidebar). Beyond that, Discourse's own choice applies.
const MAX_SECTIONS = 15;

export default apiInitializer((api) => {
  const site = api.container.lookup("service:site");
  const sections = () => {
    const top = site.categories.filter((c) => !c.parent_category_id);
    return top.length <= MAX_SECTIONS ? top.map((c) => c.id) : null;
  };

  api.registerValueTransformer(
    "sidebar-anonymous-default-categories",
    ({ value }) => sections() || value
  );
  const ids = sections();
  if (ids) {
    // In memory only: a member's saved list comes back if the site outgrows the limit.
    api.getCurrentUser()?.set("sidebar_category_ids", ids);
    api.container.lookup("service:sidebar-state").expandSection("categories");
    document.documentElement.classList.add("vekn-sidebar-sections");
  }
});
