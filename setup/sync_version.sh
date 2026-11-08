#!/bin/sh
# setup/cuda_ver.sh is the single source of truth for the CudaText version.
# This script writes that version into the files which need a copy of it,
# or verifies that they are still in sync (use --check in CI).
#
# usage: ./sync_version.sh [--check]
set -eu

cd "$(dirname "$0")"
. ./cuda_ver.sh
cuda_ver=$(echo "$cuda_ver" | tr -d '\r')

APP=../app
PLIST=$APP/cudatext.app/Contents/Info.plist
CHANGELOG=debfiles/changelog

mode_write=1
if [ "${1:-}" = "--check" ]; then
  mode_write=0
elif [ -n "${1:-}" ]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

#split "1.239.0.1" into 4 numeric parts, missing parts are 0
v1=$(echo "$cuda_ver" | cut -d. -f1)
v2=$(echo "$cuda_ver" | cut -d. -f2)
v3=$(echo "$cuda_ver" | cut -d. -f3)
v4=$(echo "$cuda_ver" | cut -d. -f4)
v2=${v2:-0}
v3=${v3:-0}
v4=${v4:-0}
ver_short=$v1.$v2.$v3

#replace in-place, keeping the rest of the file untouched
apply() {
  f=$1
  expr=$2
  sed "$expr" "$f" > "$f.tmp$$" || { rm -f "$f.tmp$$"; exit 1; }
  mv "$f.tmp$$" "$f"
}

if [ "$mode_write" = 1 ]; then
  apply "$APP/proc_msg.pas" \
    "s/cAppExeVersion[[:space:]]*=[[:space:]]*'[^']*'/cAppExeVersion = '$cuda_ver'/"
  apply "$APP/cudatext.lpi" \
    "s/<MajorVersionNr Value=\"[^\"]*\"/<MajorVersionNr Value=\"$v1\"/"
  apply "$APP/cudatext.lpi" \
    "s/<MinorVersionNr Value=\"[^\"]*\"/<MinorVersionNr Value=\"$v2\"/"
  apply "$APP/cudatext.lpi" \
    "s/<BuildVersionNr Value=\"[^\"]*\"/<BuildVersionNr Value=\"$v3\"/"
  apply "$APP/cudatext.lpi" \
    "s/<RevisionVersionNr Value=\"[^\"]*\"/<RevisionVersionNr Value=\"$v4\"/"
  apply "$PLIST" \
    "/CFBundleShortVersionString/{n;s|<string>[^<]*</string>|<string>$ver_short</string>|;}"
  apply "$PLIST" \
    "/<key>CFBundleVersion/{n;s|<string>[^<]*</string>|<string>$v4</string>|;}"
  apply "$CHANGELOG" \
    "1s/^cudatext ([^)]*)/cudatext ($cuda_ver)/"
  for f in debfiles/*/control; do
    apply "$f" "s/^Version: .*/Version: $cuda_ver-1/"
  done
  echo "written version $cuda_ver"
  exit 0
fi

got_bad=0
check() {
  if [ "$2" = "$3" ]; then
    echo "ok    $1: $2"
  else
    echo "FAIL  $1: $2 (expected $3)"
    got_bad=1
  fi
}

pas_ver=$(sed -n "s/^[[:space:]]*cAppExeVersion[[:space:]]*=[[:space:]]*'\([^']*\)'.*/\1/p" "$APP/proc_msg.pas" | tr -d '\r' | head -n1)
lpi_v1=$(sed -n "s/.*<MajorVersionNr Value=\"\([0-9]*\)\".*/\1/p" "$APP/cudatext.lpi" | head -n1)
lpi_v2=$(sed -n "s/.*<MinorVersionNr Value=\"\([0-9]*\)\".*/\1/p" "$APP/cudatext.lpi" | head -n1)
lpi_v3=$(sed -n "s/.*<BuildVersionNr Value=\"\([0-9]*\)\".*/\1/p" "$APP/cudatext.lpi" | head -n1)
lpi_v4=$(sed -n "s/.*<RevisionVersionNr Value=\"\([0-9]*\)\".*/\1/p" "$APP/cudatext.lpi" | head -n1)
plist_short=$(sed -n "/CFBundleShortVersionString/{n;s|.*<string>\([^<]*\)</string>.*|\1|p;}" "$PLIST" | tr -d '\r' | head -n1)
plist_ver=$(sed -n "/<key>CFBundleVersion/{n;s|.*<string>\([^<]*\)</string>.*|\1|p;}" "$PLIST" | tr -d '\r' | head -n1)
chg_ver=$(head -n1 "$CHANGELOG" | tr -d '\r' | sed "s/^cudatext (\([^)]*\)).*/\1/")

check "$APP/proc_msg.pas" "$pas_ver" "$cuda_ver"
check "$APP/cudatext.lpi major" "$lpi_v1" "$v1"
check "$APP/cudatext.lpi minor" "$lpi_v2" "$v2"
check "$APP/cudatext.lpi build" "$lpi_v3" "$v3"
check "$APP/cudatext.lpi revision" "$lpi_v4" "$v4"
check "$PLIST short" "$plist_short" "$ver_short"
check "$PLIST bundle" "$plist_ver" "$v4"
check "$CHANGELOG" "$chg_ver" "$cuda_ver"
for f in debfiles/*/control; do
  ctl_ver=$(sed -n "s/^Version: \(.*\)/\1/p" "$f" | tr -d '\r' | head -n1)
  check "$f" "$ctl_ver" "$cuda_ver-1"
done

if [ "$got_bad" != 0 ]; then
  echo "error: files above are out of sync with setup/cuda_ver.sh" >&2
  exit 1
fi
echo "all files match version $cuda_ver"
