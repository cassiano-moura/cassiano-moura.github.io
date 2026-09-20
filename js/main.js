/* ==============================================================================
   PORTFOLIO MAIN JAVASCRIPT - CASSIANO MOURA
   Interactive Logic, I18N Switcher, Skill Filters & Utilities
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Current active language (Default: 'en')
  let currentLang = localStorage.getItem('portfolio_lang') || 'en';

  // --- 1. LANGUAGE SWITCHER LOGIC ---
  const langButtons = document.querySelectorAll('.lang-btn');

  function updateLanguage(lang) {
    if (!translations[lang]) return;
    currentLang = lang;
    localStorage.setItem('portfolio_lang', lang);

    // Update active class on buttons
    langButtons.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });

    // Update all elements with data-i18n
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (translations[lang][key]) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.placeholder = translations[lang][key];
        } else {
          el.innerHTML = translations[lang][key];
        }
      }
    });

    // Update HTML lang attribute
    document.documentElement.lang = lang;
  }

  // Bind click on language buttons
  langButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const selectedLang = e.currentTarget.getAttribute('data-lang');
      updateLanguage(selectedLang);
    });
  });

  // Initialize with stored or default language
  updateLanguage(currentLang);


  // --- 2. STICKY NAVBAR & SCROLL HIGHLIGHTING ---
  const navbar = document.querySelector('.navbar');
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section[id]');

  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;

    // Navbar background blur on scroll
    if (scrollY > 40) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    // Active link highlighting
    sections.forEach(current => {
      const sectionHeight = current.offsetHeight;
      const sectionTop = current.offsetTop - 120;
      const sectionId = current.getAttribute('id');

      if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
          }
        });
      }
    });
  });


  // --- 3. MOBILE MENU TOGGLE ---
  const mobileBtn = document.querySelector('.mobile-menu-btn');
  if (mobileBtn) {
    mobileBtn.addEventListener('click', () => {
      navbar.classList.toggle('mobile-open');
    });

    // Close menu when clicking a link
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        navbar.classList.remove('mobile-open');
      });
    });
  }


  // --- 4. SKILLS FILTER TABS ---
  const skillTabs = document.querySelectorAll('.skill-tab-btn');
  const skillItems = document.querySelectorAll('.skill-item-card');

  skillTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active from all tabs
      skillTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const filterCategory = tab.getAttribute('data-filter');

      skillItems.forEach(item => {
        const itemCategory = item.getAttribute('data-category');
        if (filterCategory === 'all' || itemCategory === filterCategory) {
          item.style.display = 'flex';
          setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'scale(1)';
          }, 10);
        } else {
          item.style.opacity = '0';
          item.style.transform = 'scale(0.95)';
          setTimeout(() => {
            item.style.display = 'none';
          }, 200);
        }
      });
    });
  });


  // --- 5. COPY EMAIL TO CLIPBOARD WITH TOAST ---
  const copyEmailBtns = document.querySelectorAll('.btn-email-copy');
  const toast = document.getElementById('toastNotice');
  const emailToCopy = "cassiano.moura.tech@gmail.com";

  copyEmailBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(emailToCopy).then(() => {
        showToast(translations[currentLang].btnEmailCopied || "Email copied to clipboard!");
      }).catch(() => {
        // Fallback prompt if clipboard API is restricted
        prompt("Copy email address:", emailToCopy);
      });
    });
  });

  function showToast(message) {
    if (!toast) return;
    const toastText = toast.querySelector('.toast-text') || toast;
    toastText.textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
      toast.classList.remove('show');
    }, 3200);
  }


  // --- 6. SMOOTH SCROLL FOR INTERNAL LINKS ---
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        const headerOffset = 80;
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
});
