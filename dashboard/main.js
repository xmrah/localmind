/* =========================================================
   Localmind · Zihin Sarayı Paneli  —  main.js
   Gerçek localmind REST API'sine bağlanır (server_sse.py).
   Bağımlılık: d3.v7.min.js (yerel). Başka kütüphane yok.
   ========================================================= */
(function () {
  'use strict';

  /* ─────────────────────────── CONFIG ─────────────────────────── */
  const ROOM_META = {
    mimari:    { label: 'Mimari',     color: '#a855f7', icon: '🏗️' },
    guvenlik:  { label: 'Güvenlik',   color: '#4d7cff', icon: '🛡️' },
    donanim:   { label: 'Donanım',    color: '#22e3c0', icon: '🖥️' },
    ogrenme:   { label: 'Öğrenme',    color: '#f5a524', icon: '📚' },
    kisisel:   { label: 'Kişisel',    color: '#ec4899', icon: '🧬' },
    genel:     { label: 'Genel',      color: '#7c86a0', icon: '🗂️' },
    proje:     { label: 'Proje',      color: '#38bdf8', icon: '🚀' },
    fikir:     { label: 'Fikir',      color: '#c084fc', icon: '💡' },
    arastirma: { label: 'Araştırma',  color: '#2dd4bf', icon: '🔬' },
    saglik:    { label: 'Sağlık',     color: '#4ade80', icon: '❤️' },
    finans:    { label: 'Finans',     color: '#facc15', icon: '💰' },
    iletisim:  { label: 'İletişim',   color: '#fb7185', icon: '✉️' },
  };
  const FALLBACK = ['#818cf8', '#f472b6', '#34d399', '#fbbf24', '#fb923c', '#60a5fa', '#a78bfa', '#2dd4bf'];
  const ENTITY_COLOR = '#eab308';
  const DECAY = 0.99;

  function roomMeta(name) {
    const key = (name || 'genel').toLowerCase();
    if (ROOM_META[key]) return ROOM_META[key];
    let h = 0;
    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
    return { label: name || 'Genel', color: FALLBACK[h % FALLBACK.length], icon: '•' };
  }

  /* ─────────────────────────── STATE ─────────────────────────── */
  const state = {
    memories: [], links: [], entities: [],
    rooms: [], profile: null, health: null, reminders: null,
    loadedAt: 0, loading: null,
    route: { view: 'overview', param: null },
    graph: { focus: null, showEntities: true, showSemantic: true },
    timelineDays: 30,
  };

  /* ─────────────────────────── UTILS ─────────────────────────── */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const clamp = (n, a, b) => Math.max(a, Math.min(b, n));

  async function api(path, opts) {
    try {
      const r = await fetch(path, opts);
      if (!r.ok) return null;
      const ct = r.headers.get('content-type') || '';
      return ct.includes('application/json') ? await r.json() : await r.text();
    } catch (e) { return null; }
  }

  function daysOld(iso) {
    const t = Date.parse(iso);
    if (isNaN(t) || t < 946684800000) return 0;
    return Math.max(0, (Date.now() - t) / 86400000);
  }
  function fmtDate(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return '—';
    return d.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
  }
  function fmtDateTime(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return '—';
    return d.toLocaleString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
  function ago(iso) {
    const d = daysOld(iso);
    if (d < 1) return 'bugün';
    if (d < 2) return 'dün';
    if (d < 30) return Math.floor(d) + ' gün önce';
    if (d < 365) return Math.floor(d / 30) + ' ay önce';
    return Math.floor(d / 365) + ' yıl önce';
  }
  function liveness(m) { return clamp(m.importance * Math.pow(DECAY, daysOld(m.created_at)), 0, 10); }
  function forgotten(m) { return Math.max(0, m.importance - liveness(m)); }

  let toastTimer;
  function toast(msg, type = '') {
    const t = $('#toast');
    t.textContent = msg; t.className = 'toast ' + type;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.add('hidden'), 3200);
  }
  function debounce(fn, ms) { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; }

  /* ─────────────────────────── DATA ─────────────────────────── */
  async function loadCore(force) {
    if (!force && state.memories.length && Date.now() - state.loadedAt < 30000) return;
    state.loading = api('/api/graph').then(g => {
      if (!g) { state.graphError = true; return; }
      state.graphError = false;
      const nodes = g.nodes || [];
      state.memories = nodes.filter(n => n.type === 'memory' && n.oda !== 'entity')
        .map(n => ({ id: n.id, konu: n.label, bilgi: n.content, oda: n.oda || 'genel',
                     importance: Number(n.importance) || 7, tags: n.tags || [], created_at: n.created_at || '' }));
      state.entities = nodes.filter(n => n.type === 'entity');
      state.links = g.links || [];
      buildRooms();
      state.loadedAt = Date.now();
    });
    await state.loading;
  }

  async function loadHeader() {
    const [health, profile] = await Promise.all([api('/api/health'), api('/api/profile')]);
    state.health = health; state.profile = profile;
    renderHeaderStatus();
  }

  async function loadReminders() {
    // Opsiyonel /api/reminders varsa kullan, yoksa istemci tarafında türet.
    const served = await api('/api/reminders?n=12');
    state.reminders = served && Array.isArray(served) ? served : null;
  }

  function buildRooms() {
    const map = new Map();
    for (const m of state.memories) {
      const k = m.oda || 'genel';
      if (!map.has(k)) map.set(k, { key: k, count: 0, impSum: 0, last: '', newest: 0 });
      const r = map.get(k); r.count++; r.impSum += m.importance;
      const t = Date.parse(m.created_at) || 0;
      if (t >= r.newest) { r.newest = t; r.last = m.created_at; }
    }
    state.rooms = Array.from(map.values()).map(r => {
      const meta = roomMeta(r.key);
      return { ...r, label: meta.label, color: meta.color, icon: meta.icon, avgImp: r.count ? r.impSum / r.count : 0 };
    }).sort((a, b) => b.count - a.count);
  }

  /* ─────────────────────────── SSE ─────────────────────────── */
  function initSSE() {
    try {
      const es = new EventSource('/api/events');
      es.onopen = () => setPulse(true);
      es.onerror = () => setPulse(false);
      es.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data);
          if (d.type === 'pulse') {
            setPulse(true);
            $('#headerTotal').textContent = d.total ?? '–';
            $('#shPulse').textContent = '#' + d.tick;
            if (state.health) state.health.memories = d.total;
          }
        } catch (_) {}
      };
    } catch (_) { setPulse(false); }
  }
  function setPulse(on) {
    const dot = $('#pulseDot');
    dot.className = 'dot ' + (on ? 'pulse' : 'off');
    $('#pulseText').textContent = on ? 'canlı' : 'kopuk';
  }

  function renderHeaderStatus() {
    const h = state.health || {};
    $('#headerTotal').textContent = h.memories ?? state.memories.length ?? 0;
    const od = $('#ollamaDot');
    if (h.ollama === true) { od.className = 'dot on'; $('#ollamaText').textContent = 'Ollama'; }
    else if (h.ollama === false) { od.className = 'dot off'; $('#ollamaText').textContent = 'Ollama kapalı'; }
    else { od.className = 'dot'; $('#ollamaText').textContent = 'Ollama ?'; }
    $('#shTotal').textContent = h.memories ?? state.memories.length ?? 0;
    $('#shRooms').textContent = state.rooms.length;
    $('#shOllama').textContent = h.ollama === true ? '● hazır' : (h.ollama === false ? '● kapalı' : 'bilinmiyor');
    $('#shOllama').style.color = h.ollama === true ? 'var(--green)' : (h.ollama === false ? 'var(--red)' : 'var(--text-dim)');
    $('#shVersion').textContent = h.version || '—';
  }

  /* ─────────────────────────── ROUTER ─────────────────────────── */
  function navigate(view, param) {
    const target = param ? `${view}/${encodeURIComponent(param)}` : view;
    if (window.location.hash === '#' + target) {
      router();
    } else {
      window.location.hash = target;
    }
  }
  window.navigate = navigate;

  function getRoute() {
    const h = (window.location.hash || '#overview').slice(1);
    const [view, param] = h.split('/');
    return { view: view || 'overview', param: param ? decodeURIComponent(param) : null };
  }

  async function router() {
    state.route = getRoute();
    const c = $('#content');
    $$('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.view === state.route.view));
    $$('.room-link').forEach(a => a.classList.toggle('active', a.dataset.room === state.route.param));
    $('#sidebar').classList.remove('open');

    await loadCore();
    const v = state.route.view;
    if (v === 'overview') await viewOverview(c);
    else if (v === 'graph') viewGraph(c);
    else if (v === 'rooms') viewRooms(c);
    else if (v === 'room') viewRoomDetail(c, state.route.param);
    else if (v === 'timeline') viewTimeline(c);
    else if (v === 'analytics') viewAnalytics(c);
    else if (v === 'reminders') viewReminders(c);
    else await viewOverview(c);
  }

  function loadingHTML() { return '<div class="loading-full"><div class="spinner"></div><div>Zihin sarayı yükleniyor…</div></div>'; }
  function emptyHTML(msg, icon = '🧠') { return `<div class="empty"><div class="em">${icon}</div><div>${esc(msg)}</div></div>`; }
  function errorHTML() { return `<div class="empty"><div class="em">🔌</div><div>Hafızaya ulaşılamadı.<br><span class="small">Sunucunun (<code>python server_sse.py</code>) çalıştığından emin ol.</span></div></div>`; }

  function viewShell(title, subtitle, controls, inner) {
    return `<div class="page-head"><div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${controls || ''}</div>${inner || ''}`;
  }

  /* ─────────────────────────── SIDEBAR ROOMS ─────────────────────────── */
  function renderRoomNav() {
    const nav = $('#roomNav');
    if (!state.rooms.length) { nav.innerHTML = '<div class="muted small">henüz oda yok</div>'; return; }
    nav.innerHTML = state.rooms.map(r =>
      `<a class="room-link" data-room="${esc(r.key)}" onclick="navigate('room','${esc(r.key)}')">
         <span class="rdot" style="background:${r.color}"></span>${esc(r.label)}
         <span class="rcount">${r.count}</span>
       </a>`).join('');
    $$('.room-link').forEach(a => a.classList.toggle('active', a.dataset.room === state.route.param));
  }

  /* ─────────────────────────── VIEW: OVERVIEW ─────────────────────────── */
  async function viewOverview(c) {
    c.innerHTML = loadingHTML();
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    renderRoomNav();
    await loadReminders();
    const mem = state.memories;
    if (!mem.length) { c.innerHTML = viewShell('Genel Bakış', 'Zihin sarayına genel bakış', '', emptyHTML('Henüz hiç anı yok. İlk anını “+ Yeni Anı” ile ekle.', '✨')); return; }

    const total = mem.length;
    const roomCount = state.rooms.length;
    const avgImp = (mem.reduce((a, m) => a + m.importance, 0) / total);
    const last7 = mem.filter(m => daysOld(m.created_at) <= 7).length;
    const reminders = state.reminders || deriveReminders();
    const topRoom = state.rooms[0];
    const topTags = tagsFrom(mem).slice(0, 8);
    const recent = [...mem].sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0)).slice(0, 6);

    const donut = donutSVG(state.rooms.map(r => ({ label: r.label, value: r.count, color: r.color })));

    c.innerHTML = viewShell('Genel Bakış', 'Zihin sarayının anlık durumu ve öne çıkanlar', '') + `
      <div class="grid cols-kpi" style="margin-bottom:16px">
        ${kpi('Toplam Anı', total, `${roomCount} odaya dağılmış`, 'var(--violet)')}
        ${kpi('Ortalama Önem', avgImp.toFixed(1), '10 üzerinden', 'var(--amber)')}
        ${kpi('Son 7 Gün', last7, 'yeni anı eklendi', 'var(--cyan)')}
        ${kpi('Hatırlatma', reminders.length, 'unutulmaya yüz tutan', 'var(--pink)')}
        ${kpi('En Aktif Oda', topRoom ? topRoom.label : '–', topRoom ? topRoom.count + ' anı' : '', 'var(--blue)')}
      </div>

      <div class="grid cols-2" style="grid-template-columns:minmax(0,1fr) minmax(0,1.2fr); margin-bottom:16px">
        <div class="card">
          <h3>🗂️ Oda Dağılımı <span class="sub">${roomCount} oda</span></h3>
          ${donut.html}
        </div>
        <div class="card">
          <h3>🏷️ Öne Çıkan Etiketler <span class="sub">anı sayısına göre</span></h3>
          ${topTags.length ? topTags.map(t => barRow(t.tag, t.count, topTags[0].count, 'var(--cyan)')).join('') : '<div class="muted small">henüz etiket yok</div>'}
          <div style="margin-top:14px">
            <h3 style="margin-bottom:10px">🔔 Hatırlatılması Gerekenler</h3>
            ${reminders.length ? reminders.slice(0, 4).map(r => miniReminder(r)).join('') : '<div class="muted small">harika — bekleyen hatırlatma yok</div>'}
          </div>
        </div>
      </div>

      <div class="grid cols-2">
        <div class="card">
          <h3>🆕 Son Eklenen Anılar <span class="sub">en yeni 6</span></h3>
          <div class="mem-list">${recent.map(m => memItem(m)).join('')}</div>
        </div>
        <div class="card">
          <h3>🕸️ En Bağlantılı Anılar <span class="sub">semantik + varlık</span></h3>
          ${topConnected().map(x => memItem(x.m)).join('') || '<div class="muted small">bağlantı verisi yok</div>'}
        </div>
      </div>`;

    bindMemItems(c);
    bindReminderItems(c);
  }

  function kpi(label, value, sub, color) {
    return `<div class="card kpi"><div class="kpi-accent" style="background:${color}"></div>
      <div class="kpi-label">${esc(label)}</div>
      <div class="kpi-value" style="color:${color}">${esc(value)}</div>
      ${sub ? `<div class="kpi-sub">${esc(sub)}</div>` : ''}</div>`;
  }
  function barRow(label, value, max, color) {
    const effectiveMax = Math.max(max, 5);
    const w = clamp((value / effectiveMax) * 100, 5, 100);
    return `<div class="bar-row"><span class="bl" title="${esc(label)}">${esc(label)}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${w}%;background:${color}"></span></span>
      <span class="bv">${value}</span></div>`;
  }

  /* ─────────────────────────── VIEW: GRAPH ─────────────────────────── */
  function viewGraph(c) {
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    if (!window.d3) {
      c.innerHTML = viewShell('Bilgi Grafiği', 'Zihin sarayının ilişki ağı', '') +
        emptyHTML('Grafik motoru (d3.v7.min.js) bulunamadı. Dosyayı dashboard/ klasörüne koy.', '🕸️');
      return;
    }
    const rooms = state.rooms;
    const controls = `<div class="controls" style="margin:0">
      <select class="field" id="gRoom"><option value="">Tüm odalar</option>${rooms.map(r => `<option value="${esc(r.key)}">${esc(r.label)} (${r.count})</option>`).join('')}</select>
      <label class="switch"><input type="checkbox" id="gEntities" ${state.graph.showEntities ? 'checked' : ''}/><span class="track"></span>Varlıkları göster</label>
      <label class="switch"><input type="checkbox" id="gSemantic" ${state.graph.showSemantic ? 'checked' : ''}/><span class="track"></span>Anlamsal bağlar</label>
      <button class="btn small" id="gReheat">↻ Yeniden düzenle</button>
    </div>`;
    c.innerHTML = viewShell('Bilgi Grafiği', 'Anılar, kavramlar, kişiler ve teknolojiler arasındaki bağlar', controls) + `
      <div class="graph-wrap">
        <div id="graphArea"></div>
        <div class="graph-hint">Tekerle: yakınlaştır · Sürükle: taşı · Düğüme tıkla: detay</div>
        <div class="graph-legend" id="graphLegend"></div>
      </div>`;

    const rerender = () => {
      state.graph.showEntities = $('#gEntities').checked;
      state.graph.showSemantic = $('#gSemantic').checked;
      state.graph.roomFilter = $('#gRoom').value;
      renderGraph();
    };
    $('#gRoom').onchange = rerender;
    $('#gEntities').onchange = rerender;
    $('#gSemantic').onchange = rerender;
    $('#gReheat').onclick = () => renderGraph(true);
    renderGraph(true);
  }

  let graphSim = null;
  function renderGraph(reheat) {
    const area = $('#graphArea'); if (!area) return;
    const W = area.clientWidth || 800, H = area.clientHeight || 520;
    const roomFilter = state.graph.roomFilter || '';
    area.innerHTML = '';
    if (graphSim) { graphSim.stop(); graphSim = null; }

    let mem = state.memories;
    if (roomFilter) mem = mem.filter(m => (m.oda || 'genel') === roomFilter);
    const memIds = new Set(mem.map(m => m.id));

    const nodes = mem.map(m => ({
      id: m.id, label: m.konu, oda: m.oda || 'genel', importance: m.importance,
      content: m.bilgi, tags: m.tags, created_at: m.created_at, type: 'memory',
      r: 6 + clamp(m.importance, 1, 10) * 0.8,
    }));

    let links = [];
    const rawLinks = (state.links || []).map(l => ({ ...l, source: typeof l.source === 'object' ? l.source.id : l.source, target: typeof l.target === 'object' ? l.target.id : l.target }));
    if (state.graph.showSemantic) links.push(...rawLinks.filter(l => l.type !== 'entity' && memIds.has(l.source) && memIds.has(l.target)));

    if (state.graph.showEntities) {
      const entityNodes = new Map(); // id -> node
      for (const l of rawLinks) {
        if (l.type !== 'entity') continue;
        const srcStr = String(l.source);
        const tgtStr = String(l.target);
        const isSrcMem = memIds.has(srcStr);
        const isTgtMem = memIds.has(tgtStr);
        const isSrcEnt = srcStr.startsWith('entity_');
        const isTgtEnt = tgtStr.startsWith('entity_');

        // Oda filtresi varsa: sadece o odaya veya bağlı varlıklara izin ver
        if (roomFilter && !isSrcMem && !isTgtMem) continue;

        if (isSrcEnt) {
          const name = srcStr.slice(7);
          if (!entityNodes.has(srcStr)) entityNodes.set(srcStr, { id: srcStr, label: name, oda: 'entity', type: 'entity', r: 7.5 });
        }
        if (isTgtEnt) {
          const name = tgtStr.slice(7);
          if (!entityNodes.has(tgtStr)) entityNodes.set(tgtStr, { id: tgtStr, label: name, oda: 'entity', type: 'entity', r: 7.5 });
        }

        links.push({
          source: srcStr,
          target: tgtStr,
          value: l.value || 0.7,
          type: 'entity',
          label: l.label || ''
        });
      }
      nodes.push(...entityNodes.values());
    }

    const legend = $('#graphLegend');
    if (legend) legend.innerHTML = state.rooms.map(r => `<span class="lg"><i style="background:${r.color}"></i>${esc(r.label)}</span>`).join('') +
      (state.graph.showEntities ? `<span class="lg"><i style="background:${ENTITY_COLOR};border-radius:2px"></i>Varlık</span>` : '');

    if (!nodes.length) { area.innerHTML = emptyHTML('Bu filtrede gösterilecek anı yok.', '🕸️'); return; }

    const svg = d3.select(area).append('svg').attr('width', W).attr('height', H);
    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.15, 4]).on('zoom', e => g.attr('transform', e.transform)));

    const nodeList = nodes.map(n => ({ ...n }));
    const byId = new Map(nodeList.map(n => [n.id, n]));
    const linkList = links.map(l => ({ ...l })).filter(l => byId.has(l.source) && byId.has(l.target));

    const focus = state.graph.focus;
    const nb = new Set();
    if (focus) { nb.add(focus); linkList.forEach(l => { if (l.source === focus) nb.add(l.target); if (l.target === focus) nb.add(l.source); }); }
    const hasFocus = focus && nb.size > 1;

    const degree = new Map();
    linkList.forEach(l => {
      const s = l.source, t = l.target;
      degree.set(s, (degree.get(s) || 0) + 1); degree.set(t, (degree.get(t) || 0) + 1);
    });

    const cx = W / 2, cy = H / 2;

    // Odalara göre galaksi / takımyıldızı merkezleri hesapla
    const roomKeys = state.rooms.map(r => r.key);
    const roomCenters = {};
    const R_ROOM = Math.min(W, H) * 0.30;
    roomKeys.forEach((key, idx) => {
      const angle = (idx / Math.max(1, roomKeys.length)) * 2 * Math.PI - Math.PI / 2;
      roomCenters[key] = {
        x: cx + R_ROOM * Math.cos(angle),
        y: cy + R_ROOM * Math.sin(angle)
      };
    });

    nodeList.forEach(n => {
      if (n.x == null) {
        const targetCenter = (!roomFilter && roomCenters[n.oda]) ? roomCenters[n.oda] : { x: cx, y: cy };
        n.x = targetCenter.x + (Math.random() - 0.5) * 60;
        n.y = targetCenter.y + (Math.random() - 0.5) * 60;
      }
    });

    graphSim = d3.forceSimulation(nodeList)
      .force('link', d3.forceLink(linkList).id(d => d.id)
        .distance(d => d.type === 'entity' ? 60 : Math.max(65, 140 - (d.value || 0.5) * 75))
        .strength(d => d.type === 'entity' ? 0.6 : 0.35))
      .force('charge', d3.forceManyBody().strength(d => d.type === 'entity' ? -70 : -130).distanceMax(420))
      .force('collision', d3.forceCollide(d => d.r + 13));

    if (!roomFilter) {
      // Odalarına göre yumuşak galaksi çekimi
      graphSim
        .force('center', d3.forceCenter(cx, cy).strength(0.04))
        .force('roomX', d3.forceX(d => (d.type === 'entity' ? cx : (roomCenters[d.oda]?.x || cx))).strength(0.12))
        .force('roomY', d3.forceY(d => (d.type === 'entity' ? cy : (roomCenters[d.oda]?.y || cy))).strength(0.12));
    } else {
      graphSim
        .force('center', d3.forceCenter(cx, cy).strength(0.08))
        .force('x', d3.forceX(cx).strength(0.06))
        .force('y', d3.forceY(cy).strength(0.06));
    }

    const link = g.append('g').selectAll('line').data(linkList).join('line')
      .attr('stroke', d => d.type === 'entity' ? ENTITY_COLOR : roomMeta(byId.get(d.source.id || d.source)?.oda || 'genel').color)
      .attr('stroke-opacity', d => { if (!hasFocus) return d.type === 'entity' ? 0.4 : 0.45; return (nb.has(d.source.id || d.source) && nb.has(d.target.id || d.target)) ? 0.85 : 0.05; })
      .attr('stroke-width', d => d.type === 'entity' ? 1.2 : Math.max(1, (d.value || 0.4) * 2.8))
      .attr('stroke-dasharray', d => d.type === 'entity' ? '3 3' : null);

    const nodeG = g.append('g').selectAll('g').data(nodeList).join('g')
      .style('cursor', 'pointer')
      .on('mouseover', (e, d) => showTip(e, d))
      .on('mousemove', moveTip)
      .on('mouseout', hideTip)
      .on('click', (e, d) => {
        e.stopPropagation();
        if (d.type === 'entity') { toast('Varlık: ' + d.label, ''); return; }
        state.graph.focus = state.graph.focus === d.id ? null : d.id;
        renderGraph();
        openMemoryById(d.id);
      })
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) graphSim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) graphSim.alphaTarget(0); d.fx = null; d.fy = null; }));

    const dim = d => (hasFocus && !nb.has(d.id)) ? 0.15 : 1;

    nodeG.each(function (d) {
      const g2 = d3.select(this);
      const deg = degree.get(d.id) || 0;
      const isImportant = (d.importance || 5) >= 7;
      // Etiketi göster: Varlıklar, oda filtresindeyken hepsi, odaklanılan komşular, önem >= 7 veya bağlantılı anılar
      const labelIt = d.type === 'entity' || !!roomFilter || isImportant || deg >= 1 || nb.has(d.id);

      if (d.type === 'entity') {
        const s = d.r;
        g2.append('rect').attr('x', -s).attr('y', -s).attr('width', s * 2).attr('height', s * 2).attr('rx', 3)
          .attr('transform', 'rotate(45)').attr('fill', ENTITY_COLOR).attr('opacity', () => dim(d) * 0.9)
          .attr('stroke', 'var(--bg)').attr('stroke-width', 1.5);
        if (labelIt) g2.append('text').attr('text-anchor', 'middle').attr('y', s + 13).attr('font-size', 9.5)
          .attr('fill', 'var(--text-dim)').attr('opacity', () => dim(d)).attr('stroke', 'var(--bg)').attr('stroke-width', 2.5)
          .attr('paint-order', 'stroke').text(d.label.length > 20 ? d.label.slice(0, 18) + '…' : d.label);
      } else {
        const col = roomMeta(d.oda).color;
        g2.append('circle').attr('r', d.r + 5).attr('fill', col).attr('opacity', () => dim(d) * 0.15);
        g2.append('circle').attr('r', d.r).attr('fill', col).attr('opacity', () => dim(d) * 0.92)
          .attr('stroke', d.id === focus ? '#fff' : 'var(--bg)').attr('stroke-width', d.id === focus ? 2.5 : 1.5);
        if (labelIt) g2.append('text').attr('text-anchor', 'middle').attr('y', d.r + 12).attr('font-size', isImportant ? 10 : 9.2)
          .attr('font-weight', isImportant ? '600' : '400')
          .attr('fill', 'var(--text)').attr('opacity', () => dim(d) * 0.92).attr('stroke', 'var(--bg)').attr('stroke-width', 2.5)
          .attr('paint-order', 'stroke').text(d.label.length > 22 ? d.label.slice(0, 20) + '…' : d.label);
      }
    });

    graphSim.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      nodeG.attr('transform', d => `translate(${clamp(d.x, 20, W - 20)},${clamp(d.y, 20, H - 20)})`);
    });
    if (reheat) graphSim.alpha(1).restart();
  }

  function showTip(e, d) {
    const tip = $('#tooltip');
    if (d.type === 'entity') tip.innerHTML = `<b>🏷️ ${esc(d.label)}</b><div class="tt-dim">Knowledge Graph varlığı</div>`;
    else tip.innerHTML = `<b>${esc(d.label)}</b><div class="tt-dim">${esc(roomMeta(d.oda).label)} · önem ${d.importance}/10</div><div class="tt-dim">${esc(ago(d.created_at))}</div>`;
    tip.classList.remove('hidden'); moveTip(e);
  }
  function moveTip(e) { const t = $('#tooltip'); t.style.left = (e.clientX + 14) + 'px'; t.style.top = (e.clientY + 14) + 'px'; }
  function hideTip() { $('#tooltip').classList.add('hidden'); }

  /* ─────────────────────────── VIEW: ROOMS ─────────────────────────── */
  async function viewRooms(c) {
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    renderRoomNav();
    if (!state.rooms.length) { c.innerHTML = viewShell('Odalar', 'Otomatik sınıflandırılmış hafıza odaları', '', emptyHTML('Henüz oda yok.', '🗂️')); return; }
    c.innerHTML = viewShell('Odalar', 'Anıların otomatik yerleştirildiği odalar', '') + `
      <div class="grid cols-3">
        ${state.rooms.map(r => `
          <div class="card" style="cursor:pointer;border-left:3px solid ${r.color}" onclick="navigate('room','${esc(r.key)}')">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
              <span style="font-size:1.5rem">${r.icon}</span>
              <div><div style="font-weight:700">${esc(r.label)}</div><div class="muted small">${r.count} anı · ort. önem ${r.avgImp.toFixed(1)}</div></div>
            </div>
            <div class="bar-track" style="margin-bottom:8px"><div class="bar-fill" style="width:${clamp(r.count / state.rooms[0].count * 100, 4, 100)}%;background:${r.color}"></div></div>
            <div class="muted small">son güncelleme: ${r.last ? esc(ago(r.last)) : '—'}</div>
          </div>`).join('')}
      </div>`;
  }

  /* ─────────────────────────── VIEW: ROOM DETAIL ─────────────────────────── */
  async function viewRoomDetail(c, oda) {
    if (!oda) { navigate('rooms'); return; }
    const all = state.memories.filter(m => (m.oda || 'genel') === oda);
    const meta = roomMeta(oda);
    renderRoomNav();
    if (!all.length) { c.innerHTML = viewShell(meta.label, 'Bu odada anı yok', '') + emptyHTML('Bu odada henüz anı yok.', meta.icon); return; }

    c.innerHTML = viewShell(`${meta.icon} ${meta.label}`,
      `${all.length} anı · ortalama önem ${(all.reduce((a, m) => a + m.importance, 0) / all.length).toFixed(1)}`,
      `<button class="btn small ghost" onclick="navigate('rooms')">← Tüm odalar</button>`) + `
      <div class="controls">
        <input class="field" id="roomSearch" type="text" placeholder="Bu odada semantik ara…" style="min-width:280px" />
        <div class="seg" id="roomSort">
          <button data-sort="importance" class="active">Önem</button>
          <button data-sort="date">Tarih</button>
          <button data-sort="liveness">Canlılık</button>
        </div>
      </div>
      <div id="roomList"></div>`;

    let sort = 'importance';
    const render = (list) => {
      const arr = [...list];
      if (sort === 'importance') arr.sort((a, b) => b.importance - a.importance);
      else if (sort === 'date') arr.sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0));
      else arr.sort((a, b) => liveness(b) - liveness(a));
      const box = $('#roomList');
      box.innerHTML = `<div class="mem-list">${arr.map(m => memItem(m)).join('')}</div>`;
      bindMemItems(box);
    };
    render(all);

    $$('#roomSort button').forEach(b => b.onclick = () => {
      sort = b.dataset.sort;
      $$('#roomSort button').forEach(x => x.classList.toggle('active', x === b));
      render(all);
    });
    const rs = $('#roomSearch');
    rs.addEventListener('keydown', debounce(async (e) => {
      const q = rs.value.trim();
      if (!q) { render(all); return; }
      const res = await api(`/api/search?q=${encodeURIComponent(q)}&oda=${encodeURIComponent(oda)}&n=20`);
      if (!res) { render(all); return; }
      const list = res.map(r => ({ id: r.id, konu: r.konu, bilgi: r.content, oda: r.oda, importance: r.importance, tags: r.tags || [], created_at: r.created_at, _score: r.score }));
      const box = $('#roomList');
      box.innerHTML = `<div class="muted small" style="margin-bottom:10px">${list.length} sonuç · semantik arama</div>` +
        (list.length ? `<div class="mem-list">${list.map(m => memItem(m)).join('')}</div>` : emptyHTML('Sonuç yok.', '🔍'));
      bindMemItems(box);
    }, 350));
  }

  /* ─────────────────────────── VIEW: TIMELINE ─────────────────────────── */
  function viewTimeline(c) {
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    renderRoomNav();
    const days = state.timelineDays;
    const mem = state.memories.filter(m => daysOld(m.created_at) <= days);
    const controls = `<div class="seg" id="tlRange">
      ${[7, 30, 90, 3650].map(d => `<button data-d="${d}" class="${d === days ? 'active' : ''}">${d === 3650 ? 'Tümü' : 'Son ' + d + ' gün'}</button>`).join('')}
    </div>`;
    if (!mem.length) { c.innerHTML = viewShell('Zaman Çizelgesi', 'Zamana yayılmış anılar', controls) + emptyHTML('Bu aralıkta anı yok.', '🕰️'); bindRange(c); return; }

    const sorted = [...mem].sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0));
    const groups = new Map();
    for (const m of sorted) {
      const key = (m.created_at || '').slice(0, 10) || 'bilinmiyor';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(m);
    }
    const activity = dailyCounts(mem, Math.min(days, 90));

    c.innerHTML = viewShell('Zaman Çizelgesi', `${mem.length} anı · son ${days === 3650 ? 'tüm zamanlar' : days + ' gün'}`, controls) + `
      <div class="card" style="margin-bottom:16px">
        <h3>📈 Günlük Kayıt Aktivitesi <span class="sub">son ${activity.length} gün</span></h3>
        ${areaSVG(activity)}
      </div>
      <div>${Array.from(groups.entries()).map(([day, items]) => `
        <div class="tl-day">
          <div class="tl-day-label"><b>${esc(fmtDate(day))}</b><span>${items.length} anı</span></div>
          <div class="tl-rail"></div>
          <div class="tl-items">${items.map(m => memItem(m)).join('')}</div>
        </div>`).join('')}</div>`;
    bindRange(c);
    bindMemItems(c);
  }
  function bindRange(c) {
    const seg = $('#tlRange', c); if (!seg) return;
    $$('#tlRange button', c).forEach(b => b.onclick = () => { state.timelineDays = Number(b.dataset.d); viewTimeline(c); });
  }

  /* ─────────────────────────── VIEW: ANALYTICS ─────────────────────────── */
  async function viewAnalytics(c) {
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    renderRoomNav();
    const mem = state.memories;
    if (!mem.length) { c.innerHTML = viewShell('Analitik', 'Hafızanın sayısal görünümü', '') + emptyHTML('Analiz için henüz veri yok.', '📊'); return; }
    await loadReminders();

    const donut = donutSVG(state.rooms.map(r => ({ label: r.label, value: r.count, color: r.color })));
    const tags = tagsFrom(mem).slice(0, 12);
    const hist = importanceHistogram(mem);
    const scatter = decayScatter(mem);
    const weekly = dailyCounts(mem, 90);
    const avgImp = (mem.reduce((a, m) => a + m.importance, 0) / mem.length);
    const avgLive = (mem.reduce((a, m) => a + liveness(m), 0) / mem.length);
    const validMem = mem.filter(m => {
      const t = Date.parse(m.created_at);
      return !isNaN(t) && t > 946684800000;
    });
    const oldest = (validMem.length ? validMem : mem).reduce((a, m) => (Date.parse(m.created_at) < Date.parse(a.created_at) ? m : a), mem[0]);

    const archCount = state.health?.memories && state.health.memories > mem.length ? (state.health.memories - mem.length) : 0;
    const countSub = archCount > 0 ? `${archCount} arşivde (${state.health.memories} toplam)` : 'aktif kayıt';

    c.innerHTML = viewShell('Analitik', 'Oda, etiket, önem ve unutma eğrisi analizleri', '') + `
      <div class="grid cols-kpi" style="margin-bottom:16px">
        ${kpi('Aktif Anı', mem.length, countSub, 'var(--violet)')}
        ${kpi('Ort. Önem', avgImp.toFixed(2), '10 üzerinden', 'var(--amber)')}
        ${kpi('Ort. Canlılık', avgLive.toFixed(2), 'unutma sonrası', 'var(--cyan)')}
        ${kpi('En Eski Anı', ago(oldest.created_at), fmtDate(oldest.created_at), 'var(--blue)')}
      </div>

      <div class="grid cols-2" style="margin-bottom:16px">
        <div class="card"><h3>🗂️ Oda Dağılımı</h3>${donut.html}</div>
        <div class="card"><h3>🏷️ En Çok Kullanılan Etiketler <span class="sub">ilk 12</span></h3>
          ${tags.length ? tags.map(t => barRow(t.tag, t.count, tags[0].count, 'var(--cyan)')).join('') : '<div class="muted small">etiket yok</div>'}
        </div>
      </div>

      <div class="grid cols-2" style="margin-bottom:16px">
        <div class="card"><h3>📊 Önem Skoru Dağılımı <span class="sub">1–10</span></h3>${hist}</div>
        <div class="card"><h3>🌡️ Unutma Eğrisi <span class="sub">yaş × canlılık</span></h3>${scatter}
          <div class="muted small" style="margin-top:6px">Kesikli çizgi: önem=10 için teorik Ebbinghaus eğrisi (0.99<sup>gün</sup>).</div>
        </div>
      </div>

      <div class="card"><h3>📈 Kayıt Hızı <span class="sub">son 90 gün, günlük</span></h3>${areaSVG(weekly)}
        <div class="grid cols-4" style="margin-top:14px">
          ${kpiStat('Son 7 gün', mem.filter(m => daysOld(m.created_at) <= 7).length)}
          ${kpiStat('Son 30 gün', mem.filter(m => daysOld(m.created_at) <= 30).length)}
          ${kpiStat('Ort. etiket/anı', (mem.reduce((a, m) => a + (m.tags || []).length, 0) / mem.length).toFixed(2))}
          ${kpiStat('Yüksek önem (≥8)', mem.filter(m => m.importance >= 8).length)}
        </div>
      </div>`;
  }
  function kpiStat(label, value) {
    return `<div class="mg" style="padding:10px 12px;border-radius:10px;background:var(--card);border:1px solid var(--border-soft)">
      <div class="muted small">${esc(label)}</div><div style="font-size:1.2rem;font-weight:700;font-family:var(--mono);margin-top:3px">${esc(value)}</div></div>`;
  }

  /* ─────────────────────────── VIEW: REMINDERS ─────────────────────────── */
  async function viewReminders(c) {
    if (state.graphError) { c.innerHTML = errorHTML(); return; }
    renderRoomNav();
    await loadReminders();
    const rem = state.reminders || deriveReminders();
    const h = state.health || {};

    const health = `
      <div class="grid cols-4" style="margin-bottom:16px">
        ${kpi('Ollama', h.ollama === true ? 'Hazır' : (h.ollama === false ? 'Kapalı' : '?'), h.ollama === true ? 'embeddings çalışıyor' : 'model yanıtı yok', h.ollama === true ? 'var(--green)' : 'var(--red)')}
        ${kpi('Toplam Anı', h.memories ?? state.memories.length, 'ChromaDB koleksiyonu', 'var(--violet)')}
        ${kpi('Sürüm', h.version || '2.0.0', 'Localmind', 'var(--blue)')}
        ${kpi('SSE', $('#pulseText')?.textContent || '–', 'canlı nabız', 'var(--cyan)')}
      </div>`;

    c.innerHTML = viewShell('Hatırlatmalar & Sağlık', 'Önemli ama unutulmaya yüz tutmuş anılar ve sistem durumu', '') + health + `
      <div class="card">
        <h3>🔔 Hatırlatılması Gerekenler <span class="sub">önem × unutulma skoruna göre</span></h3>
        ${rem.length ? `<div class="mem-list">${rem.map(r => reminderCard(r)).join('')}</div>`
          : emptyHTML('Harika — bekleyen hatırlatma yok.', '✅')}
        <div class="muted small" style="margin-top:14px;line-height:1.6">
          Skor = önem − (önem × 0.99<sup>gün</sup>). Uzun süre erişilmeyen yüksek önemli anılar öne çıkar (Ebbinghaus unutma eğrisi).
          ${state.reminders ? '' : 'Kesin erişim sayaçları için opsiyonel /api/reminders uç noktasını etkinleştirebilirsin.'}
        </div>
      </div>`;
    bindReminderItems(c);
    bindMemItems(c);
  }
  function reminderCard(r) {
    const meta = roomMeta(r.oda);
    const fs = r.forgotten_score != null ? r.forgotten_score : r.forgotten;
    return `<div class="mem-item" style="border-left-color:${meta.color}" data-mem-id="${esc(r.id)}">
      <div class="mi-top">
        <span class="badge room" style="border-color:${meta.color}">${meta.icon} ${esc(meta.label)}</span>
        <span class="mi-title">${esc(r.konu)}</span>
        <span class="imp" style="margin-left:auto">🔔 ${Number(fs).toFixed(1)}</span>
      </div>
      <div class="mi-body">${esc((r.bilgi || r.content || '').slice(0, 200))}</div>
      <div class="mi-foot"><span>önem ${Number(r.importance).toFixed(0)}/10</span><span>·</span><span>${r.days_ago != null ? r.days_ago + ' gün önce' : esc(ago(r.created_at))}</span></div>
    </div>`;
  }
  function miniReminder(r) {
    const meta = roomMeta(r.oda);
    return `<div class="mem-item" style="margin-bottom:8px;border-left-color:${meta.color}" onclick="navigate('reminders')">
      <div class="mi-top"><span class="mi-title" style="font-size:.84rem">${esc(r.konu)}</span>
      <span class="imp" style="margin-left:auto;font-size:.72rem">🔔 ${Number(r.forgotten_score ?? r.forgotten ?? 0).toFixed(1)}</span></div>
      <div class="mi-foot">${esc(meta.label)} · ${r.days_ago != null ? r.days_ago + ' gün' : esc(ago(r.created_at))}</div>
    </div>`;
  }

  /* ─────────────────────────── MEMORY ITEMS / MODAL ─────────────────────────── */
  function memItem(m) {
    const meta = roomMeta(m.oda);
    const score = m._score != null ? `<span class="sr-score">%${(m._score * 100).toFixed(0)}</span>` : '';
    return `<div class="mem-item" style="border-left-color:${meta.color}" data-mem-id="${esc(m.id)}">
      <div class="mi-top">
        <span class="badge room" style="border-color:${meta.color}">${meta.icon} ${esc(meta.label)}</span>
        <span class="mi-title">${esc(m.konu)}</span>
        <span class="imp" style="margin-left:auto">★ ${Number(m.importance).toFixed(0)}</span>${score}
      </div>
      <div class="mi-body">${esc((m.bilgi || '').slice(0, 220))}</div>
      <div class="mi-foot">
        <span>${esc(ago(m.created_at))}</span>
        ${(m.tags || []).slice(0, 4).map(t => `<span class="tag">${esc(t)}</span>`).join('')}
      </div>
    </div>`;
  }
  function bindMemItems(root) {
    $$('.mem-item[data-mem-id]', root).forEach(el => {
      el.onclick = (e) => { if (e.target.closest('.mini')) return; openMemoryById(el.dataset.memId); };
    });
  }
  function bindReminderItems(root) {
    $$('.mem-item[data-mem-id]', root).forEach(el => {
      if (el._bound) return; el._bound = true;
    });
  }

  function openMemoryById(id) {
    const m = state.memories.find(x => x.id === id);
    if (!m) return;
    const links = (state.links || []).filter(l => (typeof l.source === 'object' ? l.source.id : l.source) === id || (typeof l.target === 'object' ? l.target.id : l.target) === id);
    const related = [];
    for (const l of links) {
      const other = (typeof l.source === 'object' ? l.source.id : l.source) === id
        ? (typeof l.target === 'object' ? l.target.id : l.target)
        : (typeof l.source === 'object' ? l.source.id : l.source);
      const mm = state.memories.find(x => x.id === other);
      if (mm && !related.find(r => r.id === mm.id)) related.push(mm);
    }
    const meta = roomMeta(m.oda);
    $('#modal').innerHTML = `
      <div class="modal-head">
        <div><h2>${esc(m.konu)}</h2>
          <div class="muted small" style="margin-top:4px">${meta.icon} ${esc(meta.label)} · ${esc(fmtDateTime(m.created_at))}</div></div>
        <span class="modal-close" onclick="closeModal()">✕</span>
      </div>
      <div class="meta-grid">
        <div class="mg"><label>Önem</label><b style="color:var(--amber)">★ ${Number(m.importance).toFixed(1)}</b></div>
        <div class="mg"><label>Canlılık</label><b style="color:var(--cyan)">${liveness(m).toFixed(2)}</b></div>
        <div class="mg"><label>Yaş</label><b>${esc(ago(m.created_at))}</b></div>
        <div class="mg"><label>Bağlantı</label><b>${related.length}</b></div>
      </div>
      <div style="margin-bottom:8px">${(m.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>
      <div class="detail-body">${esc(m.bilgi)}</div>
      ${related.length ? `<h3 style="margin:20px 0 10px">🔗 İlişkili Anılar</h3>
        <div class="mem-list">${related.slice(0, 6).map(r => memItem(r)).join('')}</div>` : ''}
      <div style="display:flex;gap:10px;margin-top:22px">
        <button class="btn" onclick="navigate('graph')">🕸️ Grafikte gör</button>
        <button class="btn" style="border-color:var(--red);color:var(--red)" onclick="archiveMemory('${esc(m.id)}')">🗄️ Arşivle</button>
      </div>`;
    $('#overlay').classList.remove('hidden');
    bindMemItems($('#modal'));
  }

  function closeModal() { $('#overlay').classList.add('hidden'); }
  window.closeModal = closeModal;

  async function archiveMemory(id) {
    if (!confirm('Bu anıyı arşivlemek istediğine emin misin? (silinmez, aktif görünümden kaldırılır)')) return;
    const r = await api('/api/memory/archive', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ memory_id: id }),
    });
    if (r && (r.status === 'archived' || r.ok !== false)) {
      toast('Anı arşivlendi.', 'ok'); closeModal();
      state.loadedAt = 0; await loadCore(true); await loadHeader(); await router();
    } else toast('Arşivleme başarısız.', 'err');
  }
  window.archiveMemory = archiveMemory;

  /* ─────────────────────────── ADD MEMORY ─────────────────────────── */
  function openAddForm() {
    const roomOpts = ['otomatik', ...Object.keys(ROOM_META)].map(k =>
      `<option value="${k === 'otomatik' ? '' : k}">${k === 'otomatik' ? 'Otomatik belirle' : ROOM_META[k].label}</option>`).join('');
    $('#modal').innerHTML = `
      <div class="modal-head"><div><h2>+ Yeni Anı Ekle</h2><div class="muted small" style="margin-top:4px">Ollama otomatik sınıflandırma ve varlık çıkarımı yapar</div></div>
        <span class="modal-close" onclick="closeModal()">✕</span></div>
      <div class="form-row"><label>Konu (başlık)</label><input class="field" id="fKonu" placeholder="Örn: NixOS flake yapılandırması" /></div>
      <div class="form-row"><label>Bilgi (içerik)</label><textarea class="field" id="fBilgi" placeholder="Kaydedilecek bilginin tamamı…"></textarea></div>
      <div class="grid cols-2">
        <div class="form-row"><label>Oda</label><select class="field" id="fOda">${roomOpts}</select></div>
        <div class="form-row"><label>Önem: <b id="fImpVal">7</b>/10</label>
          <input type="range" id="fImp" min="1" max="10" value="7" style="width:100%" /></div>
      </div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button class="btn primary" id="fSave">💾 Kaydet</button>
        <button class="btn ghost" onclick="closeModal()">İptal</button>
      </div>`;
    $('#overlay').classList.remove('hidden');
    $('#fImp').oninput = e => $('#fImpVal').textContent = e.target.value;
    $('#fSave').onclick = async () => {
      const konu = $('#fKonu').value.trim(), bilgi = $('#fBilgi').value.trim();
      if (!konu || !bilgi) { toast('Konu ve bilgi zorunlu.', 'err'); return; }
      const body = { konu, bilgi, oda: $('#fOda').value || null, importance: Number($('#fImp').value), agent_id: 'user' };
      $('#fSave').textContent = 'Kaydediliyor…'; $('#fSave').disabled = true;
      const r = await api('/api/memory', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (r) { toast(r.message || 'Anı kaydedildi.', 'ok'); closeModal(); state.loadedAt = 0; await loadCore(true); await loadHeader(); await router(); }
      else { toast('Kaydetme başarısız — sunucu/Ollama kontrol et.', 'err'); $('#fSave').textContent = '💾 Kaydet'; $('#fSave').disabled = false; }
    };
  }

  /* ─────────────────────────── SEARCH ─────────────────────────── */
  function initSearch() {
    const input = $('#globalSearch'), box = $('#searchResults');
    const run = debounce(async () => {
      const q = input.value.trim();
      if (!q) { box.classList.add('hidden'); return; }
      const res = await api(`/api/search?q=${encodeURIComponent(q)}&n=8`);
      if (!res || !res.length) { box.innerHTML = '<div class="sr-item muted">sonuç yok</div>'; box.classList.remove('hidden'); return; }
      box.innerHTML = res.map(r => `
        <div class="sr-item" data-mem-id="${esc(r.id)}">
          <div class="sr-top"><span class="badge room" style="border-color:${roomMeta(r.oda).color}">${roomMeta(r.oda).icon} ${esc(roomMeta(r.oda).label)}</span>
            <span>${esc(r.konu)}</span><span class="sr-score">%${((r.score || 0) * 100).toFixed(0)}</span></div>
          <div class="sr-body">${esc((r.content || '').slice(0, 160))}</div>
        </div>`).join('');
      box.classList.remove('hidden');
      $$('.sr-item[data-mem-id]', box).forEach(el => el.onclick = () => {
        box.classList.add('hidden'); input.value = '';
        const id = el.dataset.memId;
        if (!state.memories.find(m => m.id === id)) {
          toast('Kayıt görüntüleniyor…');
        }
        openMemoryById(id) || openTransientMemory(id, res);
      });
    }, 300);
    input.addEventListener('input', run);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { run(); } });
    document.addEventListener('click', (e) => { if (!e.target.closest('.global-search')) box.classList.add('hidden'); });
  }
  function openTransientMemory(id, res) {
    const s = res.find(r => r.id === id); if (!s) return;
    const m = { id, konu: s.konu, bilgi: s.content, oda: s.oda, importance: s.importance, tags: s.tags || [], created_at: s.created_at };
    state.memories.push(m); openMemoryById(id);
  }

  /* ─────────────────────────── CHARTS (SVG) ─────────────────────────── */
  function donutSVG(segments) {
    const total = segments.reduce((a, s) => a + s.value, 0) || 1;
    const r = 54, C = 2 * Math.PI * r, cx = 74, cy = 74;
    let off = 0;
    const arcs = segments.map(s => {
      const len = (s.value / total) * C;
      const el = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="18" stroke-dasharray="${len.toFixed(2)} ${(C - len).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"/>`;
      off += len; return el;
    }).join('');
    const svg = `<svg width="148" height="148" viewBox="0 0 148 148"><g transform="rotate(-90 ${cx} ${cy})">
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--border)" stroke-width="18"/>${arcs}</g>
      <text x="${cx}" y="${cy - 3}" text-anchor="middle" font-size="22" font-weight="700" fill="var(--text)" font-family="var(--mono)">${total}</text>
      <text x="${cx}" y="${cy + 15}" text-anchor="middle" font-size="9" fill="var(--text-dim)">anı</text></svg>`;
    const legend = segments.map(s => `<div class="dl"><i style="background:${s.color}"></i>${esc(s.label)}<b>${s.value}</b></div>`).join('');
    return { html: `<div class="donut-wrap"><div>${svg}</div><div class="donut-legend">${legend || '<span class="muted">–</span>'}</div></div>` };
  }

  function importanceHistogram(mem) {
    const bins = Array.from({ length: 10 }, (_, i) => ({ label: String(i + 1), v: 0 }));
    for (const m of mem) { const i = clamp(Math.round(m.importance), 1, 10) - 1; bins[i].v++; }
    const max = Math.max(1, ...bins.map(b => b.v));
    const W = 560, H = 190, pad = 26, bw = (W - pad * 2) / 10;
    const bars = bins.map((b, i) => {
      const h = (b.v / max) * (H - pad * 2);
      const x = pad + i * bw;
      return `<rect x="${x + 3}" y="${H - pad - h}" width="${bw - 6}" height="${Math.max(h, 1)}" rx="3" fill="var(--violet)" opacity="${0.45 + 0.5 * (b.v / max)}"/>
        <text x="${x + bw / 2}" y="${H - pad + 12}" text-anchor="middle" font-size="9" fill="var(--text-faint)">${b.label}</text>
        ${b.v ? `<text x="${x + bw / 2}" y="${H - pad - h - 4}" text-anchor="middle" font-size="9" fill="var(--text-dim)">${b.v}</text>` : ''}`;
    }).join('');
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:190px"><line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="var(--border)"/><line x1="${pad}" y1="${pad - 8}" x2="${pad}" y2="${H - pad}" stroke="var(--border)"/>${bars}</svg>`;
  }

  function decayScatter(mem) {
    const W = 560, H = 200, pad = 34;
    const validMem = mem.filter(m => {
      const t = Date.parse(m.created_at);
      return !isNaN(t) && t > 946684800000;
    });
    const items = validMem.length ? validMem : mem;
    const maxDays = Math.max(7, ...items.map(m => daysOld(m.created_at)));
    const px = d => pad + (d / maxDays) * (W - pad * 2);
    const py = v => H - pad - (clamp(v, 0, 10) / 10) * (H - pad * 2);
    let path = '';
    for (let d = 0; d <= maxDays; d += Math.max(1, maxDays / 60)) path += `${path ? 'L' : 'M'}${px(d).toFixed(1)},${py(10 * Math.pow(DECAY, d)).toFixed(1)} `;
    const pts = items.slice(0, 400).map(m => {
      const c = roomMeta(m.oda).color;
      const d = daysOld(m.created_at);
      const l = liveness(m);
      return `<circle cx="${px(d).toFixed(1)}" cy="${py(l).toFixed(1)}" r="3.4" fill="${c}" opacity="0.75"><title>${esc(m.konu)}: ${Math.round(d)} gün önce, canlılık ${l.toFixed(1)}/10 (önem ${m.importance})</title></circle>`;
    }).join('');
    const yTicks = [0, 2.5, 5, 7.5, 10].map(v => `<text x="${pad - 6}" y="${py(v) + 3}" text-anchor="end" font-size="9" fill="var(--text-faint)">${v}</text><line x1="${pad}" y1="${py(v)}" x2="${W - pad}" y2="${py(v)}" stroke="var(--border-soft)"/>`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:200px">${yTicks}
      <path d="${path}" fill="none" stroke="var(--text-faint)" stroke-width="1.4" stroke-dasharray="4 4"/>
      ${pts}
      <line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="var(--border)"/>
      <text x="${W - pad}" y="${H - pad + 14}" text-anchor="end" font-size="9" fill="var(--text-faint)">${Math.round(maxDays)} gün →</text>
      <text x="${pad}" y="14" font-size="9" fill="var(--text-faint)">canlılık ↑</text></svg>`;
  }

  function areaSVG(points) {
    const W = 700, H = 150, pad = 24;
    if (!points.length) return '<div class="muted small">veri yok</div>';
    const max = Math.max(1, ...points.map(p => p.v));
    const px = i => pad + (i / Math.max(1, points.length - 1)) * (W - pad * 2);
    const py = v => H - pad - (v / max) * (H - pad * 2);
    let line = '';
    points.forEach((p, i) => { line += `${i ? 'L' : 'M'}${px(i).toFixed(1)},${py(p.v).toFixed(1)} `; });
    const area = line + `L${px(points.length - 1).toFixed(1)},${H - pad} L${px(0).toFixed(1)},${H - pad} Z`;
    const labels = points.map((p, i) => (i % Math.ceil(points.length / 7) === 0 || i === points.length - 1)
      ? `<text x="${px(i)}" y="${H - 6}" text-anchor="middle" font-size="9" fill="var(--text-faint)">${esc(p.label)}</text>` : '').join('');
    const dots = points.map((p, i) => p.v ? `<circle cx="${px(i)}" cy="${py(p.v)}" r="2.2" fill="var(--cyan)"><title>${esc(p.label)}: ${p.v}</title></circle>` : '').join('');
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:150px">
      <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--cyan)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--cyan)" stop-opacity="0"/></linearGradient></defs>
      <path d="${area}" fill="url(#ag)"/><path d="${line}" fill="none" stroke="var(--cyan)" stroke-width="2"/>
      ${dots}<line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="var(--border)"/>${labels}</svg>`;
  }

  function dailyCounts(mem, days) {
    const out = [];
    const now = new Date(); now.setHours(0, 0, 0, 0);
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(now); d.setDate(now.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const next = new Date(d); next.setDate(d.getDate() + 1);
      const v = mem.filter(m => { const t = Date.parse(m.created_at); return t >= d.getTime() && t < next.getTime(); }).length;
      out.push({ label: `${d.getDate()}.${d.getMonth() + 1}`, v });
    }
    return out;
  }

  function tagsFrom(mem) {
    const c = new Map();
    for (const m of mem) for (const t of (m.tags || [])) if (t) c.set(t, (c.get(t) || 0) + 1);
    return Array.from(c.entries()).map(([tag, count]) => ({ tag, count })).sort((a, b) => b.count - a.count);
  }
  function topConnected() {
    const deg = new Map();
    for (const l of (state.links || [])) {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      deg.set(s, (deg.get(s) || 0) + 1); deg.set(t, (deg.get(t) || 0) + 1);
    }
    return Array.from(deg.entries()).map(([id, d]) => ({ m: state.memories.find(x => x.id === id), d }))
      .filter(x => x.m).sort((a, b) => b.d - a.d).slice(0, 6);
  }
  function deriveReminders() {
    return state.memories.map(m => ({
      id: m.id, konu: m.konu, bilgi: m.bilgi, oda: m.oda, importance: m.importance,
      created_at: m.created_at, days_ago: Math.floor(daysOld(m.created_at)), forgotten: forgotten(m), tags: m.tags,
    })).sort((a, b) => b.forgotten - a.forgotten).slice(0, 12);
  }

  /* ─────────────────────────── PARTICLES ─────────────────────────── */
  function initParticles() {
    const cv = $('#particles'); if (!cv) return;
    const ctx = cv.getContext('2d');
    let ps = [];
    function resize() {
      cv.width = innerWidth; cv.height = innerHeight;
      ps = Array.from({ length: Math.min(60, Math.floor(innerWidth / 26)) }, () => ({
        x: Math.random() * cv.width, y: Math.random() * cv.height,
        vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25, r: Math.random() * 1.6 + .4,
      }));
    }
    resize(); addEventListener('resize', resize);
    (function loop() {
      ctx.clearRect(0, 0, cv.width, cv.height);
      const light = document.documentElement.dataset.theme === 'light';
      for (const p of ps) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > cv.width) p.vx *= -1;
        if (p.y < 0 || p.y > cv.height) p.vy *= -1;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7);
        ctx.fillStyle = light ? 'rgba(120,80,200,.25)' : 'rgba(150,110,240,.35)';
        ctx.fill();
      }
      requestAnimationFrame(loop);
    })();
  }

  /* ─────────────────────────── THEME ─────────────────────────── */
  function initTheme() {
    const saved = localStorage.getItem('lm-theme');
    if (saved) document.documentElement.dataset.theme = saved;
    $('#themeToggle').onclick = () => {
      const cur = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
      document.documentElement.dataset.theme = cur;
      localStorage.setItem('lm-theme', cur);
    };
  }

  /* ─────────────────────────── INIT ─────────────────────────── */
  async function init() {
    initTheme();
    initParticles();
    initSearch();
    initSSE();
    $('#menuToggle').onclick = () => $('#sidebar').classList.toggle('open');
    $('#addBtn').onclick = openAddForm;
    $('#overlay').onclick = (e) => { if (e.target.id === 'overlay') closeModal(); };
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

    $$('.nav-link').forEach(a => {
      a.onclick = (e) => {
        e.preventDefault();
        navigate(a.dataset.view);
      };
    });

    await loadHeader();
    await router();
    await loadHeader();
    renderRoomNav();
    window.addEventListener('hashchange', router);
    // periyodik sağlık yenileme (~30 sn)
    setInterval(loadHeader, 30000);
    window.addEventListener('resize', debounce(() => { if (state.route.view === 'graph') renderGraph(); }, 250));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
