pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common

Singleton {
    id: root
    readonly property bool allowed: Config.options.policies.ai === 1
    property bool ready: false
    property bool authenticated: false
    property bool busy: false
    property bool thinking: false
    property int liveCommandIndex: -1
    onBusyChanged: if (!busy) {
        thinking = false;
        liveCommandIndex = -1;
    }
    property string account: ""
    property string error: ""
    property string diagnostics: ""
    property string threadId: ""
    property string threadCwd: ""
    property string turnId: ""
    property string loginId: ""
    property var models: []
    property var history: []
    property var approvals: []
    property var rateLimits: ({})
    property string rateLimitsError: ""
    readonly property var fiveHourLimit: quotaWindow(300)
    readonly property var weeklyLimit: quotaWindow(10080)
    property var pending: ({})
    property int nextId: 0
    property string pendingPrompt: ""
    property bool interruptRequested: false
    property bool interruptSent: false
    property bool restartAfterExit: false
    property string lastPrompt: ""
    property var attachments: []
    property bool fileDialogOpen: false
    property var lastAttachments: []
    property var pendingImages: []
    readonly property alias messages: transcript
    readonly property alias messageGroups: groupedTranscript
    readonly property string workspace: Config.options.ai.codex.workspace.trim()
    readonly property string sandbox: Config.options.ai.codex.allowEdits ? "workspace-write" : "read-only"

    ListModel { id: transcript }
    ListModel { id: groupedTranscript }

    onAllowedChanged: if (!allowed) disconnect()
    onWorkspaceChanged: {
        root.history = [];
        root.refreshHistory();
    }

    function write(message) {
        if (server.running) server.write(JSON.stringify(message) + "\n");
    }

    function request(method, params) {
        const id = ++root.nextId;
        root.pending[id] = {method: method, cwd: params?.cwd};
        root.write({id: id, method: method, params: params ?? {}});
    }

    function connect() {
        if (!root.allowed || server.running) return;
        root.error = "";
        root.diagnostics = "";
        server.running = true;
    }

    function disconnect() {
        root.ready = false;
        root.authenticated = false;
        root.rateLimits = ({});
        root.rateLimitsError = "";
        root.busy = false;
        root.approvals = [];
        root.pending = ({});
        root.pendingPrompt = "";
        root.pendingImages = [];
        root.turnId = "";
        root.loginId = "";
        root.interruptRequested = false;
        root.interruptSent = false;
        root.threadId = "";
        server.running = false;
    }

    function reconnect() {
        if (!server.running) { root.connect(); return; }
        root.restartAfterExit = true;
        root.disconnect();
    }

    function refreshHistory() {
        if (root.ready && root.authenticated)
            // ponytail: show the 20 most recent project threads; add pagination if needed.
            root.request("thread/list", {cwd: root.workspace, limit: 20});
    }

    function login() {
        if (root.ready && !root.loginId) root.request("account/login/start", {type: "chatgpt"});
    }

    function refreshLimits() {
        if (root.ready && root.authenticated && root.account === "ChatGPT"
            && !Object.values(root.pending).some(call => call.method === "account/rateLimits/read"))
            root.request("account/rateLimits/read", {});
    }

    function updateLimits(params, snapshot) {
        const limits = params.rateLimitsByLimitId?.codex ?? params.rateLimits;
        if (!limits) {
            if (snapshot) root.rateLimits = ({});
            return;
        }
        if (limits.limitId && limits.limitId !== "codex") return;
        const next = snapshot ? {} : Object.assign({}, root.rateLimits);
        for (const key of ["primary", "secondary"])
            if (snapshot || limits[key] != null) next[key] = limits[key] ?? null;
        root.rateLimits = next;
        root.rateLimitsError = "";
    }

    function quotaWindow(minutes) {
        return [root.rateLimits.primary, root.rateLimits.secondary].find(window =>
            window?.windowDurationMins === minutes && typeof window.usedPercent === "number"
            && Number.isFinite(window.usedPercent) && window.usedPercent >= 0) ?? null;
    }

    function threadOptions() {
        const options = {cwd: root.workspace, sandbox: root.sandbox,
            approvalPolicy: "on-request", approvalsReviewer: "user"};
        if (Config.options.ai.codex.model) options.model = Config.options.ai.codex.model;
        return options;
    }

    function validWorkspace() {
        if (!root.workspace.startsWith("/") || root.workspace.includes("\u0000")) {
            root.error = qsTr("Choose an absolute project directory.");
            return false;
        }
        return true;
    }

    function newConversation() {
        if (root.busy) return;
        root.threadId = "";
        root.threadCwd = "";
        root.turnId = "";
        Config.options.ai.codex.lastThreadId = "";
        groupedTranscript.clear();
        transcript.clear();
        root.error = "";
        root.attachments = [];
    }

    function attachFiles(urls) {
        if (root.busy) return;
        const files = root.attachments.slice();
        try {
            for (const url of urls) {
                const path = decodeURIComponent(String(url).replace(/^file:\/\/(?:localhost)?(?=\/)/, ""));
                if (!path.startsWith("/") || path.includes("\u0000")) throw new Error(qsTr("Scegli un file locale."));
                if (!files.includes(path)) files.push(path);
            }
            root.attachments = files;
        } catch (error) { root.error = String(error); }
    }

    function resume(id) {
        if (!root.ready || !root.authenticated || root.busy || !id || !root.validWorkspace()) return;
        root.error = "";
        root.busy = true;
        root.pendingPrompt = "";
        root.request("thread/resume", Object.assign(root.threadOptions(), {threadId: id}));
    }

    function send(text) {
        if ((!text.trim() && !root.attachments.length) || !root.ready || !root.authenticated || root.busy || !root.validWorkspace()) return false;
        if (root.attachments.some(path => typeof path !== "string" || !path.startsWith("/") || path.includes("\u0000"))) {
            root.error = qsTr("Scegli un file locale.");
            return false;
        }
        root.error = "";
        root.busy = true;
        root.interruptRequested = false;
        root.thinking = true;
        root.interruptSent = false;
        root.lastPrompt = text;
        root.lastAttachments = root.attachments.slice();
        root.pendingPrompt = text.trim() ? text : qsTr("Analizza i file allegati.");
        if (root.attachments.length)
            root.pendingPrompt += "\n\n" + qsTr("File allegati (percorsi locali):") + "\n" + root.attachments.map(path => JSON.stringify(path)).join("\n");
        root.pendingImages = root.attachments.filter(path => /\.(png|jpe?g|webp|gif)$/i.test(path));
        root.attachments = [];
        if (root.threadId && root.threadCwd === root.workspace) root.startTurn();
        else root.request("thread/start", root.threadOptions());
        return true;
    }

    function startTurn() {
        if (!root.pendingPrompt) { root.busy = false; return; }
        const policy = Config.options.ai.codex.allowEdits
            ? {type: "workspaceWrite", writableRoots: [root.workspace], networkAccess: false}
            : {type: "readOnly", networkAccess: false};
        const params = {threadId: root.threadId, cwd: root.workspace,
            approvalPolicy: "on-request", approvalsReviewer: "user", sandboxPolicy: policy,
            input: [{type: "text", text: root.pendingPrompt}].concat(root.pendingImages.map(path => ({type: "localImage", path: path})))};
        if (Config.options.ai.codex.model) params.model = Config.options.ai.codex.model;
        root.pendingPrompt = "";
        root.pendingImages = [];
        root.request("turn/start", params);
    }

    function stop() {
        root.liveCommandIndex = -1;
        root.pendingPrompt = "";
        root.pendingImages = [];
        root.interruptRequested = true;
        for (const approval of root.approvals) root.write({id: approval.id, result: {decision: "cancel"}});
        root.approvals = [];
        if (root.threadId && root.turnId && !root.interruptSent) {
            root.interruptSent = true;
            root.request("turn/interrupt", {threadId: root.threadId, turnId: root.turnId});
        }
    }

    function decide(id, accept) {
        const approval = root.approvals.find(item => item.id === id);
        if (!approval || approval.threadId !== root.threadId || approval.turnId !== root.turnId) return;
        root.write({id: id, result: {decision: accept ? "accept" : "decline"}});
        root.approvals = root.approvals.filter(item => item.id !== id);
    }

    function row(id, kind, title) {
        // ponytail: linear lookup suits a sidebar transcript; index IDs if histories become large.
        for (let i = 0; i < transcript.count; ++i)
            if (transcript.get(i).itemId === id) return i;
        const start = transcript.count;
        transcript.append({itemId: id, kind: kind, title: title, text: "", status: "", command: "", files: "[]"});
        const last = groupedTranscript.count - 1;
        const groupKind = ["commandExecution", "fileChange"].includes(kind) ? "activity" : kind;
        if (groupKind === "activity" && last >= 0 && groupedTranscript.get(last).kind === groupKind)
            groupedTranscript.setProperty(last, "itemCount", groupedTranscript.get(last).itemCount + 1);
        else groupedTranscript.append({startIndex: start, itemCount: 1, kind: groupKind, commandCount: 0, fileCount: 0});
        return transcript.count - 1;
    }

    function displayCommand(command) {
        const match = /^(?:\/usr\/bin\/|\/bin\/)?(?:bash|sh|zsh)\s+-(?:lc|cl|c)\s+([\s\S]+)$/.exec(command);
        if (!match) return command;
        // ponytail: decode one literal shell argument only; keep dynamic/compound wrappers verbatim.
        const word = match[1];
        let result = "", quote = "";
        for (let i = 0; i < word.length; ++i) {
            const ch = word[i];
            if (quote === "'") {
                if (ch === "'") quote = "";
                else result += ch;
            } else if (ch === "\\") {
                if (++i >= word.length) return command;
                const next = word[i];
                if (quote === '"' && !'\\"$`\n'.includes(next)) result += "\\";
                if (next !== "\n") result += next;
            } else if (quote === '"') {
                if (ch === '"') quote = "";
                else if (ch === "$" || ch === "`") return command;
                else result += ch;
            } else if (ch === "'" || ch === '"') quote = ch;
            else if (/^[a-zA-Z0-9_./:=+,-]$/.test(ch)) result += ch;
            else return command;
        }
        return quote ? command : result;
    }

    function updateActivity(index) {
        for (let g = groupedTranscript.count - 1; g >= 0; --g) {
            const group = groupedTranscript.get(g);
            if (group.startIndex > index) continue;
            if (group.kind !== "activity") return;
            let commands = 0;
            const files = new Set();
            for (let i = group.startIndex; i < group.startIndex + group.itemCount; ++i) {
                const message = transcript.get(i);
                if (message.kind === "commandExecution") ++commands;
                else JSON.parse(message.files).forEach(path => files.add(path));
            }
            groupedTranscript.setProperty(g, "commandCount", commands);
            groupedTranscript.setProperty(g, "fileCount", files.size);
            return;
        }
    }

    function setText(index, text) {
        if (transcript.get(index).kind === "agentMessage" && String(text ?? "").length) {
            root.thinking = false;
            root.liveCommandIndex = -1;
        }
        // ponytail: bound visible output to 128 KiB per item; Codex retains the full thread.
        transcript.setProperty(index, "text", String(text ?? "").slice(-131072));
    }

    function userMessage(content) {
        let text = content.filter(part => part.type === "text").map(part => part.text).join("\n");
        let files = content.filter(part => part.type === "localImage").map(part => part.path);
        const marker = "\n\n" + qsTr("File allegati (percorsi locali):") + "\n";
        const start = text.lastIndexOf(marker);
        if (start >= 0) {
            try {
                const paths = text.slice(start + marker.length).split("\n").map(line => JSON.parse(line));
                if (paths.length && paths.every(path => typeof path === "string" && path.startsWith("/") && !path.includes("\u0000"))) {
                    files = files.concat(paths);
                    text = text.slice(0, start);
                }
            } catch (error) { /* Keep unrecognized text intact. */ }
        }
        files = [...new Set(files.filter(path => typeof path === "string" && path.startsWith("/") && !path.includes("\u0000")))];
        return {text: text, files: files};
    }

    function item(item) {
        if (!item?.id) return;
        let title = "";
        let text = "";
        if (item.type === "userMessage") {
            title = qsTr("You");
            text = root.userMessage(item.content ?? []).text;
        } else if (item.type === "agentMessage") {
            title = "Codex";
            text = item.text ?? "";
        } else if (item.type === "commandExecution") {
            title = qsTr("Command");
            text = (item.command ?? "") + "\n" + (item.cwd ?? "") + "\n\n" + (item.aggregatedOutput ?? "");
            if (item.exitCode !== undefined && item.exitCode !== null) text += "\n" + qsTr("Exit code: %1").arg(item.exitCode);
        } else if (item.type === "fileChange") {
            title = qsTr("File changes");
            text = (item.changes ?? []).map(change => change.path + "\n" + (change.diff ?? "")).join("\n\n");
        } else if (item.type === "mcpToolCall") {
            title = qsTr("Tool");
            text = (item.server ?? "") + " / " + (item.tool ?? "");
        } else return;
        const index = root.row(item.id, item.type, title);
        if (item.type === "userMessage")
            transcript.setProperty(index, "files", JSON.stringify(root.userMessage(item.content ?? []).files));
        if (item.type === "commandExecution" && item.command)
            transcript.setProperty(index, "command", item.command);
        if (item.type === "fileChange" && item.changes)
            transcript.setProperty(index, "files", JSON.stringify([...new Set(item.changes.map(change => change.path).filter(path => typeof path === "string"))]));
        root.updateActivity(index);
        // An empty started/completed item must not erase text already streamed.
        if (text || !transcript.get(index).text) root.setText(index, text);
        transcript.setProperty(index, "status", item.status ?? "");
    }

    function response(call, result) {
        if (call.method === "initialize") {
            root.write({method: "initialized", params: {}});
            root.ready = true;
            startupTimeout.stop();
            root.request("account/read", {refreshToken: false});
            root.request("model/list", {});
        } else if (call.method === "account/read") {
            root.authenticated = !!result.account || result.requiresOpenaiAuth === false;
            root.account = result.account?.type === "chatgpt" ? "ChatGPT" : result.account?.type === "apiKey" ? "API key" : "";
            root.rateLimits = ({});
            root.refreshLimits();
            root.refreshHistory();
            const saved = Config.options.ai.codex;
            if (root.authenticated && !root.threadId && saved.lastThreadId && saved.lastThreadCwd === root.workspace)
                root.resume(saved.lastThreadId);
        } else if (call.method === "account/rateLimits/read") {
            root.updateLimits(result, true);
        } else if (call.method === "model/list") {
            root.models = result.data ?? [];
        } else if (call.method === "thread/list") {
            if (call.cwd === root.workspace) root.history = result.data ?? [];
        } else if (call.method === "account/login/start") {
            root.loginId = result.loginId ?? "";
            if (result.authUrl?.startsWith("https://")) Qt.openUrlExternally(result.authUrl);
        } else if (call.method === "thread/start" || call.method === "thread/resume") {
            root.threadId = result.thread.id;
            root.threadCwd = result.thread.cwd ?? root.workspace;
            Config.options.ai.codex.workspace = root.threadCwd;
            Config.options.ai.codex.lastThreadId = root.threadId;
            Config.options.ai.codex.lastThreadCwd = root.threadCwd;
            groupedTranscript.clear();
            transcript.clear();
            root.turnId = "";
            for (const turn of result.thread.turns ?? []) {
                for (const item of turn.items ?? []) root.item(item);
                if (turn.status === "inProgress") root.turnId = turn.id;
            }
            if (root.pendingPrompt) root.startTurn();
            else root.busy = !!root.turnId;
            root.refreshHistory();
        } else if (call.method === "turn/start") {
            if (result.turn?.status === "inProgress") {
                root.turnId = result.turn.id;
                if (root.interruptRequested) root.stop();
            }
        }
    }

    function receive(message) {
        if (!message || typeof message !== "object") return;
        const params = message.params ?? {};
        if (message.method && message.id !== undefined) {
            if (["item/commandExecution/requestApproval", "item/fileChange/requestApproval"].includes(message.method)
                && params.threadId === root.threadId && params.turnId === root.turnId) {
                const index = root.row(params.itemId, "approval", qsTr("Approval"));
                root.approvals = root.approvals.concat([{id: message.id, threadId: params.threadId,
                    turnId: params.turnId, text: params.reason ?? "", command: params.command ?? "",
                    cwd: params.cwd ?? "", changes: transcript.get(index).text}]);
            } else {
                root.write({id: message.id, error: {code: -32601, message: "Unsupported or inactive client request"}});
                root.error = qsTr("Codex requested an unsupported interaction: %1").arg(message.method);
            }
            return;
        }
        if (message.id !== undefined) {
            const call = root.pending[message.id];
            if (!call) return;
            delete root.pending[message.id];
            if (message.error) {
                if (call.method === "account/rateLimits/read") {
                    root.rateLimits = ({});
                    root.rateLimitsError = message.error.message ?? qsTr("Usage unavailable.");
                    return;
                }
                root.error = message.error.message ?? qsTr("Codex request failed.");
                if (["thread/start", "thread/resume", "turn/start"].includes(call.method)) {
                    root.busy = false;
                    root.pendingPrompt = "";
                }
            } else root.response(call, message.result ?? {});
            return;
        }
        if (message.method === "account/rateLimits/updated") {
            root.updateLimits(params, false);
            return;
        }
        if (message.method === "account/login/completed") {
            root.loginId = "";
            if (params.success) root.request("account/read", {refreshToken: false});
            else root.error = params.error ?? qsTr("Sign-in failed.");
            return;
        }
        if (message.method === "account/updated") {
            root.request("account/read", {refreshToken: false});
            return;
        }
        if (params.threadId !== root.threadId || !root.threadId) return;
        if (params.turnId && root.turnId && params.turnId !== root.turnId) return;
        if (message.method === "turn/completed" && root.turnId && params.turn.id !== root.turnId) return;
        if (message.method === "turn/started") {
            root.turnId = params.turn.id;
            root.busy = true;
            if (root.interruptRequested) root.stop();
        } else if (message.method === "turn/completed") {
            root.busy = false;
            root.turnId = "";
            root.approvals = [];
            root.interruptRequested = false;
            root.interruptSent = false;
            if (params.turn.error) root.error = params.turn.error.message ?? qsTr("Codex turn failed.");
            root.refreshHistory();
        } else if (message.method === "item/started" || message.method === "item/completed") {
            root.item(params.item);
            if (message.method === "item/started")
                root.liveCommandIndex = params.item.type === "commandExecution"
                    ? root.row(params.item.id, params.item.type, qsTr("Command")) : -1;
        } else if (message.method === "item/agentMessage/delta" || message.method === "item/commandExecution/outputDelta"
                   || message.method === "item/fileChange/outputDelta") {
            const kind = message.method === "item/agentMessage/delta" ? "agentMessage"
                : message.method === "item/fileChange/outputDelta" ? "fileChange" : "commandExecution";
            if (kind !== "commandExecution") root.liveCommandIndex = -1;
            const index = root.row(params.itemId, kind, kind === "agentMessage" ? "Codex" : qsTr("Output"));
            root.setText(index, transcript.get(index).text + (params.delta ?? ""));
            root.updateActivity(index);
        } else if (message.method === "serverRequest/resolved") {
            root.approvals = root.approvals.filter(item => item.id !== params.requestId);
        } else if (message.method === "error") {
            root.error = params.error?.message ?? qsTr("Codex error.");
        }
    }

    Timer {
        interval: 60000
        repeat: true
        running: root.ready && root.authenticated && root.account === "ChatGPT"
        onTriggered: root.refreshLimits()
    }

    Timer {
        id: startupTimeout
        interval: 20000
        onTriggered: {
            root.disconnect();
            root.error = qsTr("Codex did not respond. Check that Codex CLI is installed.");
        }
    }

    Process {
        id: server
        command: ["codex", "app-server", "--listen", "stdio://", "-c", "approvals_reviewer=\"user\""]
        stdinEnabled: true
        onRunningChanged: {
            if (!running) return;
            startupTimeout.restart();
            root.request("initialize", {clientInfo: {name: "quickshell_intelligence", title: "Intelligence", version: "0.1.0"}});
        }
        stdout: SplitParser {
            onRead: line => {
                if (!line.trim()) return;
                try { root.receive(JSON.parse(line)); }
                catch (error) { root.error = qsTr("Invalid Codex response: %1").arg(String(error)); }
            }
        }
        stderr: SplitParser {
            onRead: line => root.diagnostics = (root.diagnostics + line + "\n").slice(-8192)
        }
        onExited: (code, status) => {
            startupTimeout.stop();
            const restart = root.restartAfterExit;
            root.restartAfterExit = false;
            root.disconnect();
            if (restart) root.connect();
            else if (code !== 0 && !root.error) root.error = qsTr("Codex stopped (exit %1). %2").arg(code).arg(root.diagnostics.slice(-1000));
        }
    }
}
