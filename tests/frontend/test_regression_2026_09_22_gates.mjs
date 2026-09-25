// 组 G（2026-09-22）前端回归锁：SEV-2221 / SEV-2227 / SEV-2228 / MID-2237 / MID-2240 / MID-2253。
//
// 与 test_quality_ui.mjs 的分工：那边是「既有质量门禁」（四语目录、parseConfigBool 跨语言不变量、
// 掩码写入、登出等）；本文件只放本轮修复对应的**失效形态**锁，每条都能在把对应修复改回原样时变红。
//
// 沙箱策略与 test_quality_ui.mjs 同源（vm + 自制 DOM/fetch/定时器桩，无 npm 依赖），
// 但本文件需要「可控定时器」：SEV-2227 的失效形态是「隐藏后 setTimeout 永不再排」，
// 用 no-op 定时器根本观察不到，故改为可手动推进的假定时器队列。
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const APP_JS = readFileSync(new URL('../../web/app.js', import.meta.url), 'utf8');
const INDEX_HTML = readFileSync(new URL('../../web/index.html', import.meta.url), 'utf8');
const ROOT_INDEX_HTML = readFileSync(new URL('../../index.html', import.meta.url), 'utf8');
const WEB_API_PY = readFileSync(new URL('../../src/web_api.py', import.meta.url), 'utf8');
// SEV-2221 撤销锁要核对 main.py 里到底有没有轮次计数器（判据见该用例），
// 读原文而不猜：本文件已有「读生产源码做源码级断言」的先例（WEB_API_PY / APP_JS）。
const MAIN_PY = readFileSync(new URL('../../main.py', import.meta.url), 'utf8');

// —— DOM / 定时器 / fetch 桩 ————————————————————————————————

function makeClassList() {
    const set = new Set();
    return {
        add(...cs) { cs.forEach(c => set.add(c)); },
        remove(...cs) { cs.forEach(c => set.delete(c)); },
        // 必须支持 ElementToken.toggle(token, force) 的第二参：真实 DOM 里它是**绝对赋值**
        // （force=true 一定加上、false 一定去掉），而桩原先只有一元翻转。
        // app.js 的 renderRecordingControl 正是 `classList.toggle('hidden', !enabled)` 这种写法，
        // 一元翻转在「同一元素渲染两次」时结论完全相反（第一次对、第二次就错了），
        // SEV-2228 后半要断言三态标签（on/off/probe）的显隐，不修这条桩就测不出真实语义。
        toggle(c, force) {
            const want = force === undefined ? !set.has(c) : Boolean(force);
            if (want) set.add(c); else set.delete(c);
            return want;
        },
        contains(c) { return set.has(c); },
    };
}

function makeElement(id) {
    const listeners = {};
    const attrs = {};
    return {
        id,
        _listeners: listeners,
        innerHTML: '',
        textContent: '',
        value: '',
        // .options 是 HTMLSelectElement 独有的 HTMLOptionsCollection：app.js 的 renderDanmaku 在
        // 推进增量游标（dmLastSeq）之前会遍历 sel.options 以保留当前筛选项
        // （web/app.js `for (var k = 0; k < sel.options.length; k++)`）。桩若不建模 .options，
        // 该处读 undefined.length 抛 TypeError，位于其后的游标推进逻辑被整体跳过，danmaku 游标用例
        // 就会把「沙箱 DOM 不全」误报成「生产未推进游标」。补一个空 options 集合，让 renderDanmaku
        // 走完整条链——注意这是修桩保真度，不是改生产：真实浏览器里 select.options 恒存在。
        options: [],
        className: '',
        disabled: false,
        scrollTop: 0,
        scrollHeight: 0,
        style: {},
        dataset: {},
        classList: makeClassList(),
        addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
        setAttribute(k, v) { attrs[k] = String(v); },
        getAttribute(k) { return k in attrs ? attrs[k] : null; },
        appendChild() {},
        removeChild() {},
        closest() { return null; },
        matches() { return false; },
    };
}

// 可手动推进的定时器：nextId 单调递增（断言「是否还在排队下一次」时读它），
// runNext 只执行排在最前的一个回调，flush 反复执行直到队列空。
function makeTimers() {
    let seq = 0;
    const pending = new Map();
    return {
        pending,
        setTimeout(fn) { const id = ++seq; pending.set(id, fn); return id; },
        clearTimeout(id) { pending.delete(id); },
        // 只执行指定的一个回调（调用方先快照 id），执行前从队列摘除；
        // 不提供「跑空队列」入口——轮询回调会自我续期，跑空等于空转到稳定态。
        async runOne(id) {
            const fn = pending.get(id);
            if (!fn) return false;
            pending.delete(id);
            fn();
            return true;
        },
    };
}

function makeResponse(status, data) {
    const text = JSON.stringify(data);
    return {
        status,
        ok: status >= 200 && status < 300,
        headers: { get: () => 'application/json' },
        text: async () => text,
    };
}

// routes 键为 "METHOD path"，值为对象或 (callIndex) => 对象；path 含 query 时按前缀匹配失败，
// 故调用方须写全（本文件用到的 path 都是固定的）。
function makeFetch(routes, log) {
    return async (path, init) => {
        init = init || {};
        const method = init.method || 'GET';
        log.push({ path, method });
        const route = routes[method + ' ' + path] || routes[method + ' ' + path.split('?')[0]];
        if (!route) return makeResponse(404, { detail: 'no test route for ' + method + ' ' + path });
        const spec = typeof route === 'function' ? route(log.length) : route;
        return makeResponse(spec.status || 200, spec.json || {});
    };
}

async function flushMicrotasks(rounds) {
    for (let i = 0; i < (rounds || 10); i++) {
        await new Promise(r => setImmediate(r));
    }
}

