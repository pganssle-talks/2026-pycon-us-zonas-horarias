// Intercepts the reveal.js speaker-view popup and injects a per-slide timer.
// The notes plugin generates the speaker view via document.write() on an
// about:blank popup, so we wrap window.open and patch the DOM after write.
(function () {
    var _open = window.open;
    window.open = function (url, name, features) {
        var win = _open.apply(this, arguments);
        if (name === 'reveal.js - Notes') {
            // document.write() is called synchronously after window.open returns,
            // so defer one tick to let the DOM settle.
            setTimeout(function () { patchSpeakerView(win); }, 0);
        }
        return win;
    };

    function patchSpeakerView(win) {
        var doc = win.document;
        var timeEl = doc.querySelector('.speaker-controls-time');
        if (!timeEl) {
            // Not ready yet — try again shortly.
            setTimeout(function () { patchSpeakerView(win); }, 50);
            return;
        }

        // If document.write() was skipped (popup reused as-is), remove stale DOM.
        var oldGrid = timeEl.querySelector('.time-grid');
        if (oldGrid) {
            var rt = oldGrid.querySelector('.timer');
            var rc = oldGrid.querySelector('.clock');
            if (rt) timeEl.appendChild(rt);
            if (rc) timeEl.appendChild(rc);
            oldGrid.remove();
        }
        var oldToggle = timeEl.querySelector('label');
        if (oldToggle) oldToggle.remove();

        // --- CSS ---
        if (!doc.head.querySelector('#slide-timer-style')) {
            var style = doc.createElement('style');
            style.id = 'slide-timer-style';
            style.textContent = [
                '.speaker-controls-time .time-grid {',
                '  display: grid;',
                '  grid-template-columns: 1fr 1fr 1fr;',
                '  align-items: baseline;',
                '  column-gap: 0.5em;',
                '}',
                '.speaker-controls-time .time-grid .clock { text-align: right; }',
                '.speaker-controls-time .timer,',
                '.speaker-controls-time .clock {',
                '  width: auto !important;',
                '  float: none !important;',
                '}',
                '.speaker-controls-time .slide-timer { font-size: 1.9em; }',
                /* Scrolling container is #speaker-controls; hide overflow and make it
                   a container-query root so cqh units work in descendants. */
                '#speaker-controls { overflow: hidden !important; container-type: size; }',
                /* Font size driven by --notes-size (set in cqh by fitNotes) so it
                   automatically re-scales whenever the container changes size. */
                '.speaker-controls-notes .value { font-size: var(--notes-size, 1.2em); }',
            ].join('\n');
            doc.head.appendChild(style);
        }

        // --- DOM: wrap timer+clock in a grid, insert slide-timer column ---
        var timerDiv = timeEl.querySelector('.timer');
        var clockDiv = timeEl.querySelector('.clock');
        var oldLabel = timeEl.querySelector('h4.label:not(.pacing-title)');
        var clearDiv = timeEl.querySelector('.clear');
        if (oldLabel) oldLabel.remove();
        if (clearDiv)  clearDiv.remove();

        function mkLabel(text, withReset) {
            var h = doc.createElement('h4');
            h.className = 'label';
            h.textContent = text;
            if (withReset) {
                var span = doc.createElement('span');
                span.className = 'reset-button';
                span.textContent = 'Click to Reset';
                h.appendChild(span);
            }
            return h;
        }

        var minsEl = doc.createElement('span');
        minsEl.className = 'slide-minutes-value';
        minsEl.textContent = '00';
        var secsEl = doc.createElement('span');
        secsEl.className = 'slide-seconds-value';
        secsEl.textContent = ':00';
        var slideTimerDiv = doc.createElement('div');
        slideTimerDiv.className = 'slide-timer';
        slideTimerDiv.appendChild(minsEl);
        slideTimerDiv.appendChild(secsEl);

        var slideTimerLabel = mkLabel('Slide Time', true);

        var grid = doc.createElement('div');
        grid.className = 'time-grid';
        grid.appendChild(slideTimerLabel);
        grid.appendChild(mkLabel('Time', false));
        grid.appendChild(doc.createElement('div')); // clock column: no label
        grid.appendChild(slideTimerDiv);
        grid.appendChild(timerDiv); // moves the existing element
        grid.appendChild(clockDiv); // moves the existing element
        timeEl.insertBefore(grid, timeEl.firstChild);

        // --- Slide timer toggle checkbox ---
        var showTimer = (win.localStorage.getItem('showSlideTimer') !== 'false');

        function applyTimerVisibility(show) {
            slideTimerLabel.style.display = show ? '' : 'none';
            slideTimerDiv.style.display   = show ? '' : 'none';
            grid.style.gridTemplateColumns = show ? '1fr 1fr 1fr' : '1fr 1fr';
        }
        applyTimerVisibility(showTimer);

        var toggleLabel = doc.createElement('label');
        toggleLabel.style.cssText = 'display:flex; align-items:center; gap:0.4em; font-size:0.75em; margin-top:0.4em; cursor:pointer; user-select:none;';
        var toggleBox = doc.createElement('input');
        toggleBox.type = 'checkbox';
        toggleBox.checked = showTimer;
        toggleBox.addEventListener('change', function () {
            win.localStorage.setItem('showSlideTimer', toggleBox.checked ? 'true' : 'false');
            applyTimerVisibility(toggleBox.checked);
        });
        toggleLabel.appendChild(toggleBox);
        toggleLabel.appendChild(doc.createTextNode('Show slide timer'));
        timeEl.appendChild(toggleLabel);

        // --- Inject timer + notes-fit script into the popup's own JS context ---
        // Running as a <script> element means the interval and message listener
        // belong to the popup window, not the main page. They survive a main-page
        // refresh without needing to be re-injected.
        // window._slideTimerPatch stores handles so each injection cleans up the
        // previous one (handles popup close+reopen, or document.write refresh).
        var timerScript = doc.createElement('script');
        timerScript.textContent = [
            '(function () {',
            '  var prev = window._slideTimerPatch;',
            '  if (prev) {',
            '    clearInterval(prev.interval);',
            '    window.removeEventListener("message", prev.msgFn);',
            '    var pte = document.querySelector(".speaker-controls-time");',
            '    if (pte && prev.clickFn) pte.removeEventListener("click", prev.clickFn);',
            '    if (prev.ro) prev.ro.disconnect();',
            '  }',
            '',
            '  function zeroPad(n) { return ("0" + n).slice(-2); }',
            '',
            '  // Shrink notes font to fit #speaker-controls when it overflows.',
            '  // Result stored as cqh units so it scales automatically on container resize.',
            '  // Never grows beyond the CSS default size.',
            '  function fitNotes() {',
            '    var speaker = document.querySelector("#speaker-controls");',
            '    var notes   = document.querySelector(".speaker-controls-notes");',
            '    var value   = document.querySelector(".speaker-controls-notes .value");',
            '    if (!speaker || !notes || !value || notes.classList.contains("hidden")) return;',
            '    speaker.style.removeProperty("--notes-size");',
            '    if (speaker.scrollHeight <= speaker.clientHeight) return;',
            '    var h = speaker.clientHeight;',
            '    if (!h) return;',
            '    var defaultPx = parseFloat(window.getComputedStyle(value).fontSize);',
            '    function toCqh(p) { return (p / (h / 100)).toFixed(3) + "cqh"; }',
            '    var lo = 8, hi = defaultPx, best = lo;',
            '    for (var i = 0; i < 12; i++) {',
            '      var mid = (lo + hi) / 2;',
            '      speaker.style.setProperty("--notes-size", toCqh(mid));',
            '      if (speaker.scrollHeight <= speaker.clientHeight) { best = mid; lo = mid; }',
            '      else { hi = mid; }',
            '    }',
            '    speaker.style.setProperty("--notes-size", toCqh(best));',
            '  }',
            '',
            '  var slideStart = new Date(), lastH = -1, lastV = -1;',
            '  var msgFn = function (ev) {',
            '    try {',
            '      var d = JSON.parse(ev.data);',
            '      if (d && d.namespace === "reveal-notes" && d.type === "state" && d.state) {',
            '        if (d.state.indexh !== lastH || d.state.indexv !== lastV) {',
            '          slideStart = new Date();',
            '          lastH = d.state.indexh; lastV = d.state.indexv;',
            '        }',
            '        setTimeout(fitNotes, 0);',
            '      }',
            '    } catch (e) {}',
            '  };',
            '  window.addEventListener("message", msgFn);',
            '',
            '  var clickFn = function () { slideStart = new Date(); };',
            '  var te = document.querySelector(".speaker-controls-time");',
            '  if (te) te.addEventListener("click", clickFn);',
            '',
            '  var interval = setInterval(function () {',
            '    var s = Math.floor((Date.now() - slideStart) / 1000);',
            '    var m = document.querySelector(".slide-minutes-value");',
            '    var e = document.querySelector(".slide-seconds-value");',
            '    if (m) m.textContent = zeroPad(Math.floor(s / 60));',
            '    if (e) e.textContent = ":" + zeroPad(s % 60);',
            '  }, 1000);',
            '',
            '  // Re-fit when the window is resized or the layout dropdown changes.',
            '  var ro = null;',
            '  var spk = document.querySelector("#speaker-controls");',
            '  if (spk && window.ResizeObserver) {',
            '    ro = new ResizeObserver(fitNotes);',
            '    ro.observe(spk);',
            '  }',
            '  var layoutSel = document.querySelector("#speaker-layout select");',
            '  if (layoutSel) layoutSel.addEventListener("change", function () { setTimeout(fitNotes, 50); });',
            '',
            '  window._slideTimerPatch = { interval: interval, msgFn: msgFn, clickFn: clickFn, ro: ro };',
            '',
            '  setTimeout(fitNotes, 100);',
            '})();',
        ].join('\n');
        doc.head.appendChild(timerScript);
    }
})();
