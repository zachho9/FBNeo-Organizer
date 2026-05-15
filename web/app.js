'use strict';

let allPlatforms = [];
let selectedPlatforms = new Set();
let allGames = [];
let allowlist = [];
let activeTab = 'platforms';
let isRunning = false;
let lastTab = 'platforms';

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Tab navigation ────────────────────────────────────────────────────────────

function switchTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.remove('hidden');
    const navBtn = document.querySelector('[data-tab="' + tab + '"]');
    if (navBtn) navBtn.classList.add('active');
    updateRunButton();
    if (tab === 'allowlist' && allGames.length === 0) loadGames();
}

function switchInnerTab(inner) {
    document.querySelectorAll('.inner-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-inner="' + inner + '"]').classList.add('active');
    document.getElementById('inner-browse').classList.toggle('hidden', inner !== 'browse');
    document.getElementById('inner-mylist').classList.toggle('hidden', inner !== 'mylist');
}

// ── Settings ──────────────────────────────────────────────────────────────────

document.getElementById('browse-btn').addEventListener('click', async () => {
    const path = await window.pywebview.api.browse_folder();
    if (path) {
        document.getElementById('fbneo-path').value = path;
        await validatePath(path);
    }
});

document.getElementById('fbneo-path').addEventListener('change', async (e) => {
    if (e.target.value.trim()) await validatePath(e.target.value.trim());
});

async function validatePath(path) {
    const result = await window.pywebview.api.set_fbneo_dir(path);
    const statusEl = document.getElementById('path-status');
    const derivedEl = document.getElementById('derived-paths');
    if (result.ok) {
        statusEl.textContent = '✓ FBNeo executable found';
        statusEl.className = 'status-ok';
        document.getElementById('rom-path').textContent = path + '\\roms\\arcade';
        document.getElementById('gone-path').textContent = path + '\\roms\\arcade\\gone';
        derivedEl.classList.remove('hidden');
        allPlatforms = [];
        allGames = [];
        await loadPlatforms();
    } else {
        statusEl.textContent = result.error;
        statusEl.className = 'status-error';
        derivedEl.classList.add('hidden');
    }
    updateRunButton();
}

// ── Platforms ─────────────────────────────────────────────────────────────────

async function loadPlatforms() {
    const loadingEl = document.getElementById('platforms-loading');
    const listEl = document.getElementById('platforms-list');
    const errorEl = document.getElementById('platforms-error');
    loadingEl.classList.remove('hidden');
    listEl.classList.add('hidden');
    errorEl.classList.add('hidden');

    const result = await window.pywebview.api.get_platforms();
    loadingEl.classList.add('hidden');

    if (result.error) {
        errorEl.textContent = result.error;
        errorEl.classList.remove('hidden');
        updateRunButton();
        return;
    }

    allPlatforms = result;
    renderPlatforms();
    listEl.classList.remove('hidden');
    updateRunButton();
}

function renderPlatforms() {
    document.getElementById('platforms-list').innerHTML = allPlatforms.map(p => `
        <label class="platform-item">
            <input type="checkbox" value="${escapeHtml(p.name)}"
                ${selectedPlatforms.has(p.name) ? 'checked' : ''}
                onchange="togglePlatform('${escapeHtml(p.name)}', this.checked)">
            <span class="platform-name">${escapeHtml(p.name)}</span>
            <span class="platform-count">${p.count.toLocaleString()}</span>
        </label>`).join('');
}

function togglePlatform(name, checked) {
    if (checked) selectedPlatforms.add(name);
    else selectedPlatforms.delete(name);
    updateRunButton();
}

// ── Game browser ──────────────────────────────────────────────────────────────

async function loadGames() {
    const loadingEl = document.getElementById('game-loading');
    const errorEl = document.getElementById('game-error');
    loadingEl.classList.remove('hidden');
    errorEl.classList.add('hidden');

    const result = await window.pywebview.api.get_games();
    loadingEl.classList.add('hidden');

    if (result.error) {
        errorEl.textContent = result.error;
        errorEl.classList.remove('hidden');
        return;
    }

    allGames = result;
    renderGameList('');
}

document.getElementById('game-search').addEventListener('input', (e) => {
    renderGameList(e.target.value.toLowerCase());
});

function renderGameList(query) {
    const filtered = query
        ? allGames.filter(g =>
            g.title.toLowerCase().includes(query) ||
            g.name.toLowerCase().includes(query))
        : allGames;

    const visible = filtered.slice(0, 200);
    let html = visible.map(g => {
        const inList = allowlist.includes(g.name);
        return `<div class="game-item${inList ? ' in-list' : ''}">
            <span class="game-title">${escapeHtml(g.title)}</span>
            <span class="game-short">${escapeHtml(g.name)}</span>
            ${inList
                ? '<span class="game-added">✓</span>'
                : `<button class="add-btn" onclick="addToAllowlist('${escapeHtml(g.name)}')">+</button>`}
        </div>`;
    }).join('');

    if (filtered.length > 200) {
        html += `<p class="hint">Showing 200 of ${filtered.length.toLocaleString()} — type to filter</p>`;
    }
    document.getElementById('game-list').innerHTML = html;
}

// ── Allowlist management ──────────────────────────────────────────────────────

async function loadAllowlist() {
    allowlist = await window.pywebview.api.get_allowlist();
    renderMyList();
    updateRunButton();
}

