# AirDrop

The optional `omdrop` bar widget sends and receives files through
[Omdrop](https://github.com/brentkearney/omdrop-plugin) and a compatible radio
backend such as [Owly](https://github.com/t4t5/owly). Adding the widget or opening
its popup only reads status; receiving starts when you turn on its switch.
The receive window is ten minutes or until one file arrives.

## Dependencies and setup

The shell does not install drivers, change radio settings, enable services at
login, or bundle the backend. Install a radio backend appropriate for your Wi-Fi
hardware using that backend's instructions. For example, Owly provides the
`omdrop-owl` and `omdrop-owl-bin` packages on Arch. A successful hardware probe
does not prove that transfers work on every card; verify both directions.

Omdrop needs Python 3, `python-libarchive-c`, `keyutils`, OpenSSL, systemd user
services and the radio backend's helpers. The desktop adaptation uses
`notify-send` (`libnotify`), `xdg-open` (`xdg-utils`) and `wl-copy`
(`wl-clipboard`). File selection needs `python-gobject` and a working desktop
file chooser portal. Kitty is used only for commands that open a terminal.
Use the upstream dependency instructions for other distributions.

The integration was tested with Omdrop 0.16.1 at commit
`3f936be7faa7f49180ab5167fa82066ef6d79891` and Owly 0.4.1. Omdrop's CLI and
receiver are kept outside this repository. To prepare the tested Omdrop version
without an Omarchy installation:

```bash
# Run from the root of your end4-pC checkout. Keep the backend in a stable path.
git clone https://github.com/brentkearney/omdrop-plugin.git "$HOME/.local/share/omdrop"
git -C "$HOME/.local/share/omdrop" checkout --detach 3f936be7faa7f49180ab5167fa82066ef6d79891
patch --batch --forward -d "$HOME/.local/share/omdrop" -p1 < scripts/airdrop/omdrop-desktop.patch
"$HOME/.local/share/omdrop/bin/omdrop" setup
"$HOME/.local/bin/omdrop" doctor --json
```

Apply the patch once to a clean checkout. It adds native notification, browser
and terminal fallbacks and quotes the receiver's command argument for paths
containing spaces. `WorkingDirectory` remains an unquoted absolute path, as
required by systemd's parser. Omdrop's setup installs its user service and CLI
link; keep that checkout in place. Review the pinned version and patch together
when updating. This source patch retains Omdrop's MIT notice in
[`LICENSE.omdrop`](../scripts/airdrop/LICENSE.omdrop).

The widget defaults to `~/.local/bin/omdrop`. If the CLI lives elsewhere, set
`OMDROP_CLI` to its executable path in the environment that launches Quickshell.
Arguments are passed separately; paths and device names can contain spaces.

Once `doctor --json` reports `ready: true`, add **AirDrop** from the bar settings.
The widget is opt-in; no default layout is changed. On the Apple device, select
**Everyone for 10 minutes**. Turn on the switch, then receive a file or select
**Send…** beside a discovered device. The popup also changes the advertised
computer name and download directory. Files default to `~/Downloads`; Omdrop
stores preferences in `~/.config/airdrop` and its identity in `~/.omdrop`.

## Behaviour and limitations

- The popup reports Omdrop's actual state, remaining time and prerequisites.
  Missing CLI, unsupported hardware and failed commands do not confirm receiving.
- Hardware determines whether Wi-Fi stays connected. Owly's exclusive mode
  suspends Wi-Fi and restores it when receiving stops. Its channel 6 mode can be
  substantially slower than AirDrop between Apple devices; see Owly's known issues.
- Radio channel, regulatory domain and experimental hardware overrides belong to
  the backend's configuration. This integration supplies no machine-specific
  settings or hardware patches and does not enable `allow_untested`.
- The switch explicitly selects Everyone and saves that choice in Omdrop.
  Contacts Only and Apple identity management remain available through its CLI.
- The backend owns the receive deadline, radio recovery, transfer limits and file
  validation. Closing the popup or restarting Quickshell does not stop a window
  that is already active. Use the switch or `omdrop off` to stop it.
- Sending requires an active receive window. Peer names can take time to resolve;
  opening the AirDrop share sheet on an iPhone can help it answer discovery.
- A firewall must permit the backend's required traffic, including TCP 8771 on
  `awdl0` for this receiver. Follow the backend's firewall instructions.

## Verification

```bash
python3 tests/omdrop-ui-check.py
python3 tests/omdrop-desktop-check.py /path/to/omdrop-plugin
# From an active Hyprland/Wayland session (uses a fake CLI and isolated XDG dirs):
python3 tests/omdrop-ui-check.py --smoke --visible
```

The desktop check applies the patch to an isolated copy of the pinned Git
revision, validates the service with systemd using a path with spaces, and checks
that native actions preserve literal file and URL arguments. It does not modify
the supplied checkout or acquire the radio. The UI smoke checks ready, missing,
unsupported and invalid-output states, popup reuse, peers and failed commands,
including an unsuccessful attempt to start receiving.

For a hardware test, receive and send a file, check the files, turn AirDrop off
and confirm Wi-Fi reconnects. Also check the ten-minute and one-file deadlines
and cancellation of an active send. Include hardware and backend versions when
reporting results; UI smoke checks cannot establish radio compatibility.
