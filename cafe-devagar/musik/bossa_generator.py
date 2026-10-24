#!/usr/bin/env python3
"""Café Devagar – Testversion: erzeugt etwa eine Stunde instrumentale Bossa Nova.

Alle Klänge werden hier berechnet (Karplus-Strong-Nylongitarre, Kontrabass,
FM-E-Piano, Flöte, Vibraphon, Besen, Rimshot, Bassdrum). Es werden keine Samples
und keine fremden Aufnahmen verwendet.

Ergebnis: eine MP3 mit Kapitelmarken und eine Kapitelliste für die YouTube-Beschreibung.

Aufruf:
    python3 bossa_generator.py --out ausgabe            # ganze Stunde
    python3 bossa_generator.py --out ausgabe --tracks 1 # nur das erste Stück zum Testen
"""
import argparse
import itertools
import os
import subprocess
import wave

import numpy as np
from scipy.signal import butter, lfilter, oaconvolve, sosfilt

SR = 44100

# Akkordtypen als Intervalle über dem Grundton (Gitarre spielt sie ohne Bass-Grundton)
TYPES = {
    "maj7": [0, 4, 7, 11], "maj9": [4, 7, 11, 14], "6/9": [4, 7, 9, 14],
    "m7": [0, 3, 7, 10], "m9": [3, 7, 10, 14],
    "7": [0, 4, 7, 10], "9": [4, 7, 10, 14], "13": [4, 10, 14, 21], "7b9": [4, 7, 10, 13],
    "m7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9],
}

# 16-taktige Akkordfolgen, Grundton relativ zur Tonart
PROGS = {
    "A": [(0, "maj9"), (0, "6/9"), (2, "m9"), (7, "13"), (4, "m7"), (9, "7b9"), (2, "m9"), (7, "13"),
          (0, "maj9"), (5, "maj7"), (4, "m7"), (9, "7b9"), (2, "m9"), (7, "13"), (0, "6/9"), (0, "6/9")],
    "B": [(0, "m9"), (0, "m9"), (5, "9"), (5, "9"), (0, "m9"), (8, "maj7"), (2, "m7b5"), (7, "7b9"),
          (0, "m9"), (10, "9"), (3, "maj7"), (8, "maj7"), (2, "m7b5"), (7, "7b9"), (0, "m9"), (7, "7b9")],
    "C": [(0, "maj7"), (10, "9"), (0, "maj7"), (10, "9"), (5, "maj7"), (5, "m7"), (4, "m7"), (9, "7b9"),
          (2, "m9"), (7, "13"), (4, "m7"), (9, "7b9"), (2, "m9"), (1, "9"), (0, "6/9"), (7, "13")],
    "D": [(2, "m9"), (2, "m9"), (1, "dim7"), (1, "dim7"), (0, "maj9"), (0, "maj9"), (0, "m9"), (5, "13"),
          (10, "maj7"), (10, "m7"), (4, "m7b5"), (9, "7b9"), (2, "m9"), (7, "13"), (0, "maj9"), (0, "maj9")],
    "E": [(0, "m9"), (5, "13"), (0, "m9"), (5, "13"), (0, "m9"), (5, "13"), (3, "maj7"), (8, "maj7"),
          (2, "m7b5"), (7, "7b9"), (0, "m9"), (0, "m9"), (5, "m9"), (10, "13"), (3, "maj7"), (7, "7b9")],
}

MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]

