(function() {
  'use strict';

  // === NAV SCROLL HANDLER (rAF throttled) ===
  var nav = document.getElementById('nav');
  var ticking = false;

  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(function() {
        if (window.scrollY > 60) {
          nav.classList.add('nav--scrolled');
        } else {
          nav.classList.remove('nav--scrolled');
        }
        ticking = false;
      });
      ticking = true;
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // === MOBILE NAV TOGGLE ===
  var navToggle = document.querySelector('.nav__toggle');
  var navDrawer = document.getElementById('nav-drawer');
  var navBackdrop = document.getElementById('nav-backdrop');

  if (navToggle && navDrawer) {
    function closeNav() {
      navToggle.setAttribute('aria-expanded', 'false');
      navDrawer.classList.remove('nav__drawer--open');
      if (navBackdrop) navBackdrop.classList.remove('nav__drawer-backdrop--visible');
    }

    function openNav() {
      navToggle.setAttribute('aria-expanded', 'true');
      navDrawer.classList.add('nav__drawer--open');
      if (navBackdrop) navBackdrop.classList.add('nav__drawer-backdrop--visible');
      // Focus first link for keyboard users
      var firstLink = navDrawer.querySelector('a');
      if (firstLink) firstLink.focus();
    }

    navToggle.addEventListener('click', function() {
      var isOpen = navToggle.getAttribute('aria-expanded') === 'true';
      if (isOpen) {
        closeNav();
      } else {
        openNav();
      }
    });

    // Close on backdrop click
    if (navBackdrop) {
      navBackdrop.addEventListener('click', closeNav);
    }

    // Close on Escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
        closeNav();
        navToggle.focus();
      }
    });

    // Close when clicking nav drawer links (smooth scroll still fires)
    navDrawer.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', closeNav);
    });
  }

  // === FAQ ACCORDION ===
  var faqItems = document.querySelectorAll('.accordion-item');

  faqItems.forEach(function(item) {
    var trigger = item.querySelector('.accordion-item__trigger');
    var answer = item.querySelector('.accordion-item__answer');
    var inner = item.querySelector('.accordion-item__answer-inner');

    trigger.addEventListener('click', function() {
      var isOpen = item.getAttribute('data-open') === 'true';

      // Close all
      faqItems.forEach(function(other) {
        other.setAttribute('data-open', 'false');
        other.querySelector('.accordion-item__trigger').setAttribute('aria-expanded', 'false');
        other.querySelector('.accordion-item__answer').style.maxHeight = '0';
      });

      // Toggle current
      if (!isOpen) {
        item.setAttribute('data-open', 'true');
        trigger.setAttribute('aria-expanded', 'true');
        answer.style.maxHeight = inner.scrollHeight + 'px';
      }
    });
  });

  // === WAITLIST FORM ===
  var form = document.getElementById('waitlist-form');
  var emailInput = document.getElementById('waitlist-email');
  var errorEl = document.getElementById('waitlist-error');
  var successEl = document.getElementById('waitlist-success');

  var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function showError(msg) {
    errorEl.textContent = msg;
    emailInput.classList.add('waitlist__input--error');
  }

  function clearError() {
    errorEl.textContent = '';
    emailInput.classList.remove('waitlist__input--error');
  }

  emailInput.addEventListener('input', function() {
    if (emailInput.classList.contains('waitlist__input--error')) {
      clearError();
    }
  });

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    clearError();

    var email = emailInput.value.trim();

    if (!email) {
      showError('Please enter your email address.');
      emailInput.focus();
      return;
    }

    if (!emailRegex.test(email)) {
      showError('Please enter a valid email address.');
      emailInput.focus();
      return;
    }

    // Submit to API
    var submitBtn = form.querySelector('.waitlist__submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Joining...';

    fetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email })
    })
    .then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.status === 'ok') {
        form.style.display = 'none';
        errorEl.style.display = 'none';
        successEl.classList.add('visible');
        successEl.setAttribute('tabindex', '-1');
        successEl.focus();
      } else {
        showError(data.error || 'Something went wrong. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Get Early Access \u2192';
      }
    })
    .catch(function() {
      showError('Network error. Please try again.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Get Early Access \u2192';
    });
  });

  // === SMOOTH SCROLL FOR ANCHOR LINKS ===
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    var href = anchor.getAttribute('href');
    if (href.length <= 1) return;
    anchor.addEventListener('click', function(e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    });
  });

  // === SCROLL ANIMATIONS (IntersectionObserver) ===
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fadeEls = document.querySelectorAll('.fade-in');

  function revealElement(el) {
    if (!el.classList.contains('visible')) {
      el.classList.add('visible');
    }
  }

  if (prefersReducedMotion) {
    fadeEls.forEach(revealElement);
  } else if ('IntersectionObserver' in window) {
    var observerFired = false;
    var fadeObserver = new IntersectionObserver(function(entries) {
      observerFired = true;
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          revealElement(entry.target);
          fadeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -20px 0px' });
    fadeEls.forEach(function(el) { fadeObserver.observe(el); });

    // Safety net: reveal remaining elements after load if observer hasn't engaged
    window.addEventListener('load', function() {
      setTimeout(function() {
        if (!observerFired) {
          fadeEls.forEach(revealElement);
        }
      }, 1000);
    });
  } else {
    fadeEls.forEach(revealElement);
  }

  // === COPYRIGHT YEAR AUTO-UPDATE ===
  var copyEl = document.querySelector('.footer__copy');
  if (copyEl) {
    var existingText = copyEl.textContent;
    var yearMatch = existingText.match(/\u00A9\s*\d{4}/);
    if (yearMatch) {
      copyEl.textContent = existingText.replace(/\u00A9\s*\d{4}/, '\u00A9 ' + new Date().getFullYear());
    }
  }

  // === STICKY MOBILE CTA BAR ===
  var mobileCta = document.getElementById('mobile-cta');
  var heroSection = document.querySelector('.hero');
  var waitlistSection = document.getElementById('waitlist');

  if (mobileCta && heroSection && waitlistSection && 'IntersectionObserver' in window) {
    var heroVisible = true;
    var waitlistVisible = false;

    var mobileCtaLink = mobileCta.querySelector('a');

    function updateMobileCta() {
      if (heroVisible || waitlistVisible) {
        mobileCta.classList.remove('visible');
        mobileCta.setAttribute('aria-hidden', 'true');
        if (mobileCtaLink) mobileCtaLink.setAttribute('tabindex', '-1');
        document.body.classList.remove('mobile-cta-active');
      } else {
        mobileCta.classList.add('visible');
        mobileCta.setAttribute('aria-hidden', 'false');
        if (mobileCtaLink) mobileCtaLink.removeAttribute('tabindex');
        document.body.classList.add('mobile-cta-active');
      }
    }

    var heroObs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        heroVisible = entry.isIntersecting;
      });
      updateMobileCta();
    }, { threshold: 0.1 });

    var waitlistObs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        waitlistVisible = entry.isIntersecting;
      });
      updateMobileCta();
    }, { threshold: 0.1 });

    heroObs.observe(heroSection);
    waitlistObs.observe(waitlistSection);
  }

})();
