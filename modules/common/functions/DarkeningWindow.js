.pragma library

function create() { return {start: 0, last: 0, initialized: false, published: false}; }

function advance(state, now) {
    if (!state.initialized || now < state.last) {
        state.start = state.last = now;
        state.initialized = true;
        state.published = false;
        return [0, 0, -1, 0];
    }
    const elapsed = now - state.start;
    const windows = Math.floor(elapsed / 1.5);
    let before = (now - state.last) / 1.5, after = 0;
    if (windows >= 1) {
        before = Math.max(0, Math.min(1, (state.start + 1.5 - state.last) / 1.5));
        state.start += windows * 1.5;
        after = Math.max(0, Math.min(1, (now - state.start) / 1.5));
        state.published = true;
    }
    state.last = now;
    return [before, after, Math.min(windows, 2), 0];
}
