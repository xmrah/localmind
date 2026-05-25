/**
 * Localmind Pulse Dashboard — Final Bulletproof Edition
 * Zihin Sarayı: %100 Dinamik, Backend-Bağımsız Keşif
 */

const THRESHOLD = 0.45;
const MAX_DEPTH = 3;
const COLORS = { center: "#00FFCC", near: "#8A2BE2", far: "rgba(255,255,255,0.15)" };

const ROOM_CONFIG = {
    "architecture": { label: "Mimari",    icon: "🏗️", color: "var(--accent-violet)" },
    "mimari":       { label: "Mimari",    icon: "🏗️", color: "var(--accent-violet)" },
    "security":     { label: "Güvenlik",  icon: "🛡️", color: "var(--accent-blue)"   },
    "guvenlik":     { label: "Güvenlik",  icon: "🛡️", color: "var(--accent-blue)"   },
    "ideas":        { label: "Fikirler",  icon: "💡", color: "var(--accent-purple)" },
    "fikir":        { label: "Fikirler",  icon: "💡", color: "var(--accent-purple)" },
    "learning":     { label: "Öğrenme",   icon: "📖", color: "var(--accent-cyan)"   },
    "ogrenme":      { label: "Öğrenme",   icon: "📖", color: "var(--accent-cyan)"   },
    "donanim":      { label: "Donanım",   icon: "📱", color: "var(--accent-cyan)"   },
    "hardware":     { label: "Donanım",   icon: "📱", color: "var(--accent-cyan)"   },
    "personal":     { label: "Kişisel",   icon: "👤", color: "var(--accent-violet)" },
    "kisisel":      { label: "Kişisel",   icon: "👤", color: "var(--accent-violet)" },
    "genel":        { label: "Genel",     icon: "📂", color: "var(--text-dim)"      }
};

let rawGraph = { nodes: [], links: [] };
let focusNodeId = null;
let sseStatus = "DISCONNECTED";
let simulation = null;

// ═══════════════════════════════════════════════════════
// AMBIENT PARTICLES
// ═══════════════════════════════════════════════════════

const canvas = document.getElementById("particles");
const ctx = canvas.getContext("2d");
let particles = [];

function initParticles() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    particles = [];
    for (let i = 0; i < 40; i++) {
        particles.push({
            x: Math.random() * canvas.width, y: Math.random() * canvas.height,
            r: Math.random() * 1.2 + 0.3, dx: (Math.random() - 0.5) * 0.2, dy: (Math.random() - 0.5) * 0.2,
            a: Math.random() * 0.3 + 0.1
        });
    }
}