// 启动 app.js；hidden 控制初始 document.hidden（visibilitychange 用例要先处于可见态再切走）。
async function boot({ routes = {}, hidden = false, seedClasses = {} } = {}) {
    const fetchLog = [];
    const timers = makeTimers();
    const elements = new Map();
    const tabs = ['dashboard', 'danmaku', 'rooms', 'config', 'files'].map(v => {
        const el = makeElement('tab-' + v);
        el.setAttribute('data-view', v);
        return el;
    });
    const docListeners = {};
    // class 选择器桩：只建模 renderRecordingControl 真正用到的 .recording-state 三 span
    // （on/off/probe）。getElementById 的桩是「按 id 惰性建一个元素」，class 选择器没有对应
    // 物，故这里给每个 selector 也惰性建一个元素并在 ctx.selectors 里回读——
    // SEV-2228 后半要断言「取证失败」标签的显隐，必须有可达的断言面。
    const selectors = new Map();
    const selectorById = sel => {
        if (!selectors.has(sel)) selectors.set(sel, makeElement('class:' + sel));
        return selectors.get(sel);
    };
    const elementById = id => {
        if (!elements.has(id)) {
            const el = makeElement(id);
            (seedClasses[id] || []).forEach(c => el.classList.add(c));
            elements.set(id, el);
        }
        return elements.get(id);
    };
    const document = {
        hidden,
        getElementById: elementById,
        querySelectorAll(sel) {
            if (sel === '.tab') return tabs;
            if (sel === '.view:not(.hidden)') {
                // 只建模「仪表盘可见」这一种情形：dashboard-view 无 hidden 类即视为可见
                const v = elementById('dashboard-view');
                return v.classList.contains('hidden') ? [] : [v];
            }
            return [];
        },
        querySelector(sel) { return /^\.recording-state \.state-\w+$/.test(sel) ? selectorById(sel) : null; },
        addEventListener(type, fn) { (docListeners[type] = docListeners[type] || []).push(fn); },
        documentElement: makeElement('html'),
        body: makeElement('body'),
    };
    const storage = new Map();
    const sandbox = {
        document,
        localStorage: {
            getItem: k => (storage.has(k) ? storage.get(k) : null),
            setItem: (k, v) => storage.set(k, String(v)),
            removeItem: k => storage.delete(k),
        },
        fetch: makeFetch({
            // 语言：默认 zh_CN；/api/auth/status 与 /api/status 由用例覆盖
            'GET /api/language': { json: { language: 'zh_CN' } },
            'GET /api/auth/status': { json: { auth_required: true, warning: null } },
            ...routes,
        }, fetchLog),
        setTimeout: (fn, ms) => timers.setTimeout(fn, ms),
        clearTimeout: id => timers.clearTimeout(id),
        confirm: () => true,
        EventSource: class { constructor() {} close() {} addEventListener() {} },
    };
    sandbox.window = sandbox;
    vm.createContext(sandbox);
    vm.runInContext(APP_JS, sandbox, { filename: 'web/app.js' });
    const fire = (type, ev) => (docListeners[type] || []).forEach(fn => fn(ev || {}));
    // DOMContentLoaded 之后的启动引导会拉一次 /api/status；随后推进定时器队列把
    // 首次 dashboard 轮询（setTimeout(...,0)）也跑掉，测试才从「已进入稳态」开始。
    fire('DOMContentLoaded');
    await flushMicrotasks();
    return { sandbox, elements, selectors, tabs, fetchLog, timers, document, fire, storage };
}

// 切到仪表盘：tab 点击 → showView('dashboard') → startSSE()/loadLogs()/startLogsPolling()
// 注意只 flush 一轮：runNext 会把回调里新排的下一次轮询也执行掉，flush 到空等于空跑到稳定态，
// 会把「一次 flush = 一次请求」的计数前提摧毁（本文件多处按请求数增量断言）。
async function gotoDashboard(ctx) {
    const tab = ctx.tabs.find(t => t.getAttribute('data-view') === 'dashboard');
    tab._listeners.click[0].call(tab);
    return tick(ctx);
}

// 切到弹幕监控视图：tab 点击 → startDanmakuPolling() → 每轮 GET /api/danmaku?since=<游标>。
// 与 gotoDashboard 同理只推进一轮（一次 tick = 一次请求），用例才能按「第 N 次轮询」精确
// 安排路由返回值。
async function gotoDanmaku(ctx) {
    const tab = ctx.tabs.find(t => t.getAttribute('data-view') === 'danmaku');
    tab._listeners.click[0].call(tab);
    return tick(ctx);
}

// 推进「一轮轮询」：跑掉当前排队的定时器回调（含其内部发起的 fetch microtask 链）。
// pending.size 归零即队列已空；若回调又排了新定时器，size 非零，留给下一次 tick。
async function tick(ctx) {
    const queued = [...ctx.timers.pending.keys()];
    for (const id of queued) await ctx.timers.runOne(id);
    await flushMicrotasks();
}

// 重复推进直到队列空（或到达上限）；用于「跑完展示性 fetch 链后再断言定时器队列」。
// 注意不能用于轮询中：轮询会自我续期，跑空等于空转，本函数正是为此设了上限。
async function settle(ctx, limit) {
    let n = 0;
    while (ctx.timers.pending.size > 0) {
        if (++n > (limit || 10)) throw new Error('定时器队列未收敛（疑似轮询自激）');
        await tick(ctx);
    }
}

const STATUS_ROUTE = { 'GET /api/status': { json: { monitoring: 1, recording_count: 0, recording: [] } } };
const LOGS_ROUTE = { 'GET /api/logs': { json: { lines: ['line'] } } };

// —— MID-2237：后端不可达提示不得只写进弹幕视图的 #danmaku-stream ————————

test('MID-2237：状态请求失败时仪表盘出现可见告警，而不是只写 #danmaku-stream', async () => {
    // 失效形态：旧实现 markBackendUnreachable 只把「已断开」写进 #danmaku-stream
    // （弹幕视图的元素，仪表盘上根本看不见），且仪表盘没有任何告警元素。
    const ctx = await boot({ routes: { 'GET /api/status': { status: 500, json: { detail: 'boom' } } } });
    await gotoDashboard(ctx);
    const statusWarn = ctx.elements.get('status-warning');
    assert.ok(statusWarn, 'index.html 缺少 #status-warning（仪表盘告警横幅）');
    assert.equal(statusWarn.classList.contains('hidden'), false, '后端不可达时 #status-warning 仍隐藏');
    assert.ok(statusWarn.textContent.trim().length > 0, '#status-warning 文案为空 → 用户看不到任何提示');
    assert.match(statusWarn.textContent, /status_unavailable/, '告警应带出后端错误码，便于用户自查');
});

