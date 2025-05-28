// Fonctions d'animation et effets tactiles pour l'interface

// Ajouter des effets d'ondulation sur les boutons
function addRippleEffect(element) {
  element.addEventListener("click", function (e) {
    const ripple = document.createElement("span");
    ripple.classList.add("ripple");
    this.appendChild(ripple);

    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);

    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

    ripple.addEventListener("animationend", function () {
      ripple.remove();
    });
  });
}

// Initialiser les effets tactiles
function initTouchEffects() {
  // Ajouter des effets d'ondulation à tous les boutons
  document
    .querySelectorAll(".btn, .nav-btn, .wifi-item, .settings-button")
    .forEach((button) => {
      button.classList.add("btn-wave", "btn-touch");
      addRippleEffect(button);
    });

  // Ajouter des effets de flottement
  document
    .querySelectorAll(".ip-badge, .connection-status-indicator")
    .forEach((element) => {
      element.classList.add("float-effect");
    });

  // Ajouter des effets d'apparition
  document
    .querySelectorAll(".wifi-item, .container, .modal")
    .forEach((element, index) => {
      element.classList.add("fade-in-up");
      element.style.animationDelay = `${index * 0.1}s`;
    });

  // Ajouter des transitions douces
  document.querySelectorAll("select, input, .form-input").forEach((element) => {
    element.classList.add("smooth-transition");
  });

  // Optimisation pour écrans tactiles
  if (window.innerWidth <= 1024) {
    document.querySelectorAll(".btn, select, input").forEach((element) => {
      element.classList.add("touch-friendly");
    });

    document
      .querySelectorAll(".form-group, .control-section")
      .forEach((element) => {
        element.classList.add("touch-spacing");
      });
  }

  // Effet de profondeur pour les conteneurs
  document
    .querySelectorAll(".container, .modal, .settings-menu")
    .forEach((element) => {
      element.classList.add("depth-effect");
    });
}

// Gestion des animations lors des événements
function setupAnimationEvents() {
  // Animation lors de la sélection d'une option
  document.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", function () {
      gsap.to(this, {
        scale: 1.05,
        duration: 0.2,
        yoyo: true,
        repeat: 1,
      });
    });
  });

  // Animation lors du clic sur un bouton
  document.querySelectorAll(".btn").forEach((button) => {
    button.addEventListener("click", function () {
      if (!this.disabled) {
        gsap.to(this, {
          scale: 0.95,
          duration: 0.1,
          yoyo: true,
          repeat: 1,
        });
      }
    });
  });

  // Animation de notification
  window.showNotification = function (message, isSuccess = true) {
    const notification = document.createElement("div");
    notification.className = `notification ${
      isSuccess ? "success" : "error"
    } notification-bounce`;
    notification.innerHTML = `
      <i class="fas ${
        isSuccess ? "fa-check-circle" : "fa-exclamation-circle"
      }"></i>
      <span>${message}</span>
    `;

    document.body.appendChild(notification);

    gsap.fromTo(
      notification,
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.3, ease: "back.out(1.7)" }
    );

    setTimeout(() => {
      gsap.to(notification, {
        y: 50,
        opacity: 0,
        duration: 0.3,
        onComplete: () => notification.remove(),
      });
    }, 3000);
  };
}

// Fonction pour détecter l'orientation de l'écran et adapter l'interface
function handleOrientation() {
  const isPortrait = window.innerHeight > window.innerWidth;
  const containers = document.querySelectorAll(".container");

  containers.forEach((container) => {
    if (isPortrait) {
      container.style.maxWidth = "90%";
    } else {
      container.style.maxWidth = "600px";
    }
  });

  // Ajuster la position de la barre de navigation
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    if (isPortrait) {
      navbar.style.bottom = "20px";
    } else {
      navbar.style.bottom = "20px";
    }
  }
}

// Initialiser tous les effets
document.addEventListener("DOMContentLoaded", function () {
  initTouchEffects();
  setupAnimationEvents();
  handleOrientation();

  // Gérer les changements d'orientation
  window.addEventListener("resize", handleOrientation);
});

// Fonction pour les animations de chargement
function showLoading(element, text = "Chargement...") {
  const originalContent = element.innerHTML;
  element.innerHTML = `<span class="hourglass">⏳</span> ${text}`;
  element.disabled = true;

  return {
    hide: function () {
      element.innerHTML = originalContent;
      element.disabled = false;
    },
  };
}
