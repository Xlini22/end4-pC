"""Run python3 tests/codex-sidebar-check.py; no account or network is used."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
fake = r'''
import json, sys
def send(data):
    print(json.dumps(data), flush=True)
def notify(method, **params):
    send(dict(method=method, params=dict(threadId="thread-1", **params)))
decision = "decline"
for line in sys.stdin:
    m = json.loads(line)
    method, p = m.get("method"), m.get("params", {})
    if not method:
        if "error" in m:
            assert m["id"] == "foreign" and m["error"]["code"] == -32601
            continue
        assert m["id"] == "approval-1" and m["result"]["decision"] == decision
        notify("serverRequest/resolved", requestId="approval-1")
        notify("turn/completed", turn=dict(id="turn-1", status="completed"))
        continue
    if method == "initialized":
        continue
    result = {}
    if method == "initialize":
        assert p["clientInfo"]["name"] == "quickshell_intelligence"
    elif method == "account/read":
        result = dict(account=dict(type="chatgpt"), requiresOpenaiAuth=True)
    elif method == "account/rateLimits/read":
        result = dict(rateLimits=dict(limitId="codex",
            primary=dict(usedPercent=25, windowDurationMins=300, resetsAt=1800000000),
            secondary=dict(usedPercent=60, windowDurationMins=10080, resetsAt=1800500000)))
    elif method == "model/list":
        result = dict(data=[dict(id="model-1", model="model-1", displayName="Test model")])
    elif method == "thread/list":
        result = dict(data=[dict(id="thread-1", preview="A saved conversation")])
    elif method in ("thread/start", "thread/resume"):
        if p["cwd"] == "/invalid/project":
            send(dict(id=m["id"], error=dict(code=-32602, message="Directory does not exist")))
            continue
        assert p["approvalPolicy"] == "on-request" and p["approvalsReviewer"] == "user"
        assert p["sandbox"] in ("read-only", "workspace-write")
        result = dict(thread=dict(id="thread-1", cwd=p["cwd"], turns=[]))
        if method == "thread/resume":
            result["thread"]["turns"] = [dict(id="old", status="completed", items=[
                dict(id="saved-attachment", type="userMessage", content=[dict(type="text",text="Previous photo"),dict(type="localImage",path="/tmp/saved.png")]),
                dict(id="saved", type="agentMessage", text="Restored response"),
                dict(id="saved-command-1", type="commandExecution", command="pwd", status="completed"),
                dict(id="saved-command-2", type="commandExecution", command="ls", status="completed")])]
    elif method == "turn/start":
        if p["input"][0]["text"].startswith("attachment-check"):
            assert p["input"][1:] == [dict(type="localImage", path="/tmp/screen shot.png")]
            assert '"/tmp/source file.qml"' in p["input"][0]["text"]
        if p["input"][0]["text"].startswith("Analizza i file allegati."):
            assert p["input"][1:] == [dict(type="localImage", path="/tmp/screen shot.png")]
        editing = p["input"][0]["text"] == "edit"
        decision = "accept" if editing else "decline"
        expected = dict(type="workspaceWrite", networkAccess=False, writableRoots=["/tmp"]) if editing else dict(type="readOnly", networkAccess=False)
        assert p["sandboxPolicy"] == expected
        assert p["approvalPolicy"] == "on-request" and p["approvalsReviewer"] == "user"
        result = dict(turn=dict(id="turn-1", status="inProgress"))
    elif method == "turn/interrupt":
        notify("turn/completed", turn=dict(id="turn-1", status="interrupted"))
    else:
        raise AssertionError(method)
    send(dict(id=m["id"], result=result))
    if method != "turn/start":
        continue
    notify("turn/started", turn=dict(id="turn-1", status="inProgress"))
    if p["input"][0]["text"] == "interrupt":
        continue
    notify("item/started", item=dict(id="user", type="userMessage", content=p["input"]))
    notify("item/started", item=dict(id="answer", type="agentMessage", text=""))
    notify("item/agentMessage/delta", itemId="answer", delta="Hello ")
    notify("item/agentMessage/delta", itemId="answer", delta="world")
    notify("item/completed", item=dict(id="answer", type="agentMessage", text="Hello world"))
    notify("item/started", item=dict(id="command", type="commandExecution", command="rg main", cwd="/tmp", status="inProgress"))
    notify("item/commandExecution/outputDelta", itemId="command", delta="main.qml\n")
    notify("item/completed", item=dict(id="command", type="commandExecution", command="rg main", cwd="/tmp", aggregatedOutput="main.qml\n", exitCode=0, status="completed"))
    notify("item/started", item=dict(id="command-2", type="commandExecution", command="test -f missing.qml", status="inProgress"))
    notify("item/completed", item=dict(id="command-2", type="commandExecution", command="test -f missing.qml", exitCode=1, status="failed"))
    notify("item/completed", item=dict(id="divider", type="agentMessage", text="Next check"))
    notify("item/completed", item=dict(id="command-3", type="commandExecution", command="pwd", status="completed"))
    notify("item/started", item=dict(id="files", type="fileChange", changes=[dict(path="file.qml", diff="+ changed")]))
    send(dict(id="approval-1", method="item/fileChange/requestApproval", params=dict(threadId="thread-1", turnId="turn-1", itemId="files", reason="Review patch")))
'''
harness = r'''
import "."
import QtQuick
import Quickshell
ShellRoot {
    id: test
    property int phase: 0
    property bool failed: false
    CodexUnderTest { id: client }
    function check(condition, message) {
        if (!condition) { failed = true; console.error("CHECK FAILED: " + message); Qt.quit(); }
    }
    function entry(id) {
        for (let i = 0; i < client.messages.count; i++)
            if (client.messages.get(i).itemId === id) return client.messages.get(i);
        return null;
    }
    Component.onCompleted: client.connect()
    Timer {
        interval: 20; running: true; repeat: true
        onTriggered: {
            if (test.failed) return;
            if (test.phase === 0 && client.ready && client.authenticated && client.models.length && client.history.length && client.weeklyLimit) {
                check(client.fiveHourLimit.usedPercent === 25 && client.weeklyLimit.usedPercent === 60, "load both usage windows");
                client.receive({method:"account/rateLimits/updated", params:{rateLimits:{limitId:"codex", primary:{usedPercent:31,windowDurationMins:300,resetsAt:1800000100},secondary:null}}});
                check(client.fiveHourLimit.usedPercent === 31 && client.weeklyLimit.usedPercent === 60, "merge sparse account events outside a thread");
                client.receive({method:"account/rateLimits/updated", params:{rateLimits:{limitId:"other",primary:{usedPercent:99,windowDurationMins:300}}}});
                check(client.fiveHourLimit.usedPercent === 31, "ignore other usage buckets");
                client.updateLimits({rateLimitsByLimitId:{codex:{primary:{usedPercent:42,windowDurationMins:300}}}}, true);
                check(client.fiveHourLimit.usedPercent === 42 && !client.weeklyLimit, "snapshot clears absent windows");
                client.updateLimits({rateLimits:{primary:{usedPercent:"invalid",windowDurationMins:300}}}, true);
                check(!client.fiveHourLimit, "invalid usage must not appear as zero");
                client.pending[99998] = {method:"account/rateLimits/read"};
                client.receive({id:99998,error:{message:"Usage temporarily unavailable"}});
                check(!client.fiveHourLimit && client.rateLimitsError.length > 0 && !client.error, "usage errors stay separate from chat errors");
                client.refreshLimits();
                client.attachFiles(["https://example.com/file.txt"]);
                check(client.attachments.length === 0 && client.error.length > 0, "reject remote file URLs");
                client.attachFiles(["file:///tmp/screen%20shot.png", "file:///tmp/source%20file.qml", "file:///tmp/screen%20shot.png"]);
                check(client.attachments.length === 2 && client.attachments[0] === "/tmp/screen shot.png", "decode local URLs and deduplicate attachments");
                client.attachments = [];
                const parsed = client.userMessage([{type:"text",text:'Question\n\nFile allegati (percorsi locali):\n"/tmp/a.png"\n"/tmp/source.qml"'}, {type:"localImage",path:"/tmp/a.png"}]);
                check(parsed.text === "Question" && parsed.files.length === 2, "restore attachment cards without duplicated image paths or path footers");
                const malformed = 'Question\n\nFile allegati (percorsi locali):\nnot a JSON path';
                check(client.userMessage([{type:"text",text:malformed}]).text === malformed, "unrecognized attachment text stays intact");
                check(client.userMessage([{type:"localImage",path:"https://example.com/image.png"}]).files.length === 0, "thumbnails never load remote image paths");
                check(client.send("Inspect the code"), "send should start a turn");
                check(client.thinking, "thinking starts with the request");
                test.phase = 1;
            } else if (test.phase === 1 && client.approvals.length) {
                check(client.busy, "approval must keep the turn active");
                check(entry("answer").text === "Hello world", "streamed text should not duplicate");
                check(!client.thinking && client.busy, "thinking disappears when text starts while commands may continue");
                check(entry("command").text.includes("main.qml") && entry("command").text.includes("Exit code: 0"), "command output and status");
                check(client.messageGroups.count === 5, "consecutive commands occupy one group");
                check(client.messageGroups.get(2).itemCount === 2 && client.messageGroups.get(2).startIndex === 2, "group consecutive commands without duplicating streaming updates");
                check(client.messageGroups.get(4).itemCount === 2, "text separates command groups");
                check(client.messageGroups.get(4).fileCount === 1, "file changes join the preceding command");
                client.receive({method:"item/fileChange/outputDelta",params:{threadId:"thread-1",itemId:"files",delta:"patch output"}});
                check(entry("files").kind === "fileChange", "file output keeps its activity type");
                client.receive({method:"item/started",params:{threadId:"thread-1",item:{id:"extra-command",type:"commandExecution",command:"/usr/bin/bash -lc 'printf test'",status:"inProgress"}}});
                check(client.messages.get(client.liveCommandIndex).itemId === "extra-command", "running command is exposed outside the history fold");
                client.receive({method:"item/completed",params:{threadId:"thread-1",item:{id:"extra-command",type:"commandExecution",command:"/usr/bin/bash -lc 'printf test'",status:"completed"}}});
                check(client.liveCommandIndex >= 0 && client.messages.get(client.liveCommandIndex).status === "completed", "completed command stays visible until the next activity without running animation");
                client.receive({method:"item/started",params:{threadId:"thread-1",item:{id:"extra-files",type:"fileChange",changes:[]}}});
                check(client.liveCommandIndex === -1, "file activity archives the previous visible command");
                client.item({id:"extra-files",type:"fileChange",changes:[{path:"file.qml",diff:"+ again"},{path:"other.qml",diff:"+ new"}],status:"completed"});
                check(client.messageGroups.count === 5 && client.messageGroups.get(4).itemCount === 4, "mixed activities retain one ordered group");
                check(client.messageGroups.get(4).commandCount === 2 && client.messageGroups.get(4).fileCount === 2, "count commands and unique changed paths");
                check(client.messages.get(client.messageGroups.get(4).startIndex + 1).itemId === "files", "file changes keep execution order");
                check(client.displayCommand("/usr/bin/bash -lc 'printf test'") === "printf test", "hide literal shell wrapper");
                check(client.displayCommand("/bin/sh -c 'printf \\\"hello\\\"'") === "printf \\\"hello\\\"", "preserve escapes inside single quotes");
                check(client.displayCommand("bash -lc \\\"$HOME\\\"") === "bash -lc \\\"$HOME\\\"", "preserve dynamic wrappers");
                check(client.displayCommand("bash -lc 'pwd' extra") === "bash -lc 'pwd' extra", "preserve wrappers with extra arguments");
                check(client.displayCommand("rg main") === "rg main", "keep ordinary commands unchanged");
                check(entry("command").command === "rg main" && entry("command-2").status === "failed", "retain real commands and individual failures");
                check(client.approvals[0].changes.includes("+ changed"), "show the actual proposed patch");
                check(!client.send("second turn"), "prevent concurrent turns");
                client.decide("not-pending", true);
                check(client.approvals.length === 1, "unknown approval must not grant anything");
                client.decide("approval-1", false);
                test.phase = 2;
            } else if (test.phase === 2 && !client.busy) {
                check(client.approvals.length === 0, "clear approvals on completion");
                check(!client.thinking && client.liveCommandIndex === -1, "completion clears thinking and the live command");
                client.resume("thread-1");
                test.phase = 3;
            } else if (test.phase === 3 && !client.busy) {
                check(entry("saved").text === "Restored response", "resume must restore history");
                check(client.messageGroups.count === 3 && client.messageGroups.get(2).itemCount === 2, "resume rebuilds command groups");
                check(JSON.parse(entry("saved-attachment").files)[0] === "/tmp/saved.png", "resume restores image attachment cards");
                check(client.send("interrupt"), "start interruptible work");
                test.phase = 4;
            } else if (test.phase === 4 && client.turnId) {
                client.stop();
                client.stop();
                test.phase = 5;
            } else if (test.phase === 5 && !client.busy) {
                check(!client.turnId && !client.interruptSent, "interruption must settle the turn");
                const count = client.messages.count;
                client.receive({method: "item/agentMessage/delta", params: {threadId:"other", itemId:"wrong", delta:"ignore"}});
                check(client.messages.count === count, "ignore another thread's events");
                client.receive({method:"item/commandExecution/requestApproval", id:"foreign", params:{threadId:"other",turnId:"wrong"}});
                check(client.approvals.length === 0, "foreign approvals must fail closed");
                client.error = "";
                client.receive({id:99999, result:{}});
                check(client.error === "", "ignore unknown response IDs");
                client.newConversation();
                check(!client.threadId && client.messages.count === 0, "new conversation clears UI history");
                check(client.messageGroups.count === 0, "new conversation clears command groups");
                TestConfig.options.ai.codex.allowEdits = true;
                check(client.send("edit"), "start a workspace-write turn");
                test.phase = 6;
            } else if (test.phase === 6 && client.approvals.length) {
                client.decide("approval-1", true);
                test.phase = 7;
            } else if (test.phase === 7 && !client.busy) {
                TestConfig.options.ai.codex.workspace = "/invalid/project";
                check(client.send("server rejected"), "submit directory for server validation");
                test.phase = 8;
            } else if (test.phase === 8 && !client.busy) {
                check(client.error === "Directory does not exist", "show the actual RPC error");
                check(client.lastPrompt === "server rejected", "preserve failed prompts for recovery");
                client.response({method:"thread/list", cwd:"/another-project"}, {data:[{id:"foreign"}]});
                check(!client.history.some(item => item.id === "foreign"), "discard stale history from other projects");
                TestConfig.options.ai.codex.workspace = "relative/path";
                check(!client.send("invalid project"), "reject relative directories");
                check(client.error.length > 0, "explain invalid project");
                TestConfig.options.ai.codex.workspace = "/tmp";
                TestConfig.options.ai.codex.allowEdits = false;
                client.reconnect();
                test.phase = 9;
            } else if (test.phase === 9 && client.ready && client.authenticated && !client.busy) {
                check(entry("saved").text === "Restored response", "reconnect must resume the persisted thread");
                client.attachFiles(["file:///tmp/screen%20shot.png", "file:///tmp/source%20file.qml"]);
                check(client.send("attachment-check"), "send mixed image and source attachments");
                check(client.attachments.length === 0 && client.lastAttachments.length === 2, "clear sent attachments and retain recovery state");
                test.phase = 10;
            } else if (test.phase === 10 && client.approvals.length) {
                check(entry("user").text === "attachment-check" && JSON.parse(entry("user").files).includes("/tmp/source file.qml"), "attachments remain available as chat cards");
                client.decide("approval-1", false);
                test.phase = 11;
            } else if (test.phase === 11 && !client.busy) {
                client.attachFiles(["file:///tmp/screen%20shot.png"]);
                check(client.send(""), "allow an attachment-only message");
                test.phase = 12;
            } else if (test.phase === 12 && client.approvals.length) {
                client.decide("approval-1", false);
                test.phase = 13;
            } else if (test.phase === 13 && !client.busy) {
                client.disconnect();
                check(!client.ready && !client.busy && client.approvals.length === 0, "disconnect clears pending state");
                check(!client.fiveHourLimit && !client.weeklyLimit, "disconnect clears account usage");
                console.log("CODEX SIDEBAR CHECK PASSED");
                Qt.quit();
            }
        }
    }
    Timer { interval: 8000; running: true; onTriggered: { console.error("CHECK TIMED OUT: " + client.error + " " + client.diagnostics); Qt.quit(); } }
}
'''
with tempfile.TemporaryDirectory(prefix="codex-sidebar-check-") as directory:
    temporary = Path(directory)
    mock = temporary / "server.py"
    mock.write_text(fake)
    source = (repo / "services/Codex.qml").read_text()
    source = source.replace("pragma Singleton\n", "").replace("import qs.modules.common\n", 'import "."\n')
    source = source.replace("Singleton {", "Scope {", 1).replace("Config.", "TestConfig.")
    command = '["codex", "app-server", "--listen", "stdio://", "-c", "approvals_reviewer=\\\"user\\\""]'
    assert command in source
    source = source.replace(command, json.dumps(["python3", str(mock)]))
    (temporary / "CodexUnderTest.qml").write_text(source)
    (temporary / "qmldir").write_text("singleton TestConfig 1.0 TestConfig.qml\nCodexUnderTest 1.0 CodexUnderTest.qml\n")
    (temporary / "TestConfig.qml").write_text('''pragma Singleton
import QtQuick
QtObject {
    property QtObject options: QtObject {
        property QtObject policies: QtObject { property int ai: 1 }
        property QtObject ai: QtObject {
            property QtObject codex: QtObject {
                property string workspace: "/tmp"
                property string model: ""
                property bool allowEdits: false
                property string lastThreadId: ""
                property string lastThreadCwd: ""
            }
        }
    }
}
''')
    shell = temporary / "shell.qml"
    shell.write_text(harness)
    runtime = temporary / "runtime"
    runtime.mkdir(mode=0o700)
    result = subprocess.run(["qs", "--no-color", "-p", str(shell)], capture_output=True,
                            text=True, timeout=15, env={**os.environ, "QT_QPA_PLATFORM": "offscreen",
                            "QT_QUICK_BACKEND": "software", "QT_QPA_PLATFORMTHEME": "", "XDG_RUNTIME_DIR": str(runtime)})
    output = result.stdout + result.stderr
    assert result.returncode == 0 and "CODEX SIDEBAR CHECK PASSED" in output, output
    assert "CHECK FAILED" not in output and "TypeError" not in output and "ReferenceError" not in output, output
    print("Codex sidebar protocol, streaming, approvals, thread resume and failure boundaries passed")
