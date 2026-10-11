// Shared kit for architecture / topology diagrams (see assets/T22/01-architecture.html).
// 1. <div class="node" id="x" data-icon="router">…</div>  → the device icon is injected from ICONS below.
// 2. window.LINKS = [{a:"x", b:"y", k:"api", label:"HTTPS REST", dir:"fwd"}, …] → drawn as one SVG overlay.
//    k    : api | mgmt | control | data | phys | error           (line style, see the legend in arch.css)
//    dir  : fwd (arrow at b) | back (arrow at a) | both | none   (default: fwd for api/mgmt/control/error, none for data/phys)
//    s    : "b-t" style sides for a and b (t=top, b=bottom, l=left, r=right). Default: picked from the relative position.
//    ao/bo: shift the anchor along the edge in px (to separate parallel links). mid: 0..1, where a 3-segment path bends.
//    t    : 0..1, where along the path the label sits (default 0.5). lx/ly: nudge the label in px.
//    r    : "straight" = one direct (diagonal) line instead of right angles. Use it for meshes (spine-leaf, full mesh).
// Icons are simplified line-art in the style of the Cisco network topology icons; no external files, renders offline.
(function () {
  const B = "#1b6fa8", T = "#4f9bd1", D = "#12507a", W = "#fff";
  const arrow = (x1, y1, x2, y2) => {
    const a = Math.atan2(y2 - y1, x2 - x1), h = 3.6;
    const p1 = [x2 - h * Math.cos(a - 0.6), y2 - h * Math.sin(a - 0.6)], p2 = [x2 - h * Math.cos(a + 0.6), y2 - h * Math.sin(a + 0.6)];
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${W}" stroke-width="1.8"/><polygon points="${x2},${y2} ${p1} ${p2}" fill="${W}"/>`;
  };
  const prism = (front, top, side) =>
    `<polygon points="10,8 60,8 54,18 4,18" fill="${top || T}"/><rect x="4" y="18" width="50" height="24" fill="${front || B}"/>` +
    `<polygon points="54,18 60,8 60,32 54,42" fill="${side || D}"/>`;
  const txt = (x, y, s, size) => `<text x="${x}" y="${y}" fill="${W}" font-family="Arial" font-weight="700" font-size="${size || 11}" text-anchor="middle">${s}</text>`;
  const gear = (cx, cy, r) => {
    let p = ""; for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8, rr = i % 2 ? r : r * 1.35; p += `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)} `; }
    return `<polygon points="${p}" fill="${W}"/><circle cx="${cx}" cy="${cy}" r="${r * 0.45}" fill="${B}"/>`;
  };
  const waves = (cx, cy, c) => [6, 11, 16].map(r => `<path d="M ${cx - r * 0.75} ${cy - r * 0.65} A ${r} ${r} 0 0 1 ${cx + r * 0.75} ${cy - r * 0.65}" stroke="${c || B}" stroke-width="2.2" fill="none"/>`).join("");
  const ICONS = {
    router: `<rect x="6" y="15" width="52" height="22" fill="${B}"/><ellipse cx="32" cy="37" rx="26" ry="8" fill="${B}"/><ellipse cx="32" cy="15" rx="26" ry="8" fill="${T}"/>` +
            arrow(24, 11, 30, 14) + arrow(40, 19, 34, 16) + arrow(40, 11, 45, 13.5) + arrow(24, 19, 19, 16.5),
    switch: prism() + arrow(14, 11, 30, 11) + arrow(48, 15, 32, 15) + txt(29, 35, "⇄", 14),
    l3switch: prism() + arrow(14, 11, 30, 11) + arrow(48, 15, 32, 15) + txt(29, 35, "L3", 12),
    firewall: prism("#b9472f", "#d9765e", "#7d2a1b") +
              [24, 30, 36].map(y => `<line x1="4" y1="${y}" x2="54" y2="${y}" stroke="${W}" stroke-width="1.4"/>`).join("") +
              [[17, 18, 24], [37, 18, 24], [10, 24, 30], [29, 24, 30], [46, 24, 30], [17, 30, 36], [37, 30, 36], [10, 36, 42], [29, 36, 42], [46, 36, 42]]
                .map(([x, a, b]) => `<line x1="${x}" y1="${a}" x2="${x}" y2="${b}" stroke="${W}" stroke-width="1.4"/>`).join(""),
    lb: prism() + arrow(10, 30, 24, 30) + arrow(24, 30, 46, 22) + arrow(24, 30, 46, 30) + arrow(24, 30, 46, 38),
    server: `<polygon points="20,6 44,6 48,2 24,2" fill="${T}"/><rect x="20" y="6" width="24" height="42" fill="${B}"/><polygon points="44,6 48,2 48,44 44,48" fill="${D}"/>` +
            [12, 18, 24].map(y => `<rect x="24" y="${y}" width="16" height="3" fill="${W}"/>`).join("") + `<circle cx="32" cy="40" r="2.5" fill="${W}"/>`,
    controller: `<polygon points="20,6 44,6 48,2 24,2" fill="${T}"/><rect x="20" y="6" width="24" height="42" fill="${B}"/><polygon points="44,6 48,2 48,44 44,48" fill="${D}"/>` +
                `<rect x="24" y="11" width="16" height="3" fill="${W}"/>` + gear(32, 30, 6),
    cloud: `<path d="M16 42 C5 42 4 28 14 27 C13 16 27 12 32 20 C36 10 52 12 51 24 C61 24 62 42 50 42 Z" fill="${T}" stroke="${B}" stroke-width="2"/>`,
    ap: `<ellipse cx="32" cy="42" rx="20" ry="5" fill="${D}"/><path d="M12 42 Q32 22 52 42 Z" fill="${B}"/>` + waves(32, 24),
    wlc: prism() + waves(29, 38, W).replace(/stroke-width="2.2"/g, 'stroke-width="1.8"'),
    laptop: `<rect x="14" y="8" width="36" height="24" rx="2" fill="${B}"/><rect x="17" y="11" width="30" height="18" fill="#dbeafe"/><polygon points="8,40 56,40 50,33 14,33" fill="${D}"/>`,
    script: `<rect x="14" y="8" width="36" height="24" rx="2" fill="${B}"/><rect x="17" y="11" width="30" height="18" fill="#0f172a"/>` +
            `<text x="32" y="25" fill="#7ee787" font-family="Menlo, monospace" font-weight="700" font-size="11" text-anchor="middle">&lt;/&gt;</text><polygon points="8,40 56,40 50,33 14,33" fill="${D}"/>`,
    gui: `<rect x="10" y="5" width="44" height="30" rx="2" fill="${B}"/><rect x="13" y="8" width="38" height="24" fill="#dbeafe"/>` +
         `<rect x="16" y="11" width="14" height="8" fill="${T}"/><rect x="33" y="11" width="15" height="18" fill="${T}"/><rect x="16" y="21" width="14" height="8" fill="${T}"/><rect x="28" y="35" width="8" height="6" fill="${D}"/><rect x="20" y="41" width="24" height="4" fill="${D}"/>`,
    user: `<circle cx="32" cy="14" r="9" fill="${B}"/><path d="M14 46 Q14 26 32 26 Q50 26 50 46 Z" fill="${B}"/>`,
    phone: `<rect x="12" y="20" width="40" height="24" rx="3" fill="${B}"/><rect x="18" y="24" width="14" height="9" fill="#dbeafe"/>` +
           [36, 42].map(x => `<rect x="${x}" y="25" width="4" height="3" fill="${W}"/><rect x="${x}" y="31" width="4" height="3" fill="${W}"/>`).join("") +
           `<path d="M10 20 C10 8 54 8 54 20 L46 20 C46 14 18 14 18 20 Z" fill="${D}"/>`,
    roomdevice: `<rect x="6" y="6" width="52" height="30" rx="2" fill="${D}"/><rect x="9" y="9" width="46" height="24" fill="#dbeafe"/><circle cx="32" cy="40" r="3" fill="${B}"/><rect x="18" y="44" width="28" height="4" rx="2" fill="${B}"/>`,
    camera: `<rect x="10" y="10" width="44" height="6" rx="2" fill="${D}"/><path d="M14 16 L50 16 L50 22 A18 18 0 0 1 14 22 Z" fill="${B}"/><circle cx="32" cy="27" r="6" fill="#0f172a"/><circle cx="34" cy="25" r="1.6" fill="${W}"/>`,
    db: `<rect x="16" y="10" width="32" height="30" fill="${B}"/><ellipse cx="32" cy="40" rx="16" ry="5" fill="${B}"/><ellipse cx="32" cy="10" rx="16" ry="5" fill="${T}"/>` +
        `<path d="M16 20 A16 5 0 0 0 48 20 M16 30 A16 5 0 0 0 48 30" stroke="${W}" stroke-width="1.6" fill="none"/>`,
    chassis: `<rect x="8" y="4" width="48" height="42" rx="2" fill="${B}"/>` + [8, 16, 24, 32].map(y => `<rect x="12" y="${y}" width="40" height="6" fill="#dbeafe"/><circle cx="16" cy="${y + 3}" r="1.5" fill="${B}"/>`).join("") +
             `<rect x="12" y="40" width="40" height="3" fill="${D}"/>`,
    fi: prism() + arrow(14, 11, 30, 11) + arrow(48, 15, 32, 15) + txt(29, 35, "FI", 12),
    phonesvc: `<rect x="18" y="4" width="28" height="42" rx="2" fill="${B}"/>` + [10, 16].map(y => `<rect x="22" y="${y}" width="20" height="3" fill="${W}"/>`).join("") +
              `<path d="M24 34 C24 26 40 26 40 34 L36 34 C36 30 28 30 28 34 Z" fill="${W}"/><rect x="26" y="34" width="12" height="7" rx="1" fill="${W}"/>`,
    internet: `<circle cx="32" cy="25" r="19" fill="${T}" stroke="${B}" stroke-width="2"/><ellipse cx="32" cy="25" rx="8" ry="19" fill="none" stroke="${W}" stroke-width="1.6"/>` +
              `<line x1="13" y1="25" x2="51" y2="25" stroke="${W}" stroke-width="1.6"/><path d="M16 15 Q32 20 48 15 M16 35 Q32 30 48 35" stroke="${W}" stroke-width="1.6" fill="none"/>`,
    dns: `<polygon points="20,6 44,6 48,2 24,2" fill="${T}"/><rect x="20" y="6" width="24" height="42" fill="${B}"/><polygon points="44,6 48,2 48,44 44,48" fill="${D}"/>` + txt(32, 30, "DNS", 9),
    proxy: prism() + txt(29, 35, "⇆", 15) + `<circle cx="16" cy="13" r="3" fill="${W}"/><circle cx="44" cy="13" r="3" fill="${W}"/><line x1="19" y1="13" x2="41" y2="13" stroke="${W}" stroke-width="1.8"/>`,
  };
  window.ARCH_ICONS = ICONS;

  function draw() {
    document.querySelectorAll(".node[data-icon]").forEach(n => {
      if (n.querySelector(".ico")) return;
      const s = ICONS[n.dataset.icon]; if (!s) { console.error("unknown icon", n.dataset.icon); return; }
      const d = document.createElement("span"); d.className = "ico";
      d.innerHTML = `<svg viewBox="0 0 64 50" xmlns="http://www.w3.org/2000/svg">${s}</svg>`;
      n.prepend(d);
    });
    const sheet = document.querySelector(".sheet"), base = sheet.getBoundingClientRect();
    const box = el => { const r = el.getBoundingClientRect(); return { l: r.left - base.left, t: r.top - base.top, r: r.right - base.left, b: r.bottom - base.top }; };
    const anchor = (el, side, off) => {
      const nb = box(el), ico = el.querySelector(":scope > .ico"), ib = ico ? box(ico) : nb;
      const cx = (ib.l + ib.r) / 2 + (side === "t" || side === "b" ? off : 0), cy = (ib.t + ib.b) / 2 + (side === "l" || side === "r" ? off : 0);
      return { t: [cx, ib.t - 3], b: [cx, nb.b + 3], l: [ib.l - 5, cy], r: [ib.r + 5, cy] }[side];
    };
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg"); svg.setAttribute("class", "links");
    svg.setAttribute("width", sheet.scrollWidth); svg.setAttribute("height", sheet.scrollHeight);
    const kinds = { api: "--k-api", mgmt: "--k-mgmt", control: "--k-control", data: "--k-data", phys: "--k-phys", error: "--k-error" };
    const css = getComputedStyle(document.documentElement);
    let defs = "<defs>";
    for (const [k, v] of Object.entries(kinds)) {
      const c = css.getPropertyValue(v).trim();
      defs += `<marker id="e-${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="${k === "data" ? 3.2 : 5.5}" markerHeight="${k === "data" ? 3.2 : 5.5}" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`;
    }
    svg.innerHTML = defs + "</defs>";
    sheet.appendChild(svg);
    for (const L of window.LINKS || []) {
      const A = document.getElementById(L.a), Bn = document.getElementById(L.b);
      if (!A || !Bn) { console.error("missing node for link", L); continue; }
      let [sa, sb] = (L.s || "").split("-");
      if (!sa) {
        const a = box(A), b = box(Bn), dx = (b.l + b.r - a.l - a.r) / 2, dy = (b.t + b.b - a.t - a.b) / 2;
        if (Math.abs(dy) > Math.abs(dx) * 0.6) { sa = dy > 0 ? "b" : "t"; sb = dy > 0 ? "t" : "b"; } else { sa = dx > 0 ? "r" : "l"; sb = dx > 0 ? "l" : "r"; }
      }
      let [x1, y1] = anchor(A, sa, L.ao || 0), [x2, y2] = anchor(Bn, sb, L.bo || 0);
      const m = L.mid ?? 0.5, isNode = el => el.classList.contains("node");
      // A link into a zone (not a node) lands straight across from the other end instead of at the zone's centre.
      if (!isNode(Bn) && isNode(A)) { if ("tb".includes(sb)) x2 = x1 + (L.bo || 0); else y2 = y1 + (L.bo || 0); }
      if (!isNode(A) && isNode(Bn)) { if ("tb".includes(sa)) x1 = x2 + (L.ao || 0); else y1 = y2 + (L.ao || 0); }
      const va = "tb".includes(sa), vb = "tb".includes(sb);
      let pts;
      if (L.r === "straight") pts = [[x1, y1], [x2, y2]];
      else if (va && vb) pts = Math.abs(x1 - x2) < 3 ? [[x1, y1], [x1, y2]] : [[x1, y1], [x1, y1 + (y2 - y1) * m], [x2, y1 + (y2 - y1) * m], [x2, y2]];
      else if (!va && !vb) pts = Math.abs(y1 - y2) < 3 ? [[x1, y1], [x2, y1]] : [[x1, y1], [x1 + (x2 - x1) * m, y1], [x1 + (x2 - x1) * m, y2], [x2, y2]];
      else if (va) pts = [[x1, y1], [x1, y2], [x2, y2]];
      else pts = [[x1, y1], [x2, y1], [x2, y2]];
      const k = L.k || "phys", p = document.createElementNS(svgNS, "path");
      p.setAttribute("d", "M " + pts.map(q => q.join(" ")).join(" L "));
      p.setAttribute("class", "k-" + k);
      const dir = L.dir || (["data", "phys"].includes(k) ? "none" : "fwd");
      if (dir === "fwd" || dir === "both") p.setAttribute("marker-end", `url(#e-${k})`);
      if (dir === "back" || dir === "both") p.setAttribute("marker-start", `url(#e-${k})`);
      svg.appendChild(p);
      if (L.label) {
        const seg = [], tot = pts.slice(1).reduce((s, q, i) => { const l = Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]); seg.push(l); return s + l; }, 0);
        let want = tot * (L.t ?? 0.5), i = 0; while (i < seg.length - 1 && want > seg[i]) { want -= seg[i]; i++; }
        const f = seg[i] ? want / seg[i] : 0, lx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, ly = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f;
        const d = document.createElement("div"); d.className = "lbl"; d.innerHTML = L.label;
        d.style.left = (lx + (L.lx || 0)) + "px"; d.style.top = (ly + (L.ly || 0)) + "px";
        d.style.setProperty("--lc", css.getPropertyValue(kinds[k]).trim());
        sheet.appendChild(d);
      }
    }
    window.ARCH_READY = true;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", draw); else draw();
})();
