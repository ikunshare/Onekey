class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById("themeToggle");
    this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
    this.isTransitioning = false;

    this.createThemeIndicator();
    this.applyTheme(this.currentTheme, false);
    this.initializeEventListeners();
  }

  getStoredTheme() {
    return localStorage.getItem("theme");
  }

  getPreferredTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  createThemeIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "theme-indicator";
    indicator.id = "themeIndicator";
    document.body.appendChild(indicator);
    this.themeIndicator = indicator;
  }

  showThemeIndicator(message) {
    this.themeIndicator.textContent = message;
    this.themeIndicator.classList.add("show");

    setTimeout(() => {
      this.themeIndicator.classList.remove("show");
    }, 2000);
  }

  applyTheme(theme, animate = true) {
    if (this.isTransitioning) return;

    this.isTransitioning = true;

    if (animate) {
      document.body.classList.add("theme-transitioning");
    }

    document.documentElement.setAttribute("data-theme", theme);
    this.updateToggleButton(theme);
    localStorage.setItem("theme", theme);
    this.currentTheme = theme;

    window.dispatchEvent(
      new CustomEvent("themechange", {
        detail: { theme, animated: animate },
      }),
    );

    setTimeout(() => {
      document.body.classList.remove("theme-transitioning");
      this.isTransitioning = false;
    }, 600);
  }

  updateToggleButton(theme) {
    if (this.themeToggle) {
      const icon = this.themeToggle.querySelector(".material-icons");
      icon.textContent = theme === "dark" ? "dark_mode" : "light_mode";
      this.themeToggle.title =
        theme === "dark" ? "切换到浅色模式" : "切换到深色模式";

      icon.style.animation = "none";
      icon.offsetHeight;
      icon.style.animation = "iconRotate 300ms ease";
    }
  }

  toggleTheme(event) {
    const newTheme = this.currentTheme === "dark" ? "light" : "dark";

    if (event && event.currentTarget) {
      const rect = event.currentTarget.getBoundingClientRect();
      const x = ((rect.left + rect.width / 2) / window.innerWidth) * 100;
      const y = ((rect.top + rect.height / 2) / window.innerHeight) * 100;

      document.documentElement.style.setProperty("--x", `${x}%`);
      document.documentElement.style.setProperty("--y", `${y}%`);
    }

    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }

    this.applyTheme(newTheme);

    this.logThemeSwitch(newTheme);
  }

  logThemeSwitch(theme) {
    console.log(`主题切换到: ${theme}`);
  }

  initializeEventListeners() {
    if (this.themeToggle) {
      this.themeToggle.addEventListener("click", (e) => this.toggleTheme(e));

      this.themeToggle.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.toggleTheme(e);
        }
      });
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", (e) => {
      if (!this.getStoredTheme()) {
        this.applyTheme(e.matches ? "dark" : "light");
      }
    });

    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "T") {
        e.preventDefault();
        this.toggleTheme();
      }
    });

    window.addEventListener("storage", (e) => {
      if (e.key === "theme" && e.newValue) {
        this.applyTheme(e.newValue, false);
      }
    });
  }

  getThemePalette() {
    const computedStyle = getComputedStyle(document.documentElement);
    return {
      primary: computedStyle.getPropertyValue("--md-sys-color-primary").trim(),
      secondary: computedStyle
        .getPropertyValue("--md-sys-color-secondary")
        .trim(),
      surface: computedStyle.getPropertyValue("--md-sys-color-surface").trim(),
      background: computedStyle
        .getPropertyValue("--md-sys-color-background")
        .trim(),
      onBackground: computedStyle
        .getPropertyValue("--md-sys-color-on-background")
        .trim(),
    };
  }

  shouldUseDarkMode() {
    const hour = new Date().getHours();
    return hour >= 18 || hour < 6;
  }

  enableAutoThemeSwitch() {
    const checkTime = () => {
      if (!this.getStoredTheme()) {
        const shouldBeDark = this.shouldUseDarkMode();
        const currentTheme = this.currentTheme;

        if (
          (shouldBeDark && currentTheme === "light") ||
          (!shouldBeDark && currentTheme === "dark")
        ) {
          this.applyTheme(shouldBeDark ? "dark" : "light");
        }
      }
    };

    setInterval(checkTime, 60000);
    checkTime();
  }
}

window.ThemeManager = new ThemeManager();