test('MID-2237：index.html 里 #status-warning 确实位于仪表盘视图内且默认隐藏', () => {
    const dashIdx = INDEX_HTML.indexOf('id="dashboard-view"');
    const warnIdx = INDEX_HTML.indexOf('id="status-warning"');
    const danmakuIdx = INDEX_HTML.indexOf('id="danmaku-view"');
    assert.ok(dashIdx >= 0 && warnIdx >= 0, 'index.html 未找到 #dashboard-view / #status-warning');
    assert.ok(warnIdx > dashIdx, '#status-warning 必须在仪表盘视图内（否则提示落在他处视图中）');
    if (danmakuIdx > 0) assert.ok(warnIdx < danmakuIdx, '#status-warning 落到了弹幕视图区段');
    assert.match(INDEX_HTML.slice(warnIdx - 200, warnIdx + 200), /hidden/, '#status-warning 未默认隐藏');
});

// —— SEV-2228：HTTP 200 + {"error":"status_unavailable"} 不得渲染成假绿 ————

test('SEV-2228：/api/status 以 200 返回 error=status_unavailable 时必须告警', async () => {
    // 失效形态：后端采样失败时返回 HTTP 200 的 {"error":"status_unavailable"}（不是 5xx），
    // 旧 renderStatus 不看 error 字段 → 卡片全画成 '-'、录制表显示「暂无录制」，
    // 用户看到的是「一切正常但数字是横杠」的假绿。
    const ctx = await boot({
        routes: { 'GET /api/status': { json: { error: 'status_unavailable' } } },
    });
    await gotoDashboard(ctx);
    const warn = ctx.elements.get('status-warning');
    assert.equal(warn.classList.contains('hidden'), false, 'status_unavailable 未触发告警（假绿未修）');
    assert.match(warn.textContent, /status_unavailable/);
    const tbody = ctx.elements.get('recording-tbody');
    assert.doesNotMatch(tbody.innerHTML, /暂无录制|No recordings/, '取样失败不得显示「暂无录制」（会误导为真的没有录制）');
});

test('SEV-2228：stale=true 的陈旧快照也要显式告知用户数据可能不是最新', async () => {
    const ctx = await boot({
        routes: { 'GET /api/status': { json: { monitoring: 3, recording_count: 1, recording: [], stale: true } } },
    });
    await gotoDashboard(ctx);
    const warn = ctx.elements.get('status-warning');
    assert.equal(warn.classList.contains('hidden'), false, 'stale 快照未提示（用户会把旧数字当真）');
});

// —— SEV-2221 撤销 / SEV-2228 后半：main_loop_alive 是死路径，「取证失败」改由真信号承担 ——
//
// 本节原锁「main_loop_alive=false 的告警文案要区别于引擎已停止」。2026-09-23 实测证伪：
// 该键读的是 main.main_loop_ticks，而这个名字在 main.py 里**从未定义、从未自增**
// （下面第一条用例把这条取证做成了断言，防的就是「以后有人以为还有效」）。于是键永不下发、
// 前端 `=== false` 分支永不成立——「有一个永不生效的存活信号」比「没有该信号」更危险，
// 后端已按任务书把键从契约撤下（判据与取舍见 src/web_api.py::_read_engine_status），
// 前端不再依赖它，「取证失败」改由两个真实存在的信号承担：error（采样抛错）与 stale（超时回退）。

test('SEV-2221 撤销：main_loop_alive 不得再出现在前端、后端或 main.py 任何一侧', () => {
    // 三侧同断言，缺一条就退化成「一半代码还在等一个永不来的键」：
    // ① app.js 不再读它（否则是一条永不成立的判定，还会在 main.py 接线那天静默失效）；
    // ② web_api.py 不再有探针实现（否则 _read_engine_status 若忘了挂键，实现就是死码）；
    // ③ main.py 仍无轮次计数器——这是「撤下」而不是「留着」的事实依据。
    // 断言的是**代码引用**而不是「文件里出现过这个名字」——撤下这件事本身要在注释/契约速查里
    // 写明缘由（app.js 的 API 契约注释就写了「契约里已无 main_loop_alive」），
    // 按全文 includes 断言会把这段说明也打成违规。
    assert.doesNotMatch(APP_JS, /s\.main_loop_alive\b/, 'app.js 仍在读取 main_loop_alive（死路径未清干净）');
    assert.doesNotMatch(APP_JS, /dashboard\.engineStalled/, '该文案只服务于已撤下的分支，四语目录应一并撤下');
    assert.doesNotMatch(WEB_API_PY, /_read_main_loop_alive|_MAIN_LOOP_TICKS_ATTR/,
        'web_api.py 仍留有主循环探针实现：撤下不彻底');
    assert.doesNotMatch(MAIN_PY, /\bmain_loop_ticks\b/,
        'main.py 已定义 main_loop_ticks —— 说明停摆判据的接线点已就绪，'
        + '此时应**重新接上**该键（web_api 挂键 + 前端 === false 判定 + 四语目录），而不是让本用例长红');
});

test('SEV-2221 撤销后面板不得假装知道引擎活着：error 形态要禁用两个录制按钮', async () => {
    // SEV-2228 后半的失效形态：renderRecordingControl 用 `s.engine_alive !== false` 判活，
    // 而采样失败时后端回 HTTP 200 + {"error":"status_unavailable"}——**不带 engine_alive 键**，
    // undefined !== false 判成「活着」，于是面板在完全不知道引擎死活的状态下仍让用户点
    // 「开始/停止录制」（「停止」这条兜底路径尤其不该在取证失败时被当成可用）。
    const ctx = await boot({ routes: { 'GET /api/status': { json: { error: 'status_unavailable' } } } });
    await gotoDashboard(ctx);
    assert.equal(ctx.elements.get('recording-start-btn').disabled, true, '取证失败时「开始录制」仍可点');
    assert.equal(ctx.elements.get('recording-stop-btn').disabled, true, '取证失败时「停止录制」仍可点');
    // 状态标签必须切到「取证失败」，且不得同时留着 on/off 任一态（那是假绿：明说「在录/没在录」）
    const probe = ctx.selectors.get('.recording-state .state-probe');
    const on = ctx.selectors.get('.recording-state .state-on');
    const off = ctx.selectors.get('.recording-state .state-off');
    assert.ok(probe && !probe.classList.contains('hidden'), '未显示「取证失败」标签');
    assert.ok(on.classList.contains('hidden') && off.classList.contains('hidden'),
        '取证失败时仍显示「录制运行中/已停止」之一（把未知说成已知）');
});

