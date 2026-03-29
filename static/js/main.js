// ============================================================
// TIMODA — Main JavaScript
// ============================================================

// Quick View modal
function openQuickView(url) {
  const modal = document.getElementById('quickViewModal');
  const body = document.getElementById('quickViewBody');
  if (!modal || !body) return;

  // Reset to spinner
  body.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-muted" role="status"></div></div>';

  // Show modal
  const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
  bsModal.show();

  // Fetch content
  fetch(url, { headers: { 'HX-Request': 'true' } })
    .then(r => r.text())
    .then(html => {
      body.innerHTML = html;
      // Init tooltips inside modal
      body.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
      });
      // Handle add-to-cart form inside modal
      const form = body.querySelector('.quick-add-form');
      if (form) {
        form.addEventListener('submit', async function(e) {
          e.preventDefault();
          const btn = form.querySelector('button[type="submit"]');
          btn.disabled = true;
          try {
            const resp = await fetch(form.action, {
              method: 'POST',
              body: new FormData(form),
              headers: { 'HX-Request': 'true' }
            });
            if (resp.ok) {
              const cartHtml = await resp.text();
              const cartWrap = document.getElementById('cart-icon-wrap');
              if (cartWrap) cartWrap.outerHTML = cartHtml;
              btn.innerHTML = '<i class="bi bi-bag-check-fill me-2"></i>В корзине';
              btn.classList.remove('btn-add-to-cart');
              btn.classList.add('btn-card-cart-added');
              btn.style.background = '#2d7a3a';
              bounceCartBadge();
            } else {
              btn.disabled = false;
            }
          } catch(err) {
            btn.disabled = false;
          }
        });
      }
    })
    .catch(() => {
      body.innerHTML = '<p class="text-center text-muted py-4">Ошибка загрузки</p>';
    });
}

// Theme & Scale settings
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('timoda_theme', theme);
  document.querySelectorAll('.theme-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.theme === theme);
  });
  updateThemeIcons(theme);
}

function toggleTheme() {
  const current = localStorage.getItem('timoda_theme') || 'light';
  setTheme(current === 'dark' ? 'light' : 'dark');
}

function updateThemeIcons(theme) {
  document.querySelectorAll('#themeIconDesktop, #themeIconMobile').forEach(icon => {
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
    }
  });
}

function setScale(scale) {
  document.documentElement.setAttribute('data-scale', scale);
  localStorage.setItem('timoda_scale', scale);
  document.querySelectorAll('.scale-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.scale === scale);
  });
}

// Sync settings buttons & icons on page load
function initSettingsButtons() {
  const theme = localStorage.getItem('timoda_theme') || 'light';
  const scale = localStorage.getItem('timoda_scale') || 'medium';
  document.querySelectorAll('.theme-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.theme === theme);
  });
  document.querySelectorAll('.scale-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.scale === scale);
  });
  updateThemeIcons(theme);
}

// Cart badge bounce animation
function bounceCartBadge() {
  // Delay slightly — after outerHTML swap the new element needs to be in DOM
  setTimeout(() => {
    document.querySelectorAll('.cart-badge, .mob-cart-badge').forEach(badge => {
      badge.classList.remove('badge-bounce');
      void badge.offsetWidth;
      badge.classList.add('badge-bounce');
      setTimeout(() => badge.classList.remove('badge-bounce'), 600);
    });
  }, 50);
}

// Products rail marquee (manual jump, used by rail buttons)
function railScroll(btn, dir) {
  const rail = btn.closest('.products-rail-wrap').querySelector('.products-rail');
  const itemWidth = rail.querySelector('.rail-item')?.offsetWidth || 260;
  // Instantly shift scrollLeft so the marquee jumps forward/back
  rail.scrollLeft += dir * (itemWidth + 16) * 2;
}

