#!/usr/bin/env bash
# Baut ein YouTube-Video aus einem Bild oder kurzen Clip und einer oder mehreren Musikdateien.
# Das Bild bzw. der Clip wird so lange wiederholt, bis die Musik zu Ende ist (1920×1080, H.264, AAC).
#
# Aufruf:
#   ./video_bauen.sh bild-oder-clip  ausgabe.mp4  musik1.mp3 [musik2.mp3 ...]
# Beispiele:
#   ./video_bauen.sh herbst-cafe.mp4 video.mp4 suno/*.mp3        # animierter Higgsfield-Clip
#   ./video_bauen.sh herbst-cafe.png video.mp4 musik.mp3         # Standbild
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Aufruf: $0 bild-oder-clip ausgabe.mp4 musik1.mp3 [musik2.mp3 ...]" >&2
  exit 1
fi

visual=$1; out=$2; shift 2
n=$#

# Gesamtlänge der Musik; das Video wird genau so lang
dauer=0
for f in "$@"; do
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  dauer=$(python3 -c "print($dauer + $d)")
done

# Musik: alle Dateien auf 48 kHz Stereo bringen und hintereinanderhängen
inputs=(); filter=""
i=1
for f in "$@"; do
  inputs+=(-i "$f")
  filter+="[$i:a]aresample=48000,aformat=channel_layouts=stereo[a$i];"
  i=$((i + 1))
done
for j in $(seq 1 "$n"); do filter+="[a$j]"; done
filter+="concat=n=$n:v=0:a=1[aud];"

# Bild: Standbild-Schleife; Clip: endlos wiederholen
scale="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
case "${visual,,}" in
  *.png|*.jpg|*.jpeg|*.webp)
    vin=(-loop 1 -framerate 2 -i "$visual"); tune=(-tune stillimage) ;;
  *)
    vin=(-stream_loop -1 -i "$visual"); tune=() ;;
esac
filter+="[0:v]$scale[vid]"

ffmpeg -y -loglevel error -stats "${vin[@]}" "${inputs[@]}" \
  -filter_complex "$filter" -map "[vid]" -map "[aud]" \
  -c:v libx264 -preset veryfast -crf 23 -r 24 "${tune[@]}" \
  -c:a aac -b:a 192k -t "$dauer" -movflags +faststart "$out"

echo "Fertig: $out"
