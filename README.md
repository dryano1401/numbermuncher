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

Arrow keys / WASD to move, Space or Enter to munch (or use the on-screen buttons).

Sound effects (munch, wrong answer, Troggle appears, caught, level clear, game over) are
synthesized in the browser with Web Audio, so there are no audio files. Use the SOUND
toggle to mute. Browsers only allow audio after a click or key press.

Game rules live in `game.py`; the Streamlit UI is in `app.py`.
