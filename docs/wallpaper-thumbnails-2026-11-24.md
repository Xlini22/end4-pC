# Local wallpaper previews and scrolling

The local selector displayed empty tiles because it did not request missing
thumbnails on opening, directory changes or changes in preview size. The
requested x-large cache was incomplete. `LocalWallpaperGrid` now schedules one
batch and `Wallpapers` coalesces identical in-flight requests, passing paths as
arguments rather than interpolating them into a shell command.

The existing ImageMagick fallback processes supported images sequentially,
reuses cached results, publishes completed thumbnails atomically and reports
each generated file. It handles Unicode names and symlinks consistently with
the selector's URI hashing, respects `XDG_CACHE_HOME`, and continues past a bad
image. This avoids starting one decoder per file simultaneously.

After completing the local cache, 219 of 220 images had verified PNG previews.
The remaining source, `blapples-01-red-purple.png`, is truncated; its original
was left untouched. The user confirmed that previews appeared.

Scrolling then exposed an existing `cache: false` on the tile images. Enabling
Qt's image cache avoids repeatedly loading and decoding thumbnails when cells
are recreated. Resolution, shadows and animations remain unchanged. The user
confirmed fluid scrolling after this correction.

```sh
python3 tests/wallpaper-thumbnails-check.py
```

The check uses a mock decoder and temporary files to cover cache reuse,
partial failures, atomic publication, URI encoding, argument boundaries,
request coalescing and automatic selector requests, without rendering.