# Die 12 Stücke: Name, Tempo, Tonart (0 = C), Geschlecht, Akkordfolge, Melodie- und Zweitinstrument
TRACKS = [
    ("Primeiro Café", 124, 2, "major", "A", "flute", "rhodes", False),
    ("Janela Aberta", 128, 7, "major", "C", "rhodes", "vibes", False),
    ("Sol na Varanda", 132, 5, "major", "A", "vibes", "flute", False),
    ("Leme ao Meio-Dia", 120, 0, "minor", "B", "flute", "rhodes", False),
    ("Bonde de Santa Teresa", 136, 8, "major", "C", "rhodes", "flute", False),
    ("Pão de Queijo", 126, 4, "minor", "E", "vibes", "rhodes", False),
    ("Devagarinho", 104, 10, "major", "D", "rhodes", "vibes", True),
    ("Chuva no Arpoador", 122, 9, "minor", "B", "flute", "vibes", False),
    ("Café com Leite", 130, 3, "major", "A", "vibes", "rhodes", False),
    ("Rua das Laranjeiras", 128, 2, "minor", "E", "rhodes", "flute", False),
    ("Fim de Tarde", 118, 0, "major", "D", "flute", "vibes", True),
    ("Até Logo, Ipanema", 124, 2, "major", "C", "flute", "rhodes", False),
]

RANGES = {"flute": (69, 88), "rhodes": (62, 81), "vibes": (65, 84)}

# Melodierhythmen pro Takt in Achteln: (Start, Länge)
HEAD_POOL = [
    [(0, 3), (3, 1), (4, 4)], [(0, 2), (2, 2), (4, 4)], [(1, 1), (2, 3), (5, 3)],
    [(0, 3), (3, 3), (6, 2)], [(0, 4), (5, 1), (6, 2)], [(0, 1), (1, 1), (2, 1), (3, 1), (4, 4)],
    [(2, 2), (4, 1), (5, 3)], [(0, 6)],
]
END_POOL = [[(0, 8)], [(0, 2), (2, 6)], [(1, 7)], [(0, 3), (3, 5)]]
SOLO_POOL = [
    [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 2)],
    [(0, 1), (1, 2), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],
    [(1, 1), (2, 1), (3, 1), (4, 2), (6, 1), (7, 1)],
    [(0, 2), (2, 1), (3, 1), (4, 1), (5, 3)],
    [(0, 3), (3, 1), (4, 1), (5, 1), (6, 2)],
    [(2, 1), (3, 1), (4, 1), (5, 1), (6, 2)],
    [(0, 4), (4, 1), (5, 1), (6, 1), (7, 1)],
]
# Gitarrenbegleitung über zwei Takte in Achteln (Bossa-Clave und Varianten)
COMP = [[0, 3, 6, 10, 13], [0, 2, 5, 8, 11, 13], [0, 3, 6, 9, 12, 15], [0, 2, 4, 6, 10, 13]]
COMP_W = [0.5, 0.2, 0.15, 0.15]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fade_out(y, n):
    n = min(n, len(y))
    if n:
        y[-n:] *= np.linspace(1, 0, n)
    return y


def butter_sos(kind, freq):
    return butter(2, freq, kind, fs=SR, output="sos")


# ---------- Instrumente ----------

def ks_pluck(midi, rng, bright, dur=2.8, pos=0.18):
    """Nylonsaite nach Karplus-Strong mit Allpass-Feinstimmung."""
    f = hz(midi)
    D = SR / f
    M = int(D - 0.5)
    delta = D - 0.5 - M
    if delta < 0.1:
        M -= 1
        delta += 1.0
    c = (1 - delta) / (1 + delta)
    t60 = 3.2 * (110 / f) ** 0.5
    decay = 10 ** (-3 / (t60 * f))
    n, P = int(dur * SR), int(D)
    exc = rng.uniform(-1, 1, P)
    a = 0.25 + 0.6 * (1 - bright)
    exc = lfilter([1 - a], [1, -a], exc)
    k = max(1, int(pos * P))
    exc[k:] = exc[k:] - exc[:-k]
    x = np.zeros(n)
    x[:P] = exc
    g = 0.5 * decay
    A = np.zeros(M + 3)
    A[0], A[1] = 1, c
    A[M] -= g * c
    A[M + 1] -= g * (1 + c)
    A[M + 2] -= g
    y = lfilter([1, c], A, x)
    y /= np.max(np.abs(y)) + 1e-9
    return fade_out(y, int(0.05 * SR)).astype(np.float32)


