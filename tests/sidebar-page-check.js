// Run with node tests/sidebar-page-check.js.
const fs = require('node:fs')
const assert = require('node:assert/strict')
const vm = require('node:vm')
const source = fs.readFileSync(`${__dirname}/../modules/ii/sidebarLeft/SidebarLeftContent.qml`, 'utf8')
const key = source.match(/readonly property string mainPageKey: (.+)/)[1]
const restore = source.match(/Component.onCompleted: \{([\s\S]*?)\n    \}/)[1]
const navigate = source.match(/    function goTo\(key\) \{[\s\S]*?\n    \}/)[0]
for (const [mainPage, remember, saved, expected] of [
    ['intelligence', false, 'media', 'ai'],
    ['media', false, 'ai', 'media'],
    ['home', false, 'ai', 'home'],
    ['sports', false, 'ai', 'sports'],
    ['anime', false, 'ai', 'home'],
    ['media', true, 'ai', 'ai'],
    ['media', true, 'removed', 'home'],
]) {
    const Config = {options: {sidebar: {mainPage, leftRememberPage: remember, leftLastPage: saved}}}
    const root = {pageKeys: ['home', 'ai', 'media', 'sports'], currentKey: 'home', currentIndex: 0, restored: false}
    const context = vm.createContext({Config, root})
    root.mainPageKey = vm.runInContext(key, context)
    vm.runInContext(restore, context)
    assert.equal(root.currentKey, expected)
    assert.equal(root.restored, true)
    vm.runInContext(navigate, context)
    vm.runInContext('goTo("media")', context)
    assert.equal(root.currentKey, 'media')
    assert.equal(Config.options.sidebar.leftLastPage, remember ? 'media' : saved)
    vm.runInContext('goTo("removed")', context)
    assert.equal(root.currentKey, 'home')
}
console.log('Sidebar default page, remembered page and navigation checks passed')
