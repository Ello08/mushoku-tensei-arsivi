#!/usr/bin/env bash
# Yayınla: siteyi üret ve gh-pages dalına gönder.
#
# GitHub Pages bu depoda gh-pages dalından yayınlıyor (build_type: legacy).
# Böylece yayınlama Actions'a bağlı değil — GitHub'un iş kuyruğu
# aksa da site güncellenebiliyor.
#
# Kullanım:  bash tools/yayinla.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITNAME="$(git config user.name)"
GITMAIL="$(git config user.email)"
VERSION="$(cat "$ROOT/VERSIYON.txt" 2>/dev/null || echo '0.0.0')"
ORIGIN="$(git -C "$ROOT" remote get-url origin)"

cd "$ROOT"

echo "-> Sayfalari uretiyorum"
python3 tools/kur.py

echo "-> Dogrulamalar"
python3 tools/dogrula.py
python3 tools/css-denetle.py
python3 tools/mobil-denetle.py
node tools/test-veri.js

echo "-> Yaying agacini hazirliyorum (yalnzca derlenmis site)"
STAGE="$(mktemp -d -p /data/data/com.termux/files/usr/tmp/opencode publish-XXXXXX)"
trap 'rm -rf "$STAGE"' EXIT

cp ./*.html "$STAGE"/
cp -r assets "$STAGE"/
touch "$STAGE/.nojekyll"

cd "$STAGE"
git init -q -b gh-pages
git config user.name "$GITNAME"
git config user.email "$GITMAIL"
git add -A
git commit -q -m "Yayin: surum $VERSION

Kaynak: $(git -C "$ROOT" log --oneline -1 --format='%h %s')"
git remote add origin "$ORIGIN" 2>/dev/null || true
git push -q -f origin gh-pages

echo "✓ Yayinlandi (sürüm $VERSION)"
echo "  $ORIGIN/tree/gh-pages"