class Guitar:
    def __init__(self):
        self.cache = {}

    def note(self, midi, variant):
        key = (midi, variant)
        if key not in self.cache:
            rng = np.random.default_rng(midi * 10 + variant)
            self.cache[key] = ks_pluck(midi, rng, 0.35 + 0.3 * (variant % 2))
        return self.cache[key]


def bass_note(midi, dur):
    f = hz(midi)
    n = int((dur + 0.08) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for h, amp, dec in ((1, 1.0, 2.0), (2, 0.55, 3.2), (3, 0.28, 5.0), (4, 0.12, 7.5), (5, 0.05, 10)):
        y += amp * np.sin(2 * np.pi * f * h * t) * np.exp(-dec * t)
    y *= np.minimum(1, t / 0.006)
    rel = int(dur * SR)
    if rel < n:
        y[rel:] *= np.linspace(1, 0, n - rel)
    return y


def rhodes(midi, dur, vel, rng):
    f = hz(midi)
    n = int((dur + 0.35) * SR)
    t = np.arange(n) / SR
    idx = (0.6 + 1.2 * vel) * np.exp(-t * 3.5) + 0.12
    env = np.exp(-t * 1.1) * np.minimum(1, t / 0.003)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t)) * env
    y += 0.06 * vel * np.sin(2 * np.pi * f * 7.1 * t) * np.exp(-t * 25)
    rel = int(dur * SR)
    if rel < n:
        y[rel:] *= np.linspace(1, 0, n - rel)
    return y * (0.6 + 0.4 * vel)


def vibes(midi, dur, vel, rng):
    f = hz(midi)
    n = int((dur + 0.5) * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 0.9)
         + 0.22 * np.sin(2 * np.pi * 3.98 * f * t) * np.exp(-t * 3.5)
         + 0.06 * np.sin(2 * np.pi * 9.9 * f * t) * np.exp(-t * 9))
    y *= 1 - 0.22 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.2 * t))
    y += rng.uniform(-1, 1, n) * np.exp(-t * 900) * 0.12
    y *= np.minimum(1, t / 0.002)
    rel = int(dur * SR)
    if rel < n:
        y[rel:] *= np.linspace(1, 0, n - rel)
    return y * (0.6 + 0.4 * vel)


def flute(midi, dur, vel, rng):
    f = hz(midi)
    n = int((dur + 0.15) * SR)
    t = np.arange(n) / SR
    depth = 0.0045 * np.clip((t - 0.25) / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * (1 + depth * np.sin(2 * np.pi * 5.1 * t))) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    breath = sosfilt(butter_sos("bandpass", [min(f * 1.5, 8000), min(f * 5, 16000)]), rng.standard_normal(n))
    y += breath * (0.12 + 0.35 * np.exp(-t * 20))
    att = min(0.08, dur * 0.4)
    env = np.clip(t / att, 0, 1) * (1 - 0.15 * np.clip(t / max(dur, 0.1), 0, 1))
    rel = int(dur * SR)
    if rel < n:
        env[rel:] *= np.linspace(1, 0, n - rel)
    return y * env * (0.7 + 0.3 * vel)


SYNTHS = {"flute": flute, "rhodes": rhodes, "vibes": vibes}
MEL_GAIN = {"flute": 0.16, "rhodes": 0.23, "vibes": 0.21}


def drum_kit(rng):
    def t_of(sec):
        return np.arange(int(sec * SR)) / SR
    hp = butter_sos("highpass", 2500)
    bp = butter_sos("bandpass", [2000, 9000])
    rims, brushes = [], []
    for _ in range(3):
        t = t_of(0.06)
        tone = np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 170) + 0.5 * np.sin(2 * np.pi * 480 * t) * np.exp(-t * 120)
        nz = sosfilt(hp, rng.standard_normal(len(t))) * np.exp(-t * 300) * 0.5
        rims.append(tone * 0.6 + nz)
        t = t_of(0.16)
        nz = sosfilt(bp, rng.standard_normal(len(t)))
        brushes.append(nz * np.clip(t / 0.02, 0, 1) * np.exp(-t * 22))
    t = t_of(0.35)
    ph = 2 * np.pi * np.cumsum(48 + 30 * np.exp(-t * 30)) / SR
    kick = np.sin(ph) * np.exp(-t * 9) * np.minimum(1, t / 0.002)
    return rims, brushes, kick


