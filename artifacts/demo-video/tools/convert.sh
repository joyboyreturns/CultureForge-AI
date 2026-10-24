#!/bin/bash
# raw webm -> trimmed 1080p H.264 mp4, numbered in edit order. Usage: convert.sh <rawDir> <manifest.json> <outDir>
F=/Users/vincent/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg
RAW="$1"; MAN="$2"; OUT="$3"; mkdir -p "$OUT"
i=0
for n in landing studio places directions map test agent close; do
  i=$((i+1)); nn=$(printf "%02d" $i)
  start=$(python3 -c "import json;print(max(0,json.load(open('$MAN'))['$n']['markAt']-0.25))")
  case $n in studio) len="-t 18";; places) len="-t 12";; directions) len="-t 11";; *) len="";; esac
  "$F" -hide_banner -loglevel error -y -ss "$start" $len -i "$RAW/$n.webm" \
    -vf "scale=1920:1080:flags=lanczos,fps=30" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart -an \
    "$OUT/$nn-$n.mp4"
  dur=$("$F" -hide_banner -i "$OUT/$nn-$n.mp4" 2>&1 | grep -o "Duration: [0-9:.]*" | head -1)
  echo "$nn-$n.mp4  $dur"
done
