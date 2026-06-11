// Toggle mobile nav
function toggleNav() {
    const m = document.getElementById('navMobile');
    const iconMenu = document.getElementById('icon-menu');
    const iconX = document.getElementById('icon-x');
    if (!m) return;
    m.classList.toggle('open');
    if (m.classList.contains('open')) {
        iconMenu.style.display = 'none';
        iconX.style.display = 'block';
    } else {
        iconMenu.style.display = 'block';
        iconX.style.display = 'none';
    }
}

// Search widget tab switching
function switchTab(id, btn) {
    // Deactivate all tabs
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.search-tab').forEach(b => b.classList.remove('active'));
    // Activate selected
    const target = document.getElementById('tab-' + id);
    if (target) target.classList.add('active');
    if (btn) btn.classList.add('active');
}