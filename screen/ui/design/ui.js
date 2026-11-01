// Shared behaviour of ui.html: icons, the navigation rail and the build modes.
// ui.html?s=<screen>&mode=<bg|pressed|on|preview> shows one screen.

const NAV = [
  ['home', 'house', 'Home'], ['files', 'folder', 'Files'], ['move', 'move', 'Move'],
  ['tools', 'wrench', 'Tools'], ['settings', 'settings', 'Settings'],
];

function rail(current) {
  const items = NAV.map(([id, icon, label]) =>
    `<div class="nav${id === current ? ' cur' : ''}" data-hit="nav_${id}"><i data-icon="${icon}"></i>${label}</div>`).join('');
  return `<div class="rail"><div class="logo"><i data-icon="layers"></i></div>${items}` +
    `<div class="estop" data-hit="estop"><i data-icon="octagon-x"></i></div></div>`;
}

async function loadIcons(root) {
  const cache = {};
  for (const el of root.querySelectorAll('i[data-icon]')) {
    const name = el.dataset.icon;
    cache[name] = cache[name] || fetch(`icons/${name}.svg`).then(r => {
      if (!r.ok) throw new Error(`icon ${name}: ${r.status}`);
      return r.text();
    });
    const span = document.createElement('span');
    span.className = 'icon ' + (el.className || '');
    if (el.getAttribute('style')) span.setAttribute('style', el.getAttribute('style'));
    span.innerHTML = (await cache[name]).replace(/<!--.*?-->/s, '');
    el.replaceWith(span);
  }
}

// Rectangle of an element relative to its screen.
function rect(el, screen) {
  const a = el.getBoundingClientRect(), s = screen.getBoundingClientRect();
  return [Math.round(a.left - s.left), Math.round(a.top - s.top), Math.round(a.width), Math.round(a.height)];
}

function cssColor(value) {
  const m = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  return m ? [+m[1], +m[2], +m[3]] : [255, 255, 255];
}

// What build_assets.py stores in layout.json for one screen.
window.collect = function (id) {
  const screen = document.getElementById(id);
  const all = sel => [...screen.querySelectorAll(sel)];
  return {
    hits: all('[data-hit]').map(el => ({ id: el.dataset.hit, rect: rect(el, screen) })),
    toggles: all('[data-on]').map(el => ({ id: el.dataset.on, rect: rect(el, screen) })),
    texts: all('[data-text]').map(el => {
      const st = getComputedStyle(el);
      return {
        id: el.dataset.text, rect: rect(el, screen), font: el.dataset.font,
        color: cssColor(el.dataset.color || st.getPropertyValue('--ink') || st.color),
        align: el.dataset.align || 'left', on: el.dataset.onText || null,
      };
    }),
    bars: all('[data-bar]').map(el => ({
      id: el.dataset.bar, rect: rect(el, screen),
      track: cssColor(getComputedStyle(el).backgroundColor), fill: cssColor(el.dataset.fill || '#2DD4BF'),
    })),
    thumbs: all('[data-thumb]').map(el => ({ id: el.dataset.thumb, rect: rect(el, screen) })),
    dots: all('[data-dot]').map(el => ({
      id: el.dataset.dot, rect: rect(el, screen), color: cssColor(getComputedStyle(el).backgroundColor),
    })),
  };
};

window.ready = (async function () {
  const params = new URLSearchParams(location.search);
  const mode = params.get('mode') || 'preview';
  for (const s of document.querySelectorAll('.screen[data-nav]')) s.insertAdjacentHTML('afterbegin', rail(s.dataset.nav));
  // Text colour for the live-text annotation must be read before the mode hides it.
  for (const el of document.querySelectorAll('[data-text]')) el.style.setProperty('--ink', getComputedStyle(el).color);
  document.body.classList.add('mode-' + mode);
  await loadIcons(document);
  if (mode === 'on') for (const el of document.querySelectorAll('[data-on]')) el.classList.add('on');
  if (mode === 'bg' || mode === 'pressed') for (const el of document.querySelectorAll('[data-on]')) el.classList.remove('on');
  if (mode === 'preview') {
    for (const el of document.querySelectorAll('[data-text]')) if (el.dataset.sample !== undefined) el.textContent = el.dataset.sample;
    for (const el of document.querySelectorAll('[data-bar]')) {
      el.innerHTML = `<div style="height:100%;border-radius:inherit;width:${el.dataset.sample || 0}%;background:${el.dataset.fill || '#2DD4BF'}"></div>`;
    }
  }
  const id = params.get('s');
  if (id) document.getElementById(id).classList.add('show');
  else for (const s of document.querySelectorAll('.screen')) { s.classList.add('show'); s.style.margin = '12px'; }
  await document.fonts.ready;
  return true;
})();
