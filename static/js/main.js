/* ═══════════════════════════════════
   SAFELIFE AI — main.js
   All features: loader, particles,
   what-if, chat, voice, tracker,
   charts, language
   ═══════════════════════════════════ */

/* ── LOADING SCREEN ─────────────── */
window.addEventListener('load', () => {
  setTimeout(() => {
    const loader = document.getElementById('loader');
    if (loader) loader.classList.add('hide');
  }, 1800);
});

/* ── PARTICLES ───────────────────── */
function initParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  for (let i = 0; i < 25; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.cssText = `
      left: ${Math.random() * 100}%;
      --dur: ${6 + Math.random() * 8}s;
      --delay: ${Math.random() * 8}s;
      --drift: ${(Math.random() - 0.5) * 80}px;
      width: ${1 + Math.random() * 3}px;
      height: ${1 + Math.random() * 3}px;
      opacity: 0;
    `;
    container.appendChild(p);
  }
}

/* ── SCORE RING ──────────────────── */
function initRings() {
  document.querySelectorAll('[data-score]').forEach(el => {
    const score = parseInt(el.dataset.score || 0);
    const r = 60;
    const circ = 2 * Math.PI * r;
    el.style.strokeDasharray  = circ;
    el.style.strokeDashoffset = circ * (1 - score / 100);
    el.setAttribute('stroke',
      score >= 75 ? '#00ff88' :
      score >= 50 ? '#ffd600' : '#ff3d5a');
  });
}

/* ── WHAT-IF SIMULATOR ───────────── */
const simInputs = document.querySelectorAll('.sim-input');
let simTimer = null;

function updateVal(el) {
  const vEl = document.getElementById('v-' + el.id);
  if (vEl) vEl.textContent = el.value + (el.dataset.unit || '');
}

simInputs.forEach(el => {
  updateVal(el);
  el.addEventListener('input', () => { updateVal(el); clearTimeout(simTimer); simTimer = setTimeout(runSim, 380); });
});

const stressEl = document.getElementById('sim-stress');
if (stressEl) stressEl.addEventListener('change', () => { clearTimeout(simTimer); simTimer = setTimeout(runSim, 380); });

async function runSim() {
  const payload = {};
  simInputs.forEach(el => payload[el.id] = el.value);
  if (stressEl) payload['stress'] = stressEl.value;
  try {
    const res  = await fetch('/whatif', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });
    const data = await res.json();
    const sEl  = document.getElementById('sim-score');
    const rEl  = document.getElementById('sim-risk');
    const hEl  = document.getElementById('sim-hage');
    if (sEl) animNum(sEl, parseInt(sEl.dataset.prev||0), data.score);
    if (rEl) { rEl.textContent = data.risk + ' Risk'; rEl.className = 'risk risk-' + data.risk; }
    if (hEl) hEl.textContent = data.health_age + ' yrs';
    if (sEl) sEl.dataset.prev = data.score;
    updateSimRing(data.score);
  } catch(e) {}
}

