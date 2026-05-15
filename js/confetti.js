(function () {
    function fireConfetti() {
        var cw = window.innerWidth, ch = window.innerHeight;
        var canvas = document.createElement('canvas');
        canvas.width = cw;
        canvas.height = ch;
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
        document.body.appendChild(canvas);
        var ctx = canvas.getContext('2d');

        var colors = ['#f44336','#e91e63','#9c27b0','#3f51b5','#2196f3','#00bcd4','#4caf50','#ffeb3b','#ff9800','#ff5722'];
        var particles = [];

        for (var i = 0; i < 220; i++) {
            var angle = Math.random() * Math.PI * 2;
            var speed = Math.random() * 14 + 3;
            particles.push({
                x: cw / 2,
                y: ch / 2,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 10,
                color: colors[Math.floor(Math.random() * colors.length)],
                w: Math.random() * 10 + 5,
                h: Math.random() * 5 + 3,
                angle: Math.random() * Math.PI * 2,
                spin: (Math.random() - 0.5) * 0.4,
            });
        }

        var emoji = document.createElement('div');
        emoji.textContent = '🎉';
        emoji.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);font-size:7vw;pointer-events:none;z-index:10000;transition:opacity 1s;';
        document.body.appendChild(emoji);
        setTimeout(function () { emoji.style.opacity = '0'; }, 500);
        setTimeout(function () { emoji.remove(); }, 500);

        var start = Date.now();
        var fadeStart = 2500, fadeDuration = 1000;

        function step() {
            var elapsed = Date.now() - start;
            ctx.clearRect(0, 0, cw, ch);
            var alive = false;
            for (var i = 0; i < particles.length; i++) {
                var p = particles[i];
                p.vy += 0.3;
                p.vx *= 0.99;
                p.x += p.vx;
                p.y += p.vy;
                p.angle += p.spin;
                if (p.y > ch + 20) continue;
                alive = true;
                var alpha = elapsed < fadeStart ? 1 : Math.max(0, 1 - (elapsed - fadeStart) / fadeDuration);
                ctx.save();
                ctx.globalAlpha = alpha;
                ctx.fillStyle = p.color;
                ctx.translate(p.x, p.y);
                ctx.rotate(p.angle);
                ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
                ctx.restore();
            }
            if (alive && elapsed < fadeStart + fadeDuration) {
                requestAnimationFrame(step);
            } else {
                canvas.remove();
            }
        }
        requestAnimationFrame(step);
    }

    var revealEl = document.querySelector('.reveal');
    if (revealEl) {
        revealEl.addEventListener('fragmentshown', function (ev) {
            if (ev.fragment && ev.fragment.classList.contains('confetti-trigger')) {
                fireConfetti();
            }
        });
    }
})();
