class OnekeyWebApp {
  constructor() {
    this.socket = null;
    this.taskStatus = "idle";
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
    this.initializeSocket();
    this.initializeEventListeners();
    this.checkConfig();
  }

  initializeSocket() {
    this.connectWebSocket();
  }

  connectWebSocket() {
    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log("Connected to server");
        this.showSnackbar("Connected to server", "success");
        this.reconnectAttempts = 0;

        this.startHeartbeat();
      };

      this.socket.onclose = (event) => {
        console.log("Disconnected from server", event);
        this.showSnackbar("Disconnected from server", "error");

        this.stopHeartbeat();

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            console.log(
              `Trying reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
            );
            this.connectWebSocket();
          }, this.reconnectDelay);
        }
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (e) {
          console.error("Failed to parse message:", e);
        }
      };
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
      this.showSnackbar("Failed to connect WebSocket", "error");
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case "connected":
        console.log(message.data.message);
        break;
      case "task_progress":
        this.addLogEntry(message.data.type, message.data.message);
        break;
      case "pong":
        break;
      default:
        console.log("Unknown message type:", message.type);
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  initializeEventListeners() {
    const unlockForm = document.getElementById("unlockForm");
    unlockForm.addEventListener("submit", (e) => {
      e.preventDefault();
      this.startUnlockTask();
    });

    const resetBtn = document.getElementById("resetBtn");
    resetBtn.addEventListener("click", () => {
      this.resetForm();
    });

    const clearLogBtn = document.getElementById("clearLogBtn");
    clearLogBtn.addEventListener("click", () => {
      this.clearLogs();
    });

    const snackbarClose = document.getElementById("snackbarClose");
    snackbarClose.addEventListener("click", () => {
      this.hideSnackbar();
    });

    window.addEventListener("beforeunload", () => {
      this.disconnect();
    });
  }

  async checkConfig() {
    const configStatus = document.getElementById("configStatus");

    try {
      const response = await fetch("/api/config");
      const data = await response.json();

      if (data.success) {
        configStatus.innerHTML = this.generateConfigStatusHTML(data.config);
      } else {
        configStatus.innerHTML = `
                    <div class="status-item">
                        <span class="material-icons status-icon error">error</span>
                        <span class="status-text">Load config failed: ${data.message}</span>
                    </div>
                `;
      }
    } catch (error) {
      configStatus.innerHTML = `
                <div class="status-item">
                    <span class="material-icons status-icon error">error</span>
                    <span class="status-text">Failed to connect WebSocket</span>
                </div>
            `;
    }
  }

  generateConfigStatusHTML(config) {
    const items = [];

    if (config.steam_path) {
      items.push(`
                <div class="status-item">
                    <span class="material-icons status-icon success">check_circle</span>
                    <span class="status-text">Steam Path: ${config.steam_path}</span>
                </div>
            `);
    } else {
      items.push(`
                <div class="status-item">
                    <span class="material-icons status-icon error">error</span>
                    <span class="status-text">Steam path not found</span>
                </div>
            `);
    }

    if (config.debug_mode) {
      items.push(`
                <div class="status-item">
                    <span class="material-icons status-icon warning">bug_report</span>
                    <span class="status-text">Debug mode is enable</span>
                </div>
            `);
    }

    return items.join("");
  }

  toggleAndDLC() {
    document.getElementById("+DLC").checked = true;
  }

  async startUnlockTask() {
    if (this.taskStatus === "running") {
      this.showSnackbar("There is already a task running", "warning");
      return;
    }

    const formData = new FormData(document.getElementById("unlockForm"));
    const appId = formData.get("appId").trim();
    const toolType = formData.get("toolType");
    const ADLC = formData.get("+DLC") === "on";

    if (!appId) {
      this.showSnackbar("Please enter App ID", "error");
      return;
    }

    const appIdPattern = /^[\d-]+$/;
    if (!appIdPattern.test(appId)) {
      this.showSnackbar(
        "Invalid App ID format, should be a number or numbers separated by -",
        "error",
      );
      return;
    }

    this.taskStatus = "running";
    this.updateUIForRunningTask();
    this.clearLogs();
    this.addLogEntry("info", `Start working on the game ${appId}...`);

    try {
      const response = await fetch("/api/start_unlock", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          app_id: appId,
          tool_type: toolType,
          dlc: ADLC,
        }),
      });

      const data = await response.json();

      if (data.success) {
        this.showSnackbar("Mission has started", "success");
        this.startStatusPolling();
      } else {
        this.taskStatus = "idle";
        this.updateUIForIdleTask();
        this.showSnackbar(data.message, "error");
        this.addLogEntry("error", data.message);
      }
    } catch (error) {
      this.taskStatus = "idle";
      this.updateUIForIdleTask();
      this.showSnackbar("Failed to start task", "error");
      this.addLogEntry("error", `Failed to start task: ${error.message}`);
    }
  }

  startStatusPolling() {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch("/api/task_status");
        const data = await response.json();

        if (data.status === "completed") {
          clearInterval(pollInterval);
          this.taskStatus = "completed";
          this.updateUIForIdleTask();

          if (data.result && data.result.success) {
            this.showSnackbar(data.result.message, "success");
            this.addLogEntry("info", data.result.message);
          } else if (data.result) {
            this.showSnackbar(data.result.message, "error");
            this.addLogEntry("error", data.result.message);
          }
        } else if (data.status === "error") {
          clearInterval(pollInterval);
          this.taskStatus = "error";
          this.updateUIForIdleTask();

          if (data.result) {
            this.showSnackbar(data.result.message, "error");
            this.addLogEntry("error", data.result.message);
          }
        }
      } catch (error) {
        console.error("Status polling error:", error);
      }
    }, 1000);
  }

  updateUIForRunningTask() {
    const unlockBtn = document.getElementById("unlockBtn");
    const resetBtn = document.getElementById("resetBtn");
    const appIdInput = document.getElementById("appId");
    const toolTypeRadios = document.querySelectorAll('input[name="toolType"]');

    unlockBtn.disabled = true;
    unlockBtn.innerHTML = `
            <span class="material-icons">hourglass_empty</span>
            Executing...
        `;

    resetBtn.disabled = true;
    appIdInput.disabled = true;
    toolTypeRadios.forEach((radio) => (radio.disabled = true));
  }

  updateUIForIdleTask() {
    const unlockBtn = document.getElementById("unlockBtn");
    const resetBtn = document.getElementById("resetBtn");
    const appIdInput = document.getElementById("appId");
    const toolTypeRadios = document.querySelectorAll('input[name="toolType"]');

    unlockBtn.disabled = false;
    unlockBtn.innerHTML = `
            <span class="material-icons">play_arrow</span>
            Start unlocking
        `;

    resetBtn.disabled = false;
    appIdInput.disabled = false;
    toolTypeRadios.forEach((radio) => (radio.disabled = false));
  }

  resetForm() {
    if (this.taskStatus === "running") {
      this.showSnackbar("The task is running and cannot be reset.", "warning");
      return;
    }

    document.getElementById("unlockForm").reset();
    document.querySelector(
      'input[name="toolType"][value="steamtools"]',
    ).checked = true;
    this.clearLogs();
    this.showSnackbar("Form has been reset", "success");
  }

  addLogEntry(type, message) {
    const progressContainer = document.getElementById("progressContainer");
    const placeholder = progressContainer.querySelector(
      ".progress-placeholder",
    );

    if (placeholder) {
      placeholder.remove();
    }

    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement("div");
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-message">${this.escapeHtml(message)}</span>
        `;

    progressContainer.appendChild(logEntry);
    progressContainer.scrollTop = progressContainer.scrollHeight;
  }

  clearLogs() {
    const progressContainer = document.getElementById("progressContainer");
    progressContainer.innerHTML = `
            <div class="progress-placeholder">
                <span class="material-icons">info</span>
                <p>Wait for task to start...</p>
            </div>
        `;
  }

  showSnackbar(message, type = "info") {
    const snackbar = document.getElementById("snackbar");
    const snackbarMessage = document.getElementById("snackbarMessage");

    snackbarMessage.textContent = message;
    snackbar.className = `snackbar ${type}`;

    snackbar.offsetHeight;

    snackbar.classList.add("show");

    setTimeout(() => {
      this.hideSnackbar();
    }, 4000);
  }

  hideSnackbar() {
    const snackbar = document.getElementById("snackbar");
    snackbar.classList.remove("show");
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

const style = document.createElement("style");
style.textContent = `
  @keyframes iconRotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".card");

  cards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const percentX = (x - centerX) / centerX;
      const percentY = (y - centerY) / centerY;

      const rotateX = percentY * 5;
      const rotateY = percentX * 5;

      card.style.transform = `perspective(1000px) rotateX(${-rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
});

function typeWriter(element, text, speed = 50) {
  let i = 0;
  element.textContent = "";

  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }

  type();
}

function animateValue(element, start, end, duration) {
  const range = end - start;
  const increment = range / (duration / 16);
  let current = start;

  const timer = setInterval(() => {
    current += increment;
    if (
      (increment > 0 && current >= end) ||
      (increment < 0 && current <= end)
    ) {
      current = end;
      clearInterval(timer);
    }
    element.textContent = Math.round(current);
  }, 16);
}

document.querySelectorAll(".btn").forEach((button) => {
  button.addEventListener("mousemove", (e) => {
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    button.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
  });

  button.addEventListener("mouseleave", () => {
    button.style.transform = "";
  });
});

function createParticles() {
  const particlesContainer = document.createElement("div");
  particlesContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    `;
  document.body.appendChild(particlesContainer);

  for (let i = 0; i < 50; i++) {
    const particle = document.createElement("div");
    particle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(94, 53, 177, 0.3);
            border-radius: 50%;
            top: ${Math.random() * 100}%;
            left: ${Math.random() * 100}%;
            animation: floatParticle ${
              10 + Math.random() * 20
            }s linear infinite;
        `;
    particlesContainer.appendChild(particle);
  }

  const style = document.createElement("style");
  style.textContent = `
        @keyframes floatParticle {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) rotate(720deg);
                opacity: 0;
            }
        }
    `;
  document.head.appendChild(style);
}

const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = "1";
      entry.target.style.transform = "translateY(0)";
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll(".card").forEach((card) => {
  card.style.opacity = "0";
  card.style.transform = "translateY(20px)";
  card.style.transition = "opacity 0.6s ease, transform 0.6s ease";
  observer.observe(card);
});

document.addEventListener("mousemove", (e) => {
  const light = document.createElement("div");
  light.style.cssText = `
        position: fixed;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(94, 53, 177, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        transform: translate(-50%, -50%);
        transition: opacity 0.3s ease;
    `;
  light.style.left = e.clientX + "px";
  light.style.top = e.clientY + "px";
  document.body.appendChild(light);

  setTimeout(() => {
    light.style.opacity = "0";
    setTimeout(() => light.remove(), 300);
  }, 100);
});

document.querySelectorAll(".status-icon").forEach((icon) => {
  if (icon.classList.contains("success")) {
    icon.style.animation = "pulse-icon 2s ease-in-out infinite";
  }
});

const pulseStyle = document.createElement("style");
pulseStyle.textContent = `
    @keyframes pulse-icon {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
    }
`;
document.head.appendChild(pulseStyle);

const originalShowSnackbar = window.showSnackbar;
if (typeof originalShowSnackbar === "function") {
  window.showSnackbar = function (message, type = "info") {
    originalShowSnackbar(message, type);

    if ("vibrate" in navigator) {
      if (type === "error") {
        navigator.vibrate([100, 50, 100]);
      } else {
        navigator.vibrate(50);
      }
    }

    const audio = new Audio(
      `data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmFgU7k9n1unEiBC13yO/eizEIHWq+8+OWT` +
        `BEFS6Xj67xqGAU+lNr1unIiBCx0xvDdiTYIHWu+8+OWT`,
    );
    if (type === "success") {
      audio.volume = 0.1;
      audio.play().catch(() => {});
    }
  };
}

document.querySelectorAll(".text-field").forEach((input) => {
  input.addEventListener("focus", (e) => {
    const ripple = document.createElement("div");
    ripple.style.cssText = `
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            border: 2px solid var(--md-sys-color-primary);
            border-radius: var(--md-sys-shape-corner-medium);
            opacity: 0;
            pointer-events: none;
            animation: inputRipple 0.6s ease-out;
        `;

    const wrapper = input.parentElement;
    wrapper.style.position = "relative";
    wrapper.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
  });
});

const inputRippleStyle = document.createElement("style");
inputRippleStyle.textContent = `
    @keyframes inputRipple {
        0% {
            transform: scale(0.8);
            opacity: 1;
        }
        100% {
            transform: scale(1.2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(inputRippleStyle);

document.addEventListener("DOMContentLoaded", () => {
  createParticles();
  document.body.classList.add("loaded");
  console.log("UI enhancements loaded ✨");

  new OnekeyWebApp();
});