// Auto-scroll: continuous marquee like a ticker tape
function initRailAutoScroll() {
  document.querySelectorAll('.products-rail').forEach(rail => {
    const wrap = rail.closest('.products-rail-wrap');
    if (!wrap) return;

    const origItems = Array.from(rail.querySelectorAll('.rail-item'));
    if (origItems.length < 2) return;

    // Duplicate items so the loop is seamless
    origItems.forEach(item => {
      const clone = item.cloneNode(true);
      clone.setAttribute('aria-hidden', 'true');
      rail.appendChild(clone);
    });

    const speed = window.innerWidth < 992 ? 0.7 : 0.45;
    let paused = false;
    let origWidth = 0;

    function measure() {
      // gap is 16px between items
      origWidth = origItems.reduce((sum, item) => sum + item.offsetWidth + 16, 0);
    }
    measure();
    window.addEventListener('resize', measure, { passive: true });

    (function step() {
      if (!paused && origWidth > 0) {
        rail.scrollLeft += speed;
        // Seamless reset: when we've scrolled past originals, jump back
        if (rail.scrollLeft >= origWidth) {
          rail.scrollLeft -= origWidth;
        }
      }
      requestAnimationFrame(step);
    })();

    // Pause on hover
    wrap.addEventListener('mouseenter', () => { paused = true; });
    wrap.addEventListener('mouseleave', () => { paused = false; });

    // Pause on touch, resume 2s after finger lifts
    rail.addEventListener('touchstart', () => { paused = true; }, { passive: true });
    rail.addEventListener('touchend',   () => { setTimeout(() => { paused = false; }, 2000); }, { passive: true });
  });
}

// Called after successful cart add on product detail page
function onCartAdded(evt, productName, cartUrl) {
  if (!evt.detail.successful) return;

  // 1. Fly-to-cart effect
  const img = document.querySelector('.product-gallery-main-img');
  if (img) flyToCart(img);

  // Update local cart state so variant selector works correctly
  if (window.CART_VARIANT_IDS && window.getVariantId) {
    const vid = window.getVariantId();
    if (vid) window.CART_VARIANT_IDS.add(vid);
  }

  // 2. Button → "Перейти в корзину"
  const btn = document.getElementById('add-cart-btn');
  if (btn) {
    btn.type = 'button';
    btn.classList.add('btn-in-cart');
    btn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Перейти в корзину';
    btn.onclick = () => { window.location.href = cartUrl; };
    btn.closest('form')?.addEventListener('submit', e => e.preventDefault(), { once: false });
  }
}

// Product card left/right zone navigation
function initCardNavigation() {
  document.querySelectorAll('.product-card-img-wrap').forEach(wrap => {
    const dots = Array.from(wrap.querySelectorAll('.card-img-dot'));
    if (!dots.length) return;
    const mainImg = wrap.querySelector('.product-card-img');
    if (!mainImg) return;
    const srcs = dots.map(d => d.dataset.src);
    let current = 0;

    function goTo(idx) {
      current = (idx + srcs.length) % srcs.length;
      mainImg.style.opacity = '0';
      setTimeout(() => {
        mainImg.src = srcs[current];
        mainImg.style.opacity = '1';
      }, 160);
      dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }

    wrap.querySelector('.card-nav-prev')?.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); goTo(current - 1);
    });
    wrap.querySelector('.card-nav-next')?.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); goTo(current + 1);
    });
    dots.forEach((dot, i) => {
      dot.addEventListener('click', e => {
        e.preventDefault(); e.stopPropagation(); goTo(i);
      });
    });
  });
}

// Page loader
(function () {
  const loader = document.getElementById('page-loader');
  if (!loader) return;

  function hide() { loader.classList.add('done'); }

  // Hide on DOMContentLoaded — HTML parsed, DOM ready, don't wait for images
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hide);
  } else {
    // readyState is already 'interactive' or 'complete'
    hide();
  }

  // Fix bfcache: when browser restores page via Back button, hide loader immediately
  window.addEventListener('pageshow', e => {
    if (e.persisted) hide();
  });

  // Show on link-click navigation
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('javascript') || a.target === '_blank') return;
    if (a.hasAttribute('hx-get') || a.hasAttribute('hx-post')) return;
    if (a.getAttribute('data-bs-toggle') === 'dropdown') return;
    loader.classList.remove('done');
    // Safety: hide after 4s if new page doesn't load (e.g. download link)
    setTimeout(hide, 4000);
  });
})();

// Fade-in cards as they scroll into view
function initScrollReveal() {
  const cards = document.querySelectorAll('.product-card');
  if (!cards.length || !('IntersectionObserver' in window)) return;

  cards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(22px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const card = entry.target;
      // small stagger based on position in row
      const delay = (Array.from(card.parentElement?.children || []).indexOf(card) % 4) * 60;
      setTimeout(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
        // hand control back to CSS hover after animation
        setTimeout(() => {
          card.style.transition = '';
          card.style.opacity = '';
          card.style.transform = '';
        }, 520);
      }, delay);
      observer.unobserve(card);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -16px 0px' });

  cards.forEach(card => observer.observe(card));
}

