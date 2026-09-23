/* jobhunt-agent - the product interface (no framework, no build step).
 *
 * Every number on screen comes from the deployment's own endpoints: the tracker, the run audit, the mailbox
 * ledgers. Nothing is mocked, and a value the deployment cannot know is shown as unknown rather than guessed.
 */
'use strict';

const S = {                     // session state
  view: 'tracker',
  data: {},                     // per-view payloads
  tracker: {rows: [], status: 'all', q: '', sort: 'date', dir: -1},
  gate: null,                   // /api/auth/status
  dials: null,
  operatorToken: sessionStorage.getItem('jha_token') || '',
};
const $ = (sel) => document.querySelector(sel);
const el = (id) => document.getElementById(id);
const esc = (v) => String(v == null ? '' : v)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

async function api(path, opts) {
  const o = Object.assign({headers: {}}, opts || {});
  if (S.operatorToken) o.headers['X-Dashboard-Token'] = S.operatorToken;
  if (o.body) o.headers['Content-Type'] = 'application/json';
  const r = await fetch(path, o);
  let j = null;
  try { j = await r.json(); } catch (e) { j = {ok: false, error: 'unreadable response'}; }
  return Object.assign({_status: r.status}, j);
}

/* ------------------------------------------------------------------ helpers */
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function money(v, dp) {
  const n = Number(v || 0);
  return '$' + n.toFixed(dp === undefined ? (n < 10 ? 3 : 2) : dp);
}
function pretty(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  if (isNaN(d)) return String(iso).slice(0, 10);
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}
function isoFromNotes(notes) {
  const m = String(notes || '').match(/\b(20\d\d-\d\d-\d\d)\b/);
  return m ? m[1] : '';
}
/* The tracker renders this many rows. It used to be a bare 300 inside the map, under a heading that counted
 * every matching row, so the table could show fewer rows than it claimed. */
const TRACKER_PAGE = 300;

/* A salary is a RANGE, and a range is read at a glance: one line, an en dash with no spaces, tabular figures.
 * "EUR 4,400 - 5,000" wrapping onto two lines in a 270-row table is what made the column unreadable. */
function salaryCell(raw) {
  const t = String(raw || '').trim();
  if (!t || t === '-') return '<span class="miss">-</span>';
  const m = t.match(/^\s*([^\d]*)([\d][\d.,]*)\s*[-\u2013\u2014]\s*([\d][\d.,]*)\s*$/);
  if (m) {
    const unit = (m[1] || '').trim();
    return `<span class="amt">${esc(unit ? unit + '\u00a0' : '')}${esc(m[2])}</span>`
      + `<span class="sep">\u2013</span><span class="amt">${esc(m[3])}</span>`;
  }
  return esc(t);
}

function salaryFromNotes(notes) {
  const t = String(notes || '');
  const m = t.match(/(?:EUR|€)\s?([\d][\d.,]{2,})\s*(?:-|to|-)\s*(?:EUR|€)?\s?([\d][\d.,]{2,})/i);
  if (!m) {
    const one = t.match(/(?:salary|salaris|gross)[^\d]{0,12}([\d][\d.,]{3,})/i);
    return one ? '€' + one[1] : '';
  }
  return '€' + m[1] + '-' + m[2];
}
function gateLine(row) {
  const n = String(row.notes || '');
  const ind = /IND/i.test(n) ? 'IND ✓' : 'IND ?';
  const fit = row.fit ? `${row.fit}/5` : '-';
  const dutch = /dutch|nederlands/i.test(n) ? 'NL-check ✓' : 'NL-check -';
  return `${fit} fit · ${ind} · ${dutch}`;
}
function statusClass(st) {
  /* One class per state, so an interview cannot look like a plain submission and a blocked row cannot look
   * like the primary action. The names match the tones in app.css. */
  const s = String(st || '').toLowerCase();
  if (s === 'offer') return 'offer';
  if (s === 'interview') return 'interview';
  if (s === 'rejected') return 'rejected';
  if (s === 'blocked') return 'blocked';
  if (s === 'submitted' || s === 'emailed' || s === 'applied') return 'pass';
  return 'wait';
}
function docsHtml(docs, slug) {
  if (!docs || !docs.length) return '<span class="miss">no documents on file</span>';
  return docs.map((d) => `<a href="${esc(d.url)}" target="_blank" rel="noopener" ` +
    `title="${esc(d.label)} · ${Math.round(d.bytes / 1024)} KB">${esc(d.name)}</a>`).join('');
}

