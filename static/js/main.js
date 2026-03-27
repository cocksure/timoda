// ============================================================
// TIMODA — Main JavaScript
// ============================================================

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

    const speed = 0.45; // px per frame — slow, like water current
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

// Cart toast notification
function showCartToast(productName) {
  const toastEl = document.getElementById('cartToast');
  if (!toastEl) return;
  const msg = document.getElementById('cartToastMsg');
  if (msg && productName) msg.textContent = `«${productName}» добавлен в корзину`;
  const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 2500 });
  toast.show();
}

// Called after successful cart add on product detail page
function onCartAdded(evt, productName, cartUrl) {
  if (!evt.detail.successful) return;

  // 1. Toast
  showCartToast(productName);

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
    // Prevent form submit while in "in-cart" state
    btn.closest('form')?.addEventListener('submit', e => e.preventDefault(), { once: false });
  }

  // 3. Shake cart icon (after HTMX swap the icon is re-rendered)
  setTimeout(() => {
    const icon = document.querySelector('.cart-icon-btn i');
    if (icon) {
      icon.classList.remove('cart-icon-shake');
      void icon.offsetWidth; // force reflow so animation restarts
      icon.classList.add('cart-icon-shake');
      setTimeout(() => icon.classList.remove('cart-icon-shake'), 600);
    }
  }, 80);
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

document.addEventListener('DOMContentLoaded', () => {
  initCardNavigation();
  initRailAutoScroll();
  initScrollReveal();
  initDropdownBlur();

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

  // HTMX error fallback: if request fails, do a regular redirect to cart
  document.body.addEventListener('htmx:sendError', (e) => {
    if (e.target.closest('.quick-add-form')) {
      e.target.closest('form').submit();
    }
  });

});
