# Number Munchers (Streamlit)

A turn-based Streamlit take on the 1986 Apple IIe classic *Number Munchers*.

Move the Muncher around the grid and eat only the numbers that match the rule
(multiples, factors, primes, less/greater than, equals). Wrong munches cost a life,
and Troggles chase you around the board.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Controls

- **Touch:** tap a square to walk there (one square per turn, so Troggles move too), then tap
  the Muncher's own square again to munch. Double-tapping a far square walks and munches.
  Phones also get optional vibration feedback (VIBRATE toggle).
- **Keyboard:** arrow keys / WASD to move, Space or Enter to munch.
- **Mouse:** click squares, or use the on-screen D-pad (hidden on touch devices).

Sound effects (munch, wrong answer, Troggle appears, caught, level clear, game over) are
synthesized in the browser with Web Audio, so there are no audio files. Use the SOUND
toggle to mute. Browsers only allow audio after a click or key press.

Game rules live in `game.py`; the Streamlit UI is in `app.py`.
