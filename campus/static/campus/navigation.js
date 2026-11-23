(() => {
  const toggle = document.getElementById("nav-toggle");
  const drawer = document.getElementById("navigation-drawer");
  const content = document.getElementById("navigation-drawer-content");
  const closeButton = document.getElementById("nav-close");
  const mainNavigation = document.getElementById("main-navigation");
  const directoryNavigation = document.getElementById("directory-navigation");
  if (!toggle || !drawer || !content || !closeButton || !mainNavigation || !directoryNavigation || !drawer.showModal) return;

  const mobile = window.matchMedia("(max-width: 750px)");
  // Move the same links into the drawer; restore their desktop positions on resize.
  const panels = [mainNavigation, directoryNavigation].map((panel) => {
    const placeholder = document.createComment("Navigation desktop position");
    panel.before(placeholder);
    return { panel, placeholder };
  });

  const syncState = () => {
    toggle.setAttribute("aria-expanded", String(drawer.open));
    toggle.setAttribute("aria-label", drawer.open ? "Close navigation" : "Open navigation");
    document.documentElement.classList.toggle("nav-open", drawer.open);
  };

  const close = () => {
    if (drawer.open) drawer.close();
    syncState();
  };

  const updateLayout = () => {
    const focused = document.activeElement;
    const navigationFocused = drawer.contains(focused) || panels.some(({ panel }) => panel.contains(focused));
    close();
    toggle.hidden = !mobile.matches;
    panels.forEach(({ panel, placeholder }) => {
      if (mobile.matches) content.append(panel);
      else placeholder.after(panel);
    });

    if (mobile.matches && navigationFocused) {
      toggle.focus();
    } else if (!mobile.matches && (focused === toggle || focused === closeButton)) {
      mainNavigation.querySelector("a").focus();
    } else if (!mobile.matches && navigationFocused) {
      focused.focus();
    }
  };

  toggle.addEventListener("click", () => {
    if (!mobile.matches) return;
    drawer.showModal();
    syncState();
  });
  closeButton.addEventListener("click", close);
  // Native dialog provides Escape dismissal, focus containment and focus return.
  drawer.addEventListener("close", syncState);
  drawer.addEventListener("click", (event) => {
    const bounds = drawer.getBoundingClientRect();
    const outside = event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
    if ((event.target === drawer && outside) || event.target.closest("a")) close();
  });

  mobile.addEventListener("change", updateLayout);
  updateLayout();
})();
