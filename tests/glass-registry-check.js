// Run: node tests/glass-registry-check.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../modules/common/widgets/WindowGlass.qml'), 'utf8');
const body = source.match(/    function syncClaim\(\) \{([\s\S]*?)\n    \}/)[1];
assert.match(source, /onTrackingChanged:\s*\{\s*syncClaim\(\)/);
assert.match(source, /onEnhancedNativeChanged:\s*\{\s*syncClaim\(\)/);
const registry = new Set();
let writes = 0;
const context = vm.createContext({root: {}, GlassLayers: {backdropConsumers: 0},
    GlassFloating: {claim() {}, release() {}}, GlassCompositor: {
        registerGlass(item) { assert(!registry.has(item)); registry.add(item); writes++; },
        unregisterGlass(item) { assert(registry.delete(item)); writes++; }
    }});
vm.runInContext('function syncClaim() {' + body + '\n}', context);
const item = context.root;
Object.assign(item, {enhancedNative: true, tracking: false, nativeClaimed: false,
    wantsBackdropTracking: false, backdropClaimed: false, wantsFloatTracking: false, claimed: false});
for (let i = 0; i < 500; i++) context.syncClaim();
assert.equal(writes, 0, 'Hidden cached surfaces must not register');
item.tracking = true;
for (let i = 0; i < 500; i++) context.syncClaim();
assert.equal(writes, 1, 'Visible native surface must register exactly once');
item.enhancedNative = false;
context.syncClaim();
assert.equal(registry.size, 0, 'Disabling native glass must withdraw geometry');
item.enhancedNative = true;
context.syncClaim();
assert.equal(registry.size, 1, 'Re-enabling must restore geometry');
item.tracking = false;
context.syncClaim();
assert.equal(registry.size, 0, 'Closing or hiding must withdraw geometry');
item.wantsBackdropTracking = true;
context.syncClaim(); context.syncClaim();
assert.equal(context.GlassLayers.backdropConsumers, 1);
item.wantsBackdropTracking = false;
context.syncClaim();
assert.equal(context.GlassLayers.backdropConsumers, 0);
console.log('PASS: active native registry, cached hide/reopen, profile toggles and independent fallback claims');
