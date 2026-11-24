#!/usr/bin/env bash

# Generate thumbnails for files using ImageMagick, following Freedesktop spec
# Usage:
#   ./generate-thumbnails-magick.sh --file <path>
#   ./generate-thumbnails-magick.sh --directory <path>

set -e

# Thumbnail sizes mapping
get_thumbnail_size() {
    case "$1" in
        normal) echo 128 ;;
        large) echo 256 ;;
        x-large) echo 512 ;;
        xx-large) echo 1024 ;;
        *) echo 128 ;;
    esac
}

usage() {
    echo "Usage: $0 --file <path> | --directory <path>"
    exit 1
}

md5() {
    # Calculate md5 hash of the file's absolute path
    echo -n "$1" | md5sum | awk '{print $1}'
}

generate_thumbnail() {
    local src="$1"
    local abs_path
    abs_path="$(realpath -s "$src")"
    # Skip files with multiple frames (GIFs, videos, etc.)
    case "${abs_path,,}" in
        *.gif|*.mp4|*.webm|*.mkv|*.avi|*.mov)
            return
            ;;
    esac
    local encoded_path
    encoded_path="$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe="/!~*\x27()"))' "$abs_path")"
    local uri
    uri="file://$encoded_path"
    local hash
    hash="$(md5 "$uri")"
    local out="$CACHE_DIR/$hash.png"
    mkdir -p "$CACHE_DIR"
    if [ -s "$out" ]; then
        return
    fi
    local tmp
    tmp="$(mktemp "$CACHE_DIR/.thumbnail-XXXXXXXX.png")"
    if magick "${abs_path}[0]" -thumbnail "${THUMBNAIL_SIZE}x${THUMBNAIL_SIZE}>" "$tmp"; then
        mv -- "$tmp" "$out"
        printf 'FILE %s\n' "$abs_path"
    else
        rm -f -- "$tmp"
        printf 'Thumbnail failed: %s\n' "$abs_path" >&2
        return 1
    fi
}

# Parse arguments
SIZE_NAME="normal"
MODE=""
TARGET=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --file|-f)
            MODE="file"
            TARGET="$2"
            shift 2
            ;;
        --directory|-d)
            MODE="dir"
            TARGET="$2"
            shift 2
            ;;
        --size|-s)
            SIZE_NAME="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
    # Only one mode allowed
    [[ -n "$MODE" ]] && break
done

THUMBNAIL_SIZE="$(get_thumbnail_size "$SIZE_NAME")"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/thumbnails/$SIZE_NAME"

if [ -z "$MODE" ] || [ -z "$TARGET" ]; then
    usage
fi

case "$MODE" in
    file)
        if [ ! -f "$TARGET" ]; then
            echo "File not found: $TARGET"
            exit 2
        fi
        generate_thumbnail "$TARGET"
        ;;
    dir)
        if [ ! -d "$TARGET" ]; then
            echo "Directory not found: $TARGET"
            exit 2
        fi
        failed=0
        for f in "$TARGET"/*; do
            [ -f "$f" ] || continue
            case "${f,,}" in
                *.jpg|*.jpeg|*.png|*.webp|*.avif|*.bmp|*.tif|*.tiff|*.svg) ;;
                *) continue ;;
            esac
            # ponytail: one worker bounds decoding memory; add a bounded pool only if measured too slow.
            generate_thumbnail "$f" || failed=1
        done
        exit "$failed"
        ;;
    *)
        usage
        ;;
esac

