#!/usr/bin/env bash
set -uo pipefail

REPORT="${1:-/tmp/mac-disk-scan.txt}"
: > "$REPORT"

log() { printf '%s\n' "$*" >> "$REPORT"; }
section() { printf '\n===== %s =====\n' "$1" >> "$REPORT"; }

size_of() {
    [ -e "$1" ] || return 0
    local result
    result=$(du -sh "$1" 2>/dev/null | cut -f1)
    printf '%s' "${result:-locked}"
}

short() { printf '%s' "${1/#$HOME/\~}"; }

section 'DISK'
df -h /System/Volumes/Data | tail -1 | awk '{print "Free: "$4" of "$2"   ("$5" used)"}' >> "$REPORT"

section 'HOME TOP LEVEL'
du -sh "$HOME"/* 2>/dev/null | sort -rh | head -20 >> "$REPORT"

section 'LIBRARY BREAKDOWN'
for dir in "Group Containers" Containers "Application Support" Caches Developer Logs; do
    [ -d "$HOME/Library/$dir" ] && printf '%-22s %s\n' "$dir" "$(size_of "$HOME/Library/$dir")" >> "$REPORT"
done

section 'LARGEST LIBRARY SUBDIRS'
for dir in "Group Containers" Containers "Application Support" Caches Developer; do
    [ -d "$HOME/Library/$dir" ] || continue
    log "-- $dir"
    du -sh "$HOME/Library/$dir"/* 2>/dev/null | sort -rh | head -8 >> "$REPORT"
done

section 'DEV CACHES (safe to delete, all regenerate)'
for path in \
    "$HOME/Library/Developer/Xcode/DerivedData" \
    "$HOME/Library/Developer/Xcode/Archives" \
    "$HOME/Library/Developer/Xcode/iOS DeviceSupport" \
    "$HOME/Library/Developer/CoreSimulator/Devices" \
    "$HOME/Library/Caches/Homebrew" \
    "$HOME/Library/Caches/CocoaPods" \
    "$HOME/Library/Caches/ms-playwright" \
    "$HOME/Library/Caches/pnpm" \
    "$HOME/Library/Caches/JetBrains" \
    "$HOME/Library/pnpm/store" \
    "$HOME/.npm" \
    "$HOME/.cache/uv" \
    "$HOME/.cache/puppeteer" \
    "$HOME/.cache/pip" \
    "$HOME/.cache/yarn" \
    "$HOME/.gradle/caches" \
    "$HOME/.m2/repository" \
    "$HOME/.cargo/registry" \
    "$HOME/go/pkg/mod" \
    "$HOME/.rustup/toolchains" ; do
    [ -e "$path" ] && printf '%8s  %s\n' "$(size_of "$path")" "$(short "$path")" >> "$REPORT"
done

section 'STALE APP UPDATER INSTALLERS'
find "$HOME/Library/Caches" -maxdepth 1 -name '*.ShipIt' -exec du -sh {} \; 2>/dev/null | sort -rh >> "$REPORT"

section 'APPLICATIONS OVER 100MB (with last activity)'
APPS_TMP=$(mktemp)
find /Applications -maxdepth 1 -name '*.app' -print0 2>/dev/null | while IFS= read -r -d '' app; do
    mb=$(du -sm "$app" 2>/dev/null | cut -f1)
    [ "${mb:-0}" -lt 100 ] 2>/dev/null && continue
    base=$(basename "$app" .app)
    newest=$(find "$HOME/Library/Preferences" "$HOME/Library/Application Support" \
                  "$HOME/Library/Saved Application State" "$HOME/Library/Containers" \
                  -maxdepth 1 -iname "*${base}*" -exec stat -f '%m' {} \; 2>/dev/null | sort -rn | head -1)
    if [ -n "$newest" ]; then
        when=$(date -r "$newest" '+%Y-%m-%d')
    else
        when='no-data'
    fi
    printf '%6s M  %-12s  %s\n' "$mb" "$when" "$base" >> "$APPS_TMP"
done
sort -rn "$APPS_TMP" >> "$REPORT"
rm -f "$APPS_TMP"

section 'DOCKER'
if docker info >/dev/null 2>&1; then
    docker system df >> "$REPORT" 2>&1
    log ''
    log "named volumes (HOLD LOCAL DB DATA - never prune without asking):"
    docker volume ls --format '{{.Name}}' 2>/dev/null | grep -vE '^[0-9a-f]{64}$' | head -25 >> "$REPORT"
    log "named: $(docker volume ls --format '{{.Name}}' 2>/dev/null | grep -vcE '^[0-9a-f]{64}$')  anonymous: $(docker volume ls --format '{{.Name}}' 2>/dev/null | grep -cE '^[0-9a-f]{64}$')"
else
    log 'docker not running'
    raw="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
    [ -e "$raw" ] && log "Docker.raw on disk: $(size_of "$raw")  (start Docker to see what is reclaimable)"
fi

section 'LARGE FILES OVER 1GB IN HOME (excluding Library)'
find "$HOME" -maxdepth 4 -type f -size +1G -not -path "$HOME/Library/*" -exec du -h {} \; 2>/dev/null | sort -rh | head -15 >> "$REPORT"

section 'TRASH AND DOWNLOADS'
printf 'Trash      %s\n' "$(size_of "$HOME/.Trash")" >> "$REPORT"
printf 'Downloads  %s\n' "$(size_of "$HOME/Downloads")" >> "$REPORT"

section 'PERSONAL MEDIA STORES (never delete without an inventory first)'
for path in \
    "$HOME/Library/Group Containers/group.net.whatsapp.WhatsApp.shared" \
    "$HOME/Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram" \
    "$HOME/Library/Messages" \
    "$HOME/Pictures/Photos Library.photoslibrary" \
    "$HOME/Library/Application Support/Slack" ; do
    [ -e "$path" ] && printf '%8s  %s\n' "$(size_of "$path")" "$(short "$path")" >> "$REPORT"
done
log '(locked = macOS TCC blocks access; grant Full Disk Access to size it)'

printf '\nreport written to %s\n' "$REPORT"
cat "$REPORT"
