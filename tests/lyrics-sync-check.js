// Run with node tests/lyrics-sync-check.js.
const fs = require('node:fs')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const source = fs.readFileSync(`${__dirname}/../services/LyricsService.qml`, 'utf8')
const indexAt = source.slice(source.indexOf('    function indexAt('), source.indexOf('    function update('))
const currentPosition = source.slice(source.indexOf('    function currentPosition('), source.indexOf('    function resync('))
const root = {lyricsLines: [{time: 0}, {time: 10}, {time: 10}, {time: 20}],
    basePosition: 5, baseTime: 1000, playing: true}
const context = vm.createContext({root, Date: {now: () => 1500}})
vm.runInContext(indexAt + currentPosition, context)
for (const [position, expected] of [[-1,-1],[0,0],[9,0],[10,2],[20,3],[100,3]])
    assert.equal(vm.runInContext(`indexAt(${position})`, context), expected)
assert.equal(vm.runInContext('currentPosition()', context), 5.5)
root.playing = false
assert.equal(vm.runInContext('currentPosition()', context), 5)
root.lyricsLines = []
assert.equal(vm.runInContext('indexAt(10)', context), -1)
const readPosition = source.match(/id: readPositionTimer[\s\S]*?onTriggered: \{([\s\S]*?)\n        \}/)[1]
context.MediaArtwork = {playbackPosition: 12}
root.activePlayer = {position: 900}
root.update = () => {}
vm.runInContext(readPosition, context)
assert.equal(root.basePosition, 12, 'Lyrics must use the calibrated track position')
console.log('Lyrics sync checks passed')
