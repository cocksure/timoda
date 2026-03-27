// ============================================================
// Product Detail page
// Depends on window.VARIANT_MAP, STOCK_MAP, COLOR_IMAGE_MAP,
// ADD_CART_BASE, CART_VARIANT_IDS, CART_URL — set in template
// ============================================================

function changeQty(delta) {
  const input = document.getElementById('quantity');
  const val = parseInt(input.value) + delta;
  if (val >= 1 && val <= 99) input.value = val;
}

function setMainImage(url) {
  const mainImg = document.getElementById('mainImage');
  if (!mainImg || mainImg.src.endsWith(url)) return;
  mainImg.style.opacity = '0';
  setTimeout(() => { mainImg.src = url; mainImg.style.opacity = '1'; }, 150);
}

function selectGalleryThumb(thumbEl, url) {
  setMainImage(url);
  document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
  thumbEl.classList.add('active');
}

function switchGalleryToColor(colorId) {
  const colorStr = String(colorId);
  const thumbs = Array.from(document.querySelectorAll('.gallery-thumb'));
  if (!thumbs.length) return;
  thumbs.forEach(t => t.classList.remove('color-match'));
  const colorThumbs = thumbs.filter(t => t.dataset.color === colorStr);
  if (!colorThumbs.length) return;
  colorThumbs.forEach(t => t.classList.add('color-match'));
  colorThumbs[0].classList.add('active');
  thumbs.filter(t => !colorThumbs.includes(t)).forEach(t => t.classList.remove('active'));
  colorThumbs[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
  const firstImg = colorThumbs[0].querySelector('img');
  if (firstImg) setMainImage(firstImg.src);
}

window.getVariantId = function () {
  const sizeId  = parseInt(document.querySelector('.size-radio:checked')?.value) || null;
  const colorId = parseInt(document.querySelector('.color-radio:checked')?.value) || null;
  if (sizeId && colorId && window.VARIANT_MAP[sizeId]?.[colorId]) return window.VARIANT_MAP[sizeId][colorId];
  if (sizeId && window.VARIANT_MAP[sizeId]) return Object.values(window.VARIANT_MAP[sizeId])[0];
  if (Object.keys(window.VARIANT_MAP).length) return Object.values(Object.values(window.VARIANT_MAP)[0])[0];
  return null;
};

function updateStockInfo() {
  const el = document.getElementById('stock-info');
  if (!el) return;
  const variantId = window.getVariantId();
  if (variantId === null || window.STOCK_MAP[variantId] === undefined) { el.innerHTML = ''; return; }
  const stock = window.STOCK_MAP[variantId];
  if (stock === 0) {
    el.innerHTML = '<span class="stock-badge stock-none"><i class="bi bi-x-circle me-1"></i>Нет в наличии</span>';
  } else if (stock <= 5) {
    el.innerHTML = `<span class="stock-badge stock-low"><i class="bi bi-exclamation-circle me-1"></i>Осталось: ${stock} шт. — торопитесь!</span>`;
  } else {
    el.innerHTML = `<span class="stock-badge stock-ok"><i class="bi bi-check-circle me-1"></i>В наличии: ${stock} шт.</span>`;
  }
}

function updateCartFormAction() {
  const btn  = document.getElementById('add-cart-btn');
  const form = document.getElementById('add-to-cart-form');
  if (!form || !btn) return;
  const variantId = window.getVariantId();

  if (variantId) {
    form.action = `${window.ADD_CART_BASE}${variantId}/`;
    if (window.STOCK_MAP[variantId] === 0) {
      btn.disabled = true; btn.type = 'submit'; btn.onclick = null;
      btn.classList.remove('btn-in-cart');
      btn.innerHTML = 'Нет в наличии';
    } else if (window.CART_VARIANT_IDS.has(variantId)) {
      btn.disabled = false; btn.type = 'button';
      btn.classList.add('btn-in-cart');
      btn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Перейти в корзину';
      btn.onclick = () => { window.location.href = window.CART_URL; };
    } else {
      btn.disabled = false; btn.type = 'submit'; btn.onclick = null;
      btn.classList.remove('btn-in-cart');
      btn.innerHTML = '<i class="bi bi-bag-plus me-2"></i>Добавить в корзину';
    }
  } else {
    btn.disabled = true;
    btn.classList.remove('btn-in-cart');
    btn.innerHTML = 'Нет в наличии';
  }
  updateStockInfo();
}

// Add to cart via fetch (correct variant URL, no HTMX quirks)
document.getElementById('add-to-cart-form')?.addEventListener('submit', async function (e) {
  e.preventDefault();
  const variantId = window.getVariantId();
  if (!variantId || window.STOCK_MAP[variantId] === 0) return;

  const btn = document.getElementById('add-cart-btn');
  btn.disabled = true;
  const url = `${window.ADD_CART_BASE}${variantId}/`;

  try {
    const resp = await fetch(url, {
      method: 'POST',
      body: new FormData(this),
      headers: { 'HX-Request': 'true' }
    });
    if (resp.ok) {
      const html = await resp.text();
      const cartWrap = document.getElementById('cart-icon-wrap');
      if (cartWrap) cartWrap.outerHTML = html;
      window.CART_VARIANT_IDS.add(variantId);
      btn.disabled = false; btn.type = 'button';
      btn.classList.add('btn-in-cart');
      btn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Перейти в корзину';
      btn.onclick = () => { window.location.href = window.CART_URL; };
      showCartToast(this.dataset.productName);
      setTimeout(() => {
        const icon = document.querySelector('.cart-icon-btn i');
        if (icon) {
          icon.classList.remove('cart-icon-shake');
          void icon.offsetWidth;
          icon.classList.add('cart-icon-shake');
          setTimeout(() => icon.classList.remove('cart-icon-shake'), 600);
        }
      }, 80);
    } else {
      btn.disabled = false;
      this.submit();
    }
  } catch {
    btn.disabled = false;
    this.submit();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const firstColor = document.querySelector('.color-radio:checked');
  if (firstColor) {
    const label = document.getElementById('selected-color');
    if (label) label.textContent = firstColor.closest('label').querySelector('.color-swatch')?.title || '';
    if (Object.keys(window.COLOR_IMAGE_MAP).length > 0) switchGalleryToColor(firstColor.value);
  }
  const firstSize = document.querySelector('.size-radio:checked');
  if (firstSize) {
    const label = document.getElementById('selected-size');
    if (label) label.textContent = firstSize.closest('label').querySelector('.size-btn')?.textContent || '';
  }

  document.querySelectorAll('.color-radio').forEach(r => {
    r.addEventListener('change', () => {
      const label = document.getElementById('selected-color');
      if (label) label.textContent = r.closest('label').querySelector('.color-swatch')?.title || '';
      if (Object.keys(window.COLOR_IMAGE_MAP).length > 0) switchGalleryToColor(r.value);
      updateCartFormAction();
    });
  });

  document.querySelectorAll('.size-radio').forEach(r => {
    r.addEventListener('change', updateCartFormAction);
  });

  updateCartFormAction();

  // Image zoom (loupe)
  const galleryMain = document.querySelector('.product-gallery-main');
  const mainImg = document.getElementById('mainImage');
  if (galleryMain && mainImg) {
    galleryMain.addEventListener('mousemove', e => {
      const rect = galleryMain.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width * 100).toFixed(1);
      const y = ((e.clientY - rect.top) / rect.height * 100).toFixed(1);
      mainImg.style.transformOrigin = `${x}% ${y}%`;
      galleryMain.classList.add('zooming');
    });
    galleryMain.addEventListener('mouseleave', () => {
      galleryMain.classList.remove('zooming');
      mainImg.style.transformOrigin = '50% 50%';
    });
  }

  // Mobile buy button
  document.getElementById('mobileBuyBtn')?.addEventListener('click', () => {
    document.getElementById('add-cart-btn')?.click();
  });

  // Hide mobile buy bar when main button is in view
  const bar     = document.getElementById('mobileBuyBar');
  const mainBtn = document.getElementById('add-cart-btn');
  if (bar && mainBtn) {
    new IntersectionObserver(entries => {
      bar.classList.toggle('hidden', entries[0].isIntersecting);
    }, { threshold: 0.1 }).observe(mainBtn);
  }
});