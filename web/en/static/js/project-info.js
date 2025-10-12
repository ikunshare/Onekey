class ProjectInfoEnhancer {
  constructor() {
    this.initializeProjectInfo();
  }

  initializeProjectInfo() {
    this.addProjectLinkTracking();

    this.addVersionClickEaster();

    this.addLogoClickEffect();
  }

  addProjectLinkTracking() {
    const projectLinks = document.querySelectorAll(".project-link");
    projectLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        const linkType = link.classList.contains("github")
          ? "GitHub repository"
          : link.classList.contains("releases")
            ? "Download release version"
            : link.classList.contains("docs")
              ? "Use documentation"
              : link.classList.contains("issues")
                ? "Problem feedback"
                : "unknown link";

        console.log(`User clicked on ${linkType} link`);

        link.style.transform = "scale(0.95)";
        setTimeout(() => {
          link.style.transform = "";
        }, 150);
      });
    });
  }

  addVersionClickEaster() {
    const versionLabels = document.querySelectorAll(".version-label");
    let clickCount = 0;

    versionLabels.forEach((label) => {
      label.addEventListener("click", () => {
        clickCount++;

        if (clickCount === 5) {
          this.showEasterEgg();
          clickCount = 0;
        }

        label.style.animation = "pulse 0.3s ease";
        setTimeout(() => {
          label.style.animation = "";
        }, 300);
      });
    });
  }

  addLogoClickEffect() {
    const logos = document.querySelectorAll(".project-logo");

    logos.forEach((logo) => {
      logo.addEventListener("click", () => {
        logo.style.transform = "rotate(360deg)";
        logo.style.transition = "transform 0.6s ease";

        setTimeout(() => {
          logo.style.transform = "";
          logo.style.transition = "";
        }, 600);

        this.showTooltip(logo, "🎮 Onekey - Steam unlocking made easy!");
      });
    });
  }

  showEasterEgg() {
    const messages = [
      "🎉 You found a hidden easter egg!",
      "🚀 Thank you for using Onekey Tools!",
      "⭐ Don’t forget to give the project a star!",
      "🎮 Happy gaming!",

      "🔓 Unlock it with one click and enjoy the game!",
    ];

    const randomMessage = messages[Math.floor(Math.random() * messages.length)];

    const easterEgg = document.createElement("div");
    easterEgg.className = "easter-egg";
    easterEgg.textContent = randomMessage;
    easterEgg.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(45deg, #6750a4, #7d5260);
            color: white;
            padding: 20px 30px;
            border-radius: 15px;
            font-size: 18px;
            font-weight: 500;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 9999;
            animation: easterEggBounce 0.6s ease-out;
        `;

    if (!document.getElementById("easter-egg-styles")) {
      const style = document.createElement("style");
      style.id = "easter-egg-styles";
      style.textContent = `
                @keyframes easterEggBounce {
                    0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
                    50% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
                    100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                }
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
            `;
      document.head.appendChild(style);
    }

    document.body.appendChild(easterEgg);

    setTimeout(() => {
      easterEgg.style.animation = "easterEggBounce 0.3s ease-in reverse";
      setTimeout(() => {
        if (easterEgg.parentNode) {
          easterEgg.parentNode.removeChild(easterEgg);
        }
      }, 300);
    }, 3000);
  }

  showTooltip(element, message) {
    const tooltip = document.createElement("div");
    tooltip.className = "custom-tooltip";
    tooltip.textContent = message;
    tooltip.style.cssText = `
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        `;

    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + rect.width / 2 + "px";
    tooltip.style.top = rect.bottom + 10 + "px";
    tooltip.style.transform = "translateX(-50%)";

    document.body.appendChild(tooltip);

    setTimeout(() => {
      tooltip.style.opacity = "1";
    }, 10);

    setTimeout(() => {
      tooltip.style.opacity = "0";
      setTimeout(() => {
        if (tooltip.parentNode) {
          tooltip.parentNode.removeChild(tooltip);
        }
      }, 300);
    }, 2000);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new ProjectInfoEnhancer();
});