test('SEV-2228 后半：stale 陈旧快照与 error 同等对待（两键同样禁用）', async () => {
    // 超时回退走的是另一条分支：HTTP 200 + 完整旧快照 + stale:true，engine_alive 是**上一轮**的
    // true。只看 engine_alive !== false 会认为引擎健康并允许点录制——那是在一份过期证据上
    // 做不可逆操作，与 error 形态同等禁用才是自洽口径。
    const ctx = await boot({
        routes: { 'GET /api/status': { json: { engine_alive: true, recording_enabled: true, monitoring: 1, stale: true } } },
    });
    await gotoDashboard(ctx);
    assert.equal(ctx.elements.get('recording-start-btn').disabled, true, 'stale 快照下「开始录制」仍可点');
    assert.equal(ctx.elements.get('recording-stop-btn').disabled, true, 'stale 快照下「停止录制」仍可点');
    assert.ok(!ctx.selectors.get('.recording-state .state-probe').classList.contains('hidden'),
        'stale 未切到「取证失败」标签');
});

test('SEV-2228 后半反向边界：健康快照不得把按钮锁死（防线不得做成永久禁用）', async () => {
    // 最省事错法是「renderRecordingControl 里一律 disabled」——那既能骗过上面三条用例，
    // 又让面板再也无法开始/停止录制。engine_alive:true 且 recording_enabled:false 时
    // 「开始」必须可用、「停止」必须禁用（后者是既有语义，一并钉住）。
    const ctx = await boot({
        routes: { 'GET /api/status': { json: { engine_alive: true, recording_enabled: false, monitoring: 1, recording: [] } } },
    });
    await gotoDashboard(ctx);
    assert.equal(ctx.elements.get('recording-start-btn').disabled, false, '健康态下「开始录制」被误锁');
    assert.equal(ctx.elements.get('recording-stop-btn').disabled, true, '未在录制时「停止录制」应禁用');
    assert.ok(ctx.selectors.get('.recording-state .state-probe').classList.contains('hidden'),
        '健康态却显示「取证失败」');
    assert.ok(!ctx.selectors.get('.recording-state .state-off').classList.contains('hidden'),
        '健康态未显示「录制已停止」');
});

test('SEV-2221：字段缺失（未接线）一律视为健康，不得把健康面板刷成告警', async () => {
    // 反向锁（撤销后仍成立、且更重要）：现在契约里**没有任何**可选的存活字段，
    // 前端若改用真假值判定（`if (!s.engine_alive)`），每一个不带该键的正常响应都会被刷红。
    const ctx = await boot({ routes: STATUS_ROUTE });
    await gotoDashboard(ctx);
    const warn = ctx.elements.get('status-warning');
    assert.equal(warn.classList.contains('hidden'), true, '缺少 engine_alive 字段时误报告警（假告警）');
});

test('SEV-2221：app.js 对存活字段用 === 严格判定，不得退化为真假值判定', () => {
    // 源码级锁：`if (!s.engine_alive)` 会让 undefined（未带该键的正常快照）判成故障。
    // 旧版这条还要求 main_loop_alive 也用 === false 判定——那个键已撤下，
    // 若继续断言就会逼着实现保留一条永不成立的分支，故改为断言它**不存在**。
    const body = APP_JS.slice(APP_JS.indexOf('function updateStatusWarning'), APP_JS.indexOf('function renderRecordingControl'));
    assert.match(body, /s\.engine_alive\s*===\s*false/, 'updateStatusWarning 未用 === false 判定 engine_alive');
    assert.doesNotMatch(body, /!\s*s\.engine_alive\b/, '存在真假值判定（undefined 会被判成故障）');
    assert.doesNotMatch(body, /main_loop_alive/, 'updateStatusWarning 仍判已被撤下的 main_loop_alive');
});

// —— SEV-2228 后半：/api/danmaku 的 danmaku_unavailable 前端必须消费 ——————————

test('SEV-2228 后半：/api/danmaku 回 error=danmaku_unavailable 时不得清空房间表，必须显式说明', async () => {
    // 失效形态：后端采样失败回 HTTP 200 + {rooms:[], messages:[], last_seq:<原 since>,
    // error:'danmaku_unavailable'}。旧 renderDanmaku 不看 error：rooms 为空 → 房间表被刷成
    // 「暂无监控数据」、筛选下拉重建为只剩「全部房间」且当前选择被静默丢掉，
    // 用户以为监控真的断了或自己筛错了房间，而真实原因是一次内部异常。
    const roomRow = { name: '小乃', platform: '快手直播', connected: true, msg_total: 3, msg_rate: '1/s', gift_total: 0, online: 1, started_at: '09:00' };
    let n = 0;
    const ctx = await boot({
        routes: {
            'GET /api/danmaku': () => (++n <= 1
                ? { json: { rooms: [roomRow], messages: [], last_seq: 7, truncated: false } }
                : { json: { rooms: [], messages: [], last_seq: 7, truncated: false, error: 'danmaku_unavailable' } }),
        },
    });
    await gotoDanmaku(ctx);
    const tbody = ctx.elements.get('danmaku-rooms-tbody');
    assert.match(tbody.innerHTML, /小乃/, '用例前提不成立：第一轮未渲染出房间行');
    // 第二轮取到的是错误形态：断言它**没有**被当成「真的没有监控数据」
    await gotoDanmaku(ctx);
    assert.match(tbody.innerHTML, /小乃/, '采样失败把已有房间表刷空（用户误判为监控断了）');
    const stream = ctx.elements.get('danmaku-stream');
    assert.match(stream.textContent, /danmaku_unavailable/, '未在消息流上显式说明取不到（静默降级）');
});

