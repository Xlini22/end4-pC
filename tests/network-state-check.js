// Run with node tests/network-state-check.js.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync(`${__dirname}/../services/Network.qml`, 'utf8')
const block = source.slice(source.indexOf('    Process {\n        id: updateConnectionType'),
    source.indexOf('    Process {\n        id: updateNetworkName'))
const startCheck = block.slice(block.indexOf('        function startCheck'), block.indexOf('        stdout:'))
const onExited = block.slice(block.indexOf('onExited: ') + 'onExited: '.length, block.lastIndexOf('\n    }'))
const pending = []
const context = vm.createContext({
    root: {}, running: false, refreshPending: false,
    connectionStateOutput: {text: ''}, Qt: {callLater: fn => pending.push(fn)}
})
vm.runInContext(`${startCheck}\nconst done = ${onExited}`, context)
function read(text, exitCode = 0) {
    context.connectionStateOutput.text = text
    vm.runInContext(`done(${exitCode}, 0)`, context)
    return context.root
}
assert.equal(read('wifi:connected\nethernet:disconnected').wifiStatus, 'connected')
assert.equal(context.root.ethernet, false)
assert.equal(read('wifi:connected (externally)').wifi, true)
assert.equal(read('wifi:connected\nwifi:disconnected\nwifi:unavailable').wifiStatus, 'connected')
assert.equal(read('wifi:unavailable\nwifi:connected').wifiStatus, 'connected')
assert.equal(read('wifi:connecting (getting IP configuration)\nwifi:unavailable').wifiStatus, 'connecting')
assert.equal(read('wifi:unavailable').wifiStatus, 'disabled')
assert.equal(read('wifi:disconnected\nethernet:connected').ethernet, true)
assert.equal(context.root.wifiStatus, 'disconnected')
read('wifi:connected')
assert.equal(read('', 1).wifiStatus, 'connected', 'Failed reads must retain the previous state')
context.running = true
vm.runInContext('startCheck(); startCheck()', context)
assert.equal(context.refreshPending, true)
read('wifi:connecting (prepare)')
assert.equal(pending.length, 1, 'Overlapping monitor events must queue one complete follow-up read')
context.running = false
pending.shift()()
assert.equal(context.running, true)
assert.equal(context.refreshPending, false)
assert.equal(read('wifi:connected').wifiStatus, 'connected')
console.log('Network state checks passed')
