# Ein Video wie bei Caffena Jazz – Rezept für Café Devagar

Recherche vom 26.10.2026 zum Video aus deinem Foto:
**„🍂 October Morning Bossa Nova Jazz - Warm Autumn Coffee Music for Positive Energy“** von **Caffena Jazz** (@CaffenaJazz),
https://www.youtube.com/watch?v=4bnC3hDDT8Y – 2:02:33 lang, 84.475 Aufrufe und 458 Likes nach 9 Tagen.

## Welches KI-Programm wurde benutzt?

**Das verrät der Kanal nicht.** In Beschreibung, Titel und Tags steht kein Programmname. Das kleine **„KI“** unter dem Titel auf deinem Fernseher ist kein Programmname. Es ist YouTubes Kennzeichnung **„Veränderte oder synthetische Inhalte“**. Die setzt der Kanal beim Hochladen selbst, und YouTube schreibt sie für realistisch wirkende KI-Inhalte vor.

Was man am Video sieht (eine begründete Einschätzung, keine Gewissheit):

| Teil | Wie es typischerweise gemacht wird |
|---|---|
| **Bild** | Ein KI-Standbild (Herbstfenster, Kaffeetasse, Himbeeren, Gebäck), z. B. mit Midjourney, GPT Image oder Nano Banana |
| **Bewegung** | Das Bild wird mit einem KI-Videomodell 5–10 Sekunden animiert (Dampf, Blätter, Lichtstrahlen) und dann endlos wiederholt, z. B. mit Kling, Seedance, Hailuo oder Runway |
| **Musik** | 2 Stunden KI-Musik, meist aus einem Musikgenerator wie **Suno** oder **Udio**, viele 3–4-Minuten-Stücke hintereinander |
| **Texte** | Titel nach Schema *Monat + Tageszeit + Bossa Nova Jazz – Stimmung + Nutzen*, lange Beschreibung mit Fragen an die Zuschauer, viele Tags |

Der Kanal lädt fast täglich ein neues Video mit demselben Titel hoch. Diese Masche wird inzwischen von vielen kopiert. Andere Kanäle laden sogar wortgleiche Titel hoch.

## So machst du es selbst

### 1. Bild erstellen – in Higgsfield
Modell **Nano Banana Pro** oder **GPT Image 2**, Seitenverhältnis **16:9**, Auflösung 2k:

```
Cozy autumn café corner by a large window in the morning, golden maple leaves glowing outside,
warm sunbeams falling across a white marble table, a steaming ceramic cup of coffee,
a small bowl of fresh raspberries and a flaky croissant, soft bokeh, warm orange and green tones,
photorealistic, cinematic lighting, peaceful, no people, no text
```
Eigene Café-Devagar-Varianten (passend zum Kanal):
```
Small corner café in Rio de Janeiro at sunrise, terracotta tiles, a nylon-string guitar leaning
against a wooden chair, espresso cup with steam on a marble table, pão de queijo on a plate,
palm leaves moving outside the open window, black-and-white Copacabana wave pavement visible
on the street, warm soft light, photorealistic, no people, no text
```
```
Rainy afternoon in a quiet Lisbon-style café, blue azulejo tiles, raindrops on the window,
a cup of café com leite and an open book on a wooden table, soft lamp light, cozy, photorealistic,
no people, no text
```

### 2. Bild animieren – in Higgsfield
Modell **Seedance 1.5 Pro** (oder Minimax Hailuo), Dauer **8 Sekunden**, **Ton aus**, das Bild als **Start- und Endbild**, damit die Schleife ohne Sprung läuft:
```
Gentle steam rising slowly from the coffee cup, leaves swaying softly in the breeze outside,
sunbeams shimmering slightly, static camera, calm and slow, seamless loop
```
Wichtig: **Kamera fest** lassen. Nur Dampf, Blätter und Licht bewegen sich, dann fällt die Wiederholung nicht auf.
Hinweis: Am 24.10.2026 hattest du 20 Credits. Ein Videoclip kostet meist deutlich mehr als ein Bild. Schau vor dem Start in der App, was er kostet.