test('SEV-2228 后半：danmaku_unavailable 不得推进增量游标（否则跳过失败期间的消息）', async () => {
    // 游标 dmLastSeq 只能由**成功**响应的 last_seq 推进。错误形态里 last_seq 虽等于 since
    // （后端刻意如此），但这条锁防的是「顺手把 data.last_seq 无条件写进游标」的实现漂移——
    // 一旦后端某天在错误分支也带回一个更大的 last_seq，就会静默丢掉那段弹幕。
    // 需三轮才锁得住：req2 的 path 由 req1（成功，last_seq:7）决定，验证「成功必须推进」；
    // req3 的 path 才反映 req2（error，刻意带更大的 last_seq:99）有没有被误用来推进游标。
    // （旧写法只断言到 req2 的 since=7，永远观察不到 error 响应里的 last_seq:99，
    // 与本用例标题承诺的不变量错位——那是一条只锁住「成功推进」、锁不住「错误不得推进」的半失效锁。）
    let n = 0;
    const ctx = await boot({
        routes: {
            'GET /api/danmaku': () => (++n <= 1
                ? { json: { rooms: [], messages: [], last_seq: 7, truncated: false } }
                : { json: { rooms: [], messages: [], last_seq: 99, truncated: false, error: 'danmaku_unavailable' } }),
        },
    });
    await gotoDanmaku(ctx);  // req1 → 成功 last_seq:7
    await gotoDanmaku(ctx);  // req2 → 拿到 error（last_seq:99）；其 path 由 req1 结果决定
    await gotoDanmaku(ctx);  // req3 → 其 path 才暴露「req2 的 error 有没有把游标推到 99」
    const calls = ctx.fetchLog.filter(r => r.path.startsWith('/api/danmaku'));
    assert.equal(calls.length, 3, '轮询次数与用例安排不符（前提不成立）: ' + JSON.stringify(ctx.fetchLog.map(x => x.path)));
    // 首轮从 0 起；req2 必须带上 req1 成功推进出的 since=7。
    assert.match(calls[0].path, /since=0$/, `首轮游标未从 0 起: ${JSON.stringify(calls.map(c => c.path))}`);
    assert.match(calls[1].path, /since=7$/, `成功响应的 last_seq 未推进游标: ${JSON.stringify(calls.map(c => c.path))}`);
    // 关键不变量：req2 的 error 响应带着更大的 last_seq:99，但错误分支不得推进游标——
    // req3 仍须是 since=7。若退化成无条件写 data.last_seq，这里会变成 since=99（静默丢掉 7→99 段的弹幕）。
    assert.match(calls[2].path, /since=7$/, `错误响应的 last_seq 被用于推进游标: ${JSON.stringify(calls.map(c => c.path))}`);
});


// —— SEV-2227：visibilitychange 后轮询必须自愈 ————————————————

test('SEV-2227：隐藏后回到前台，/api/status 轮询继续增长（不得永久停摆）', async () => {
    // 失效形态：旧实现隐藏时 stopSSE() 把 sseStopped 置 true，回前台的
    // `if (!sseStopped) startSSE()` 恒假 → 轮询永不恢复，面板数字冻结在切走前那一帧。
    const ctx = await boot({ routes: STATUS_ROUTE });
    await gotoDashboard(ctx);
    const statusCalls = () => ctx.fetchLog.filter(r => r.path === '/api/status').length;
    const before = statusCalls();
    assert.ok(before >= 1, '进入仪表盘未发出任何 /api/status 请求（用例前提不成立）');

    // 切走 → 回前台，两轮
    ctx.document.hidden = true;
    ctx.fire('visibilitychange');
    ctx.document.hidden = false;
    ctx.fire('visibilitychange');
    await tick(ctx);
    const afterFirst = statusCalls();
    await tick(ctx);
    const afterSecond = statusCalls();

    assert.ok(afterFirst > before, '回到前台后没有补拉状态（恢复分支未生效）');
    assert.ok(afterSecond > afterFirst, '回到前台后轮询不再继续排期（SEV-2227 回归：轮询永久停摆）');
});

test('SEV-2227：隐藏期间必须真正停掉轮询（不得退化为「隐藏也照发请求」）', async () => {
    // 反向锁：修 SEV-2227 最省事的错法是「隐藏时什么都不停」，那样后台标签页会持续请求。
    const ctx = await boot({ routes: STATUS_ROUTE });
    await gotoDashboard(ctx);
    const before = ctx.fetchLog.filter(r => r.path === '/api/status').length;
    ctx.document.hidden = true;
    ctx.fire('visibilitychange');
    await tick(ctx);
    await tick(ctx);
    assert.equal(ctx.fetchLog.filter(r => r.path === '/api/status').length, before,
        '页面隐藏期间仍在发 /api/status 请求');
    assert.equal(ctx.timers.pending.size, 0, '页面隐藏后仍有定时器在排队');
});

test('SEV-2227：切离仪表盘（非隐藏）不得留下轮询定时器，且切回不得双份轮询', async () => {
    const ctx = await boot({ routes: STATUS_ROUTE });
    await gotoDashboard(ctx);
    const cfgTab = ctx.tabs.find(t => t.getAttribute('data-view') === 'config');
    cfgTab._listeners.click[0].call(cfgTab);
    // showView('config') → loadConfig() 的 fetch 链仍在飞（它内部会排一次展示性定时器），
    // 必须让它彻底跑完再看队列——否则量到的是 loadConfig 的残留而不是状态/日志轮询。
    await settle(ctx);
    assert.equal(ctx.timers.pending.size, 0, '切离仪表盘后仍有定时器（状态/日志轮询未停）');

    // 切回仪表盘后再单独发一次可见性事件：不得叠出第二条轮询链（否则请求数翻倍）
    const dashTab = ctx.tabs.find(t => t.getAttribute('data-view') === 'dashboard');
    dashTab._listeners.click[0].call(dashTab);
    await flushMicrotasks();
    ctx.fire('visibilitychange');
    await flushMicrotasks();
    const before = ctx.fetchLog.filter(r => r.path === '/api/status').length;
    await tick(ctx);
    const after = ctx.fetchLog.filter(r => r.path === '/api/status').length;
    assert.ok(after - before <= 1, `一轮推进后续期了 ${after - before} 次状态请求（疑似双份轮询）`);
});

// —— MID-2240：仪表盘日志轮询 ————————————————————————————

test('MID-2240：停留在仪表盘上日志会继续刷新（不再只拉一次）', async () => {
    // 失效形态：旧实现只在 showView('dashboard') 里 loadLogs() 一次，
    // 用户不切视图就永远看不到新日志，「实时日志」名不副实。
    const ctx = await boot({ routes: { ...STATUS_ROUTE, ...LOGS_ROUTE } });
    await gotoDashboard(ctx);
    const logsCalls = () => ctx.fetchLog.filter(r => r.path.startsWith('/api/logs')).length;
    const before = logsCalls();
    assert.ok(before >= 1, '进入仪表盘未拉日志');
    await tick(ctx);
    const middle = logsCalls();
    await tick(ctx);
    assert.ok(middle > before && logsCalls() > middle, '日志请求数未持续增长 → 日志不再刷新（MID-2240 回归）');
});