# ---------- Harmonik und Melodie ----------

def chord_pcs(root, ctype):
    return {(root + i) % 12 for i in TYPES[ctype]} | {root % 12}


def chord_scale(root, ctype, key_pcs):
    ct = chord_pcs(root, ctype)
    keep = {s for s in key_pcs if s in ct or not ({(s - 1) % 12, (s + 1) % 12} & ct)}
    return ct | keep


def voicing(root, ctype, prev):
    pcs = sorted({(root + i) % 12 for i in TYPES[ctype]})
    opts = [[m for m in range(52, 74) if m % 12 == pc] for pc in pcs]
    best, best_cost = None, 1e9
    for span in (16, 19, 24):
        for combo in itertools.product(*opts):
            v = sorted(combo)
            if v[-1] - v[0] > span:
                continue
            cost = sum(abs(a - b) for a, b in zip(v, prev)) + 0.3 * abs(np.mean(v) - 62)
            if cost < best_cost:
                best, best_cost = v, cost
        if best:
            return best
    return sorted(m[0] for m in opts)


def pick_note(rng, cands, p, target):
    c = np.array(cands)
    w = np.exp(-np.abs(c - target) / 1.5)
    w[c == p] *= 0.4
    w[np.abs(c - p) > 7] *= 0.1
    return int(rng.choice(c, p=w / w.sum()))


def snap(m, allowed, lo, hi):
    cands = [x for x in range(lo, hi + 1) if x % 12 in allowed]
    return min(cands, key=lambda x: (abs(x - m), x))