### 3. Musik erstellen
Higgsfield hat **kein Musikmodell für lange Stücke**, nur Sprachausgabe und kurze Spiele-Sounds. Für die Musik brauchst du einen Musikgenerator, z. B. **Suno** (suno.com). Für YouTube-Monetarisierung brauchst du dort ein **bezahltes Abo**, denn nur dann gehören dir die Rechte an den Stücken.

Suno-Einstellungen: **Instrumental** einschalten, Style-Feld:
```
soft bossa nova, warm nylon-string guitar, gentle brushed drums, upright bass, mellow rhodes piano,
relaxing morning café jazz, slow tempo, instrumental, cozy, smooth, no vocals
```
Etwa 30–40 Stücke für 2 Stunden. Lösche die Stücke, die dir nicht gefallen. Alternativ nimmst du die sanfte Musik aus unserem eigenen Generator (`../musik/bossa_generator.py --sanft`).

### 4. Zusammenbauen – mit dem Skript in diesem Ordner
```
./video_bauen.sh herbst-cafe.mp4 cafe-devagar-video.mp4 musik/*.mp3
```
Das Skript wiederholt den Clip (oder das Standbild) so lange, bis die Musik zu Ende ist, und gibt ein fertiges 1080p-Video aus. Du brauchst dafür ffmpeg. Unter Windows geht es auch mit einem Videoprogramm wie CapCut oder DaVinci Resolve: Clip auf die Länge der Musik ziehen und auf „Schleife“ stellen.

### 5. Hochladen
- **Titel** (eigener, nicht kopiert):
  `☕ Slow Morning Bossa Nova – Soft Café Music for Calm Work & Study | Café Devagar`
- **Beschreibung:**
  ```
  ☕ Slow Morning Bossa Nova – Soft Café Music for Calm Work & Study

  Welcome to Café Devagar – "devagar" means "slowly" in Portuguese.
  Take a seat by the window, pour your first coffee and let soft nylon-string guitar,
  gentle brushes and warm Rhodes piano slow your morning down.

  Perfect for working from home, studying, reading or an unhurried breakfast.

  🎵 What are you drinking this morning – espresso, café com leite or tea?
  🍂 What does your perfect slow morning look like?

  Subscribe for a new slow bossa session every week.

  [Kapitel einfügen, z. B. aus kapitel-youtube.txt]

  #bossanova #coffeemusic #cafemusic #morningjazz #studymusic
  ```
- **Tags:** bossa nova, slow bossa nova, coffee shop music, cafe music, morning jazz, relaxing jazz, study music, work music, soft jazz, cafe ambience, café devagar
- **KI-Kennzeichnung:** Unter „Veränderte oder synthetische Inhalte“ **„Ja“** wählen, wenn Bild oder Musik von einer KI stammen. Dann erscheint dieses kleine „KI“ wie bei Caffena Jazz. Wer das weglässt, riskiert Strafen bis zur Sperre der Monetarisierung.
- **Thumbnail:** Ein Standbild aus dem Clip mit großem Text (z. B. „SLOW MORNING ☕“) und dem Logo aus `../logo/`.

## Worauf du achten solltest
- **Nichts kopieren:** Bilder, Musik und Texte von Caffena Jazz sind urheberrechtlich geschützt (steht in ihrer Beschreibung). Das Rezept nachzumachen ist in Ordnung, ihre Dateien zu übernehmen nicht.
- **YouTube-Regeln:** Massenhaft gleichförmige, wiederholte Videos können von der Monetarisierung ausgeschlossen werden („inauthentic content“). Jedes Video sollte deshalb ein eigenes Bild, eigene Musik und einen eigenen Titel haben.
