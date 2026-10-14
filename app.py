"""Number Munchers (Apple IIe, 1986) -- Streamlit edition.  Run: streamlit run app.py"""
import streamlit as st

from game import COLS, ROWS, START_LIVES, Game

st.set_page_config(page_title="Number Munchers", page_icon="🟩", layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
:root { --g:#33ff66; --gd:#118833; --bg:#021006; --red:#ff5544; }
.stApp { background:#000; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { max-width: 640px; padding-top: 1.5rem; }
html, body, .stApp, .stApp * { font-family:'VT323','Courier New',monospace; }
.crt { background:var(--bg); border:4px solid var(--gd); border-radius:18px;
       padding:14px 18px; color:var(--g); text-shadow:0 0 6px rgba(51,255,102,.7);
       box-shadow: 0 0 30px rgba(51,255,102,.15) inset; }
.title { text-align:center; font-size:46px; letter-spacing:4px; line-height:1; margin:0 0 6px; }
.status { display:flex; justify-content:space-between; font-size:26px; border-bottom:2px solid var(--gd);
          padding-bottom:4px; margin-bottom:8px; }
.rule { text-align:center; font-size:34px; background:var(--g); color:var(--bg); text-shadow:none;
        padding:2px 0; margin-bottom:10px; letter-spacing:2px; }
table.board { width:100%; border-collapse:separate; border-spacing:4px; table-layout:fixed; }
table.board td { height:62px; text-align:center; vertical-align:middle; border:2px solid var(--gd);
                 font-size:34px; line-height:1; position:relative; }
td .who { display:block; font-size:22px; line-height:18px; height:18px; }
td.me { background:var(--g); color:var(--bg); text-shadow:none; }
td.trog { background:var(--red); color:#200; text-shadow:none; border-color:var(--red); }
td.empty { border-color:#0a3d1a; }
.msg { text-align:center; font-size:28px; margin-top:10px; min-height:34px; }
.crt.good { border-color:var(--g); } .crt.bad, .crt.caught { border-color:var(--red); }
.crt.level { border-color:#ffee55; }
.over { text-align:center; font-size:40px; color:var(--red); text-shadow:none; }
div[class*="st-key-"] button { width:100%; font-size:26px; background:#021006; color:#33ff66;
       border:2px solid #118833; border-radius:6px; height:2.6rem; }
div[class*="st-key-"] button:hover { background:#33ff66; color:#021006; border-color:#33ff66; }
div[class*="st-key-"] button p { font-size:26px; }
.help { color:#33ff66; font-size:20px; text-align:center; margin-top:6px; opacity:.8; }
</style>
"""

KEYS_JS = """
<script>(() => {

const doc = document;

// ---- sound: 1-bit-speaker style square-wave blips, synthesized with Web Audio ----
window.__nmCtx = window.__nmCtx || null;
window.__nmUnlock = () => {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!window.__nmCtx && AC) window.__nmCtx = new AC();
    if (window.__nmCtx && window.__nmCtx.state === 'suspended') window.__nmCtx.resume();
  } catch (e) {}
};
// notes: [startFreq, endFreq, seconds, wave?]; played back to back
const CUES = {
  step:    [[180, 180, 0.03]],
  nope:    [[110, 90, 0.12]],
  munch:   [[330, 660, 0.06], [660, 220, 0.07], [330, 700, 0.06], [700, 260, 0.08]],
  oops:    [[220, 110, 0.18], [196, 98, 0.18], [175, 87, 0.18], [147, 55, 0.35]],
  troggle: [[140, 220, 0.08], [220, 140, 0.08], [140, 220, 0.08], [220, 140, 0.08]],
  caught:  [[523, 262, 0.09], [494, 247, 0.09], [466, 233, 0.09], [440, 220, 0.09],
            [415, 208, 0.09], [392, 196, 0.09], [370, 98, 0.30]],
  level:   [[523, 523, 0.09], [659, 659, 0.09], [784, 784, 0.09], [1047, 1047, 0.09],
            [784, 784, 0.07], [1047, 1047, 0.07], [1319, 1319, 0.28]],
  start:   [[262, 262, 0.08], [330, 330, 0.08], [392, 392, 0.08], [523, 523, 0.16]],
  gameover:[[392, 392, 0.22], [370, 370, 0.22], [349, 349, 0.22], [330, 165, 0.6]],
};
window.__nmPlay = (cue, seq) => {
  if (window.__nmLastSeq === seq) return;      // each action's cue plays once
  window.__nmLastSeq = seq;
  const ctx = window.__nmCtx, notes = CUES[cue];
  if (!ctx || ctx.state !== 'running' || !notes) return;
  let t = ctx.currentTime + 0.01;
  for (const [f0, f1, dur] of notes) {
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(f0, t);
    osc.frequency.linearRampToValueAtTime(f1, t + dur);
    const vol = cue === 'step' ? 0.025 : 0.07;
    gain.gain.setValueAtTime(vol, t);
    gain.gain.setValueAtTime(vol, t + dur * 0.85);
    gain.gain.linearRampToValueAtTime(0, t + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t); osc.stop(t + dur + 0.01);
    t += dur;
  }
};
['keydown', 'pointerdown'].forEach(ev => document.addEventListener(ev, window.__nmUnlock, true));
const map = {ArrowUp:'up', w:'up', W:'up', ArrowDown:'down', s:'down', S:'down',
             ArrowLeft:'left', a:'left', A:'left', ArrowRight:'right', d:'right', D:'right',
             ' ':'munch', Enter:'munch'};
if (window.__nmHandler) {
  doc.removeEventListener('keydown', window.__nmHandler, true);
  doc.removeEventListener('keyup', window.__nmBlock, true);
}
window.__nmHandler = (e) => {
  const k = map[e.key];
  if (!k || e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target;
  if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return;
  const btn = doc.querySelector('.st-key-' + k + ' button');
  if (!btn) return;
  e.preventDefault(); e.stopPropagation();
  if (doc.activeElement && doc.activeElement.blur) doc.activeElement.blur();
  if (!e.repeat) btn.click();
};
window.__nmBlock = (e) => { if (map[e.key]) e.preventDefault(); };
doc.addEventListener('keydown', window.__nmHandler, true);
doc.addEventListener('keyup', window.__nmBlock, true);
})();</script>

"""


def new_game():
    best = st.session_state.get("best", 0)
    g = st.session_state.get("game")
    if g is not None:
        best = max(best, g.score)
    st.session_state.best = best
    st.session_state.game = Game()


if "game" not in st.session_state:
    new_game()
game: Game = st.session_state.game


def render_board(g: Game) -> str:
    troggles = {(t.r, t.c): t for t in g.troggles}
    rows = []
    for r in range(ROWS):
        cells = []
        for c in range(COLS):
            v = g.grid[r][c]
            text = "&nbsp;" if v is None else str(v)
            cls, who = "", ""
            if (r, c) == (g.pr, g.pc):
                cls, who = "me", "☻"
            elif (r, c) in troggles:
                cls, who = "trog", "☠"
            elif v is None:
                cls = "empty"
            if who:
                cells.append(f'<td class="{cls}"><span class="who">{who}</span>{text}</td>')
            else:
                cells.append(f'<td class="{cls}">{text}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<table class="board">' + "".join(rows) + "</table>"


st.markdown(CSS, unsafe_allow_html=True)

lives = "☻ " * game.lives or "-"
over = '<div class="over">GAME OVER<br>PRESS NEW GAME</div>' if game.over else ""
st.markdown(
    f"""
<div class="crt {game.flash}">
  <div class="title">NUMBER MUNCHERS</div>
  <div class="status"><span>SCORE {game.score:04d}</span><span>LEVEL {game.level}</span>
       <span>{lives}</span></div>
  <div class="rule">{game.rule.title}</div>
  {render_board(game)}
  <div class="msg">{game.message}</div>
  {over}
</div>
""",
    unsafe_allow_html=True,
)

st.write("")
disabled = game.over
_, up, _ = st.columns([1, 1, 1])
left, munch, right = st.columns([1, 1, 1])
_, down, _ = st.columns([1, 1, 1])
up.button("▲", key="up", on_click=game.move, args=(-1, 0), disabled=disabled)
left.button("◀", key="left", on_click=game.move, args=(0, -1), disabled=disabled)
munch.button("MUNCH", key="munch", on_click=game.munch, disabled=disabled)
right.button("▶", key="right", on_click=game.move, args=(0, 1), disabled=disabled)
down.button("▼", key="down", on_click=game.move, args=(1, 0), disabled=disabled)

new_col, snd_col = st.columns([1, 1])
new_col.button("NEW GAME", key="new", on_click=new_game)
sound_on = snd_col.toggle("SOUND", value=True, key="sound_on")
best = max(st.session_state.get("best", 0), game.score)
st.markdown(
    f'<div class="help">ARROWS / WASD MOVE &middot; SPACE MUNCHES &middot; HI-SCORE {best:04d}<br>'
    f"AVOID THE TROGGLES (☠). WRONG MUNCH = LOSE A LIFE. YOU START WITH {START_LIVES}.</div>",
    unsafe_allow_html=True,
)
cue = game.sound if sound_on else ""
st.html(
    KEYS_JS + f"<script>window.__nmPlay({cue!r}, {game.sound_seq});</script>",
    unsafe_allow_javascript=True,
)