def make_melody(rng, chords, key_pcs, lo, hi, solo):
    """Gibt Noten (takt, start, länge, midi, stärke) für 16 Takte zurück."""
    events, p = [], (lo + hi) // 2
    phrase0 = []
    base_rh = [rng.choice(len(HEAD_POOL)) for _ in range(3)]
    for ph in range(len(chords) // 4):
        reuse = not solo and ph in (1, 3)
        for b in range(4):
            bar = ph * 4 + b
            root, ct = chords[bar]
            ctones = chord_pcs(root, ct)
            scale = chord_scale(root, ct, key_pcs)
            if reuse and b < 3:
                for (_, s, l, m, v) in [e for e in phrase0 if e[0] == b]:
                    strong = s % 4 == 0 or l >= 3
                    m = snap(m, ctones if strong else scale, lo, hi)
                    events.append((bar, s, l, m, v))
                    p = m
                continue
            if solo:
                rh = END_POOL[rng.integers(len(END_POOL))] if b == 3 and rng.random() < 0.4 else SOLO_POOL[rng.integers(len(SOLO_POOL))]
            elif b == 3:
                rh = END_POOL[rng.integers(len(END_POOL))]
            else:
                rh = HEAD_POOL[base_rh[b]] if ph == 0 or ph == 2 and rng.random() < 0.3 else HEAD_POOL[rng.integers(len(HEAD_POOL))]
            d = 1 if b < 2 else -1
            for i, (s, l) in enumerate(rh):
                strong = s % 4 == 0 or l >= 3 or (b == 3 and i == len(rh) - 1)
                allowed = ctones if strong else scale
                cands = [m for m in range(lo, hi + 1) if m % 12 in allowed]
                step = int(rng.choice([1, 2, 2, 3, 4, 5])) * (1 if rng.random() < 0.8 else -1)
                target = int(np.clip(p + d * step, lo + 2, hi - 2))
                m = pick_note(rng, cands, p, target)
                v = 0.6 + 0.3 * rng.random() + (0.1 if strong else 0)
                events.append((bar, s, l, m, v))
                if ph == 0:
                    phrase0.append((b, s, l, m, v))
                p = m
    return events


# ---------- Ein Stück rendern ----------

def place(bus, t, sig, gain):
    i = int(round(t * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(bus), i + len(sig))
    if j > i:
        bus[i:j] += gain * sig[: j - i]


def plan_sections(loops):
    n_mid = loops - 4
    mid = ["solo"] * n_mid
    if n_mid >= 3:
        mid[n_mid // 2] = "break"
    return ["head", "head"] + mid + ["head", "head2"]


def track_seconds(bpm, loops, gap):
    return (4 + 16 * loops) * 8 * 60 / bpm / 2 + 6.5 + gap


def render_track(spec, loops, seed, guitar, gap=1.5):
    name, bpm, key, mode, prog_id, inst1, inst2, light = spec
    rng = np.random.default_rng(seed)
    st = 60 / bpm / 2
    bar_t = 8 * st
    key_pcs = {(key + s) % 12 for s in (MAJOR if mode == "major" else MINOR)}
    prog = [((key + r) % 12, ct) for r, ct in PROGS[prog_id]]
    sections = plan_sections(loops)

    # Taktliste: (Akkord, Abschnitt, Takt im Abschnitt)
    bars = [(prog[i], "intro", i) for i in range(4)]
    for sec in sections:
        bars += [(prog[i], sec, i) for i in range(16)]
    n_bars = len(bars)
    end_t = n_bars * bar_t
    total = end_t + 6.5 + gap
    N = int(total * SR)
    buses = {k: np.zeros(N, np.float32) for k in ("gtr", "bass", "mel", "mel2", "rim", "brush", "kick")}
    rims, brushes, kick = drum_kit(rng)

    # Gitarre: Stimmführung über alle Takte
    voic, prev = [], [55, 59, 62, 66]
    for (root, ct), _, _ in bars:
        prev = voicing(root, ct, prev)
        voic.append(prev)
    tonic = "maj9" if mode == "major" else "m9"
    final_v = voicing(key, tonic, voic[-1])

    hits = []
    for b0 in range(0, n_bars, 2):
        pat = COMP[rng.choice(len(COMP), p=COMP_W)]
        for s in pat:
            bar = b0 + s // 8
            if bar >= n_bars:
                continue
            step = s % 8
            vb = bar + 1 if step == 7 and bar + 1 < n_bars else bar
            hits.append(((bar * 8 + step) * st, vb, s == pat[0]))
    hits.sort()
    for i, (t, vb, acc) in enumerate(hits):
        nxt = hits[i + 1][0] if i + 1 < len(hits) else end_t
        dur = nxt - t + 0.02
        vel = (1.0 if acc else 0.8) * (0.85 + 0.3 * rng.random())
        t += rng.normal(0, 0.005)
        for j, m in enumerate(voic[vb]):
            sig = guitar.note(m, int(rng.integers(4)) | (1 if acc else 0))
            n = min(len(sig), int(dur * SR))
            place(buses["gtr"], t + j * 0.007, fade_out(sig[:n].copy(), int(0.025 * SR)), 0.45 * vel)

    # Bass und Schlagzeug
    bass_ev = []
    for bi, ((root, ct), sec, _) in enumerate(bars):
        if sec == "intro" and bi < 2:
            continue
        r = 36 + (root - 36) % 12
        fifth = r + 7 if r + 7 <= 50 else r - 5
        nroot = bars[bi + 1][0][0] if bi + 1 < n_bars else key
        nr = 36 + (nroot - 36) % 12
        approach = nr + (1 if rng.random() < 0.5 else -1) if rng.random() < 0.3 else nr
        pattern = [(0, r, 1.0), (3, fifth, 0.55), (4, fifth, 0.8), (7, approach, 0.5)]
        if rng.random() < 0.2:
            pattern.pop(1)
        for s, m, v in pattern:
            bass_ev.append(((bi * 8 + s) * st, m, v))
    bass_ev.append((end_t, 36 + (key - 36) % 12, 1.0))
    for i, (t, m, v) in enumerate(bass_ev):
        nxt = bass_ev[i + 1][0] if i + 1 < len(bass_ev) else t + 3.5
        place(buses["bass"], t + rng.normal(0, 0.004), bass_note(m, nxt - t), 0.22 * v)

    for bi, (_, sec, inb) in enumerate(bars):
        t0 = bi * bar_t
        full = sec in ("head", "head2", "solo") and not light
        for s in range(8):
            for half, g in ((0, 0.9 if s % 2 else 0.6), (0.5, 0.35)):
                gain = 0.15 * g * (0.6 if sec == "break" or light else 1.0)
                place(buses["brush"], t0 + (s + half) * st + rng.normal(0, 0.004), brushes[rng.integers(3)], gain)
        if full or sec == "break":
            for s, g in ((0, 0.1), (3, 0.045), (4, 0.08), (7, 0.035)):
                place(buses["kick"], t0 + s * st, kick, g)
        if full:
            for s in [0, 3, 6, 10, 13]:
                if s // 8 == bi % 2:
                    place(buses["rim"], t0 + (s % 8) * st + rng.normal(0, 0.004), rims[rng.integers(3)], 0.2)

    # Melodien
    lo1, hi1 = RANGES[inst1]
    head = make_melody(rng, prog, key_pcs, lo1, hi1, solo=False)
    bar_cursor, solo_count = 4, 0
    last_mel = (inst1, (lo1 + hi1) // 2)
    for sec in sections:
        t_sec = bar_cursor * bar_t
        parts = []
        if sec in ("head", "head2"):
            parts.append(("mel", inst1, head, 0))
            if sec == "head2":
                lo2, hi2 = RANGES[inst2]
                shift = -12 if min(e[3] for e in head) - 12 >= lo2 - 5 else 0
                parts.append(("mel2", inst2, head, shift))
        elif sec == "solo":
            inst = inst2 if solo_count % 2 == 0 else inst1
            lo, hi = RANGES[inst]
            parts.append(("mel2" if inst == inst2 else "mel", inst, make_melody(rng, prog, key_pcs, lo, hi, solo=True), 0))
            solo_count += 1
        for bus, inst, evs, shift in parts:
            synth = SYNTHS[inst]
            for bar, s, l, m, v in evs:
                t = t_sec + (bar * 8 + s) * st + rng.normal(0, 0.008)
                sig = synth(m + shift, l * st * 0.92, v, rng)
                place(buses[bus], t, sig, MEL_GAIN[inst] * (0.5 if bus == "mel2" and sec == "head2" else 1.0))
            last_mel = (inst, evs[-1][3] + shift)
        bar_cursor += 16

    # Schlussakkord
    for j, m in enumerate(final_v):
        place(buses["gtr"], end_t + j * 0.06, guitar.note(m, 1), 0.5)
    inst, p = last_mel
    lo, hi = RANGES[inst]
    m_end = snap(p, {key % 12, (key + (4 if mode == "major" else 3)) % 12, (key + 7) % 12}, lo, hi)
    place(buses["mel"], end_t + 0.1, SYNTHS[inst](m_end, 3.2, 0.7, rng), MEL_GAIN[inst])

    return mix(buses, rng, N, end_t), name, total


PANS = {"gtr": -0.3, "bass": 0.0, "mel": 0.25, "mel2": -0.15, "rim": 0.3, "brush": -0.25, "kick": 0.0}
SENDS = {"gtr": 0.22, "bass": 0.03, "mel": 0.35, "mel2": 0.3, "rim": 0.15, "brush": 0.1, "kick": 0.0}


def mix(buses, rng, N, end_t):
    buses["gtr"] = sosfilt(butter_sos("highpass", 80), buses["gtr"])
    buses["gtr"] = sosfilt(butter_sos("lowpass", 5500), buses["gtr"])
    buses["bass"] = sosfilt(butter_sos("lowpass", 1200), buses["bass"])
    L, R, send = np.zeros(N), np.zeros(N), np.zeros(N)
    for k, b in buses.items():
        a = (PANS[k] + 1) * np.pi / 4
        L += b * np.cos(a)
        R += b * np.sin(a)
        send += b * SENDS[k]
    n_ir = int(1.8 * SR)
    t = np.arange(n_ir) / SR
    for out in (L, R):
        ir = rng.standard_normal(n_ir) * np.exp(-t * 4.6)
        ir = lfilter([0.35], [1, -0.65], ir)
        ir = np.concatenate([np.zeros(int(0.012 * SR)), ir])
        ir /= np.sqrt(np.sum(ir ** 2))
        out += 0.35 * oaconvolve(send, ir)[:N]

    # leises Knistern wie von einer Schallplatte
    bed = lfilter([0.05, -0.05], [1, -0.995], rng.standard_normal(N)) * 0.0008
    clicks = np.zeros(N)
    pos = rng.integers(0, N, int(N / SR * 3))
    clicks[pos] = rng.uniform(-1, 1, len(pos)) * rng.uniform(0.002, 0.02, len(pos))
    clicks = lfilter([0.5], [1, -0.5], clicks)
    L += bed + clicks
    R += bed + clicks

    stereo = np.stack([L, R], axis=1)
    stereo = sosfilt(butter_sos("highpass", 30), stereo, axis=0)
    body = stereo[: int(end_t * SR)]
    stereo *= 0.09 / (np.sqrt(np.mean(body ** 2)) + 1e-9)
    tail_start = int((end_t + 3.0) * SR)
    fade_n = int(3.0 * SR)
    stereo[tail_start: tail_start + fade_n] *= np.linspace(1, 0, fade_n)[:, None][: len(stereo) - tail_start]
    stereo[tail_start + fade_n:] = 0
    return np.tanh(stereo / 0.95) * 0.95


def write_wav(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def fmt(sec):
    sec = int(round(sec))
    h, rem = divmod(sec, 3600)
    return f"{h}:{rem // 60:02d}:{rem % 60:02d}" if h else f"{rem // 60:02d}:{rem % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ausgabe")
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--tracks", type=int, default=len(TRACKS))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tmp = os.path.join(args.out, "tmp")
    os.makedirs(tmp, exist_ok=True)

    specs = TRACKS[: args.tracks]
    loops = [7] * len(specs)
    target = args.minutes * 60 * len(specs) / len(TRACKS)
    while sum(track_seconds(s[1], l, 1.5) for s, l in zip(specs, loops)) < target:
        i = min(range(len(specs)), key=lambda k: track_seconds(specs[k][1], loops[k], 1.5))
        loops[i] += 1

    guitar = Guitar()
    files, chapters, t = [], [], 0.0
    for i, (spec, l) in enumerate(zip(specs, loops)):
        stereo, name, total = render_track(spec, l, args.seed + i, guitar)
        path = os.path.join(tmp, f"{i + 1:02d}.wav")
        write_wav(path, stereo)
        files.append(path)
        chapters.append((t, t + total, name))
        print(f"{fmt(t)}  {name}  ({fmt(total)}, Spitze {np.max(np.abs(stereo)):.2f})", flush=True)
        t += total

    with open(os.path.join(tmp, "liste.txt"), "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in files)
    with open(os.path.join(tmp, "meta.txt"), "w") as f:
        f.write(";FFMETADATA1\ntitle=Manhã de Café (Testversion)\nartist=Café Devagar\nalbum=Café Devagar Vol. 01\n")
        for a, b, name in chapters:
            f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(a * 1000)}\nEND={int(b * 1000)}\ntitle={name}\n")
    with open(os.path.join(args.out, "kapitel-youtube.txt"), "w") as f:
        f.writelines(f"{fmt(a)} {name}\n" for a, _, name in chapters)

    mp3 = os.path.join(args.out, "cafe-devagar-manha-de-cafe-testversion.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(tmp, "liste.txt"), "-i", os.path.join(tmp, "meta.txt"),
                    "-map", "0:a", "-map_metadata", "1", "-map_chapters", "1",
                    "-c:a", "libmp3lame", "-b:a", "160k", mp3], check=True)
    print(f"Fertig: {mp3} ({fmt(t)})")


if __name__ == "__main__":
    main()
