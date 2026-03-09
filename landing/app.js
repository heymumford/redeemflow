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

  // === FAQ ACCORDION ===
  var faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach(function(item) {
    var trigger = item.querySelector('.faq-item__trigger');
    var answer = item.querySelector('.faq-item__answer');
    var inner = item.querySelector('.faq-item__answer-inner');

    trigger.addEventListener('click', function() {
      var isOpen = item.getAttribute('data-open') === 'true';

      // Close all
      faqItems.forEach(function(other) {
        other.setAttribute('data-open', 'false');
        other.querySelector('.faq-item__trigger').setAttribute('aria-expanded', 'false');
        other.querySelector('.faq-item__answer').style.maxHeight = '0';
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
        submitBtn.textContent = 'Join Waitlist \u2192';
      }
    })
    .catch(function() {
      showError('Network error. Please try again.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Join Waitlist \u2192';
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
  if (prefersReducedMotion) {
    fadeEls.forEach(function(el) { el.classList.add('visible'); });
  } else if ('IntersectionObserver' in window) {
    var fadeObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    fadeEls.forEach(function(el) { fadeObserver.observe(el); });
  } else {
    fadeEls.forEach(function(el) { el.classList.add('visible'); });
  }

  // === COUNTER ANIMATION ===
  var statEl = document.querySelector('.big-stat__value[data-target]');
  if (statEl && 'IntersectionObserver' in window) {
    if (prefersReducedMotion) {
      var target = parseInt(statEl.getAttribute('data-target'), 10);
      statEl.textContent = '$' + target.toLocaleString();
    } else {
      var counted = false;
      var counterObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting && !counted) {
            counted = true;
            var target = parseInt(statEl.getAttribute('data-target'), 10);
            var duration = 1500;
            var start = performance.now();
            function step(now) {
              var elapsed = now - start;
              var progress = Math.min(elapsed / duration, 1);
              var eased = 1 - Math.pow(1 - progress, 3);
              var current = Math.round(eased * target);
              statEl.textContent = '$' + current.toLocaleString();
              if (progress < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
            counterObserver.unobserve(statEl);
          }
        });
      }, { threshold: 0.5 });
      counterObserver.observe(statEl);
    }
  }

  // === COPYRIGHT YEAR AUTO-UPDATE ===
  var copyEl = document.querySelector('.footer__copy');
  if (copyEl) copyEl.textContent = '\u00A9 ' + new Date().getFullYear() + ' RedeemFlow';

})();