function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.dx; p.y += p.dy;
        if (p.x < 0) p.x = canvas.width; if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height; if (p.y > canvas.height) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(138, 43, 226, ${p.a})`; ctx.fill();
    });
    requestAnimationFrame(drawParticles);
}
initParticles(); drawParticles(); window.addEventListener("resize", initParticles);

// ═══════════════════════════════════════════════════════
// DATA LAYER (BACKEND INDEPENDENT)
// ═══════════════════════════════════════════════════════

async function api(path) {
    try { const res = await fetch(path); return res.ok ? await res.json() : null; } catch { return null; }
}

async function loadGraphData() {
    const data = await api("/api/graph");
    rawGraph = data || { nodes: [], links: [] };
    if (rawGraph.nodes.length > 0 && !focusNodeId) focusNodeId = rawGraph.nodes[0].id;
}

function getRoomInfo(key) {
    const k = key.toLowerCase();
    return ROOM_CONFIG[k] || { label: key, icon: "📁", color: "var(--text-dim)" };
}

function parseStatsFromNodes(nodes) {
    const counts = {};
    // Entity grafik düğümlerini filtrele — sadece gerçek hafıza anıları
    const memoryNodes = nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    memoryNodes.forEach(n => { const o = (n.oda || "genel").toLowerCase(); counts[o] = (counts[o] || 0) + 1; });
    const rooms = Object.entries(counts).map(([key, count]) => {
        const info = getRoomInfo(key);
        return { key, count, ...info };
    }).sort((a, b) => b.count - a.count);
    return { rooms, total: memoryNodes.length };
}

// ═══════════════════════════════════════════════════════
// SPA ROUTER
// ═══════════════════════════════════════════════════════

function navigate(view, param) { window.location.hash = param ? `${view}/${param}` : view; }
window.navigate = navigate;

function getRoute() {
    const hash = window.location.hash.replace("#", "") || "home";
    const parts = hash.split("/");
    return { view: parts[0], param: decodeURIComponent(parts[1] || "") };
}

async function router() {
    const { view, param } = getRoute();
    document.querySelectorAll(".nav-link").forEach(l => l.classList.toggle("active", l.dataset.view === view));
    const el = document.getElementById("mainContent");
    switch (view) {
        case "home": await viewHome(el); break;
        case "rooms": await viewRooms(el); break;
        case "room": await viewRoomDetail(el, param); break;
        case "timeline": viewTimeline(el); break;
        case "graph": viewGraph(el); break;
        case "analytics": await viewAnalytics(el); break;
        case "settings": await viewSettings(el); break;
        default: await viewHome(el);
    }
}
window.addEventListener("hashchange", router);

// ═══════════════════════════════════════════════════════
// SIDEBAR
// ═══════════════════════════════════════════════════════

async function loadSidebar() {
    if (rawGraph.nodes.length === 0) await loadGraphData();
    const { rooms, total } = parseStatsFromNodes(rawGraph.nodes);
    document.getElementById("headerTotal").innerText = total;
    const nav = document.getElementById("roomNav");
    nav.innerHTML = rooms.filter(r => r.count > 0).map(r => `
        <a class="room-link" onclick="navigate('room','${r.key}')">
            <span>${r.icon}</span> ${r.label} <span class="room-count">${r.count}</span>
        </a>`).join("");
}

// ═══════════════════════════════════════════════════════
// VIEWS
// ═══════════════════════════════════════════════════════

async function viewHome(el) {
    if (rawGraph.nodes.length === 0) await loadGraphData();
    const memNodes = rawGraph.nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    const { rooms, total } = parseStatsFromNodes(rawGraph.nodes);
    const activeRooms = rooms.filter(r => r.count > 0);

    const linkCount = rawGraph.links.filter(l => {
        const ids = new Set(memNodes.map(n => n.id));
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        return ids.has(s) && ids.has(t);
    }).length;

    const avgImp = memNodes.length
        ? (memNodes.reduce((sum, n) => sum + (Number(n.importance) || 0), 0) / memNodes.length).toFixed(1)
        : 0;

    // Son 7 eklenen anı (created_at'e göre)
    const recent = [...memNodes]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 7);

    const impBadge = imp => {
        const v = Number(imp) || 0;
        if (v >= 9) return `<span class="imp-badge imp-critical">${v}</span>`;
        if (v >= 7) return `<span class="imp-badge imp-high">${v}</span>`;
        if (v >= 4) return `<span class="imp-badge imp-med">${v}</span>`;
        return `<span class="imp-badge imp-low">${v}</span>`;
    };

    el.innerHTML = `<div class="view home-dashboard">

        <!-- Arama -->
        <div class="search-container home-search">
            <span class="search-icon">🔍</span>
            <input type="text" class="search-bar" id="searchInput" placeholder="Zihninde ara...">
            <div class="search-results" id="searchResults"></div>
        </div>

        <!-- İstatistik satırı -->
        <div class="stats-row">
            <div class="stat-card"><div class="stat-val">${total}</div><div class="stat-lbl">Toplam Anı</div></div>
            <div class="stat-card"><div class="stat-val">${activeRooms.length}</div><div class="stat-lbl">Oda</div></div>
            <div class="stat-card"><div class="stat-val">${avgImp}</div><div class="stat-lbl">Ort. Önem</div></div>
            <div class="stat-card"><div class="stat-val">${linkCount}</div><div class="stat-lbl">Bağlantı</div></div>
        </div>

        <!-- Alt iki kolon -->
        <div class="home-cols">
            <!-- Sol: Son anılar -->
            <div class="home-recent">
                <div class="home-col-title">SON EKLENEN ANILAR</div>
                ${recent.length === 0
                    ? `<div class="empty-state">Henüz anı yok.</div>`
                    : recent.map(m => {
                        const info = getRoomInfo(m.oda || "genel");
                        const payload = JSON.stringify({label:m.label,oda:m.oda,content:m.content,tags:m.tags,importance:m.importance,created_at:m.created_at}).replace(/'/g,"&#39;");
                        return `<div class="recent-item" onclick='openMemory(${payload})'>
                            <div class="recent-dot" style="background:${info.color}"></div>
                            <div class="recent-body">
                                <div class="recent-title">${m.label}</div>
                                <div class="recent-meta">
                                    <span class="tl-room">${info.icon} ${info.label}</span>
                                    ${impBadge(m.importance)}
                                </div>
                            </div>
                        </div>`;
                    }).join("")}
                <div class="home-more" onclick="navigate('timeline')">Tümünü gör →</div>
            </div>

            <!-- Sağ: Odalar -->
            <div class="home-rooms-col">
                <div class="home-col-title">ODALAR</div>
                ${activeRooms.map(r => `
                    <div class="home-room-row" onclick="navigate('room','${r.key}')">
                        <span class="home-room-icon">${r.icon}</span>
                        <span class="home-room-name">${r.label}</span>
                        <span class="home-room-count">${r.count}</span>
                    </div>`).join("")}
                <div class="home-more" onclick="navigate('graph')">Zihin haritası →</div>
            </div>
        </div>
    </div>`;
    initSearch();
}

function viewGraph(el) {
    const memNodes = rawGraph.nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    const linkCount = rawGraph.links.filter(l => {
        const ids = new Set(memNodes.map(n => n.id));
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        return ids.has(s) && ids.has(t);
    }).length;

    el.innerHTML = `<div class="view graph-page">
        <div class="graph-page-header">
            <span class="graph-title">ZİHİN HARİTASI</span>
            <span class="graph-subtitle" id="graphSubtitle">${memNodes.length} anı · ${linkCount} bağlantı</span>
        </div>
        <div id="graphArea"></div>
    </div>`;
    renderGraph();
}


async function viewRooms(el) {
    const { rooms } = parseStatsFromNodes(rawGraph.nodes);
    el.innerHTML = `<div class="view"><h1 class="section-title">🚪 Hafıza Odaları</h1><div class="cards-grid">
        ${rooms.map(r => `<div class="room-card" onclick="navigate('room','${r.key}')" style="border-left:3px solid ${r.color}">
            <span style="font-size:2rem">${r.icon}</span><h3>${r.label}</h3><div class="room-stat">${r.count}</div></div>`).join("")}
    </div></div>`;
}

async function viewRoomDetail(el, roomKey) {
    const info = getRoomInfo(roomKey);
    el.innerHTML = `<div class="view">
        <div class="breadcrumb"><a href="#rooms">Odalar</a> / <strong>${info.label}</strong></div>
        <h1 class="section-title">${info.label} Odası</h1>
        <div class="memory-list" id="roomMemoryList"><div style="color:var(--text-dim);padding:20px">Yükleniyor…</div></div>
    </div>`;
    const memories = await api(`/api/room/${encodeURIComponent(roomKey)}`) || [];
    const list = document.getElementById("roomMemoryList");
    if (!list) return;
    if (memories.length === 0) {
        list.innerHTML = `<div style="color:var(--text-dim);padding:20px">Bu odada henüz anı yok.</div>`;
        return;
    }
    list.innerHTML = memories.map(m => {
        const dateStr = m.created_at ? new Date(m.created_at).toLocaleDateString("tr-TR") : "";
        const tags = (m.tags || []).map(t => `<span class="memory-tag">${t}</span>`).join("");
        const payload = JSON.stringify({label: m.konu, oda: m.oda, content: m.content, tags: m.tags, importance: m.importance, created_at: m.created_at}).replace(/'/g,"&#39;");
        return `<div class="memory-item" onclick='openMemory(${payload})'>
            <h4>${m.konu}</h4>
            <p>${(m.content||"").substring(0,200)}${m.content && m.content.length > 200 ? "…" : ""}</p>
            ${tags || dateStr ? `<div class="memory-meta">${tags}${dateStr ? `<span class="memory-tag" style="margin-left:auto;background:rgba(77,124,255,0.1);color:var(--accent-blue)">${dateStr}</span>` : ""}</div>` : ""}
        </div>`;
    }).join("");
}

function viewTimeline(el) {
    const memNodes = rawGraph.nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    const sorted = [...memNodes].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    // Tarihe göre grupla
    const groups = {};
    sorted.forEach(n => {
        const d = n.created_at ? new Date(n.created_at).toLocaleDateString("tr-TR", {day:"numeric",month:"long",year:"numeric"}) : "Bilinmeyen tarih";
        if (!groups[d]) groups[d] = [];
        groups[d].push(n);
    });

    const impBadge = imp => {
        const v = Number(imp) || 0;
        if (v >= 9) return `<span class="imp-badge imp-critical">${v}</span>`;
        if (v >= 7) return `<span class="imp-badge imp-high">${v}</span>`;
        if (v >= 4) return `<span class="imp-badge imp-med">${v}</span>`;
        return `<span class="imp-badge imp-low">${v}</span>`;
    };

    const rows = Object.entries(groups).map(([date, mems]) => `
        <div class="tl-group">
            <div class="tl-date">${date}</div>
            <div class="tl-items">
                ${mems.map(m => {
                    const info = getRoomInfo(m.oda || "genel");
                    const payload = JSON.stringify({label:m.label,oda:m.oda,content:m.content,tags:m.tags,importance:m.importance,created_at:m.created_at}).replace(/'/g,"&#39;");
                    return `<div class="tl-item" onclick='openMemory(${payload})'>
                        <div class="tl-dot" style="background:${info.color}"></div>
                        <div class="tl-body">
                            <div class="tl-title">${m.label}</div>
                            <div class="tl-meta">
                                <span class="tl-room">${info.icon} ${info.label}</span>
                                ${impBadge(m.importance)}
                            </div>
                        </div>
                    </div>`;
                }).join("")}
            </div>
        </div>`).join("");

    el.innerHTML = `<div class="view">
        <h1 class="section-title">📅 Hafıza Zaman Çizelgesi</h1>
        ${sorted.length === 0
            ? `<div class="empty-state">Henüz kayıtlı anı yok.</div>`
            : `<div class="timeline">${rows}</div>`}
    </div>`;
}

async function viewAnalytics(el) {
    const memNodes = rawGraph.nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    const { rooms, total } = parseStatsFromNodes(rawGraph.nodes);
    const linkCount = rawGraph.links.filter(l => {
        const ids = new Set(memNodes.map(n => n.id));
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        return ids.has(s) && ids.has(t);
    }).length;

    const avgImp = memNodes.length
        ? (memNodes.reduce((sum, n) => sum + (Number(n.importance) || 0), 0) / memNodes.length).toFixed(1)
        : 0;

    // Top 5 by importance
    const top5 = [...memNodes].sort((a, b) => (Number(b.importance)||0) - (Number(a.importance)||0)).slice(0, 5);

    // Importance bands
    const bands = {low:0, med:0, high:0, critical:0};
    memNodes.forEach(n => {
        const v = Number(n.importance) || 0;
        if (v >= 9) bands.critical++;
        else if (v >= 7) bands.high++;
        else if (v >= 4) bands.med++;
        else bands.low++;
    });
    const bandMax = Math.max(...Object.values(bands), 1);

    el.innerHTML = `<div class="view">
        <h1 class="section-title">📊 Analitik</h1>

        <!-- Özet satırı -->
        <div class="stats-row">
            <div class="stat-card"><div class="stat-val">${total}</div><div class="stat-lbl">Toplam Anı</div></div>
            <div class="stat-card"><div class="stat-val">${rooms.length}</div><div class="stat-lbl">Oda</div></div>
            <div class="stat-card"><div class="stat-val">${avgImp}</div><div class="stat-lbl">Ort. Önem</div></div>
            <div class="stat-card"><div class="stat-val">${linkCount}</div><div class="stat-lbl">Bağlantı</div></div>
        </div>

        <div class="analytics-grid">
            <!-- Oda dağılımı -->
            <div class="analytics-card">
                <h3>ODA DAĞILIMI</h3>
                <div class="bar-chart">${rooms.map(r => `
                    <div class="bar-row">
                        <span class="bar-label">${r.label}</span>
                        <div class="bar-track"><div class="bar-fill" style="width:${total>0?(r.count/total)*100:0}%;background:${r.color}"></div></div>
                        <span class="bar-value">${r.count}</span>
                    </div>`).join("")}
                </div>
            </div>

            <!-- Top 5 anı -->
            <div class="analytics-card">
                <h3>EN ÖNEMLİ 5 ANI</h3>
                <div class="top-list">
                    ${top5.map((m, i) => {
                        const info = getRoomInfo(m.oda || "genel");
                        const payload = JSON.stringify({label:m.label,oda:m.oda,content:m.content,tags:m.tags,importance:m.importance,created_at:m.created_at}).replace(/'/g,"&#39;");
                        return `<div class="top-item" onclick='openMemory(${payload})'>
                            <span class="top-rank">#${i+1}</span>
                            <div class="top-info">
                                <div class="top-title">${m.label}</div>
                                <div class="top-room">${info.icon} ${info.label}</div>
                            </div>
                            <span class="top-imp" style="color:${info.color}">${Number(m.importance)||0}</span>
                        </div>`;
                    }).join("")}
                </div>
            </div>

            <!-- Önem dağılımı -->
            <div class="analytics-card">
                <h3>ÖNEM DAĞILIMI</h3>
                <div class="bar-chart">
                    <div class="bar-row"><span class="bar-label imp-label-critical">Kritik 9-10</span><div class="bar-track"><div class="bar-fill" style="width:${(bands.critical/bandMax)*100}%;background:#ef4444"></div></div><span class="bar-value">${bands.critical}</span></div>
                    <div class="bar-row"><span class="bar-label imp-label-high">Yüksek 7-8</span><div class="bar-track"><div class="bar-fill" style="width:${(bands.high/bandMax)*100}%;background:#f59e0b"></div></div><span class="bar-value">${bands.high}</span></div>
                    <div class="bar-row"><span class="bar-label imp-label-med">Orta 4-6</span><div class="bar-track"><div class="bar-fill" style="width:${(bands.med/bandMax)*100}%;background:#4d7cff"></div></div><span class="bar-value">${bands.med}</span></div>
                    <div class="bar-row"><span class="bar-label imp-label-low">Düşük 1-3</span><div class="bar-track"><div class="bar-fill" style="width:${(bands.low/bandMax)*100}%;background:#64748b"></div></div><span class="bar-value">${bands.low}</span></div>
                </div>
            </div>
        </div>
    </div>`;
}

async function viewSettings(el) {
    el.innerHTML = `<div class="view"><h1 class="section-title">⚙️ Ayarlar</h1><div style="color:var(--text-dim);padding:20px">Yükleniyor…</div></div>`;
    const health = await api("/api/health") || {};
    const profile = await api("/api/profile") || {};

    el.innerHTML = `<div class="view">
        <h1 class="section-title">⚙️ Ayarlar</h1>

        <div class="settings-group">
            <h3>SİSTEM DURUMU</h3>
            <div class="setting-row">
                <span class="setting-label">Servis</span>
                <span class="setting-value ${health.status==='ok' ? 'status-ok' : 'status-err'}">${health.status === 'ok' ? '● Aktif' : '● Hata'}</span>
            </div>
            <div class="setting-row">
                <span class="setting-label">Ollama</span>
                <span class="setting-value ${health.ollama ? 'status-ok' : 'status-err'}">${health.ollama ? '● Bağlı' : '● Bağlı değil'}</span>
            </div>
            <div class="setting-row">
                <span class="setting-label">Versiyon</span>
                <span class="setting-value">${health.version || '—'}</span>
            </div>
            <div class="setting-row">
                <span class="setting-label">Son güncelleme</span>
                <span class="setting-value">${health.timestamp ? new Date(health.timestamp).toLocaleString("tr-TR") : '—'}</span>
            </div>
        </div>

        <div class="settings-group">
            <h3>HAFIZA</h3>
            <div class="setting-row">
                <span class="setting-label">Toplam anı</span>
                <span class="setting-value">${health.memories ?? '—'}</span>
            </div>
            <div class="setting-row">
                <span class="setting-label">Agent</span>
                <span class="setting-value">${profile.agent_id || 'default'}</span>
            </div>
            <div class="setting-row">
                <span class="setting-label">Benzerlik eşiği</span>
                <span class="setting-value">${THRESHOLD}</span>
            </div>
        </div>

        <div class="settings-group">
            <h3>MCP ARAÇLARI</h3>
            ${["hafizaya_yaz","hafizada_ara","hafizayi_aktar","oturum_ozetle","gecmise_bak","hatirlat","grafik_sorgula","oda_listele","profil_goster","hafizayi_unut"]
                .map(t => `<div class="setting-row"><span class="setting-label">${t}</span><span class="setting-value status-ok">● Aktif</span></div>`)
                .join("")}
        </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════

function initSearch() {
    const input = document.getElementById("searchInput");
    const box = document.getElementById("searchResults");
    let _searchTimer = null;
    input?.addEventListener("input", () => {
        const q = input.value.trim();
        if (q.length < 2) return box.classList.remove("active");
        clearTimeout(_searchTimer);
        _searchTimer = setTimeout(async () => {
            const results = await api(`/api/search?q=${encodeURIComponent(q)}&n=5`) || [];
            box.innerHTML = results.map(m => `<div class="search-result-item" onclick='openMemory(${JSON.stringify({label:m.konu,oda:m.oda,content:m.content,tags:m.tags,importance:m.importance,created_at:m.created_at}).replace(/'/g,"&#39;")})'>
                <h4>${m.konu}</h4><p>${(m.content||"").substring(0,80)}…</p></div>`).join("");
            box.classList.toggle("active", results.length > 0);
        }, 300);
    });
}

function renderGraph() {
    const area = document.getElementById("graphArea"); if (!area) return;
    const w = area.clientWidth || 700;
    const h = area.clientHeight || 600;
    area.innerHTML = "";

    const allNodes = rawGraph.nodes.filter(n => n.type !== "entity" && n.oda !== "entity");
    const nodeIds = new Set(allNodes.map(n => n.id));
    const allLinks = rawGraph.links.filter(l => {
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        return nodeIds.has(s) && nodeIds.has(t);
    });

    if (allNodes.length === 0) {
        area.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-dim);font-size:0.9rem;flex-direction:column;gap:12px"><span style="font-size:2rem">🧠</span>Henüz hafıza anısı yok</div>';
        return;
    }

    const odaColor = {
        mimari:"#a855f7", guvenlik:"#4d7cff", donanim:"#00FFCC",
        ogrenme:"#f59e0b", kisisel:"#ec4899", genel:"#64748b"
    };
    const getColor = oda => odaColor[(oda||"genel").toLowerCase()] || "#64748b";

    // Focus: hangi nodelar bağlı?
    const focusNeighbors = new Set();
    if (focusNodeId) {
        focusNeighbors.add(focusNodeId);
        allLinks.forEach(l => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            if (s === focusNodeId) focusNeighbors.add(t);
            if (t === focusNodeId) focusNeighbors.add(s);
        });
    }
    const hasFocus = focusNodeId && focusNeighbors.size > 0;

    const svg = d3.select("#graphArea").append("svg")
        .attr("width", w).attr("height", h)
        .style("background", "radial-gradient(ellipse at 50% 40%, rgba(138,43,226,0.07) 0%, rgba(5,5,8,0) 65%)")
        .call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", e => g.attr("transform", e.transform)));

    // SVG Defs: glow filtresi + gradient
    const defs = svg.append("defs");
    ["violet","cyan","blue","amber","pink"].forEach((name, i) => {
        const cols = ["#a855f7","#00FFCC","#4d7cff","#f59e0b","#ec4899"];
        const filt = defs.append("filter").attr("id", `glow-${name}`).attr("x","-50%").attr("y","-50%").attr("width","200%").attr("height","200%");
        filt.append("feGaussianBlur").attr("stdDeviation","5").attr("result","blur");
        const fm = filt.append("feMerge");
        fm.append("feMergeNode").attr("in","blur");
        fm.append("feMergeNode").attr("in","SourceGraphic");
    });

    const glowId = oda => {
        const m = {mimari:"violet", guvenlik:"blue", donanim:"cyan", ogrenme:"amber", kisisel:"pink"};
        return `glow-${m[(oda||"genel").toLowerCase()] || "violet"}`;
    };

    const g = svg.append("g");

    // Düğüm kopyaları (D3 mutate eder)
    const nodes = allNodes.map(n => ({...n}));
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const links = allLinks.map(l => ({
        source: typeof l.source === "object" ? l.source.id : l.source,
        target: typeof l.target === "object" ? l.target.id : l.target,
        value: l.value || 0.5
    }));

    simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(d => hasFocus && focusNeighbors.has(d.source.id||d.source) ? 120 : 160))
        .force("charge", d3.forceManyBody().strength(-450))
        .force("center", d3.forceCenter(w/2, h/2))
        .force("collision", d3.forceCollide(d => d.id === focusNodeId ? 80 : 55));

    // Bağlantı çizgileri
    const link = g.selectAll(".gl").data(links).join("line").attr("class","gl")
        .attr("stroke", d => {
            if (!hasFocus) return getColor(nodeMap.get(d.source)?.oda || "genel");
            const active = focusNeighbors.has(d.source) && focusNeighbors.has(d.target);
            return active ? getColor(nodeMap.get(d.source)?.oda || "genel") : "rgba(100,100,120,0.1)";
        })
        .attr("stroke-opacity", d => {
            if (!hasFocus) return 0.45;
            return (focusNeighbors.has(d.source) && focusNeighbors.has(d.target)) ? 0.75 : 0.08;
        })
        .attr("stroke-width", d => {
            if (!hasFocus) return Math.max(1.5, d.value * 3);
            return (focusNeighbors.has(d.source) && focusNeighbors.has(d.target)) ? Math.max(2, d.value * 4) : 0.5;
        });

    // Düğüm grupları
    const nodeG = g.selectAll(".gn").data(nodes).join("g").attr("class","gn")
        .style("cursor","pointer")
        .on("click", (e, d) => {
            e.stopPropagation();
            if (focusNodeId === d.id) { focusNodeId = null; } // ikinci tıkta focus kaldır
            else { focusNodeId = d.id; openMemory(d); }
            renderGraph();
        })
        .call(d3.drag()
            .on("start",(e,d)=>{if(!e.active)simulation.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;})
            .on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y;})
            .on("end",(e,d)=>{if(!e.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;}));

    // Focus dışı düğümleri soldur
    const nodeOpacity = d => {
        if (!hasFocus) return 1;
        return focusNeighbors.has(d.id) ? 1 : 0.18;
    };

    // Glow hale
    nodeG.append("circle")
        .attr("r", d => d.id===focusNodeId ? 42 : (hasFocus && focusNeighbors.has(d.id) ? 28 : 22))
        .attr("fill", d => getColor(d.oda))
        .attr("opacity", d => {
            if (!hasFocus) return 0.07;
            return d.id===focusNodeId ? 0.25 : (focusNeighbors.has(d.id) ? 0.12 : 0.02);
        })
        .attr("filter", d => `url(#${glowId(d.oda)})`);

    // Ana daire
    nodeG.append("circle")
        .attr("r", d => d.id===focusNodeId ? 22 : (hasFocus && focusNeighbors.has(d.id) ? 16 : 13))
        .attr("fill", d => getColor(d.oda))
        .attr("opacity", d => nodeOpacity(d) * 0.92)
        .attr("stroke", d => d.id===focusNodeId ? "rgba(255,255,255,0.7)" : (hasFocus && focusNeighbors.has(d.id) ? "rgba(255,255,255,0.3)" : "transparent"))
        .attr("stroke-width", 1.5)
        .attr("filter", d => d.id===focusNodeId || (hasFocus && focusNeighbors.has(d.id)) ? `url(#${glowId(d.oda)})` : "none");

    // Oda baş harfi
    nodeG.append("text")
        .attr("text-anchor","middle").attr("dominant-baseline","central")
        .attr("font-size", d => d.id===focusNodeId ? "13px" : "9px")
        .attr("font-weight","700")
        .attr("fill", d => `rgba(255,255,255,${nodeOpacity(d) > 0.5 ? 0.9 : 0.2})`)
        .attr("pointer-events","none")
        .text(d => (d.oda||"G").charAt(0).toUpperCase());

    // Etiket arka planı
    const labelPad = 6;
    const maxChars = d => d.id===focusNodeId ? 30 : 22;

    nodeG.append("rect")
        .attr("x", d => d.id===focusNodeId ? 26 : 18)
        .attr("y", -9)
        .attr("width", d => Math.min(d.label.length, maxChars(d)) * (d.id===focusNodeId ? 7.5 : 6.2) + labelPad*2)
        .attr("height", 18).attr("rx", 5)
        .attr("fill","rgba(5,5,12,0.82)")
        .attr("stroke", d => getColor(d.oda))
        .attr("stroke-width", 0.6)
        .attr("opacity", d => nodeOpacity(d));

    // Etiket metni
    nodeG.append("text")
        .attr("x", d => d.id===focusNodeId ? 32 : 24)
        .attr("y", 4)
        .attr("font-size", d => d.id===focusNodeId ? "11.5px" : "10px")
        .attr("fill", d => {
            if (d.id===focusNodeId) return "#fff";
            if (!hasFocus || focusNeighbors.has(d.id)) return "#d1ddef";
            return "rgba(150,150,170,0.3)";
        })
        .attr("font-family","Outfit,sans-serif")
        .attr("font-weight", d => d.id===focusNodeId ? "600" : "400")
        .attr("pointer-events","none")
        .text(d => {
            const mc = maxChars(d);
            return d.label.length > mc ? d.label.substring(0,mc)+"…" : d.label;
        });

    // Canvas tıklanınca focus kaldır
    svg.on("click", () => { if (focusNodeId) { focusNodeId = null; renderGraph(); } });

    simulation.on("tick",()=>{
        link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
            .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
        nodeG.attr("transform",d=>`translate(${d.x},${d.y})`);
    });

    // Graph subtitle güncelle
    const sub = document.getElementById("graphSubtitle");
    if (sub) {
        if (hasFocus) {
            const focused = allNodes.find(n => n.id===focusNodeId);
            sub.textContent = `"${focused?.label||""}" · ${focusNeighbors.size-1} bağlantı · boşluğa tıkla serbest bırak`;
            sub.style.color = getColor(focused?.oda);
        } else {
            sub.textContent = `${allNodes.length} anı · ${allLinks.length} bağlantı`;
            sub.style.color = "";
        }
    }

}


