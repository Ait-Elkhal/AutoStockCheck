// theme.js - Dark / Light mode (sans export)

// Initialisation du thème
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
      document.body.classList.add('dark-mode');
      document.body.classList.remove('light-mode');
  } else {
      document.body.classList.add('light-mode');
      document.body.classList.remove('dark-mode');
  }
  
  const toggle = document.getElementById('themeToggle');
  if (toggle) {
      toggle.addEventListener('click', function() {
          if (document.body.classList.contains('dark-mode')) {
              document.body.classList.remove('dark-mode');
              document.body.classList.add('light-mode');
              localStorage.setItem('theme', 'light');
          } else {
              document.body.classList.remove('light-mode');
              document.body.classList.add('dark-mode');
              localStorage.setItem('theme', 'dark');
          }
      });
  }
}

// Détection du thème système
function detectSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.body.classList.add('dark-mode');
      document.body.classList.remove('light-mode');
  } else {
      document.body.classList.add('light-mode');
      document.body.classList.remove('dark-mode');
  }
}

// Appliquer le thème sauvegardé ou système
function applyTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
      document.body.classList.add('dark-mode');
      document.body.classList.remove('light-mode');
  } else if (savedTheme === 'light') {
      document.body.classList.add('light-mode');
      document.body.classList.remove('dark-mode');
  } else {
      detectSystemTheme();
  }
}

// Exécuter au chargement
applyTheme();