test('MID-2240：日志轮询节拍必须严格慢于状态轮询（/api/logs 是读文件，不能同频/更频）', () => {
    // 源码级锁：/api/logs 是读文件（比 /api/status 的缓存快照重得多），节拍必须严格更大。
    // 断言 `>`（不是 `>=`）：把 LOGS_POLL_INTERVAL 调到与 SSE_OK_INTERVAL 同值也是缺陷形态。
    const logsIv = APP_JS.match(/var LOGS_POLL_INTERVAL\s*=\s*(\d+)/);
    const sseIv = APP_JS.match(/var SSE_OK_INTERVAL\s*=\s*(\d+)/);
    assert.ok(logsIv && sseIv, '未找到 LOGS_POLL_INTERVAL / SSE_OK_INTERVAL');
    assert.ok(Number(logsIv[1]) > Number(sseIv[1]),
        `日志轮询节拍 ${logsIv[1]}ms 未严格大于状态轮询 ${sseIv[1]}ms（会放大磁盘读压力）`);
});

test('MID-2240：页面隐藏时日志轮询一并停止', async () => {
    const ctx = await boot({ routes: { ...STATUS_ROUTE, ...LOGS_ROUTE } });
    await gotoDashboard(ctx);
    const before = ctx.fetchLog.filter(r => r.path.startsWith('/api/logs')).length;
    ctx.document.hidden = true;
    ctx.fire('visibilitychange');
    await tick(ctx);
    await tick(ctx);
    assert.equal(ctx.fetchLog.filter(r => r.path.startsWith('/api/logs')).length, before,
        '页面隐藏期间仍在拉日志');
});

// —— MID-2253：已翻译模板不得混入中文常量值 ————————————————