function openMemory(data) {
    let panel = document.getElementById("detailPanel");
    if (!panel) {
        document.body.insertAdjacentHTML("beforeend", `<div id="detailPanel" class="detail-panel">
            <div class="detail-header"><span id="detailBadge" class="detail-badge">ODA</span><button class="close-btn" onclick="closeDetail()">×</button></div>
            <h2 id="detailTitle"></h2>
            <div id="detailMeta" class="detail-meta"></div>
            <div id="detailContent" class="detail-body"></div>
            <div id="detailTags" class="detail-tags"></div>
        </div>`);
        panel = document.getElementById("detailPanel");
    }
    document.getElementById("detailTitle").innerText = data.label || data.konu || "";
    document.getElementById("detailBadge").innerText = (data.oda || "genel").toUpperCase();
    document.getElementById("detailContent").innerText = data.content || "";

    const metaEl = document.getElementById("detailMeta");
    const parts = [];
    if (data.importance) parts.push(`Önem: ${Number(data.importance).toFixed(0)}/10`);
    if (data.created_at) parts.push(new Date(data.created_at).toLocaleDateString("tr-TR", {day:"numeric",month:"long",year:"numeric"}));
    metaEl.innerText = parts.join("  ·  ");

    const tagsEl = document.getElementById("detailTags");
    const tags = data.tags || [];
    tagsEl.innerHTML = tags.map(t => `<span class="memory-tag">${t}</span>`).join("");

    panel.classList.add("active");
}
window.closeDetail = () => document.getElementById("detailPanel")?.classList.remove("active");
document.addEventListener("keydown", e => { if (e.key === "Escape") window.closeDetail(); });


let _lastTotal = -1;
const sse = new EventSource("/api/events");
sse.onmessage = async e => {
    try {
        const data = JSON.parse(e.data);
        sseStatus = "CONNECTED";
        const total = data.total ?? 0;
        document.getElementById("headerTotal").innerText = total;
        if (_lastTotal !== -1 && total !== _lastTotal) {
            await loadGraphData();
            await loadSidebar();
            const { view } = getRoute();
            if (view === "home") renderGraph();
        }
        _lastTotal = total;
    } catch { sseStatus = e.data; }
};
sse.onopen = () => { sseStatus = "CONNECTED"; document.getElementById("pulseStatus").innerText = "Aktif (SSE)"; };
sse.onerror = () => { sseStatus = "DISCONNECTED"; document.getElementById("pulseStatus").innerText = "Bağlantı kesildi"; };

(async () => { await loadSidebar(); await router(); })();