/* ------------------------------------------------------------------ sign-in */
function renderGate() {
  const g = S.gate || {};
  const perms = g.permissions || [
    {service: 'Gmail', why: 'Read-only, to triage replies and detect interview invites'},
    {service: 'Google Calendar', why: 'To schedule and show interview alerts'},
    {service: 'Google Sheets', why: 'This is where the application tracker lives'},
  ];
  const clientReady = g.client_configured !== false;
  const body = `
    <div class="wordmark">jobhunt-agent</div>
    <div class="tag">automated applications, tailored per role</div>
    <button class="gbtn" id="goog" ${clientReady ? '' : 'disabled'}>
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
        <path fill="#4285F4" d="M17.6 9.2c0-.6-.1-1.2-.2-1.7H9v3.3h4.8c-.2 1.1-.8 2-1.8 2.7v2.2h2.9c1.7-1.6 2.7-3.9 2.7-6.5z"/>
        <path fill="#34A853" d="M9 17.6c2.4 0 4.5-.8 6-2.2l-2.9-2.2c-.8.5-1.8.9-3.1.9-2.4 0-4.4-1.6-5.1-3.8H.9v2.3C2.4 15.6 5.5 17.6 9 17.6z"/>
        <path fill="#FBBC05" d="M3.9 10.3c-.2-.6-.3-1.2-.3-1.8s.1-1.3.3-1.8V4.4H.9C.3 5.8 0 7.4 0 9s.3 3.2.9 4.6l3-2.3z"/>
        <path fill="#EA4335" d="M9 3.5c1.3 0 2.5.5 3.4 1.3l2.6-2.6C13.5.8 11.4 0 9 0 5.5 0 2.4 2 0.9 4.9l3 2.3C4.6 5.1 6.6 3.5 9 3.5z"/>
      </svg>
      Continue with Google
    </button>
    ${clientReady ? '' : `<p class="warn" style="margin-top:14px">This host has no Google OAuth client
      configured, so sign-in cannot start. Put the client's JSON at
      <span class="mono">${esc(g.client_source || '~/.hermes/google_client_secret.json')}</span> and reload.</p>`}
    <div class="perm">
      <p class="note" style="margin:0 0 6px">jobhunt-agent asks for three permissions:</p>
      ${perms.map((p) => `<div class="p"><b>${esc(p.service)}</b><span>${esc(p.why)}</span></div>`).join('')}
    </div>
    <p class="fineprint">It reads your mail so it can triage replies and notice interview invitations, reads
      your calendar to schedule and show those interviews, and writes the tracker to a spreadsheet in your own
      Drive. It does not send mail from your mailbox as part of these three permissions, and it never posts to
      LinkedIn.</p>
    <p class="fineprint">You can revoke the connection at any time from your Google account settings
      (<a href="${esc(g.can_revoke_at || 'https://myaccount.google.com/permissions')}" target="_blank"
      rel="noopener">myaccount.google.com/permissions</a>). Revoking it stops the hunt immediately; the tracker
      stays in your Drive.</p>
    ${clientReady ? '' : `<p class="fineprint"><button class="btn ghost" id="skip">Continue without Google
      (local mode - the dashboard still reads this host's tracker)</button></p>`}
    <p class="fineprint" id="gate-msg"></p>`;
  el('gate-body').innerHTML = body;
  el('gate').hidden = false;
  const go = el('goog');
  if (go) go.onclick = startSignIn;
  const skip = el('skip');
  if (skip) skip.onclick = () => { el('gate').hidden = true; boot(true); };
}

async function startSignIn() {
  const msg = el('gate-msg');
  msg.textContent = 'Opening Google...';
  const r = await api('/api/auth/start');
  if (!r.ok) { msg.textContent = r.error || 'could not start sign-in'; return; }
  window.location.href = r.url;
}

/* ------------------------------------------------------------------ first-run setup */
function renderSetup() {
  const opts = (S.dials && S.dials.countries && S.dials.countries.options) ||
    ['NL','DE','BE','IE','AT','ES','FR','SE','DK','PL'];
  const cadence = (S.dials && S.dials.cadence && S.dials.cadence.options) ||
    ['every 720m','every 360m','every 180m','every 120m','every 60m'];
  el('setup-body').innerHTML = `
    <div class="wordmark">Set up the hunt</div>
    <div class="tag">three dials, then it runs on its own</div>
    <p class="note">The dashboard is empty because no targeting exists yet. These are the same dials you can
      change later in Settings.</p>

    <fieldset style="margin-top:16px">
      <legend>1. Targeting</legend>
      <label class="f">Primary market (the one you are actually in)</label>
      <div class="chips" id="s-primary"></div>
      <label class="f">Secondary markets</label>
      <div class="chips" id="s-secondary"></div>
      <label class="f">Effort split - primary % of the sweep</label>
      <input type="number" id="s-share" value="80" min="10" max="100" step="5">
      <label class="f">Role keywords (one per line, up to 8)</label>
      <textarea id="s-roles" rows="4" style="background:#fff;border:1px solid var(--rule);padding:6px 8px;
        font:12.5px var(--mono);width:100%">Data Engineer
Analytics Engineer
Data Platform Engineer</textarea>
    </fieldset>

    <fieldset style="margin-top:14px">
      <legend>2. Salary</legend>
      <div class="row">
        <div><label class="f">Current gross / month</label>
          <input type="number" id="s-current" value="3300"></div>
        <div><label class="f">Target floor (skip below this)</label>
          <input type="number" id="s-floor" value="4000"></div>
      </div>
      <div class="row" style="margin-top:8px">
        <div><label class="f">Ask from</label><input type="number" id="s-ask-lo" value="4400"></div>
        <div><label class="f">Ask to</label><input type="number" id="s-ask-hi" value="5000"></div>
      </div>
      <p class="note">Quoted in application emails as a range, never below your floor.</p>
    </fieldset>

    <fieldset style="margin-top:14px">
      <legend>3. Schedule</legend>
      <div class="row">
        <div><label class="f">Sweep (discovery + applications)</label>
          <select id="s-sweep">${cadence.map((c) => `<option value="${esc(c)}"
            ${c === 'every 180m' ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select></div>
        <div><label class="f">Mailbox check</label>
          <select id="s-mail">
            <option value="every 60m">every 60m</option>
            <option value="every 20m" selected>every 20m</option>
            <option value="every 10m">every 10m</option>
          </select></div>
      </div>
      <p class="note">The sweep is the token-heavy job; the mailbox check is what notices a reply quickly.</p>
    </fieldset>

    <div style="margin-top:16px;display:flex;gap:10px;align-items:center">
      <button class="btn primary" id="s-save">Start the hunt</button>
      <span class="saved" id="s-msg"></span>
    </div>
    <p class="fineprint" id="s-token"></p>`;
  el('setup').hidden = false;

  const chips = (host, list, selected) => {
    el(host).innerHTML = list.map((c) => `<label class="${selected.includes(c) ? 'on' : ''}">
      <input type="checkbox" value="${esc(c)}" ${selected.includes(c) ? 'checked' : ''}>${esc(c)}</label>`).join('');
    el(host).querySelectorAll('input').forEach((cb) => {
      cb.onchange = () => cb.closest('label').classList.toggle('on', cb.checked);
    });
  };
  chips('s-primary', opts, ['NL']);
  chips('s-secondary', opts, []);
  const pick = (host) => Array.from(el(host).querySelectorAll('input:checked')).map((i) => i.value);
  el('s-save').onclick = async () => {
    const payload = {
      countries: {primary: pick('s-primary'), secondary: pick('s-secondary'),
                  primary_share: Number(el('s-share').value) / 100},
      roles: el('s-roles').value.split('\n').map((x) => x.trim()).filter(Boolean),
      salary: {current_gross: Number(el('s-current').value), target_floor: Number(el('s-floor').value),
               ask_range: [Number(el('s-ask-lo').value), Number(el('s-ask-hi').value)]},
      schedule: {sweep: el('s-sweep').value, mailbox: el('s-mail').value},
    };
    await saveDials(payload, 's-msg', 's-token', () => { el('setup').hidden = true; boot(true); });
  };
}

/* ------------------------------------------------------------------ the rail + views */
const VIEWS = [
  ['tracker', 'Tracker'], ['applications', 'Applications'], ['alerts', 'Alerts'],
  ['cost', 'Cost'], ['plan', 'Plan'], ['settings', 'Settings'],
];
/* Repaint without stealing the caret.
 *
 * Typing in the filter field re-rendered the whole section, which destroyed and rebuilt the input: focus and
 * caret position went with it, so a word typed at reading speed landed out of order. Capture the focused
 * element and its caret first, repaint, then put both back. */
function withFocus(paint) {
  const before = document.activeElement;
  const id = before && before.id ? before.id : '';
  const caret = before && typeof before.selectionStart === 'number' ? before.selectionStart : null;
  paint();
  if (!id) return;
  const again = el(id);
  if (!again || typeof again.focus !== 'function') return;
  again.focus();
  if (caret !== null && typeof again.setSelectionRange === 'function') {
    try { again.setSelectionRange(caret, caret); } catch (e) { /* not a text field */ }
  }
}

function renderRail(state) {
  const counts = (state && state.counts) || {};
  el('rail-tenant').textContent = (state && state.tenant && state.tenant.name) || 'this host';
  el('nav').innerHTML = VIEWS.map(([id, label]) => {
    let badge = '';
    if (id === 'tracker') badge = state && state.total_rows ? state.total_rows : '';
    if (id === 'alerts') badge = (S.data.alerts && S.data.alerts.counts && S.data.alerts.counts.alerts) || '';
    if (id === 'applications') badge = counts.Emailed || counts.Submitted || '';
    return `<button data-view="${id}" class="${S.view === id ? 'on' : ''}">${label}
      ${badge ? `<i>${esc(badge)}</i>` : ''}</button>`;
  }).join('');
  el('nav').querySelectorAll('button').forEach((b) => { b.onclick = () => go(b.dataset.view); });
  const h = (S.data.state && S.data.state.hunt) || {};
  const u = (S.data.state && S.data.state.usage) || {};
  el('rail-foot').innerHTML = `sweep <b>${esc((S.data.state && S.data.state.dials && S.data.state.dials.schedule &&
    S.data.state.dials.schedule.sweep) || '-')}</b><br>
    jobs <b>${esc(h.jobs_active || 0)}/${esc(h.jobs_total || 0)} live</b><br>
    plan <b>${esc((S.data.state && S.data.state.plan) || '-')}</b><br>
    today <b>${esc(new Date().toISOString().slice(0, 10))}</b>`;
}
/* The dark console is the product's own look; light is a deliberate choice, kept in this browser. */
function applyTheme(name) {
  if (name === 'light' || name === 'dark') document.documentElement.dataset.theme = name;
  else delete document.documentElement.dataset.theme;
}
function themePreference() {
  try { return localStorage.getItem('jha_theme') || ''; } catch (e) { return ''; }
}
function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  applyTheme(next);
  try { localStorage.setItem('jha_theme', next); } catch (e) { /* private mode: for this session only */ }
  render();
}

function go(view) {
  S.view = view;
  renderRail(S.data.state);
  render();
}
async function render() {
  const map = {tracker: viewTracker, applications: viewApplications, alerts: viewAlerts,
               cost: viewCost, plan: viewPlan, settings: viewSettings};
  const titles = {tracker: 'Tracker', applications: 'Applications', alerts: 'Alerts', cost: 'Cost',
                  plan: 'Plan', settings: 'Settings'};
  el('section-title').textContent = titles[S.view];
  const st = S.data.state || {};
  const h = st.hunt || {};
  const light = document.documentElement.dataset.theme === 'light';
  el('topmeta').innerHTML = `<span>${esc((st.tenant && st.tenant.name) || '')} ·
      ${esc(pretty(st.generated_at))}<br>hunt ${h.live ? 'live' : 'idle'} ·
      ${esc(st.total_rows || 0)} tracked rows</span>
    <button class="tbtn" id="theme" title="Switch the surface ladder">${light ? 'Dark' : 'Light'}</button>`;
  const tb = el('theme');
  if (tb) tb.onclick = toggleTheme;
  try {
    await map[S.view]();
  } catch (e) {
    el('view').innerHTML = `<p class="warn">This section could not be loaded: ${esc(e.message)}</p>`;
  }
}

/* ---- Tracker */
async function viewTracker() {
  if (!S.data.tracker) {
    const r = await api('/api/applications?limit=400');
    S.data.tracker = {rows: r.rows || [], total: r.total || 0};
  }
  const all = S.data.tracker.rows.map((r) => Object.assign({}, r, {
    date: isoFromNotes(r.notes), salary: salaryFromNotes(r.notes),
  }));
  const counts = {};
  all.forEach((r) => { counts[r.status] = (counts[r.status] || 0) + 1; });
  const statuses = ['all'].concat(Object.keys(counts).sort((a, b) => counts[b] - counts[a]));
  let rows = all.filter((r) => S.tracker.status === 'all' ||
    String(r.status).toLowerCase() === S.tracker.status.toLowerCase());
  if (S.tracker.q) {
    const q = S.tracker.q.toLowerCase();
    rows = rows.filter((r) => [r.company, r.role, r.location, r.status].join(' ').toLowerCase().includes(q));
  }
  const key = {company: (r) => r.company, role: (r) => r.role, status: (r) => r.status, fit: (r) => Number(r.fit || 0),
               date: (r) => r.date, location: (r) => r.location}[S.tracker.sort] || ((r) => r.id);
  rows = rows.slice().sort((a, b) => {
    const x = key(a), y = key(b);
    if (typeof x === 'number' && typeof y === 'number') return (x - y) * S.tracker.dir;
    return String(x || '').localeCompare(String(y || '')) * S.tracker.dir;
  });
  const th = (id, label, num) => `<th class="sortable ${num ? 'num' : ''}" data-sort="${id}">${label}${
    S.tracker.sort === id ? `<span class="arrow">${S.tracker.dir < 0 ? ' ▾' : ' ▴'}</span>` : ''}</th>`;
  withFocus(() => { el('view').innerHTML = `
    <div class="kicker">Section 01 / tracker</div>
    <h2 class="sec">Tracker <span class="count">${rows.length} of ${all.length} rows shown</span></h2>
    <div class="filters">
      ${statuses.map((s) => `<button data-st="${esc(s)}" class="${S.tracker.status === s ? 'on' : ''}">
        ${esc(s === 'all' ? 'All' : s)} ${s === 'all' ? all.length : counts[s]}</button>`).join('')}
      <input id="tq" placeholder="filter company, role, location" value="${esc(S.tracker.q)}">
      <button class="btn ghost grow" id="tref">refresh</button>
    </div>
    <div class="tablewrap"><table><thead><tr>
      ${th('company', 'Company / role')}${th('status', 'Status')}
      ${th('date', 'Applied')}${th('location', 'Location')}${th('fit', 'Fit', true)}
      <th>Salary</th><th>Source</th>
    </tr></thead><tbody>
    ${rows.length ? rows.slice(0, TRACKER_PAGE).map((r) => `<tr>
      <td class="who" title="${esc(r.company)} - ${esc(r.role)}"><div class="l1"><span
        class="co">${esc(r.company)}</span>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener"
        title="open the posting">↗</a>` : ''}</div><span class="role">${esc(r.role)}</span></td>
      <td><span class="st ${statusClass(r.status)}">${esc(r.status)}</span></td>
      <td class="date">${esc(pretty(r.date))}</td>
      <td class="loc" title="${esc(r.location || '')}">${esc(r.location || '-')}</td>
      <td class="num">${esc(r.fit || '-')}</td>
      <td class="salary">${salaryCell(r.salary)}</td>
      <td class="src" title="${esc(r.ats || r.source || '')}">${esc(r.ats || r.source || '-')}</td>
    </tr>`).join('') : `<tr><td colspan="7" class="empty">Nothing matches this filter.</td></tr>`}
    </tbody></table></div>
    ${rows.length > TRACKER_PAGE ? `<p class="note">Showing the first ${TRACKER_PAGE} of ${rows.length}
      matching rows. Narrow the filter to see the rest: the count above is the total, this table is not.</p>` : ''}
    <p class="note">Sortable by any column; filters are the status chips. The tracker's source of truth is the
      Google Sheet linked in the Plan section - this view reads the same rows.</p>`; });
  el('view').querySelectorAll('th.sortable').forEach((h) => {
    h.onclick = () => {
      const id = h.dataset.sort;
      S.tracker.dir = S.tracker.sort === id ? -S.tracker.dir : (id === 'fit' ? -1 : 1);
      S.tracker.sort = id;
      render();
    };
  });
  el('view').querySelectorAll('[data-st]').forEach((b) => {
    b.onclick = () => { S.tracker.status = b.dataset.st; render(); };
  });
  el('tq').oninput = (e) => { S.tracker.q = e.target.value; clearTimeout(S._t);
    S._t = setTimeout(render, 220); };
  el('tref').onclick = async () => { S.data.tracker = null; await render(); };
}

/* ---- Applications */
async function viewApplications() {
  if (!S.data.alerts) S.data.alerts = await api('/api/alerts');
  const a = S.data.alerts;
  const seen = new Set();
  const feed = [];
  ['alerts', 'receipts', 'muted'].forEach((group) => (a[group] || []).forEach((r) => {
    if (seen.has(r.id)) return;
    seen.add(r.id);
    feed.push(Object.assign({group}, r));
  }));
  feed.sort((x, y) => String(y.last_date).localeCompare(String(x.last_date)));
  el('view').innerHTML = `
    <div class="kicker">Section 02 / applications</div>
    <h2 class="sec">Applications <span class="count">${feed.length} with a record on this host</span></h2>
    <p class="note">One entry per application: what it passed, and the documents generated for it. A document
      link opens the file the engine actually sent, not a copy.</p>
    <div class="feed">
      ${feed.length ? feed.slice(0, 60).map((r) => `<div class="item">
        <div>
          <div class="who">${esc(r.company)} <span class="st ${statusClass(r.status)}">${esc(r.status)}</span></div>
          <div class="what">${esc(r.role)}${r.location ? ' · ' + esc(r.location) : ''} ·
            ${esc(gateLine(r))}</div>
          <div class="docs">${docsHtml(r.docs, r.slug)}</div>
        </div>
        <div class="when">${esc(pretty(r.last_date))}<br>${r.url ? `<a href="${esc(r.url)}"
          target="_blank" rel="noopener">posting ↗</a>` : ''}</div>
      </div>`).join('') : '<div class="empty">No applications recorded yet.</div>'}
    </div>`;
}

/* ---- Alerts */
async function viewAlerts() {
  if (!S.data.alerts) S.data.alerts = await api('/api/alerts');
  const a = S.data.alerts;
  const alerts = a.alerts || [];
  const muted = a.muted || [];
  const receipts = a.receipts || [];
  const inv = a.invitations || [];
  el('view').innerHTML = `
    <div class="kicker">Section 03 / alerts</div>
    <h2 class="sec">Alerts <span class="count">${alerts.length} need you</span></h2>
    ${(a.backoff && a.backoff.active) ? `<div class="backoff"><span class="dot"></span>${esc(a.backoff.line)}
      <span class="k">Turn this off in Settings</span></div>` : ''}
    ${(a.budget && a.budget.line) ? `<div class="backoff budget"><span class="dot"></span>${esc(a.budget.line)}
      <span class="k">Budget ${money(((a.budget.budget) || {}).daily_usd || 0, 2)}/day ·
        ${money(a.budget.spent_today_usd || 0, 2)} spent today</span></div>` : ''}
    ${alerts.length ? alerts.map((r) => `<div class="alert ${r.status === 'Offer' ? 'offer' : ''}">
      <div class="h"><b>${esc(r.company)}</b>
        <span class="st ${statusClass(r.status)}">${esc(r.status)}</span>
        <span class="count">${esc(r.role)}</span>
        <span class="count" style="margin-left:auto">${esc(pretty(r.last_date))}</span></div>
      <p class="note">${esc(String(r.notes || '').slice(0, 300) || 'promoted from a mailbox message')}</p>
      <div class="docs">${docsHtml(r.docs, r.slug)}</div>
    </div>`).join('') : `<div class="empty">No interview invitations or offers right now. When one arrives,
      this is the only place the hunt will interrupt you.</div>`}

    ${inv.length ? `<h3 class="sub">Invitations filed from the mailbox</h3>
    ${inv.map((i) => `<div class="item"><div><div class="who">${esc(i.files.join(', '))}</div>
      <div class="what">${esc(i.key)}</div></div>
      <div class="when">${esc(i.ts)}<br>${esc(i.channel)}</div></div>`).join('')}` : ''}

    <details class="quiet"><summary>Receipts and rejections - ${receipts.length} receipts,
      ${muted.length} rejections (logged quietly, no alerts)</summary>
      <div class="body">
        ${muted.slice(0, 40).map((r) => `<div class="row"><span><b>${esc(r.company)}</b> ·
          ${esc(r.role)}</span><span>rejected ${esc(pretty(r.last_date))}</span></div>`).join('')}
        ${receipts.slice(0, 40).map((r) => `<div class="row"><span><b>${esc(r.company)}</b> ·
          ${esc(r.role)}</span><span>receipt ${esc(pretty(r.last_date))}</span></div>`).join('')}
      </div></details>
    <p class="note">A rejection needs no action and a receipt is not news, so neither is raised as an alert -
      both are counted here and kept in the tracker.</p>`;
}

/* ---- Cost */
async function viewCost() {
  const u = S.data.usage || (S.data.usage = await api('/api/usage'));
  const m = u.this_month || {};
  const days = Object.entries(u.spend_by_day || {});
  const peak = Math.max(0.0001, ...days.map(([, v]) => v));
  const included = Number(u.includes_runs || 0);
  const used = Number(m.runs || 0);
  const pct = included ? Math.min(100, Math.round((used / included) * 100)) : 0;
  const planCost = Number(u.price_usd_month || 0);
  const measured = Number(m.cost || 0);
  // the budget the gate actually enforces, and what it bought today
  const B = u.budget || {};
  const BD = B.budget || {};
  const spentToday = Number(B.spent_today_usd || 0);
  const dailyLimit = Number(BD.daily_usd || 0);
  const dayPct = dailyLimit ? Math.min(100, Math.round((spentToday / dailyLimit) * 100)) : 0;
  el('view').innerHTML = `
    <div class="kicker">Section 04 / cost</div>
    <h2 class="sec">Cost <span class="count">billing period ${esc(u.window || '')}</span></h2>
    <div class="metrics">
      <div class="metric"><div class="v">${esc(used)}</div><div class="k">agent runs this period</div>
        <div class="d">${included ? esc(included) + ' included' : 'no allowance reported'}</div></div>
      <div class="metric"><div class="v">${money(measured, 2)}</div><div class="k">measured spend</div>
        <div class="d">${esc(u.measurement_source || '')}</div></div>
      <div class="metric"><div class="v">${money(u.per_run_cost || 0, 3)}</div><div class="k">per run</div>
        <div class="d">${esc(m.sweeps || 0)} sweeps · ${esc(m.mail || 0)} mailbox runs</div></div>
      <div class="metric"><div class="v">${money(spentToday, 2)}</div><div class="k">spent today</div>
        <div class="d">${dailyLimit ? 'of ' + money(dailyLimit, 2) + '/day (' + dayPct + '%)' : 'no daily budget set'}</div></div>
      <div class="metric"><div class="v">${money(planCost, 0)}</div><div class="k">plan cost</div>
        <div class="d">${esc(u.plan || '')} · ${money(u.price_usd_per_extra_run || 0, 2)} per extra run</div></div>
      <div class="metric"><div class="v">${u.margin_multiple ? esc(u.margin_multiple) + '×' : '-'}</div>
        <div class="k">price / measured</div><div class="d">across all time on this host</div></div>
    </div>
    ${included ? `<div style="margin:14px 0 0"><div class="count">${used} of ${included} runs used
      (${pct}%)${u.runs_remaining != null ? ', ' + esc(u.runs_remaining) + ' left' : ''}</div>
      <div class="bar"><i style="width:${pct}%"></i></div></div>` : ''}
    <h3 class="sub">Spend by day</h3>
    ${days.length ? `<div class="chartwrap"><div class="chart">
      ${days.map(([d, v]) => `<div class="col" style="height:${Math.max(2, Math.round((v / peak) * 96))}px"
        title="${esc(d)}: ${money(v, 3)}"></div>`).join('')}
    </div><div style="display:flex;gap:3px;margin-top:20px">
      ${days.map(([d]) => `<div style="flex:1;font:10px var(--mono);color:var(--muted);text-align:center">
        ${esc(d.slice(5))}</div>`).join('')}
    </div></div>` : '<p class="note">No runs recorded in this period yet.</p>'}
    ${dailyLimit ? `<div style="margin:14px 0 0"><div class="count">today: ${money(spentToday, 2)} of
      ${money(dailyLimit, 2)} (${dayPct}%) · on_exceed ${esc(BD.on_exceed || 'warn')} at
      ${Math.round(Number(BD.throttle_rate || 0.25) * 100)}% of the run's cap</div>
      <div class="bar"><i style="width:${dayPct}%"></i></div></div>` : ''}
    ${B.line ? `<p class="note">${esc(B.line)}</p>` : ''}
    ${(B.degraded || []).map((n) => `<p class="note">budget degraded: ${esc(n)}</p>`).join('')}
    <p class="note">Measured spend is the model's own usage, priced at ${money((u.rates || {}).input || 0, 3)}
      per 1M input and ${money((u.rates || {}).output || 0, 3)} per 1M output tokens
      (cache reads ${money((u.rates || {}).cache_read || 0, 3)}). A typical sweep costs
      ${money(u.per_run_cost || 0, 3)}; the mailbox check is the frequent, cheap one.</p>`;
}

/* ---- Plan */
async function viewPlan() {
  const st = S.data.state || {};
  const u = S.data.usage || (S.data.usage = await api('/api/usage'));
  const lim = u.plan_limits || {};
  const plan = String(u.plan || st.plan || '');
  const plans = [['starter', 'Starter', 39], ['pro', 'Pro', 70], ['scale', 'Scale', 129]];
  el('view').innerHTML = `
    <div class="kicker">Section 05 / plan</div>
    <h2 class="sec">Plan <span class="count">${esc(plan)}</span></h2>
    <table><tbody>
      <tr><th>Sweep cadence</th><td class="mono">${esc((st.dials && st.dials.schedule &&
        st.dials.schedule.sweep) || '-')}</td>
        <th>Plan allows</th><td class="mono">every ${esc(lim.sweep_interval_minutes || '-')}m</td></tr>
      <tr><th>Mailbox check</th><td class="mono">${esc((st.dials && st.dials.schedule &&
        st.dials.schedule.mailbox) || '-')}</td>
        <th>Plan allows</th><td class="mono">every ${esc(lim.mail_interval_minutes || '-')}m</td></tr>
      <tr><th>Countries</th><td class="mono">${esc(((st.dials && st.dials.countries &&
        [].concat(st.dials.countries.primary || [], st.dials.countries.secondary || [])).join(', ')) || '-')}</td>
        <th>Plan includes</th><td class="mono">${esc(lim.max_countries || '-')}</td></tr>
      <tr><th>Role keywords</th><td class="mono">${esc((st.dials && st.dials.roles &&
        (st.dials.roles.current || []).length) || 0)}</td>
        <th>Plan includes</th><td class="mono">${esc(lim.max_role_keywords || '-')}</td></tr>
      <tr><th>Runs included</th><td class="mono">${esc(lim.agent_runs_included_month || '-')}</td>
        <th>Support</th><td class="mono">${esc(lim.support || '-')}</td></tr>
      <tr><th>Tracker</th><td colspan="3"><a href="${esc((st.health && st.health.sheet &&
        st.health.sheet.sheet_url) || '#')}" target="_blank" rel="noopener">the Google Sheet</a>
        ${st.health && st.health.sheet && st.health.sheet.in_sync ? ' · in sync' : ' · check sync'}</td></tr>
    </tbody></table>
    <h3 class="sub">Change plan</h3>
    <div class="chips" id="plans">
      ${plans.map(([id, label, price]) => `<label class="${id === plan ? 'on' : ''}">
        <input type="radio" name="plan" value="${id}" ${id === plan ? 'checked' : ''}>
        ${label} · $${price}/mo</label>`).join('')}
    </div>
    <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
      <button class="btn primary" id="plan-go">Request the change</button>
      <span class="saved" id="plan-msg"></span>
    </div>
    <p class="note">Billing is operator-side: the request is recorded here and the plan is switched on the
      account. Nothing is charged by this button.</p>`;
  el('plans').querySelectorAll('input').forEach((r) => {
    r.onchange = () => el('plans').querySelectorAll('label').forEach((l) =>
      l.classList.toggle('on', l.querySelector('input').checked));
  });
  el('plan-go').onclick = async () => {
    const chosen = (el('plans').querySelector('input:checked') || {}).value;
    const r = await api('/api/config', {method: 'POST', body: JSON.stringify({billing: {plan: chosen}})});
    const msg = el('plan-msg');
    msg.className = 'saved ' + (r.ok ? 'ok' : 'bad');
    msg.textContent = r.ok ? `plan change recorded: ${chosen}` : (r.error || r.message || 'refused');
  };
}

/* ---- Settings */
function chipList(host, list, selected, single) {
  el(host).innerHTML = list.map((c) => `<label class="${selected.includes(c) ? 'on' : ''}">
    <input type="${single ? 'radio' : 'checkbox'}" name="${host}" value="${esc(c)}"
      ${selected.includes(c) ? 'checked' : ''}>${esc(c)}</label>`).join('');
  el(host).querySelectorAll('input').forEach((i) => {
    i.onchange = () => {
      if (single) el(host).querySelectorAll('label').forEach((l) =>
        l.classList.toggle('on', l.querySelector('input').checked));
      else i.closest('label').classList.toggle('on', i.checked);
    };
  });
}
async function viewSettings() {
  const d = S.dials || (S.dials = await api('/api/config/dials'));
  // the backoff dial arrives as {current:{enabled,rate}} from this endpoint, but as
  // {enabled,rate} from /api/config. Resolve both shapes once, here, rather than inline.
  const _b = (d.interview_backoff && (d.interview_backoff.current || d.interview_backoff)) || {};
  const BO = {enabled: _b.enabled !== false, rate: Number(_b.rate) > 0 && Number(_b.rate) <= 1 ? Number(_b.rate) : 0.4};
  // the model budget: the dial from the config, today's spend from the gate's own state (the usage
  // payload carries it), so the interface and the gate can never show two different numbers.
  const _bud = (d.budget && (d.budget.current || d.budget)) || {};
  const BUD = {daily_usd: Number(_bud.daily_usd) > 0 ? Number(_bud.daily_usd) : 1,
               on_exceed: ['warn', 'throttle', 'stop'].includes(_bud.on_exceed) ? _bud.on_exceed : 'warn',
               throttle_rate: Number(_bud.throttle_rate) > 0 && Number(_bud.throttle_rate) <= 1
                 ? Number(_bud.throttle_rate) : 0.25};
  const u = S.data.usage || (S.data.usage = await api('/api/usage'));
  const BUDS = u.budget || {};
  const BSPENT = Number(BUDS.spent_today_usd || 0);
  const st = S.data.state || {};
  const n = S.data.notify || (S.data.notify = await api('/api/notify'));
  const a = S.data.auth || (S.data.auth = await api('/api/auth/status'));
  const opts = (d.countries && d.countries.options) || [];
  const cad = (d.cadence && d.cadence.options) || [];
  el('view').innerHTML = `
    <div class="kicker">Section 06 / settings</div>
    <h2 class="sec">Settings <span class="count">${esc((d.tenant && d.tenant.name) || '')}</span></h2>
    <div class="grid2">

      <fieldset><legend>Targeting</legend>
        <label class="f">Primary market</label><div class="chips" id="c-primary"></div>
        <label class="f">Secondary markets</label><div class="chips" id="c-secondary"></div>
        <label class="f">Rotation (tier 3, one country per sweep)</label>
        <div class="chips" id="c-rotation"></div>
        <label class="f">Effort split - primary share of each sweep</label>
        <input type="number" id="c-share" min="10" max="100" step="5"
          value="${esc(Math.round(((d.countries && d.countries.primary_share) || 0.8) * 100))}">
        <label class="f">Role keywords (one per line, limit ${esc((d.roles && d.roles.limit) || 8)})</label>
        <textarea id="c-roles" rows="5" style="background:#fff;border:1px solid var(--rule);padding:6px 8px;
          font:12.5px var(--mono);width:100%">${esc(((d.roles && d.roles.current) || []).join('\n'))}</textarea>
        <p class="note">${esc((d.countries && d.countries.rule) || '')}</p>
      </fieldset>

      <fieldset><legend>Salary</legend>
        <div class="row">
          <div><label class="f">Current gross / month</label>
            <input type="number" id="c-current" value="${esc((d.salary && d.salary.current_gross) || 0)}"></div>
          <div><label class="f">Target floor</label>
            <input type="number" id="c-floor" value="${esc((d.salary && d.salary.target_floor) || 0)}"></div>
        </div>
        <div class="row" style="margin-top:8px">
          <div><label class="f">Ask from</label>
            <input type="number" id="c-ask-lo" value="${esc((d.salary && d.salary.ask_range &&
              d.salary.ask_range[0]) || 0)}"></div>
          <div><label class="f">Ask to</label>
            <input type="number" id="c-ask-hi" value="${esc((d.salary && d.salary.ask_range &&
              d.salary.ask_range[1]) || 0)}"></div>
        </div>
        <p class="note">Legal floor on record: ${esc((d.salary && d.salary.legal_floor) || '-')} ·
          apply when the posting pays above ${esc((d.salary && d.salary.current_gross) || '-')}.</p>
      </fieldset>

      <fieldset><legend>Schedule</legend>
        <label class="f">When an interview is pending</label>
        <div class="chips">
          <label class="${BO.enabled ? 'on' : ''}">
            <input type="checkbox" id="c-backoff" ${BO.enabled ? 'checked' : ''}>
            apply at ${Math.round(BO.rate * 100)}%</label>
        </div>
        <p class="note">An interview is worth more than volume, so new applications slow to 40% of the usual cap
          while one is pending, and the Alerts view says so while it is happening. Untick for the full cap every
          run.</p>
        <label class="f">Sweep (discovery + applications)</label>
        <select id="c-sweep">${cad.map((c) => `<option value="${esc(c)}"
          ${c === (st.dials && st.dials.schedule && st.dials.schedule.sweep) ? 'selected' : ''}>${esc(c)}</option>`)
          .join('')}</select>
        <label class="f">Mailbox check</label>
        <select id="c-mail">${['every 60m','every 20m','every 10m'].map((c) => `<option value="${esc(c)}"
          ${c === (st.dials && st.dials.schedule && st.dials.schedule.mailbox) ? 'selected' : ''}>${esc(c)}</option>`)
          .join('')}</select>
        <label class="f">Quiet hours (no alert between)</label>
        <div class="row">
          <input type="text" id="c-qstart" value="${esc((d.quiet_hours && d.quiet_hours.current &&
            d.quiet_hours.current[0]) || '22:00')}">
          <input type="text" id="c-qend" value="${esc((d.quiet_hours && d.quiet_hours.current &&
            d.quiet_hours.current[1]) || '07:00')}">
        </div>
        <p class="note">A faster sweep than the plan allows is charged per extra run
          (${money((d.cadence && d.cadence.extra_run_price_usd) || 0.39, 2)}).</p>
      </fieldset>

      <fieldset><legend>Model budget</legend>
        <div class="row">
          <div><label class="f">Daily limit (USD)</label>
            <input type="number" id="c-budget" min="0.05" step="0.25" value="${esc(BUD.daily_usd)}"></div>
          <div><label class="f">When the day's limit is reached</label>
            <select id="c-on-exceed">${((d.budget && d.budget.options) || ['warn', 'throttle', 'stop'])
              .map((o) => `<option value="${esc(o)}" ${o === BUD.on_exceed ? 'selected' : ''}>${esc(o)}</option>`)
              .join('')}</select></div>
        </div>
        <p class="note">What the model may spend on this account in one UTC day, measured from the engine's
          own usage audit. Today: ${money(BSPENT, 2)} of ${money(BUD.daily_usd, 2)}
          ${BUDS.action && BUDS.action !== 'ok' ? ' - ' + esc(BUDS.action) + ' is active' : ''}.
          <b>warn</b> only says so, <b>throttle</b> applies at ${Math.round(BUD.throttle_rate * 100)}% of the
          run's usual cap, <b>stop</b> skips the sweep entirely and tells you why. A sweep that was slowed
          says so in the Alerts view.</p>
        ${(BUDS.degraded || []).map((n) => `<p class="note">budget degraded: ${esc(n)}</p>`).join('')}
      </fieldset>

      <fieldset><legend>Notifications</legend>
        <div class="locked"><span>Telegram</span><span class="v">${n.telegram && n.telegram.token_present ?
          'connected' : 'not connected'}</span></div>
        <div class="locked"><span>Chat</span><span class="v">${esc((n.telegram && n.telegram.chat_id) || '-')}
          </span></div>
        <div class="locked"><span>Alert on</span><span class="v">${esc(((n.thresholds) || []).join(', ') ||
          'interview, offer')}</span></div>
        <p class="note" style="margin-top:8px">Alerts go out on the candidate's own bot: interviews, offers and
          anything needing a decision. Connect it by putting the bot token in the profile's token file and
          setting the chat id in <span class="mono">notify.json</span>; the dashboard never stores it.</p>
        <button class="btn" id="n-test" style="margin-top:8px">Send a test alert</button>
        <span class="saved" id="n-msg"></span>
      </fieldset>

      <fieldset><legend>Transport rules (always on)</legend>
        <div class="locked"><span>Mailbox access</span><span class="v">read-only</span></div>
        <div class="locked"><span>Alert channel</span><span class="v">outbound only</span></div>
        <div class="locked"><span>Application email</span><span class="v">${a.connected ?
          'one per role, plus one follow-up' : 'not enabled'}</span></div>
        <div class="locked"><span>Replies to employers</span><span class="v">refused</span></div>
        <div class="locked"><span>Automation wording</span><span class="v">stripped before sending</span></div>
        <p class="note" style="margin-top:8px">These are not settings. The engine reads mail and never sends from
          it, alerts only ever go out to the candidate, and every outbound message is checked for wording that
          would describe it as automated.</p>
      </fieldset>

      <fieldset><legend>Google connection</legend>
        <div class="locked"><span>Status</span><span class="v">${a.connected ? 'connected' :
          'not connected'}</span></div>
        <div class="locked"><span>Token</span><span class="v">${esc(a.token_path || '-')}</span></div>
        ${(a.permissions || []).map((p) => `<div class="locked"><span>${esc(p.service)}</span>
          <span class="v">${a.granted && a.granted.some((s) => s.includes(p.service.toLowerCase().split(' ')[0]))
            ? 'granted' : '-'}</span></div>`).join('')}
        <p class="note" style="margin-top:8px">Revoke access any time at
          <a href="${esc(a.can_revoke_at || 'https://myaccount.google.com/permissions')}" target="_blank"
          rel="noopener">myaccount.google.com/permissions</a>.</p>
      </fieldset>
    </div>

    <div style="margin-top:18px;display:flex;gap:10px;align-items:center">
      <button class="btn primary" id="c-save">Save the dials</button>
      <button class="btn" id="c-reload">Discard changes</button>
      <span class="saved" id="c-msg"></span>
    </div>
    <p class="fineprint" id="c-token"></p>`;

  chipList('c-primary', opts, ((d.countries && d.countries.primary) || []));
  chipList('c-secondary', opts, ((d.countries && d.countries.secondary) || []));
  chipList('c-rotation', opts, ((d.countries && d.countries.rotation) || []));
  el('n-test').onclick = async () => {
    const msg = el('n-msg');
    const r = await api('/api/control/alert-test', {method: 'POST', body: JSON.stringify({dry_run: true})});
    msg.className = 'saved ' + (r.ok ? 'ok' : 'bad');
    msg.textContent = r.ok ? 'test alert sent' : (r.error || r.message || 'could not send');
  };
  el('c-reload').onclick = () => { S.dials = null; S.data.notify = null; render(); };
  el('c-save').onclick = async () => {
    const pick = (host) => Array.from(el(host).querySelectorAll('input:checked')).map((i) => i.value);
    const payload = {
      countries: {primary: pick('c-primary'), secondary: pick('c-secondary'), rotation: pick('c-rotation'),
                  primary_share: Number(el('c-share').value) / 100},
      roles: el('c-roles').value.split('\n').map((x) => x.trim()).filter(Boolean),
      salary: {current_gross: Number(el('c-current').value), target_floor: Number(el('c-floor').value),
               ask_range: [Number(el('c-ask-lo').value), Number(el('c-ask-hi').value)]},
      schedule: {sweep: el('c-sweep').value, mailbox: el('c-mail').value},
      interview_backoff: {enabled: el('c-backoff').checked},
      budget: {daily_usd: Number(el('c-budget').value), on_exceed: el('c-on-exceed').value},
      quiet_hours: [el('c-qstart').value, el('c-qend').value],
    };
    await saveDials(payload, 'c-msg', 'c-token');
  };
}

/* ------------------------------------------------------------------ saving (and the operator token) */
async function saveDials(payload, msgId, tokenId, onOk) {
  const msg = el(msgId);
  msg.className = 'saved';
  msg.textContent = 'saving...';
  let r = await api('/api/config', {method: 'POST', body: JSON.stringify(payload)});
  if (r._status === 401 && !S.operatorToken) {
    msg.className = 'saved bad';
    msg.textContent = 'this deployment protects writes with an operator token';
    if (tokenId) el(tokenId).innerHTML = `Writes need the deployment's operator token
      (<span class="mono">DASHBOARD_TOKEN</span>). Paste it once and the dashboard keeps it for this tab:
      <input type="text" id="${tokenId}-in" placeholder="operator token" style="max-width:280px;margin-top:6px">
      <button class="btn" id="${tokenId}-go">use token</button>`;
    if (tokenId) el(tokenId + '-go').onclick = async () => {
      S.operatorToken = el(tokenId + '-in').value.trim();
      sessionStorage.setItem('jha_token', S.operatorToken);
      await saveDials(payload, msgId, tokenId, onOk);
    };
    return;
  }
  msg.className = 'saved ' + (r.ok ? 'ok' : 'bad');
  msg.textContent = r.ok ? 'saved' : (r.error || r.message || 'refused');
  if (r.ok) {
    S.dials = null;
    S.data.state = await api('/api/state');
    if (onOk) onOk();
    else { renderRail(S.data.state); render(); }
  }
}

/* ------------------------------------------------------------------ boot */
applyTheme(themePreference());

async function boot(skipGate) {
  S.data.state = await api('/api/state');
  S.data.usage = await api('/api/usage');
  S.dials = await api('/api/config/dials');
  el('gate').hidden = true;
  el('setup').hidden = true;
  el('shell').hidden = false;
  renderRail(S.data.state);
  renderAccount();
  const firstRun = !Number(S.data.state.total_rows || 0);
  if (firstRun && !S.data.setupDone) {
    el('shell').hidden = true;
    renderSetup();
    return;
  }
  await render();
}

/* ------------------------------------------------------------------ whose account is on screen */
function renderAccount() {
  const me = S.me;
  const foot = el('rail-foot');
  if (!foot) return;
  if (!me || !me.signed_in) {
    // single-tenant deployment: the rail says nothing about accounts, exactly as before
    return;
  }
  const missing = Array.isArray(me.missing) ? me.missing : [];
  const label = (sc) => (sc.split('/').pop() || sc);
  foot.insertAdjacentHTML('afterbegin', `
    <div class="acct">
      <div class="who" title="the account this hunt belongs to">${esc(me.slug)}</div>
      <div class="sub">signed in with Google${me.workspace ? ` · ${esc(String(me.workspace).replace(/^.*\//, ''))}` : ''}</div>
      <button class="btn ghost" id="signout">Sign out</button>
    </div>
    ${missing.length ? `<div class="permnote">This account has not granted
      ${missing.map((m) => `<b>${esc(label(m))}</b>`).join(', ')}. The hunt still runs; interview alerts and the
      tracker need those permissions, so re-run the sign-in when you can.</div>` : ''}`);
  const so = el('signout');
  if (so) {
    so.onclick = () => {
      so.disabled = true;
      so.textContent = 'Signing out...';
      window.location.href = '/api/auth/logout';
    };
  }
  const meta = el('topmeta');
  if (meta && missing.length) {
    meta.insertAdjacentHTML('afterbegin',
      `<span class="warnpill" title="re-run the sign-in to grant: ${esc(missing.join(', '))}">`
      + `${missing.length} permission${missing.length > 1 ? 's' : ''} missing</span>`);
  }
}

function renderTokenPrompt(what) {
  el('gate').hidden = true;
  el('setup').hidden = true;
  el('shell').hidden = true;
  document.body.insertAdjacentHTML('beforeend', `
    <div id="gate2" style="position:fixed;inset:0;background:var(--paper);display:flex;align-items:flex-start;
      justify-content:center;padding:12vh 20px;z-index:30">
      <div class="panel">
        <div class="wordmark">Operator token</div>
        <div class="tag">${esc(what || 'this deployment is not loopback-only')}</div>
        <p class="fineprint">This deployment is reachable from outside loopback, so every endpoint needs the
          operator token (<span class="mono">DASHBOARD_TOKEN</span>). It is kept for this tab only.</p>
        <label class="f">Token</label>
        <input type="password" id="tok" placeholder="DASHBOARD_TOKEN">
        <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
          <button class="btn primary" id="tokgo">Open the dashboard</button>
          <span class="saved" id="tokmsg"></span>
        </div>
      </div>
    </div>`);
  el('tokgo').onclick = () => {
    S.operatorToken = el('tok').value.trim();
    sessionStorage.setItem('jha_token', S.operatorToken);
    const g = el('gate2');
    if (g) g.remove();
    start();
  };
  el('tok').addEventListener('keydown', (e) => { if (e.key === 'Enter') el('tokgo').click(); });
}

async function notePublishedView() {
  /* A viewer serves a snapshot with an age. Saying so is not decoration: without it a stale row looks live,
   * and the reader has no way to know the hunt is not what they are looking at. */
  const h = await api('/api/healthz');
  if (!h || h.mode !== 'viewer') return;
  const age = Number(h.snapshot_age_seconds);
  const when = h.snapshot_at ? new Date(h.snapshot_at) : null;
  const human = Number.isFinite(age)
    ? (age < 120 ? 'just now' : age < 7200 ? `${Math.round(age / 60)} minutes ago` : `${Math.round(age / 3600)} hours ago`)
    : 'unknown';
  const bar = document.createElement('div');
  bar.id = 'viewer-note';
  bar.style.cssText = [
    'padding:7px 26px', 'background:#f0e2cb', 'border-bottom:1px solid #d8d1c3',
    'font:12px/1.5 ui-monospace,Menlo,monospace', 'color:#1d2430', 'display:flex', 'gap:10px',
    'flex-wrap:wrap',
  ].join(';');
  bar.innerHTML = '<b style="color:#b06f16">PUBLISHED VIEW</b>' +
    `<span>read-only, pushed by the deployment ${esc(human)}` +
    (when ? ` (${esc(when.toISOString().slice(0, 16).replace('T', ' '))} UTC)` : '') +
    `</span><span style="margin-left:auto">${esc(h.snapshot_rows || 0)} rows</span>`;
  const main = document.querySelector('#main');
  if (main) main.insertBefore(bar, main.firstChild);
}

(async function start() {
  // WHO is looking comes first. In multi-tenant mode /api/auth/me answers it: no session -> sign in, and a
  // session -> that person's own hunt. In single-tenant mode it describes the deployment, as before.
  const me = await api('/api/auth/me');
  if (me && me.needs_login) {
    S.gate = me;
    renderGate();
    return;
  }
  if (me && me.signed_in) S.me = me;
  const auth = await api('/api/auth/status');
  if (auth._status === 401 && !(me && me.signed_in)) { renderTokenPrompt(auth.error); return; }
  await notePublishedView();
  S.gate = auth;
  S.data.auth = auth;
  const state = await api('/api/state');
  S.data.state = state;
  const firstRun = !Number(state.total_rows || 0);
  if (!auth.connected && !firstRun && !(me && me.signed_in)) {
    renderGate();
    return;
  }
  await boot(true);
})();