function initDropdownBlur() {
  const overlay = document.createElement('div');
  overlay.id = 'dropdown-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;z-index:999;backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);background:rgba(0,0,0,.18);opacity:0;pointer-events:none;transition:opacity .2s ease';
  document.body.appendChild(overlay);

  let justShown = false;

  document.querySelectorAll('.navbar .dropdown').forEach(dropdown => {
    dropdown.addEventListener('show.bs.dropdown', () => {
      justShown = true;
      overlay.style.pointerEvents = 'auto';
      overlay.style.opacity = '1';
      setTimeout(() => { justShown = false; }, 100);
    });
    dropdown.addEventListener('hide.bs.dropdown', () => {
      if (!justShown) {
        overlay.style.opacity = '0';
        overlay.style.pointerEvents = 'none';
      }
    });
  });

  overlay.addEventListener('click', () => {
    document.querySelectorAll('.navbar .dropdown-menu.show').forEach(menu => {
      bootstrap.Dropdown.getOrCreateInstance(menu.previousElementSibling)?.hide();
    });
  });
}

// Floating hearts particles
function spawnHearts(anchor) {
  const rect = anchor.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  for (let i = 0; i < 6; i++) {
    const heart = document.createElement('span');
    heart.textContent = '\u2764';
    heart.className = 'floating-heart';
    heart.style.left = cx + 'px';
    heart.style.top = cy + 'px';
    heart.style.setProperty('--dx', (Math.random() - 0.5) * 60 + 'px');
    heart.style.setProperty('--dy', -(30 + Math.random() * 40) + 'px');
    heart.style.animationDelay = (i * 0.06) + 's';
    document.body.appendChild(heart);
    setTimeout(() => heart.remove(), 900);
  }
}

// Heart icon pop on favorite toggle
function initFavEffects() {
  document.body.addEventListener('htmx:afterSwap', e => {
    const btn = e.target.closest?.('.btn-fav, .btn-fav-detail') || e.target;
    if (!btn.classList.contains('btn-fav') && !btn.classList.contains('btn-fav-detail')) return;
    if (!btn.classList.contains('active')) return;

    // Icon bounce
    const icon = btn.querySelector('i');
    if (icon) {
      icon.classList.remove('animate');
      void icon.offsetWidth;
      icon.classList.add('animate');
      setTimeout(() => icon.classList.remove('animate'), 600);
    }

    // Button flash ring / bg
    btn.classList.remove('flash');
    void btn.offsetWidth;
    btn.classList.add('flash');
    setTimeout(() => btn.classList.remove('flash'), 650);

    // Floating hearts particles
    spawnHearts(btn);
  });

  // On favorites page: remove card when unfavorited
  document.body.addEventListener('htmx:afterSwap', e => {
    const btn = e.target.closest?.('.btn-fav') || e.target;
    if (!btn.classList.contains('btn-fav')) return;
    if (btn.classList.contains('active')) return; // added, not removed
    if (!window.location.pathname.includes('favorites')) return;

    const card = btn.closest('.col-6, .col-md-4, .col-xl-3');
    if (card) {
      card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      card.style.opacity = '0';
      card.style.transform = 'scale(0.9)';
      setTimeout(() => card.remove(), 320);
    }
  });
}

// Quick-add button effect + prevent double-add
function initQuickAddEffect() {
  document.body.addEventListener('htmx:afterOnLoad', e => {
    const elt = e.detail.elt;
    if (!elt || !elt.classList?.contains('quick-add-form')) return;

    const btn = elt.querySelector('.btn-card-cart, .btn-quick-add');
    if (!btn || btn.dataset.added) return;

    // Mark as added — prevent further clicks
    btn.dataset.added = 'true';
    btn.innerHTML = '<i class="bi bi-bag-check-fill me-1"></i>В корзине';
    btn.classList.add('btn-card-cart-added');
    btn.disabled = true;

    // Bounce cart badge
    bounceCartBadge();

    // Also update mobile cart badge
    const mobileBadge = document.querySelector('.mob-nav-item .mob-cart-badge');
    const mobileCartLink = document.querySelector('.mob-nav-item [class*="bi-bag"]')?.closest('a');
    if (mobileBadge) {
      mobileBadge.textContent = parseInt(mobileBadge.textContent || '0') + 1;
      mobileBadge.classList.add('badge-bounce');
      setTimeout(() => mobileBadge.classList.remove('badge-bounce'), 500);
    } else if (mobileCartLink) {
      const badge = document.createElement('span');
      badge.className = 'mob-cart-badge badge-bounce';
      badge.textContent = '1';
      mobileCartLink.appendChild(badge);
    }
  });
}