function animNum(el, from, to) {
  let s = null;
  function step(ts) {
    if (!s) s = ts;
    const p = Math.min((ts - s) / 700, 1);
    el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function updateSimRing(score) {
  const ring = document.getElementById('sim-ring');
  if (!ring) return;
  const circ = 2 * Math.PI * 60;
  ring.style.strokeDasharray  = circ;
  ring.style.strokeDashoffset = circ * (1 - score / 100);
  ring.setAttribute('stroke', score>=75?'#00ff88':score>=50?'#ffd600':'#ff3d5a');
}

/* ── AI CHATBOT ──────────────────── */
const chatWin = document.getElementById('chat-window');
const chatInp = document.getElementById('chat-input');

function addMsg(text, role) {
  if (!chatWin) return;
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = `<div class="msg-av">${role==='bot'?'🤖':'👤'}</div><div class="msg-bubble">${text}</div>`;
  chatWin.appendChild(div);
  chatWin.scrollTop = chatWin.scrollHeight;
}

async function sendChat() {
  const msg = chatInp?.value?.trim();
  if (!msg) return;
  chatInp.value = '';
  addMsg(msg, 'user');
  const typing = document.createElement('div');
  typing.className = 'msg bot'; typing.id = 'typing';
  typing.innerHTML = `<div class="msg-av">🤖</div><div class="msg-bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
  chatWin.appendChild(typing);
  chatWin.scrollTop = chatWin.scrollHeight;
  try {
    const res  = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg}) });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    addMsg(data.reply, 'bot');
  } catch(e) {
    document.getElementById('typing')?.remove();
    addMsg('⚠️ Connection error. Please try again.', 'bot');
  }
}

if (chatInp) chatInp.addEventListener('keydown', e => { if (e.key==='Enter') sendChat(); });
function quickAsk(t) { if (chatInp) { chatInp.value = t; sendChat(); } }

/* ── VOICE INPUT ─────────────────── */
function startVoice() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    alert('Voice input not supported in this browser. Please use Chrome.');
    return;
  }
  const SR   = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec  = new SR();
  rec.lang   = 'en-IN';
  rec.interimResults = false;
  rec.onstart  = () => { document.getElementById('voice-btn').textContent = '🔴 Listening...'; };
  rec.onresult = (e) => { const t = e.results[0][0].transcript; if (chatInp) { chatInp.value = t; sendChat(); } };
  rec.onerror  = () => { document.getElementById('voice-btn').textContent = '🎤 Voice'; };
  rec.onend    = () => { document.getElementById('voice-btn').textContent = '🎤 Voice'; };
  rec.start();
}

/* ── DOCTOR FILTER ───────────────── */
function filterDocs(spec) {
  document.querySelectorAll('.spec-card').forEach(c => c.classList.toggle('sel', c.dataset.spec===spec));
  document.querySelectorAll('.doc-card').forEach(c => c.style.display = (spec==='all'||c.dataset.spec===spec)?'':'none');
}

/* ── CONDITION TABS ──────────────── */
function showCond(c) {
  document.querySelectorAll('.ctab').forEach(t => t.classList.toggle('active', t.dataset.cond===c));
  document.querySelectorAll('.cond-panel').forEach(p => p.style.display = p.id==='c-'+c?'':'none');
}

/* ── WATER TRACKER ───────────────── */
function toggleCup(n) {
  const cups = document.querySelectorAll('.cup');
  cups.forEach((c, i) => c.classList.toggle('filled', i < n));
  const inp = document.getElementById('water-cups-val');
  if (inp) inp.value = n;
}

/* ── CHART.JS ────────────────────── */
function initCharts() {
  const scoreCanvas = document.getElementById('score-chart');
  if (scoreCanvas && typeof Chart !== 'undefined') {
    const labels = JSON.parse(scoreCanvas.dataset.labels || '[]');
    const scores = JSON.parse(scoreCanvas.dataset.scores || '[]');
    new Chart(scoreCanvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Health Score',
          data: scores,
          borderColor: '#00e5ff',
          backgroundColor: 'rgba(0,229,255,0.06)',
          pointBackgroundColor: '#00e5ff',
          pointRadius: 5,
          pointHoverRadius: 8,
          fill: true,
          tension: 0.4,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { ticks:{ color:'#3a5a7a', font:{family:'DM Sans',size:11} }, grid:{ color:'rgba(255,255,255,.03)' } },
          y: { min:0, max:100, ticks:{ color:'#3a5a7a', font:{family:'DM Sans',size:11} }, grid:{ color:'rgba(255,255,255,.04)' } }
        },
        plugins: {
          legend: { labels:{ color:'#8ab0cc', font:{family:'DM Sans'} } },
          tooltip: { backgroundColor:'#071428', borderColor:'#0e2a50', borderWidth:1, titleColor:'#e8f4ff', bodyColor:'#8ab0cc' }
        }
      }
    });
  }

  const bmiCanvas = document.getElementById('bmi-chart');
  if (bmiCanvas && typeof Chart !== 'undefined') {
    const labels = JSON.parse(bmiCanvas.dataset.labels || '[]');
    const bmis   = JSON.parse(bmiCanvas.dataset.bmis   || '[]');
    new Chart(bmiCanvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'BMI',
          data: bmis,
          backgroundColor: bmis.map(b => b>=30?'rgba(255,61,90,.5)':b>=25?'rgba(255,214,0,.5)':b<18.5?'rgba(255,140,66,.5)':'rgba(0,229,255,.5)'),
          borderColor:      bmis.map(b => b>=30?'#ff3d5a':b>=25?'#ffd600':b<18.5?'#ff8c42':'#00e5ff'),
          borderWidth: 1, borderRadius: 6
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { ticks:{ color:'#3a5a7a' }, grid:{ color:'rgba(255,255,255,.03)' } },
          y: { min:10, max:40, ticks:{ color:'#3a5a7a' }, grid:{ color:'rgba(255,255,255,.04)' } }
        },
        plugins: { legend:{ labels:{ color:'#8ab0cc' } }, tooltip:{ backgroundColor:'#071428', borderColor:'#0e2a50', borderWidth:1, titleColor:'#e8f4ff', bodyColor:'#8ab0cc' } }
      }
    });
  }
}

/* ── LANGUAGE SWITCHER ───────────── */
const translations = {
  en: { dashboard:'Dashboard', health:'Health Check', reports:'Reports', assistant:'AI Assistant', doctors:'Doctors', emergency:'Emergency', welcome:'Welcome back', newcheck:'+ New Check' },
  hi: { dashboard:'डैशबोर्ड', health:'स्वास्थ्य जाँच', reports:'रिपोर्ट', assistant:'AI सहायक', doctors:'डॉक्टर', emergency:'आपातकाल', welcome:'वापस स्वागत है', newcheck:'+ नई जाँच' },
  ta: { dashboard:'டாஷ்போர்டு', health:'உடல் பரிசோதனை', reports:'அறிக்கைகள்', assistant:'AI உதவியாளர்', doctors:'மருத்துவர்கள்', emergency:'அவசரகாலம்', welcome:'மீண்டும் வரவேற்கிறோம்', newcheck:'+ புதிய பரிசோதனை' },
  te: { dashboard:'డాష్‌బోర్డ్', health:'ఆరోగ్య తనిఖీ', reports:'నివేదికలు', assistant:'AI సహాయకుడు', doctors:'వైద్యులు', emergency:'అత్యవసరం', welcome:'తిరిగి స్వాగతం', newcheck:'+ కొత్త తనిఖీ' }
};

function switchLang(lang) {
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang===lang));
  const t = translations[lang] || translations['en'];
  document.querySelectorAll('[data-t]').forEach(el => { if (t[el.dataset.t]) el.textContent = t[el.dataset.t]; });
  localStorage.setItem('safelife_lang', lang);
}

/* ── AMBULANCE ───────────────────── */
function callAmb() {
  if (confirm('📞 Call Ambulance - 108\n\nThis will initiate an emergency call. Proceed?')) window.location.href = 'tel:108';
}

/* ── EMERGENCY CONTACTS (localStorage) ── */
function loadContacts() {
  const list = document.getElementById('contacts-list');
  if (!list) return;
  const contacts = JSON.parse(localStorage.getItem('em_contacts') || '[]');
  list.innerHTML = '';
  if (!contacts.length) { list.innerHTML = '<p style="color:var(--text-3);font-size:13px;">No contacts saved yet.</p>'; return; }
  contacts.forEach((c, i) => {
    list.innerHTML += `<div class="med-card"><div><div class="med-name">👤 ${c.name}</div><div class="med-info"><a href="tel:${c.phone}" style="color:var(--cyan)">${c.phone}</a></div></div><button onclick="removeContact(${i})" class="btn btn-danger btn-sm">Remove</button></div>`;
  });
}
function addContact() {
  const n = document.getElementById('cn')?.value?.trim();
  const p = document.getElementById('cp')?.value?.trim();
  if (!n || !p) return;
  const contacts = JSON.parse(localStorage.getItem('em_contacts') || '[]');
  contacts.push({ name:n, phone:p });
  localStorage.setItem('em_contacts', JSON.stringify(contacts));
  document.getElementById('cn').value = ''; document.getElementById('cp').value = '';
  loadContacts();
}
function removeContact(i) {
  const contacts = JSON.parse(localStorage.getItem('em_contacts') || '[]');
  contacts.splice(i, 1);
  localStorage.setItem('em_contacts', JSON.stringify(contacts));
  loadContacts();
}

/* ── INIT ─────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initRings();
  initCharts();
  loadContacts();
  if (simInputs.length > 0) runSim();
  const savedLang = localStorage.getItem('safelife_lang');
  if (savedLang && savedLang !== 'en') switchLang(savedLang);
});

