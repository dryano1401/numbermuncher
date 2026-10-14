"""Number Munchers (Apple IIe, 1986) -- Streamlit edition.  Run: streamlit run app.py"""
import streamlit as st

from game import COLS, ROWS, START_LIVES, Game

st.set_page_config(page_title="Number Munchers", page_icon="🟩", layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
:root { --g:#33ff66; --gd:#118833; --bg:#021006; --red:#ff5544; }
html, body, .stApp { background:#000; touch-action:manipulation; overscroll-behavior:none; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { max-width: 640px; padding-top: 1.5rem; }
html, body, .stApp, .stApp * { font-family:'VT323','Courier New',monospace; }

/* the "monitor" */
.st-key-screen { background:var(--bg); border:4px solid var(--gd); border-radius:18px;
       padding:14px 18px; box-shadow: 0 0 30px rgba(51,255,102,.15) inset; user-select:none; }
.title, .status, .rule, .msg { color:var(--g); text-shadow:0 0 6px rgba(51,255,102,.7); }
.title { text-align:center; font-size:46px; letter-spacing:4px; line-height:1; margin:0 0 6px; }
.status { display:flex; justify-content:space-between; font-size:26px; border-bottom:2px solid var(--gd);
          padding-bottom:4px; margin-bottom:8px; }
.rule { text-align:center; font-size:34px; background:var(--g); color:var(--bg) !important;
        text-shadow:none; padding:2px 0; letter-spacing:2px; }
.msg { text-align:center; font-size:28px; min-height:34px; }
.over { text-align:center; font-size:40px; color:var(--red); text-shadow:none; }

/* keep rows of buttons side by side even on phones (Streamlit stacks columns by default) */
.st-key-board [data-testid="stHorizontalBlock"], .st-key-pad [data-testid="stHorizontalBlock"],
.st-key-bar [data-testid="stHorizontalBlock"] {
       flex-wrap:nowrap !important; gap:4px !important; }
.st-key-board [data-testid="stColumn"], .st-key-pad [data-testid="stColumn"],
.st-key-bar [data-testid="stColumn"] {
       min-width:0 !important; flex:1 1 0 !important; width:auto !important; }
.st-key-board [data-testid="stVerticalBlock"] { gap:4px; }
.st-key-board { margin-top:10px; }

/* board cells are real Streamlit buttons so taps reach Python */
.st-key-board button { height:62px; min-height:0; width:100%; padding:0; border-radius:0;
       background:transparent; color:var(--g); border:2px solid var(--gd);
       text-shadow:0 0 6px rgba(51,255,102,.7); }
.st-key-board button p { font-size:34px; line-height:1; margin:0; }
.st-key-board button:hover:not(:disabled) { background:rgba(51,255,102,.18); border-color:var(--g); color:var(--g); }
.st-key-board button:disabled { opacity:1; color:var(--g); cursor:default; }
.st-key-board button:focus:not(:active) { color:var(--g); border-color:var(--gd); }

.st-key-pad button, .st-key-new button { width:100%; background:#021006; color:var(--g);
       border:2px solid var(--gd); border-radius:6px; height:2.6rem; }
.st-key-pad button p, .st-key-new button p { font-size:26px; }
.st-key-pad button:hover, .st-key-new button:hover { background:var(--g); color:var(--bg); border-color:var(--g); }
.st-key-bar { margin-top:8px; }
.st-key-bar [data-testid="stColumn"] { align-self:center; }
.st-key-bar label p { color:var(--g); font-size:22px; }
.help { color:var(--g); font-size:20px; text-align:center; margin-top:6px; opacity:.8; }
.help-touch { display:none; }
@media (pointer: coarse) {
  .st-key-pad { display:none; }            /* touch: tap the board instead */
  .help-touch { display:inline; } .help-keys { display:none; }
}
@media (max-width: 640px) {
  .block-container { padding:0.6rem 0.4rem 2rem; }
  .st-key-screen { padding:8px; border-width:3px; border-radius:12px; }
  .title { font-size:34px; letter-spacing:2px; } .status { font-size:22px; }
  .rule { font-size:26px; } .msg { font-size:22px; min-height:28px; }
  .st-key-board button { height:clamp(46px, 14vw, 62px); }
  .st-key-board button p { font-size:28px; }
}
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
const BUZZ = {munch:[15], oops:[90], caught:[60,40,60,40,160], level:[30,40,30,40,100],
              gameover:[300], nope:[20]};
window.__nmPlay = (cue, seq, mute, vibrate) => {
  if (window.__nmLastSeq === seq) return;      // each action's cue plays once
  window.__nmLastSeq = seq;
  if (vibrate && BUZZ[cue] && navigator.vibrate) navigator.vibrate(BUZZ[cue]);
  if (mute) return;
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
['keydown', 'pointerdown', 'touchend', 'click'].forEach(ev => document.addEventListener(ev, window.__nmUnlock, true));
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


NBSP = " "


def cell_css(g: Game) -> str:
    """Per-cell styling for the Muncher, Troggles and eaten squares."""
    rules = []
    glyph = "content:'%s'; font-size:20px; line-height:16px; height:16px; display:block;"
    for r in range(ROWS):
        for c in range(COLS):
            k = f".st-key-cell_{r}_{c} button"
            if (r, c) == (g.pr, g.pc):
                rules.append(f"{k}{{background:var(--g) !important; color:var(--bg) !important;"
                             f"flex-direction:column; text-shadow:none !important;}}"
                             f"{k} p{{color:var(--bg) !important;}}{k}::before{{{glyph % '☻'}}}")
            elif any((t.r, t.c) == (r, c) for t in g.troggles):
                rules.append(f"{k}{{background:var(--red) !important; border-color:var(--red) !important;"
                             f"color:#200 !important; flex-direction:column; text-shadow:none !important;}}"
                             f"{k} p{{color:#200 !important;}}{k}::before{{{glyph % '☠'}}}")
            elif g.grid[r][c] is None:
                rules.append(f"{k}{{border-color:#0a3d1a !important;}}")
    border = {"bad": "var(--red)", "caught": "var(--red)", "level": "#ffee55", "good": "var(--g)"}.get(g.flash)
    if border:
        rules.append(f".st-key-screen{{border-color:{border} !important;}}")
    return "<style>" + "".join(rules) + "</style>"


st.markdown(CSS + cell_css(game), unsafe_allow_html=True)

lives = "☻ " * game.lives or "-"
over = '<div class="over">GAME OVER<br>PRESS NEW GAME</div>' if game.over else ""
with st.container(key="screen"):
    st.markdown(
        f"""
<div class="title">NUMBER MUNCHERS</div>
<div class="status"><span>SCORE {game.score:04d}</span><span>LEVEL {game.level}</span>
     <span>{lives}</span></div>
<div class="rule">{game.rule.title}</div>
""",
        unsafe_allow_html=True,
    )
    with st.container(key="board"):
        for r in range(ROWS):
            cols = st.columns(COLS, gap="small")
            for c in range(COLS):
                v = game.grid[r][c]
                cols[c].button(
                    NBSP if v is None else str(v),
                    key=f"cell_{r}_{c}",
                    on_click=game.tap,
                    args=(r, c),
                    disabled=game.over,
                    width="stretch",
                )
    st.markdown(f'<div class="msg">{game.message}</div>{over}', unsafe_allow_html=True)

# Keyboard / on-screen D-pad (hidden on touch devices; the keyboard shortcuts click these)
disabled = game.over
with st.container(key="pad"):
    _, up, _ = st.columns(3)
    left, munch, right = st.columns(3)
    _, down, _ = st.columns(3)
    up.button("▲", key="up", on_click=game.move, args=(-1, 0), disabled=disabled, width="stretch")
    left.button("◀", key="left", on_click=game.move, args=(0, -1), disabled=disabled, width="stretch")
    munch.button("MUNCH", key="munch", on_click=game.munch, disabled=disabled, width="stretch")
    right.button("▶", key="right", on_click=game.move, args=(0, 1), disabled=disabled, width="stretch")
    down.button("▼", key="down", on_click=game.move, args=(1, 0), disabled=disabled, width="stretch")

with st.container(key="bar"):
    new_col, snd_col, vib_col = st.columns([1.3, 1, 1.1])
    new_col.button("NEW GAME", key="new", on_click=new_game, width="stretch")
    sound_on = snd_col.toggle("SOUND", value=True, key="sound_on")
    vibrate_on = vib_col.toggle("VIBRATE", value=True, key="vibrate_on")
best = max(st.session_state.get("best", 0), game.score)
st.markdown(
    f'<div class="help"><span class="help-keys">ARROWS / WASD MOVE &middot; SPACE MUNCHES &middot; </span>'
    f'<span class="help-touch">TAP A SQUARE TO WALK THERE &middot; TAP YOUR MUNCHER AGAIN TO MUNCH '
    f"&middot; </span>HI-SCORE {best:04d}<br>"
    f"AVOID THE TROGGLES (☠). WRONG MUNCH = LOSE A LIFE. YOU START WITH {START_LIVES}.</div>",
    unsafe_allow_html=True,
)
st.html(
    KEYS_JS
    + f"<script>window.__nmPlay({game.sound!r}, {game.sound_seq}, "
    f"{str(not sound_on).lower()}, {str(vibrate_on).lower()});</script>",
    unsafe_allow_javascript=True,
)