function addToAllowlist(name) {
    if (!allowlist.includes(name)) {
        allowlist.push(name);
        window.pywebview.api.save_allowlist(allowlist);
        renderGameList(document.getElementById('game-search').value.toLowerCase());
        renderMyList();
        updateRunButton();
    }
}

function removeFromAllowlist(name) {
    allowlist = allowlist.filter(n => n !== name);
    window.pywebview.api.save_allowlist(allowlist);
    renderGameList(document.getElementById('game-search').value.toLowerCase());
    renderMyList();
    updateRunButton();
}

function renderMyList() {
    const container = document.getElementById('allowlist-items');
    const emptyMsg = document.getElementById('allowlist-empty');
    if (allowlist.length === 0) {
        container.innerHTML = '';
        emptyMsg.classList.remove('hidden');
    } else {
        emptyMsg.classList.add('hidden');
        container.innerHTML = allowlist.map(name =>
            `<div class="allowlist-item">
                <span>${escapeHtml(name)}</span>
                <button class="remove-btn" onclick="removeFromAllowlist('${escapeHtml(name)}')">✕</button>
            </div>`
        ).join('');
    }
}

// ── Run button state ──────────────────────────────────────────────────────────

function updateRunButton() {
    const runBtn = document.getElementById('run-btn');
    let canRun = false;
    if (activeTab === 'platforms') canRun = selectedPlatforms.size > 0 && allPlatforms.length > 0;
    else if (activeTab === 'allowlist') canRun = allowlist.length > 0;
    runBtn.disabled = !canRun || isRunning;
}

// ── Run ───────────────────────────────────────────────────────────────────────

document.getElementById('run-btn').addEventListener('click', async () => {
    const dryRun = document.getElementById('dry-run').checked;
    const mode = activeTab;
    const selected = mode === 'platforms' ? [...selectedPlatforms] : [];
    lastTab = activeTab;

    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.getElementById('tab-results').classList.remove('hidden');
    document.getElementById('results-loading').classList.remove('hidden');
    document.getElementById('results-content').classList.add('hidden');
    isRunning = true;
    updateRunButton();

    const result = await window.pywebview.api.run(mode, selected, dryRun);

    isRunning = false;
    document.getElementById('results-loading').classList.add('hidden');
    document.getElementById('results-content').classList.remove('hidden');
    renderResults(result);
});

function renderResults(result) {
    const summaryEl = document.getElementById('results-summary');
    const warningsEl = document.getElementById('results-warnings');

    if (result.error) {
        summaryEl.innerHTML = `<div class="error-msg">${escapeHtml(result.error)}</div>`;
        warningsEl.innerHTML = '';
        return;
    }

    const counts = result.counts;
    const labelKeys = result.label_keys;
    const keptTotal = labelKeys.reduce((s, k) => s + (counts[k] || 0), 0) + (counts['BIOS'] || 0);
    const parts = labelKeys.filter(k => counts[k] > 0).map(k => `${escapeHtml(k)}: ${counts[k].toLocaleString()}`);
    if (counts['BIOS'] > 0) parts.push(`BIOS: ${counts['BIOS'].toLocaleString()}`);
    const action = result.dry_run ? 'Would move' : 'Moved';

    summaryEl.innerHTML = `
        <div class="result-row">
            <span class="result-label">Kept</span>
            <span class="result-value">${keptTotal.toLocaleString()}</span>
            <span class="result-detail">${parts.join(', ')}</span>
        </div>
        <div class="result-row">
            <span class="result-label">${escapeHtml(action)}</span>
            <span class="result-value">${(counts['moved'] || 0).toLocaleString()}</span>
            <span class="result-detail">→ arcade\\gone\\</span>
        </div>
        ${(counts['skipped_duplicate'] || 0) > 0
            ? `<div class="result-row"><span class="result-label">Skipped</span><span class="result-value">${counts['skipped_duplicate'].toLocaleString()}</span><span class="result-detail">duplicates in gone\\</span></div>`
            : ''}
        ${(counts['move_errors'] || 0) > 0
            ? `<div class="result-row result-error"><span class="result-label">Errors</span><span class="result-value">${counts['move_errors']}</span><span class="result-detail">failed to move</span></div>`
            : ''}`;

    if (result.warnings && result.warnings.length > 0) {
        warningsEl.innerHTML = `<h3>Warnings (${result.warnings.length})</h3>
            <ul class="warnings-list">${result.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}</ul>`;
    } else {
        warningsEl.innerHTML = '';
    }
}

document.getElementById('back-btn').addEventListener('click', () => switchTab(lastTab));

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('pywebviewready', async () => {
    const config = await window.pywebview.api.get_config();
    if (config.fbneo_dir) document.getElementById('fbneo-path').value = config.fbneo_dir;
    await loadAllowlist();

    if (!config.valid) {
        if (config.fbneo_dir) {
            document.getElementById('path-status').textContent = 'FBNeo executable not found at this path';
            document.getElementById('path-status').className = 'status-error';
        }
        switchTab('settings');
    } else {
        const path = config.fbneo_dir;
        document.getElementById('path-status').textContent = '✓ FBNeo executable found';
        document.getElementById('path-status').className = 'status-ok';
        document.getElementById('rom-path').textContent = path + '\\roms\\arcade';
        document.getElementById('gone-path').textContent = path + '\\roms\\arcade\\gone';
        document.getElementById('derived-paths').classList.remove('hidden');
        await loadPlatforms();
        switchTab('platforms');
    }
});