test('MID-2253：i18n.tr 模板的字符串实参不得是中文常量（其它语言下会中英混杂）', () => {
    // 失效形态（web.py:297）：
    //   tr("[web] 认证: {web_auth_enable}", web_auth_enable="开启" if ... else "关闭")
    // 模板被翻译成「Authentication: {web_auth_enable}」，而值仍是中文 → en_US 下输出
    // 「Authentication: 开启」。这类错法在中文下完全看不出，只有跨语言才暴露。
    // 锁做成**文件无关**的：任何 i18n.tr(...) 调用里出现「中文常量 + 无 tr 包装」即判红，
    // 这样新增同类写法（不止 web.py）也会被拦下。
    const files = ['web.py', 'src/web_api.py'];
    const offenders = [];
    for (const rel of files) {
        const src = readFileSync(new URL('../../' + rel, import.meta.url), 'utf8');
        // 逐行看：行内含 i18n.tr( 且含中文字符串字面量，但该字面量没有被 i18n.tr( 紧邻包裹
        for (const [i, line] of src.split('\n').entries()) {
            if (line.trim().startsWith('#')) continue;
            if (!/i18n\.tr\(/.test(line)) continue;
            // 找出所有中文字符串字面量，排除那些本身作为 tr 的模板（tr("...") 的首个实参）
            for (const m of line.matchAll(/(?:^|[^.\w])(["'])([^"']*[\u4e00-\u9fff][^"']*)\1/g)) {
                const at = m.index + m[0].indexOf(m[1]);
                // 模板实参：紧跟在 tr( 之后（允许空白）
                const before = line.slice(0, at);
                const isTemplate = /i18n\.tr\(\s*$/.test(before);
                if (!isTemplate) offenders.push(`${rel}:${i + 1}: ${line.trim()}`);
            }
        }
    }
    // 去重（同一行可能命中多次）
    assert.deepEqual([...new Set(offenders)], [],
        'i18n.tr 模板里插入了中文常量值（非模板实参），其它语言下会中英混杂');
});

test('MID-2253：web.py 认证开关播报必须走 i18n.tr 或字面量目录，不得内联中文条件式', () => {
    // web.py 是组 G 独占文件；此锁直接钉住该行的写法形态。
    // 只查**代码行**：修复注释里会引用旧写法原文（那正是「就地改正 + 说明」的要求），
    // 注释行不算违规。
    const webPy = readFileSync(new URL('../../web.py', import.meta.url), 'utf8');
    const code = webPy.split('\n').filter(l => !l.trim().startsWith('#'));
    const line = code.find(l => l.includes('web_auth_enable='));
    assert.ok(line, 'web.py 未找到 web_auth_enable= 播报行');
    const rhs = line.slice(line.indexOf('web_auth_enable=') + 'web_auth_enable='.length);
    assert.doesNotMatch(rhs, /[\u4e00-\u9fff]/, `认证播报仍内联中文值: ${line.trim()}`);
    // 值必须来自 i18n.tr（本地化字面量），不能是裸布尔（会渲染成 True/False）
    assert.match(rhs, /i18n\.tr\(|_auth_text|^\s*\w+\s*$/, '认证播报的值未走本地化，其它语言下不可读');
});

// —— MIN-2237：前端 isSensitiveField 判定顺序必须与后端 is_sensitive_item 逐字对齐 ————

test('MIN-2237：敏感节命中必须优先于 NOT_SECRET_KEY_RE 例外（顺序与后端一致）', () => {
    // 失效形态：原实现把例外表提到最前短路
    //   if (NOT_SECRET_KEY_RE.test(key)) return false;
    //   return !!SENSITIVE_SECTIONS[section] || SENSITIVE_KEY_RE.test(key);
    // 而后端是 section in SENSITIVE_SECTIONS or is_sensitive_key(key)，例外只在 is_sensitive_key 内部
    // → `[Cookie] 抖音cookie有效期` 这类键后端脱敏、前端判非敏感并渲染成明文 text，用户误读成「没被保护」。
    // 断言顺序而非结果：节命中必须在例外之前返回 true。
    const fn = APP_JS.match(/function isSensitiveField\(section, key\) \{[\s\S]*?\n    \}/);
    assert.ok(fn, '未找到 isSensitiveField');
    const body = fn[0];
    const sectionIdx = body.indexOf('SENSITIVE_SECTIONS[section]');
    const notSecretIdx = body.indexOf('NOT_SECRET_KEY_RE.test(key)');
    assert.ok(sectionIdx >= 0 && notSecretIdx >= 0, 'isSensitiveField 缺少节判定或例外判定');
    assert.ok(sectionIdx < notSecretIdx,
        'isSensitiveField 的例外表仍在节判定之前短路 → 与后端 is_sensitive_item 顺序分叉');
});

// —— MID-2238：storage 访问必须走安全封装，init 不得因隐私模式整段中断 ————————————

test('MID-2238：app.js 不存在裸 localStorage/sessionStorage 访问（除封装内部）', () => {
    // 失效形态：initTheme() 是 DOMContentLoaded 回调第一条语句，裸 localStorage 在
    // Safari 无痕/「禁用站点数据」下抛异常 → 后续 tab、按钮、事件委托、引导监听器一个都不注册。
    // 锁法：白名单只有 _tokenStore/safeGetItem/safeSetItem 三个封装函数体允许直接接触 storage。
    const lines = APP_JS.split('\n');
    const offenders = [];
    let inWrapper = false;
    for (const [i, line] of lines.entries()) {
        const trimmed = line.trim();
        if (trimmed.startsWith('//')) continue;
        if (/^function\s+(_tokenStore|safeGetItem|safeSetItem)\s*\(/.test(trimmed)) inWrapper = true;
        else if (inWrapper && trimmed === '}') inWrapper = false;
        if (inWrapper) continue;
        if (/(?<![\w.])(localStorage|sessionStorage)\b/.test(line)
            && !/typeof\s+(localStorage|sessionStorage)/.test(line)) {
            offenders.push(`app.js:${i + 1}: ${trimmed}`);
        }
    }
    assert.deepEqual(offenders, [], '存在裸 storage 访问（隐私模式下会抛异常带走整个 init 回调）');
});

test('MID-2238：initTheme 与 initLanguage 各自 try/catch，单点失败不得带走后续绑定', () => {
    // 只要 initTheme 内部出现 try/catch，隐私模式下的 storage 异常就不会中断 DOMContentLoaded。
    const fn = APP_JS.match(/function initTheme\(\) \{[\s\S]*?\n    \}/);
    assert.ok(fn, '未找到 initTheme');
    assert.match(fn[0], /try\s*\{/, 'initTheme 未包 try/catch（storage 异常会中断整个 DOMContentLoaded）');
});

// —— MID-2239：PUT /api/language 必须消费生效码与回退说明 ————————————————

test('MID-2239：语言切换必须按响应里的 language（生效码）更新，不得回写请求值', () => {
    // 失效形态：`.then(function () { currentLang = target; ... })` —— 形参被丢掉、恒按请求值本地切换。
    // 后端可能回退（如 PyYAML 缺失使 zh_TW 装载不到 → 实际生效 en_US），前端必须以后端回的生效码为准。
    assert.match(APP_JS, /currentLang\s*=\s*\(res\s*&&\s*res\.language\)\s*\|\|\s*target/,
        '未按响应 language 生效码更新 currentLang');
    assert.match(APP_JS, /res\.fallback/, '未消费 fallback 标记，回退说明不会显示给用户');
    assert.match(APP_JS, /res\.notice/, '未消费后端返回的本地化回退说明 notice');
});

// —— MIN-2239：saveConfig 中途失败必须善后（不得留下「看起来已保存」的界面） ————————

test('MIN-2239：saveConfig 失败分支必须先回拉配置再返回，且标出失败行', () => {
    // 失效形态：失败即 `return`，跳过头注释要防的「半份配置落盘更难排查」——
    // 界面仍是用户填的样子、无任何未保存标记，用户以为已保存直接切走。
    const fn = APP_JS.match(/async function saveConfig\(\) \{[\s\S]*?\n    \}/);
    assert.ok(fn, '未找到 saveConfig');
    const body = fn[0];
    // 失败分支内必须有 await loadConfig()（在 return 之前）
    const catchIdx = body.indexOf("t('config.saveRejected')");
    assert.ok(catchIdx >= 0, 'saveConfig 缺少 400 专用文案分支（既有回归锁依赖它）');
    const after = body.slice(catchIdx);
    const returnIdx = after.indexOf('return;');
    assert.ok(returnIdx >= 0, 'saveConfig 失败分支缺少 return');
    assert.ok(after.slice(0, returnIdx).includes('await loadConfig()'),
        'saveConfig 失败分支未回拉服务端真值就 return → 界面停留在「看起来已保存」的假象');
    assert.ok(after.slice(0, returnIdx).includes('markRowFailed'),
        'saveConfig 失败分支未标出失败行 → 用户不知道哪一项没保存');
});

test('MIN-2239：index.html 提供常驻保存状态行 #config-save-status 且默认隐藏', () => {
    const idx = INDEX_HTML.indexOf('id="config-save-status"');
    assert.ok(idx >= 0, 'index.html 缺少 #config-save-status（常驻失败明细；toast 会消失且被覆盖）');
    assert.match(INDEX_HTML.slice(idx - 120, idx + 160), /hidden/, '#config-save-status 未默认隐藏');
});

// —— MIN-2238：downloadFile 失败必须解析 detail，不得用恒空的 statusText ————————

test('MIN-2238：downloadFile 失败分支不得使用 res.statusText（HTTP/2 下恒为空串）', () => {
    // 失效形态：`if (!res.ok) throw new Error(res.statusText)` →
    // 现代浏览器对 reason phrase 恒给空串，toast 渲染成「下载失败: 」，用户拿不到任何可报障信息。
    const fn = APP_JS.match(/window\.downloadFile = function \(path\) \{[\s\S]*?\n    \};/);
    assert.ok(fn, '未找到 downloadFile');
    const body = fn[0].split('\n').filter(l => !l.trim().startsWith('//')).join('\n');
    assert.doesNotMatch(body, /res\.statusText/, 'downloadFile 仍用 statusText 抛错（恒为空串）');
    assert.match(body, /apiError\(/, 'downloadFile 失败分支未复用 apiError 解析 detail');
});

// —— MID-2241：认证两键改动必须二次确认 + 复验口令 ————————————————

test('MID-2241：saveConfig 对 Web 认证两键先 confirm 再要求复验口令', () => {
    // 失效形态：这两键走与「循环时间(秒)」完全相同的普通写入通道，前后端都零确认——
    // 一次 PUT 即可关掉认证或改写口令（连带踢掉全部在线会话），且该降级不随 token 吊销回滚。
    const fn = APP_JS.match(/async function saveConfig\(\) \{[\s\S]*?\n    \}/);
    assert.ok(fn, '未找到 saveConfig');
    const body = fn[0];
    assert.match(body, /key === 'web_auth_enable' \|\| key === 'web_password'/,
        'saveConfig 未对认证两键做特殊处理（缺少确认/复验入口）');
    const guardIdx = body.search(/key === 'web_auth_enable'/);
    const confirmIdx = body.indexOf('confirm(t(\'config.authChangeConfirm\')', guardIdx);
    assert.ok(confirmIdx > guardIdx, '认证两键改动未弹二次确认');
    const promptIdx = body.indexOf('config.authChangeReauth', guardIdx);
    assert.ok(promptIdx > confirmIdx, '认证两键改动未要求复验口令');
    assert.match(body, /body\.reauth_password\s*=\s*\w+/, '复验口令未随请求下发');
    // 反向边界：其余键的请求体不得被污染（既有回归锁按整体 deepEqual 断言 body 形状）
    assert.match(body, /var body = \{ section: section, key: key, value: newVal \};/,
        '请求体基础形状被改动（会破坏其余配置键的既有请求契约）');
});

test('MID-2241：后端 update_config 不得对认证两键做**强制**复验（既有契约不可打死）', () => {
    // 2026-09-22 定稿形态：本条的防线落在前端二次确认（上一条用例），后端只接收 reauth_password
    // 而**不据它做准入判定**。曾一度把「认证当前开启 ⇒ 缺字段即 403」实现在 update_config 里，
    // 被 tests/test_web_api.py 的 10 个既有用例否决：
    //   TestAuthDowngradeRejected::test_downgrade_on_loopback_allowed、
    //   TestInsecureBindInvariantUsesRealAddress::test_two_step_sequence_allowed_when_real_bind_is_loopback、
    //   TestPasswordManagement::test_password_change_revokes_tokens / test_new_password_stored_hashed、
    //   TestSensitiveValueBlankRejected::test_mask_sensitive_value_rejected[Web-web_password-***]
    // 等（详情见 src/web_api.py::ConfigUpdate.reauth_password 注释）。
    // 本用例锁的是**不许回退到强复验**：一旦有人重新加回那段 403，这里立刻变红。
    assert.match(WEB_API_PY, /reauth_password:\s*str\s*\|\s*None\s*=\s*None/,
        'ConfigUpdate 缺少 reauth_password 可选字段（前端确认链的载荷载体）');
    const fn = WEB_API_PY.match(/def update_config\(req: ConfigUpdate\)[\s\S]*?\n    @app\.get\("\/api\/language"\)/);
    assert.ok(fn, '未找到 update_config');
    const body = fn[0];
    assert.doesNotMatch(body, /verify_web_password\(_reauth, _stored\)/,
        '后端又加回了强复验（会打死既有 test_web_api.py 契约，并让 web_password=*** 的 400 被 403 抢占）');
    assert.doesNotMatch(body, /修改认证配置需复验当前口令/,
        '后端强复验的 403 文案仍在 update_config 内');
});

// —— MIN-2241：根 index.html 的远端脚本必须钉内容（SRI），钉版本不足以挡替换 ————————

test('MIN-2241：根 index.html 的每个跨源 <script> 都带 integrity 与 crossorigin', () => {
    // 失效形态：只写 src="https://cdn.jsdelivr.net/npm/hls.js@1.7.2/..."。钉版本 ≠ 钉内容——
    // jsdelivr 上同名同版本的文件仍可被替换，而本页不经 web_api 的 CSP/nosniff 中间件
    // （create_app 只挂 web/index.html 与 /web），是唯一把用户输入流地址直喂 hls.js/flv.js 的页面。
    // 断言按**每个 script 标签**逐个检查，而不是全文件 grep：否则「一个标签有、另一个没有」
    // 会被整体命中蒙混过去（本条正是两处脚本各自失效的形态）。
    const scriptTags = ROOT_INDEX_HTML.match(/<script\b[^>]*\bsrc="https?:\/\/[^"]*"[^>]*>/g) || [];
    assert.ok(scriptTags.length > 0, '根 index.html 未找到任何跨源 script（选择器已漂移）');
    for (const tag of scriptTags) {
        assert.match(tag, /\sintegrity="sha(256|384|512)-[A-Za-z0-9+/=]+"/,
            `跨源脚本未钉内容（缺 integrity）: ${tag}`);
        assert.match(tag, /\scrossorigin=("anonymous"|"")/,
            `缺 crossorigin 会使 SRI 对跨源响应不生效: ${tag}`);
    }
});

test('MIN-2241：integrity 哈希必须是 sha384 且长度为真哈希，不得是占位串', () => {
    // 反向锁：把 integrity 写成 "sha384-x" 之类占位串能让上一条通过，却会让页面整段静默失效
    // （浏览器拒绝执行不匹配的脚本）。sha384 的 base64 定长为 64 字符。
    const hashes = ROOT_INDEX_HTML.match(/integrity="sha384-([A-Za-z0-9+/=]+)"/g) || [];
    assert.ok(hashes.length >= 2, `expected >=2 sha384 integrity, got ${hashes.length}`);
    for (const h of hashes) {
        const b64 = h.slice('integrity="sha384-'.length, -1);
        assert.equal(b64.length, 64, `sha384 base64 长度应为 64，实为 ${b64.length}: ${h}`);
        assert.match(b64, /^[A-Za-z0-9+/]+={0,2}$/, `不是合法 base64: ${h}`);
    }
});

test('MIN-2241：根 index.html 仍未被 Web 面板链路服务（修复不得把它挂进路由）', () => {
    // 反向边界：本条的处置是「保留独立工具页 + 补 SRI」，不是「把它接进面板」。
    // / 必须仍指向 web/index.html——若有人顺手把它改成项目根 index.html，
    // CSP/鉴权/同源判定全都会被绕开（这正是本条要防的另一半）。
    // src/web_api.py 是纯 CRLF（本机实测 1510/0），而 node 的 readFileSync(...,'utf8') 不做换行归一，
    // 故写死 `\n\n` 的「空行」锚点在 CRLF 源上恒不匹配（正是 AGENTS.md「注释检查工具的盲点 3」点名的
    // 现例，也是本用例此前恒红的根因）。改成 `\r?\n\r?\n` 让空行判定与行尾形态无关，无论检出的是
    // LF 还是 CRLF 都能定位到函数体结尾后的第一个空行。
    const idx = WEB_API_PY.match(/async def index\(\)[\s\S]*?\r?\n\r?\n/);
    assert.ok(idx, '未找到 / 路由');
    assert.match(idx[0], /_WEB_DIR\s*\/\s*"index\.html"/, '/ 未指向 web/index.html');
});
