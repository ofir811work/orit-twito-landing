// Reveal on scroll
const io = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('in'), (e.target.dataset.d || 0));
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach((el, i) => {
  if (el.classList.contains('card')) el.dataset.d = (i % 3) * 120;
  io.observe(el);
});

// Count-up number
const counter = document.querySelector('.count');
if (counter) {
  new IntersectionObserver((en, ob) => {
    if (!en[0].isIntersecting) return;
    const to = +counter.dataset.to; let n = 0;
    const t = setInterval(() => { counter.textContent = ++n; if (n >= to) clearInterval(t); }, 90);
    ob.disconnect();
  }, { threshold: 0.6 }).observe(counter);
}

// Slow floating hearts
const box = document.getElementById('hearts');
if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
  for (let i = 0; i < 12; i++) {
    const h = document.createElement('span');
    h.textContent = i % 3 ? '🤍' : '💗';
    h.style.left = Math.random() * 100 + '%';
    h.style.fontSize = 12 + Math.random() * 16 + 'px';
    h.style.animationDuration = 14 + Math.random() * 14 + 's';
    h.style.animationDelay = -Math.random() * 20 + 's';
    h.style.setProperty('--dx', (Math.random() * 80 - 40) + 'px');
    box.appendChild(h);
  }
}
