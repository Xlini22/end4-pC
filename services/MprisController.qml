pragma Singleton
pragma ComponentBehavior: Bound

// From https://git.outfoxxed.me/outfoxxed/nixnew
// It does not have a license, but the author is okay with redistribution.

import QtQml.Models
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Mpris
import qs.modules.common
import "MprisFilter.js" as MprisFilter

/**
 * A service that provides easy access to the active Mpris player.
 */
Singleton {
	id: root;
	property list<MprisPlayer> players: Mpris.players.values.filter(player => isRealPlayer(player) && isAllowedPlayer(player));
	property MprisPlayer trackedPlayer: null;

	readonly property string preferredPlayerName: Config.options.bar.media.preferredPlayer.trim().toLowerCase();
	readonly property bool preferredPlayerExclusive: Config.options.bar.media.preferredPlayerExclusive;
	readonly property string playerBlacklist: Config.options.bar.media.playerBlacklist;
	readonly property var rememberedTrack: Persistent.states.media.lastPreferredTrack;
	readonly property var rememberedTrackSource: ({
		identity: root.rememberedTrack.identity,
		desktopEntry: root.rememberedTrack.desktopEntry,
		dbusName: "",
		metadata: { "xesam:url": root.rememberedTrack.sourceUrl }
	});
	readonly property bool hasRememberedTrack: root.preferredPlayerExclusive
		&& root.rememberedTrack.title.trim().length > 0
		&& MprisFilter.isAllowed(root.rememberedTrackSource, root.preferredPlayerName, true, root.playerBlacklist);
	readonly property string displayTrackTitle: root.activePlayer?.trackTitle || (root.hasRememberedTrack ? root.rememberedTrack.title : "");
	readonly property string displayTrackArtist: root.activePlayer?.trackArtist || (root.hasRememberedTrack ? root.rememberedTrack.artist : "");
	readonly property string displayTrackAlbum: root.activePlayer?.trackAlbum || (root.hasRememberedTrack ? root.rememberedTrack.album : "");
	property bool resumeWhenAvailable: false;

	function matchesSource(player, query) {
		return MprisFilter.matches(player, query);
	}

	function isAllowedPlayer(player) {
		return MprisFilter.isAllowed(player, root.preferredPlayerName, root.preferredPlayerExclusive, root.playerBlacklist);
	}

	readonly property MprisPlayer preferredPlayer: {
		if (preferredPlayerName.length === 0) return null;
		const _ = root.players.length;
		for (const p of root.players) {
			if (root.matchesSource(p, preferredPlayerName))
				return p;
		}
		return null;
	}

	property MprisPlayer activePlayer: preferredPlayer
		?? (root.players.includes(trackedPlayer) ? trackedPlayer : null)
		?? root.players[0] ?? null;
	signal trackChanged(reverse: bool);

	onPreferredPlayerExclusiveChanged: {
		if (root.preferredPlayerExclusive) root.rememberActiveTrack();
	}

	onActivePlayerChanged: {
		root.updateTrack();
		if (root.activePlayer && root.resumeWhenAvailable) resumePlaybackTimer.restart();
	}

	property bool __reverse: false;

	property var activeTrack;

	function raiseActivePlayer() {
		const desktopEntry = String(root.activePlayer?.desktopEntry ?? "").replace(/\.desktop$/i, "").toLowerCase();
		const windows = ToplevelManager.toplevels.values.filter(window => desktopEntry.length > 0
			&& String(window.appId ?? "").toLowerCase() === desktopEntry);
		const title = root.activePlayer?.trackTitle ?? "";
		const window = windows.find(window => title.length > 0 && window.title.includes(title))
			?? windows.find(window => window.activated) ?? windows[0];
		window?.activate();
		const busName = root.activePlayer?.dbusName ?? "";
		if (busName.length === 0 || raisePlayerProcess.running)
			return;
		raisePlayerProcess.command = [
			"gdbus", "call", "--session",
			"--dest", busName,
			"--object-path", "/org/mpris/MediaPlayer2",
			"--method", "org.mpris.MediaPlayer2.Raise"
		];
		raisePlayerProcess.running = true;
	}

	Process {
		id: raisePlayerProcess
		running: false
	}

	Timer {
		id: resumeTimeoutTimer
		interval: 30000
		repeat: false
		onTriggered: root.resumeWhenAvailable = false
	}

	Timer {
		id: resumePlaybackTimer
		interval: 750
		repeat: false
		onTriggered: {
			if (root.activePlayer && !root.activePlayer.isPlaying && root.activePlayer.canTogglePlaying)
				root.activePlayer.togglePlaying();
			root.resumeWhenAvailable = false;
			resumeTimeoutTimer.stop();
		}
	}

	readonly property bool hasActivePlasmaIntegration: Mpris.players.values.some(
		p => p.dbusName?.startsWith('org.mpris.MediaPlayer2.plasma-browser-integration')
	)
	function isRealPlayer(player) {
        if (!Config.options.media.filterDuplicatePlayers) {
            return true;
        }
        return (
            // Remove native browser buses only if plasma-browser-integration is actually active on D-Bus
            !(hasActivePlasmaIntegration && player.dbusName.startsWith('org.mpris.MediaPlayer2.firefox')) && !(hasActivePlasmaIntegration && player.dbusName.startsWith('org.mpris.MediaPlayer2.chromium')) &&
            // playerctld just copies other buses and we don't need duplicates
            !player.dbusName?.startsWith('org.mpris.MediaPlayer2.playerctld') &&
            // Non-instance mpd bus
            !(player.dbusName?.endsWith('.mpd') && !player.dbusName.endsWith('MediaPlayer2.mpd')));
    }

	// Original stuff from fox below
	Instantiator {
		model: Mpris.players;

		Connections {
			required property MprisPlayer modelData;
			target: modelData;

			Component.onCompleted: {
				if (root.isAllowedPlayer(modelData) && (root.trackedPlayer == null || modelData.isPlaying)) {
					root.trackedPlayer = modelData;
				}
			}

			Component.onDestruction: {
				if (root.trackedPlayer == null || !root.trackedPlayer.isPlaying) {
					for (const player of root.players) {
						if (player.playbackState.isPlaying) {
							root.trackedPlayer = player;
							break;
						}
					}

					if (trackedPlayer == null && root.players.length != 0) {
						trackedPlayer = root.players[0];
					}
				}
			}

			function onPlaybackStateChanged() {
				if (root.isAllowedPlayer(modelData) && root.trackedPlayer !== modelData) root.trackedPlayer = modelData;
			}
		}
	}

	Connections {
		target: activePlayer

		function onPostTrackChanged() {
			root.updateTrack();
		}

		function onTrackArtUrlChanged() {
			// console.log("arturl:", activePlayer.trackArtUrl)
			// root.updateTrack();
			if (root.activePlayer.uniqueId == root.activeTrack.uniqueId && root.activePlayer.trackArtUrl != root.activeTrack.artUrl) {
				// cantata likes to send cover updates *BEFORE* updating the track info.
				// as such, art url changes shouldn't be able to break the reverse animation
				const r = root.__reverse;
				root.updateTrack();
				root.__reverse = r;

			}
		}
	}

	function updateTrack() {
		//console.log(`update: ${this.activePlayer?.trackTitle ?? ""} : ${this.activePlayer?.trackArtists}`)
		this.activeTrack = {
			uniqueId: this.activePlayer?.uniqueId ?? 0,
			artUrl: this.activePlayer?.trackArtUrl ?? "",
			title: this.activePlayer?.trackTitle || Translation.tr("Unknown Title"),
			artist: this.activePlayer?.trackArtist || Translation.tr("Unknown Artist"),
			album: this.activePlayer?.trackAlbum || Translation.tr("Unknown Album"),
		};
		root.rememberActiveTrack();

		this.trackChanged(__reverse);
		this.__reverse = false;
	}

	property bool isPlaying: this.activePlayer && this.activePlayer.isPlaying;
	property bool canTogglePlaying: this.activePlayer?.canTogglePlaying ?? false;
	function togglePlaying() {
		if (this.canTogglePlaying) this.activePlayer.togglePlaying();
		else if (!this.activePlayer) root.resumeLastPreferred();
	}

	function rememberActiveTrack() {
		const player = root.activePlayer;
		if (!root.preferredPlayerExclusive || !player || !root.isAllowedPlayer(player)) return;
		const title = String(player.trackTitle ?? "").trim();
		if (title.length === 0) return;
		const remembered = root.rememberedTrack;
		remembered.title = title;
		remembered.artist = String(player.trackArtist ?? "");
		remembered.album = String(player.trackAlbum ?? "");
		remembered.artUrl = String(player.trackArtUrl ?? "");
		remembered.sourceUrl = String(player.metadata?.["xesam:url"] ?? "");
		remembered.identity = String(player.identity ?? "");
		remembered.desktopEntry = String(player.desktopEntry ?? "");
	}

	function resumeLastPreferred() {
		if (!root.hasRememberedTrack) return;
		const command = MprisFilter.launchCommand(root.preferredPlayerName,
			root.rememberedTrack.sourceUrl, root.rememberedTrack.desktopEntry);
		if (command.length === 0) return;
		root.resumeWhenAvailable = true;
		resumeTimeoutTimer.restart();
		Quickshell.execDetached(command);
	}

	property bool canGoPrevious: this.activePlayer?.canGoPrevious ?? false;
	function previous() {
		if (this.canGoPrevious) {
			this.__reverse = true;
			this.activePlayer.previous();
		}
	}

	property bool canGoNext: this.activePlayer?.canGoNext ?? false;
	function next() {
		if (this.canGoNext) {
			this.__reverse = false;
			this.activePlayer.next();
		}
	}

	property bool canChangeVolume: this.activePlayer && this.activePlayer.volumeSupported && this.activePlayer.canControl;

	property bool loopSupported: this.activePlayer && this.activePlayer.loopSupported && this.activePlayer.canControl;
	property var loopState: this.activePlayer?.loopState ?? MprisLoopState.None;
	function setLoopState(loopState: var) {
		if (this.loopSupported) {
			this.activePlayer.loopState = loopState;
		}
	}

	property bool shuffleSupported: this.activePlayer && this.activePlayer.shuffleSupported && this.activePlayer.canControl;
	property bool hasShuffle: this.activePlayer?.shuffle ?? false;
	function setShuffle(shuffle: bool) {
		if (this.shuffleSupported) {
			this.activePlayer.shuffle = shuffle;
		}
	}

	function setActivePlayer(player: MprisPlayer) {
		const targetPlayer = player ?? root.players[0];
		console.log(`[Mpris] Active player ${targetPlayer} << ${activePlayer}`)

		if (targetPlayer && this.activePlayer) {
			this.__reverse = root.players.indexOf(targetPlayer) < root.players.indexOf(this.activePlayer);
		} else {
			// always animate forward if going to null
			this.__reverse = false;
		}

		this.trackedPlayer = targetPlayer;
	}

	IpcHandler {
		target: "mpris"

		function pauseAll(): void {
			for (const player of Mpris.players.values) {
				if (player.canPause) player.pause();
			}
		}

		function playPause(): void { root.togglePlaying(); }
		function previous(): void { root.previous(); }
		function next(): void { root.next(); }
	}
}
