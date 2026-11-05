window.Appearance = {
  bindToggle(button) {
    const root = document.documentElement;
    const sync = () => {
      button.setAttribute('aria-pressed', String(root.dataset.theme === 'dark'));
      button.setAttribute('aria-label', 'Switch colour theme');
      button.title = 'Switch colour theme';
    };
    button.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('letterkeep-theme', root.dataset.theme); } catch {}
      sync();
    });
    sync();
  }
};
