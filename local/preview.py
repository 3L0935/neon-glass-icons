"""Write the local Hairline Glass preview page from glyphs.json."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
glyphs = json.loads((HERE / "glyphs.json").read_text())
out = Path(sys.argv[1])

APPS = [  # id, family, label
    ("zen", "media", "Zen"), ("dolphin", "sys", "Dolphin"), ("tauon", "media", "Tauon"), ("hermes", "sys", "Hermes Hub"),
    ("steam", "game", "Steam"), ("discord", "media", "Discord"), ("obsidian", "sys", "Obsidian"), ("zed", "sys", "Zed"),
    ("kitty", "sys", "kitty"), ("settings", "sys", "Paramètres"), ("discover", "sys", "Discover"), ("heroic", "game", "Heroic"),
    ("protonplus", "game", "ProtonPlus"), ("mango", "game", "MangoJuice"), ("lsfg", "game", "lsfg-vk"), ("btop", "sys", "btop"),
    ("easyeffects", "media", "Easy Effects"), ("kdeconnect", "sys", "KDE Connect"), ("spectacle", "media", "Spectacle"),
    ("kate", "sys", "Kate"), ("haruna", "media", "Haruna"), ("cachy", "sys", "CachyOS Hello"), ("partition", "sys", "Partitions"),
]
PANEL = ["obsidian", "tauon", "zed", "kitty", "dolphin", "zen", "steam", "discord"]

html = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hairline Glass</title>
<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root { color-scheme: dark; --bg:#0d0b1f; --edge:rgba(140,130,230,.22); --text:#e8e6ff; --muted:#9a94d0; --faint:#5d579a; --cyan:#46b5e7; --pink:#e45ad8 }
* { box-sizing: border-box }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.55 Inter, system-ui, sans-serif }
.wrap { max-width:1120px; margin:0 auto; padding:40px 16px 72px }
h1,h2 { font-family:"Chakra Petch", Inter, sans-serif; font-weight:600; margin:0 }
h1 { font-size:40px } h1 span { color:var(--cyan) } h2 { font-size:20px; margin-top:36px }
.kicker { font:500 11px "JetBrains Mono", monospace; letter-spacing:.16em; text-transform:uppercase; color:var(--pink) }
.sub { color:var(--muted); max-width:70ch; margin:8px 0 0 }
.desk { margin-top:14px; border-radius:12px; border:1px solid var(--edge); padding:18px; display:grid; gap:18px;
  background: radial-gradient(110% 80% at 50% 115%, rgba(70,181,231,.28), transparent 60%), radial-gradient(60% 50% at 85% 10%, rgba(228,90,216,.12), transparent 70%), linear-gradient(180deg,#110e29,#1b1442) }
.panel { display:flex; gap:10px; padding:7px 10px; border-radius:9px; background:rgba(13,11,31,.75); border:1px solid var(--edge); overflow-x:auto }
.panel svg { width:30px; height:30px; flex:none }
.apps { display:grid; grid-template-columns:repeat(auto-fill,minmax(92px,1fr)); gap:16px 8px }
.item { display:grid; justify-items:center; gap:4px; font:11px "JetBrains Mono", monospace; color:var(--muted); text-align:center }
.item svg { width:64px; height:64px }
.item span { max-width:92px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
.orig { display:grid; grid-template-columns:repeat(auto-fill,minmax(92px,1fr)); gap:16px 8px }
.orig img { width:48px; height:48px }
.tray { display:flex; align-items:center; gap:14px; padding:8px 14px; border-radius:9px; background:rgba(13,11,31,.85); border:1px solid var(--edge); width:max-content; max-width:100% ; overflow-x:auto }
.tray .ti { display:grid; justify-items:center; gap:4px; font:10px "JetBrains Mono", monospace; color:var(--faint) }
.tray svg { width:22px; height:22px }
.tray.big svg { width:56px; height:56px }
.tray .ti span { display:none } .tray.big .ti span { display:block }
.matrix { overflow-x:auto }
.matrix table { border-collapse:collapse }
.matrix th { font:500 10.5px "JetBrains Mono", monospace; color:var(--faint); padding:4px 6px; text-align:center; white-space:nowrap }
.matrix th.row { text-align:right; color:var(--muted) }
.matrix td { padding:4px 6px; text-align:center }
.matrix svg { width:52px; height:52px; display:block }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:18px } @media (max-width:900px){ .tray { display:flex; align-items:center; gap:14px; padding:8px 14px; border-radius:9px; background:rgba(13,11,31,.85); border:1px solid var(--edge); width:max-content; max-width:100% ; overflow-x:auto }
.tray .ti { display:grid; justify-items:center; gap:4px; font:10px "JetBrains Mono", monospace; color:var(--faint) }
.tray svg { width:22px; height:22px }
.tray.big svg { width:56px; height:56px }
.tray .ti span { display:none } .tray.big .ti span { display:block }
.matrix { overflow-x:auto }
.matrix table { border-collapse:collapse }
.matrix th { font:500 10.5px "JetBrains Mono", monospace; color:var(--faint); padding:4px 6px; text-align:center; white-space:nowrap }
.matrix th.row { text-align:right; color:var(--muted) }
.matrix td { padding:4px 6px; text-align:center }
.matrix svg { width:52px; height:52px; display:block }
.cols { grid-template-columns:1fr } }
</style></head><body><div class="wrap">
<div class="kicker">Glass Lagoon · icônes · v2</div>
<h1>Hairline <span>Glass</span></h1>
<p class="sub">Cette fois, les symboles viennent des vrais logos : versions monochromes de char-white quand elles existent, sinon le logo officiel de l'appli, vectorisé puis recoloré. Symboles pleins en dégradé (v5 : mini-icônes du tray, dossiers aux symboles plus grands).</p>

<h2>Tes applis</h2>
<div class="desk"><div class="panel" id="panel-fill"></div><div class="apps" id="apps-fill"></div></div>
<h2>Mini-icônes · zone de notification</h2>
<p class="sub">Dans le tray, pas de tuile : le symbole seul en lavande, avec une pastille de couleur pour les états (nouvelle notification, mise à jour, enregistrement). En taille réelle (22 px), puis zoomé.</p>
<div class="desk">
  <div class="tray" id="tray-real"></div>
  <div class="tray big" id="tray-zoom"></div>
  <p class="sub" style="margin:0">⚠ Discord et GPU Screen Recorder envoient une image toute faite au lieu d'un nom d'icône : aucun thème ne peut les remplacer. Je fournis quand même les icônes GPU Screen Recorder (idle / recording / paused), au cas où il passerait par les noms.</p>
</div>
<h2>Dossiers · 14 symboles × 7 coloris</h2>
<p class="sub">Le nom de chaque coloris suit la convention de Papirus (folder-cyan-github, folder-violet-games…). On choisit le coloris par défaut, et Dolphin permet de changer la couleur d'un dossier précis (clic droit → Propriétés → icône).</p>
<div class="desk"><div class="matrix" id="folders"></div></div>
<h2>Les logos d'origine, pour comparer</h2>
<div class="desk"><div class="orig" id="orig"></div></div>
</div>
<script>
const GLYPHS = __GLYPHS__;
const APPS = __APPS__;
const PANEL = __PANEL__;
const FAM = { sys: ['#46b5e7', '#a55ae9'], media: ['#a55ae9', '#e45ad8'], game: ['#e45ad8', '#46b5e7'] };
let uid = 0;
function icon(name, fam, mode) {
  const g = GLYPHS[name], id = 'i' + (uid++), [a, b] = FAM[fam];
  const [x0, y0, x1, y1] = g.bbox, bw = x1 - x0, bh = y1 - y0;
  const k = 14 / Math.max(bw, bh), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  // potrace paths are in tenths of a point: a 1-unit hairline is 1 / (k * 0.1) path units
  const paint = mode === 'fill'
    ? `fill="url(#${id})"`
    : `fill="none" stroke="url(#${id})" stroke-width="${(0.9 / (k * 0.1)).toFixed(1)}" stroke-linejoin="round"`;
  return `<svg viewBox="0 0 24 24" aria-hidden="true">
    <defs>
      <linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
      <linearGradient id="${id}e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${a}" stop-opacity=".55"/><stop offset="1" stop-color="${b}" stop-opacity=".18"/></linearGradient>
    </defs>
    <rect x="1" y="1" width="22" height="22" rx="6" fill="#171339" fill-opacity=".92" stroke="url(#${id}e)" stroke-width=".5"/>
    <path d="M3 7.5C3 4.5 4.5 3 7.5 3h9C19.5 3 21 4.5 21 7.5" fill="none" stroke="#fff" stroke-opacity=".07" stroke-width=".6"/>
    <g transform="translate(12 12) scale(${k.toFixed(5)}) translate(${-cx} ${-cy})"><g transform="${g.transform}"><path d="${g.d}" ${paint} fill-rule="evenodd"/></g></g>
  </svg>`;
}
const fam = Object.fromEntries(APPS.map(a => [a[0], a[1]]));
for (const mode of ['fill']) {
  document.getElementById('panel-' + mode).innerHTML = PANEL.map(n => icon(n, fam[n], mode)).join('');
  document.getElementById('apps-' + mode).innerHTML = APPS.map(([n, f, l]) => `<div class="item">${icon(n, f, mode)}<span>${l}</span></div>`).join('');
}
function mini(name, dot) {
  const g = GLYPHS[name], [x0, y0, x1, y1] = g.bbox, k = 17 / Math.max(x1 - x0, y1 - y0);
  const badge = !dot ? '' : dot === 'slash'
    ? '<path d="M4 20 20 4" stroke="#0d0b1f" stroke-width="3.2" stroke-linecap="round"/><path d="M4 20 20 4" stroke="#ff6ba8" stroke-width="1.6" stroke-linecap="round"/>'
    : `<circle cx="19" cy="5" r="4" fill="#0d0b1f"/><circle cx="19" cy="5" r="2.8" fill="${dot}"/>`;
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><g transform="translate(12 12) scale(${k.toFixed(5)}) translate(${-(x0 + x1) / 2} ${-(y0 + y1) / 2})"><g transform="${g.transform}"><path d="${g.d}" fill="#d6d3f5" fill-rule="evenodd"/></g></g>${badge}</svg>`;
}
const TRAY = [['t-check', '', 'à jour'], ['t-update', '#e45ad8', 'mise à jour'], ['t-gsr', '', 'gsr idle'], ['t-gsr', '#ff6ba8', 'gsr rec'], ['t-gsr', '#ffe08a', 'gsr pause'],
  ['easyeffects', '', 'easy effects'], ['steam', '', 'steam'], ['t-bell', '', 'notifs'], ['t-bell', '#46b5e7', 'nouvelle notif'], ['t-bell', 'slash', 'ne pas déranger']];
for (const id of ['tray-real', 'tray-zoom'])
  document.getElementById(id).innerHTML = TRAY.map(([n, d, l]) => `<div class="ti">${mini(n, d)}<span>${l}</span></div>`).join('');
const COLORS = { cyan: ['#46b5e7', '#6cc8f2'], violet: ['#a55ae9', '#c08af5'], pink: ['#e45ad8', '#ff8fbd'], mint: ['#8af0c0', '#46b5e7'],
  lagoon: ['#46b5e7', '#a55ae9'], dusk: ['#a55ae9', '#e45ad8'], aurora: ['#e45ad8', '#46b5e7'] };
const FOLDERS = [['', 'dossier'], ['home', 'home'], ['desktop', 'bureau'], ['documents', 'documents'], ['download', 'télécharg.'], ['music', 'musique'],
  ['pictures', 'images'], ['videos', 'vidéos'], ['development', 'dev'], ['git', 'git'], ['github', 'github'], ['games', 'jeux'], ['steam', 'steam'], ['publicshare', 'partage']];
function folder(sym, [a, b]) {
  const id = 'f' + (uid++);
  let glyph = '';
  if (sym) {
    const g = GLYPHS['f-' + sym], [x0, y0, x1, y1] = g.bbox, k = 9.2 / Math.max(x1 - x0, y1 - y0);
    glyph = `<g transform="translate(12 14.5) scale(${k.toFixed(5)}) translate(${-(x0 + x1) / 2} ${-(y0 + y1) / 2})"><g transform="${g.transform}"><path d="${g.d}" fill="url(#${id})" fill-rule="evenodd"/></g></g>`;
  }
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><defs>
    <linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
    <linearGradient id="${id}e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${a}" stop-opacity=".85"/><stop offset="1" stop-color="${b}" stop-opacity=".35"/></linearGradient></defs>
    <path d="M2.5 6.5A1.5 1.5 0 0 1 4 5h5.2l2 2H20a1.5 1.5 0 0 1 1.5 1.5V10h-19z" fill="#171339" stroke="url(#${id}e)" stroke-width=".5"/>
    <rect x="2.5" y="8.6" width="19" height="11.6" rx="2" fill="#1d1846" fill-opacity=".96" stroke="url(#${id}e)" stroke-width=".6"/>
    <path d="M4.5 9.4h15" stroke="#fff" stroke-opacity=".08" stroke-width=".5"/>
    ${glyph || `<path d="M6 17.6h12" stroke="url(#${id})" stroke-width="1.1" stroke-linecap="round"/>`}</svg>`;
}
document.getElementById('folders').innerHTML = '<table><tr><th></th>' + FOLDERS.map(f => `<th>${f[1]}</th>`).join('') + '</tr>' +
  Object.entries(COLORS).map(([c, ab]) => `<tr><th class="row">${c}</th>` + FOLDERS.map(f => `<td>${folder(f[0], ab)}</td>`).join('') + '</tr>').join('') + '</table>';
document.getElementById('orig').innerHTML = APPS.map(([n, f, l]) => `<div class="item"><img src="orig/${n}.png" alt="${l}"><span>${l}</span></div>`).join('');
</script></body></html>
"""
html = (html.replace("__GLYPHS__", json.dumps(glyphs))
            .replace("__APPS__", json.dumps(APPS, ensure_ascii=False))
            .replace("__PANEL__", json.dumps(PANEL)))
out.write_text(html)
print("wrote", out)
