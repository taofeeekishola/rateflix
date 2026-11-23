// Light/dark theme switch. The saved choice is applied by a small script in <head>
// before the page paints; this file wires up the toggle buttons.
(function () {
  var root = document.documentElement;

  function current() {
    return root.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light';
  }

  function label(btn) {
    var next = current() === 'dark' ? 'light' : 'dark';
    btn.setAttribute('aria-label', 'Switch to ' + next + ' theme');
    btn.setAttribute('title', 'Switch to ' + next + ' theme');
  }

  document.querySelectorAll('[data-rf-theme-toggle]').forEach(function (btn) {
    label(btn);
    btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-bs-theme', next);
      try { localStorage.setItem('rf-theme', next); } catch (e) { /* private mode: still switches for this page */ }
      document.querySelectorAll('[data-rf-theme-toggle]').forEach(label);
    });
  });
})();
