// ============================================================
// TIMODA — Main JavaScript
// ============================================================

// Cart toast notification (called by HTMX hx-on::after-request)
function showCartToast(productName) {
  const toastEl = document.getElementById('cartToast');
  if (!toastEl) return;
  const msg = document.getElementById('cartToastMsg');
  if (msg && productName) msg.textContent = `«${productName}» добавлен в корзину`;
  const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 2500 });
  toast.show();
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

  // Show on link-click navigation
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('javascript') || a.target === '_blank') return;
    if (a.hasAttribute('hx-get') || a.hasAttribute('hx-post')) return;
    loader.classList.remove('done');
    // Safety: hide after 4s if new page doesn't load (e.g. download link)
    setTimeout(hide, 4000);
  });
})();

document.addEventListener('DOMContentLoaded', () => {
  initCardNavigation();

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