// Search autocomplete
function initSearchAutocomplete() {
  const pairs = [
    ['searchInput', 'searchDropdown'],
    ['searchInputMobile', 'searchDropdownMobile'],
  ];
  pairs.forEach(([inputId, dropdownId]) => {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;

    let timer = null;
    let activeIdx = -1;

    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { dropdown.innerHTML = ''; dropdown.classList.remove('open'); return; }
      timer = setTimeout(() => {
        fetch(`/products/search-suggest/?q=${encodeURIComponent(q)}`)
          .then(r => r.json())
          .then(items => {
            activeIdx = -1;
            if (!items.length) {
              dropdown.innerHTML = '<div class="search-no-results">Ничего не найдено</div>';
              dropdown.classList.add('open');
              return;
            }
            dropdown.innerHTML = items.map((item, i) => `
              <a href="${item.url}" class="search-item" data-idx="${i}">
                ${item.image ? `<img src="${item.image}" alt="" class="search-item-img">` : ''}
                <div class="search-item-info">
                  <span class="search-item-name">${item.name}</span>
                  <span class="search-item-meta">${item.category} &middot; ${Number(item.price).toLocaleString('ru')} сум</span>
                </div>
              </a>
            `).join('');
            dropdown.classList.add('open');
          });
      }, 300);
    });

    // Keyboard navigation
    input.addEventListener('keydown', e => {
      const items = dropdown.querySelectorAll('.search-item');
      if (!items.length) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeIdx = Math.min(activeIdx + 1, items.length - 1);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeIdx = Math.max(activeIdx - 1, 0);
      } else if (e.key === 'Enter' && activeIdx >= 0) {
        e.preventDefault();
        items[activeIdx].click();
        return;
      } else if (e.key === 'Escape') {
        dropdown.innerHTML = ''; dropdown.classList.remove('open');
        return;
      } else { return; }
      items.forEach((el, i) => el.classList.toggle('active', i === activeIdx));
      items[activeIdx]?.scrollIntoView({ block: 'nearest' });
    });

    // Close on click outside
    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.innerHTML = ''; dropdown.classList.remove('open');
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initCardNavigation();
  initRailAutoScroll();
  initScrollReveal();
  initDropdownBlur();
  initFavEffects();
  initQuickAddEffect();
  initSearchAutocomplete();
  initSettingsButtons();

  // Chrome blocks autoplay unless muted is set programmatically too
  document.querySelectorAll('video[autoplay]').forEach(v => {
    v.muted = true;
    v.play().catch(() => {});
  });

  // Initialize Bootstrap tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // Auto-dismiss alerts after 4s
  setTimeout(() => {
    document.querySelectorAll('.alert.fade.show').forEach(alert => {
      bootstrap.Alert.getOrCreateInstance(alert)?.close();
    });
  }, 4000);

  // Navbar scroll shadow
  const nav = document.querySelector('.main-nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.style.boxShadow = window.scrollY > 10 ? '0 2px 16px rgba(0,0,0,.08)' : 'none';
    }, { passive: true });
  }

  // HTMX after-swap: re-init tooltips
  document.body.addEventListener('htmx:afterSwap', () => {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      new bootstrap.Tooltip(el);
    });
  });

  // After review submitted via HTMX, reload to show the new review
  document.body.addEventListener('htmx:afterSwap', e => {
    if (e.target.closest('.review-form-card')) {
      setTimeout(() => location.reload(), 1200);
    }
  });

  // HTMX error fallback: if request fails, do a regular redirect to cart
  document.body.addEventListener('htmx:sendError', (e) => {
    if (e.target.closest('.quick-add-form')) {
      e.target.closest('form').submit();
    }
  });

});
