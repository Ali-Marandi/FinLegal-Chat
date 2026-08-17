const state = {
  activeView: 'overview',
  documents: [],
  analyses: [
    { icon: '◈', title: 'Acme acquisition — material obligations', meta: '18 documents · 24 findings', time: '12 min ago' },
    { icon: '⌁', title: 'Vendor MSA portfolio review', meta: '42 documents · 11 findings', time: 'Yesterday' },
    { icon: '✓', title: 'Board pack risk scan', meta: '6 documents · Complete', time: 'Jun 14' }
  ]
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function switchView(view) {
  state.activeView = view;
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === view));
  $$('.view').forEach((section) => section.classList.toggle('active', section.id === `${view}-view`));
  const titles = { overview: 'Executive overview', documents: 'Documents', analysis: 'Analysis runs', controls: 'Controls & audit' };
  $('#page-title').textContent = titles[view] || 'Executive overview';
}

function renderActivity() {
  $('#activity-list').innerHTML = state.analyses.map((item) => `
    <div class="activity-item">
      <div class="activity-icon">${item.icon}</div>
      <div><strong>${item.title}</strong><span>${item.meta}</span></div>
      <time>${item.time}</time>
    </div>`).join('');
}

function renderDocuments(query = '') {
  const filtered = state.documents.filter((doc) => doc.name.toLowerCase().includes(query.toLowerCase()));
  $('#document-count').textContent = `${state.documents.length} document${state.documents.length === 1 ? '' : 's'}`;
  if (!filtered.length) {
    $('#document-table').innerHTML = `<div class="empty-state"><div class="placeholder-icon">▤</div><strong>No documents in this workspace</strong><span>Upload a PDF, DOCX, TXT, Markdown, or CSV file to begin.</span></div>`;
    return;
  }
  $('#document-table').innerHTML = `
    <div class="doc-row head"><span>Document</span><span>Status</span><span>Source</span><span>Added</span></div>
    ${filtered.map((doc) => `<div class="doc-row"><strong>${doc.name}</strong><span class="doc-status">● ${doc.status || 'Ready for analysis'}</span><span class="muted">Local source</span><span class="muted">Now</span></div>`).join('')}`;
}

async function persist() {
  if (window.finlegal?.saveWorkspace) await window.finlegal.saveWorkspace({ documents: state.documents, analyses: state.analyses });
}

async function openDocuments() {
  if (!window.finlegal?.openDocuments) {
    showToast('Document picker is available in the desktop build.');
    return;
  }
  try {
    const picked = await window.finlegal.openDocuments();
    if (!picked.length) return;
    await addDocuments(picked);
  } catch (error) {
    console.error('Document picker failed', error);
    showToast('The document picker could not be opened. Try again.');
  }
}

async function addDocuments(picked) {
  const known = new Set(state.documents.map((doc) => doc.path));
  const additions = picked.filter((doc) => !known.has(doc.path));
  if (!additions.length) {
    showToast('Those documents are already in this workspace.');
    return;
  }
  state.documents.push(...additions);
  renderDocuments();
  await persist();
  switchView('documents');
  showToast(`${additions.length} document${additions.length === 1 ? '' : 's'} added to the workspace.`);
}

function setupEvents() {
  $$('.nav-item').forEach((item) => item.addEventListener('click', () => switchView(item.dataset.view)));
  $$('[data-view-link]').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.viewLink)));
  $('#hero-upload').addEventListener('click', openDocuments);
  $('#upload-documents').addEventListener('click', openDocuments);
  $('#new-analysis').addEventListener('click', () => { switchView('analysis'); $('#analysis-question').focus(); });
  $('#open-settings').addEventListener('click', () => showToast('Workspace settings are restricted to authorized administrators.'));
  $('#document-search').addEventListener('input', (event) => renderDocuments(event.target.value));
  $('#dropzone-browse').addEventListener('click', openDocuments);
  const dropzone = $('#document-dropzone');
  ['dragenter', 'dragover'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add('is-over');
  }));
  ['dragleave', 'drop'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove('is-over');
  }));
  dropzone.addEventListener('drop', async (event) => {
    const files = Array.from(event.dataTransfer?.files || []);
    const supported = /\.(pdf|docx|txt|md|csv)$/i;
    const picked = files.filter((file) => supported.test(file.name)).map((file) => ({
      name: file.name,
      path: file.path,
      status: 'Ready for analysis'
    }));
    if (!picked.length) {
      showToast('Use PDF, DOCX, TXT, Markdown, or CSV sources.');
      return;
    }
    await addDocuments(picked);
  });
  $('#run-analysis').addEventListener('click', async () => {
    const question = $('#analysis-question').value.trim();
    if (!question) { showToast('Add an investigation question before running an analysis.'); return; }
    if (!state.documents.length) { showToast('Upload at least one source document first.'); switchView('documents'); return; }
    const item = { icon: '◈', title: question.length > 52 ? `${question.slice(0, 52)}…` : question, meta: `${state.documents.length} documents · Queued`, time: 'Just now' };
    state.analyses.unshift(item);
    renderActivity();
    await persist();
    showToast('Analysis queued. Source validation will begin in the secure workspace.');
    switchView('overview');
  });
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      switchView('analysis');
      $('#analysis-question').focus();
    }
    if (event.key === 'Escape' && document.activeElement?.tagName === 'TEXTAREA') {
      document.activeElement.blur();
    }
  });
}

(async function init() {
  try {
    const saved = window.finlegal?.loadWorkspace ? await window.finlegal.loadWorkspace() : null;
    if (saved?.documents) state.documents = saved.documents;
    if (saved?.analyses?.length) state.analyses = saved.analyses;
  } catch (error) {
    console.warn('Workspace state unavailable', error);
  }
  renderActivity();
  renderDocuments();
  setupEvents();
})();
