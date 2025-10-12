class SettingsManager {
  constructor() {
    this.currentConfig = {};
    this.currentKeyInfo = null;
    this.newKeyData = null;
    this.initializeEventListeners();
    this.loadConfig();
    this.loadKeyInfo();
  }

  initializeEventListeners() {
    document.getElementById("saveConfig").addEventListener("click", () => {
      this.saveConfig();
    });

    document.getElementById("resetConfig").addEventListener("click", () => {
      this.showConfirmDialog(
        "Reset configuration",
        "Are you sure you want to reset all configurations to default? This operation is irreversible.",
        () => this.resetConfig(),
      );
    });

    document.getElementById("testConfig").addEventListener("click", () => {
      this.testConfig();
    });

    document.getElementById("detectSteamPath").addEventListener("click", () => {
      this.detectSteamPath();
    });

    document.getElementById("steamPath").addEventListener("input", () => {
      this.validateSteamPath();
    });

    document.getElementById("verifyNewKey").addEventListener("click", () => {
      this.verifyNewKey();
    });

    document.getElementById("changeKey").addEventListener("click", () => {
      this.showConfirmDialog(
        "Change card password",
        "Are you sure you want to change to a new card password? Re-verification is required after replacement.",
        () => this.changeKey(),
      );
    });

    document.getElementById("newKey").addEventListener("input", () => {
      this.resetNewKeyStatus();
    });

    document.getElementById("newKey").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.verifyNewKey();
      }
    });

    document.getElementById("dialogCancel").addEventListener("click", () => {
      this.hideConfirmDialog();
    });

    document.getElementById("dialogConfirm").addEventListener("click", () => {
      this.executeConfirmAction();
    });

    document.getElementById("snackbarClose").addEventListener("click", () => {
      this.hideSnackbar();
    });
  }

  async loadConfig() {
    try {
      const response = await fetch("/api/config/detailed");
      const data = await response.json();

      if (data.success) {
        this.currentConfig = data.config;
        this.populateForm();
        this.updateConfigStatus();
      } else {
        this.showSnackbar(
          "Failed to load configuration: " + data.message,
          "error",
        );
      }
    } catch (error) {
      this.showSnackbar("Unable to connect to server", "error");
      console.error("Load config error:", error);
    }
  }

  async loadKeyInfo() {
    const keyInfoSection = document.getElementById("keyInfoSection");

    try {
      const configResponse = await fetch("/api/config/detailed");
      const configData = await configResponse.json();

      if (!configData.success || !configData.config.key) {
        keyInfoSection.innerHTML = `
                    <div class="expiry-warning">
                        <span class="material-icons">warning</span>
                        <div>
                            <strong>No card password set</strong><br>
                            Please enter your authorization card password below
                        </div>
                    </div>
                `;
        return;
      }

      const keyResponse = await fetch("/api/getKeyInfo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ key: configData.config.key }),
      });

      const keyData = await keyResponse.json();

      if (keyData.key && keyData.info) {
        this.currentKeyInfo = keyData.info;
        this.displayKeyInfo(keyData.info);
      } else {
        keyInfoSection.innerHTML = `
                    <div class="expiry-warning">
                        <span class="material-icons">error</span>
                        <div>
                            <strong>Card password verification failed</strong><br>
                            The current card password is invalid or expired, please replace it with a new one
                        </div>
                    </div>
                `;
      }
    } catch (error) {
      keyInfoSection.innerHTML = `
                <div class="expiry-warning">
                    <span class="material-icons">error</span>
                    <div>
                        <strong>Failed to obtain card password information</strong><br>
                        Please check the network connection or contact customer service
                    </div>
                </div>
            `;
      console.error("Load key info error:", error);
    }
  }

  displayKeyInfo(keyInfo) {
    const keyInfoSection = document.getElementById("keyInfoSection");
    const expiresAt = new Date(keyInfo.expiresAt);
    const createdAt = new Date(keyInfo.createdAt);
    const firstUsedAt = keyInfo.firstUsedAt
      ? new Date(keyInfo.firstUsedAt)
      : null;
    const now = new Date();

    const isExpired = expiresAt < now;
    const daysLeft = Math.ceil((expiresAt - now) / (1000 * 60 * 60 * 24));
    const isExpiringSoon = daysLeft <= 7 && daysLeft > 0;

    const typeNames = {
      day: "day card",
      week: "Weekly card",
      month: "monthly card",
      year: "Annual Pass",
      permanent: "permanent card",
    };

    let statusBadge = "";
    if (isExpired && keyInfo.type != "permanent") {
      statusBadge =
        '<span class="key-status-badge expired"><span class="material-icons" style="font-size: 14px;">cancel</span>Expired</span>';
    } else if (!keyInfo.isActive) {
      statusBadge =
        '<span class="key-status-badge inactive"><span class="material-icons" style="font-size: 14px;">pause</span>Not activated</span>';
    } else {
      statusBadge =
        '<span class="key-status-badge active"><span class="material-icons" style="font-size: 14px;">check_circle</span>normal</span>';
    }

    let warningSection = "";
    if (isExpiringSoon) {
      warningSection = `
                <div class="expiry-warning">
                    <span class="material-icons">schedule</span>
                    <div>
                        <strong>upcoming expiry reminder</strong><br>
                        Your card password will expire in ${daysLeft} days, please renew in time
                    </div>
                </div>
            `;
    }

    keyInfoSection.innerHTML = `
            <div class="key-info-grid">
                <div class="key-info-card">
                    <span class="material-icons key-info-icon">fingerprint</span>
                    <div class="key-info-content">
                        <div class="key-info-label">Cardamom</div>
                        <div class="key-info-value">${keyInfo.key.substring(
                          0,
                          8,
                        )}...${keyInfo.key.substring(
                          keyInfo.key.length - 8,
                        )}</div>
                    </div>
                </div>
                
                <div class="key-info-card">
                    <span class="material-icons key-info-icon">label</span>
                    <div class="key-info-content">
                        <div class="key-info-label">Type</div>
                        <div class="key-info-value">${
                          typeNames[keyInfo.type] || keyInfo.type
                        }</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">toggle_on</span>
                    <div class="key-info-content">
                        <div class="key-info-label">State</div>
                        <div class="key-info-value">${statusBadge}</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">event</span>
                    <div class="key-info-content">
                        <div class="key-info-label">Expiration time</div>
                        <div class="key-info-value">${expiresAt.toLocaleDateString()} ${expiresAt
                          .toLocaleTimeString()
                          .substring(0, 5)}</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">analytics</span>
                    <div class="key-info-content">
                        <div class="key-info-label">Number of uses</div>
                        <div class="key-info-value">${keyInfo.usageCount} / ${
                          keyInfo.totalUsage || "∞"
                        }</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">schedule</span>
                    <div class="key-info-content">
                        <div class="key-info-label">Creation time</div>
                        <div class="key-info-value">${createdAt.toLocaleDateString()}</div>
                    </div>
                </div>
            </div>
            ${warningSection}
        `;
  }

  async verifyNewKey() {
    const newKeyInput = document.getElementById("newKey");
    const key = newKeyInput.value.trim();

    if (!key) {
      this.showSnackbar("Please enter new card password", "error");
      return;
    }

    if (!key.match(/^[A-Z0-9_-]+$/)) {
      this.showSnackbar("The card password format is incorrect", "error");
      return;
    }

    const verifyBtn = document.getElementById("verifyNewKey");
    const changeBtn = document.getElementById("changeKey");

    verifyBtn.disabled = true;
    verifyBtn.innerHTML =
      '<span class="material-icons">hourglass_empty</span>Verifying...';

    try {
      const response = await fetch("/api/getKeyInfo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ key: key }),
      });

      const data = await response.json();

      if (data.key && data.info) {
        this.newKeyData = data.info;
        this.showSnackbar(
          "New card password verification successful!",
          "success",
        );

        changeBtn.style.display = "flex";
        verifyBtn.style.display = "none";

        const typeNames = {
          day: "day card",
          week: "Weekly card",
          month: "Monthly card",
          year: "Annual Pass",
          permanent: "permanent card",
        };

        const expiresAt = new Date(data.info.expiresAt);
        this.showSnackbar(
          `Verification successful! New card password type:
            ${typeNames[data.info.type]}
          }, valid until:${expiresAt.toLocaleDateString()}`,
          "success",
        );
      } else {
        this.showSnackbar(
          "The new card password is invalid or expired",
          "error",
        );
        this.newKeyData = null;
      }
    } catch (error) {
      this.showSnackbar(
        "Verification failed, please check network connection",
        "error",
      );
      console.error("New key verification error:", error);
    } finally {
      verifyBtn.disabled = false;
      verifyBtn.innerHTML = '<span class="material-icons">check</span>Verify';
    }
  }

  async changeKey() {
    if (!this.newKeyData) {
      this.showSnackbar("Please verify the new card password first", "error");
      return;
    }

    try {
      const newKey = document.getElementById("newKey").value.trim();

      const updateData = {
        key: newKey,
        steam_path: this.currentConfig.steam_path || "",
        debug_mode: this.currentConfig.debug_mode || false,
        logging_files: this.currentConfig.logging_files !== false,
        show_console: this.currentConfig.show_console !== false,
      };

      const response = await fetch("/api/config/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      const data = await response.json();

      if (data.success) {
        this.showSnackbar("Card secret changed successfully!", "success");

        await this.loadKeyInfo();

        this.resetNewKeyStatus();
        document.getElementById("newKey").value = "";
      } else {
        this.showSnackbar("Replacement failed: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar(
        "An error occurred while changing the card password",
        "error",
      );
      console.error("Change key error:", error);
    }

    this.hideConfirmDialog();
  }

  resetNewKeyStatus() {
    const verifyBtn = document.getElementById("verifyNewKey");
    const changeBtn = document.getElementById("changeKey");

    verifyBtn.style.display = "flex";
    changeBtn.style.display = "none";
    this.newKeyData = null;
  }

  populateForm() {
    document.getElementById("steamPath").value =
      this.currentConfig.steam_path || "";
    document.getElementById("debugMode").checked =
      this.currentConfig.debug_mode || false;
    document.getElementById("loggingFiles").checked =
      this.currentConfig.logging_files !== false;
    document.getElementById("showConsole").checked =
      this.currentConfig.show_console !== false;

    this.validateSteamPath();
  }

  async saveConfig() {
    try {
      const config = {
        key: this.currentConfig.key || "",
        steam_path: document.getElementById("steamPath").value.trim(),
        debug_mode: document.getElementById("debugMode").checked,
        logging_files: document.getElementById("loggingFiles").checked,
        show_console: document.getElementById("showConsole").checked,
      };

      const response = await fetch("/api/config/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (data.success) {
        this.showSnackbar("Configuration saved", "success");
        await this.loadConfig();
      } else {
        this.showSnackbar("Save failed: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar(
        "An error occurred while saving the configuration",
        "error",
      );
      console.error("Save config error:", error);
    }
  }

  async resetConfig() {
    try {
      const response = await fetch("/api/config/reset", {
        method: "POST",
      });

      const data = await response.json();

      if (data.success) {
        this.showSnackbar(
          "The configuration has been reset (the card password remains unchanged)",
          "success",
        );
        await this.loadConfig();
      } else {
        this.showSnackbar("Reset failed: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar(
        "An error occurred while resetting the configuration",
        "error",
      );
      console.error("Reset config error:", error);
    }

    this.hideConfirmDialog();
  }

  async testConfig() {
    this.showSnackbar("Testing configuration...", "info");

    try {
      const response = await fetch("/api/config");
      const data = await response.json();

      if (data.success) {
        let messages = [];

        if (data.config.steam_path) {
          messages.push("✓ Steam Path configuration is normal");
        } else {
          messages.push("✗ Steam Abnormal path configuration");
        }

        if (this.currentKeyInfo) {
          const expiresAt = new Date(this.currentKeyInfo.expiresAt);
          let isExpired = expiresAt < new Date();

          if ((this.currentKeyInfo.type = "permanent")) {
            isExpired = false;
          }

          if (this.currentKeyInfo.isActive && !isExpired) {
            messages.push("✓ Card secret status is normal");
          } else {
            messages.push("✗ Abnormal card secret status");
          }
        }

        this.showSnackbar(
          `Configuration test completed: ${messages.join(", ")}`,
          "success",
        );
      } else {
        this.showSnackbar(
          "Configuration test failed: " + data.message,
          "error",
        );
      }
    } catch (error) {
      this.showSnackbar(
        "An error occurred while configuring the test",
        "error",
      );
      console.error("Test config error:", error);
    }
  }

  detectSteamPath() {
    const commonPaths = [
      "C:\\Program Files (x86)\\Steam",
      "C:\\Program Files\\Steam",
      "D:\\Steam",
      "E:\\Steam",
    ];

    const suggestedPath = commonPaths[0];
    document.getElementById("steamPath").value = suggestedPath;

    this.validateSteamPath();
    this.showSnackbar(
      "It has been set as a common path, please confirm whether it is correct",
      "info",
    );
  }

  validateSteamPath() {
    const steamPath = document.getElementById("steamPath").value.trim();
    const statusElement = document.getElementById("steamPathStatus");

    if (!steamPath) {
      statusElement.className = "status-indicator";
      statusElement.innerHTML = `
                <span class="material-icons status-icon">info</span>
                <span class="status-text">The automatically detected path will be used</span>
            `;
    } else {
      if (steamPath.toLowerCase().includes("steam")) {
        statusElement.className = "status-indicator success";
        statusElement.innerHTML = `
                    <span class="material-icons status-icon">check_circle</span>
                    <span class="status-text">The path format looks correct</span>
                `;
      } else {
        statusElement.className = "status-indicator warning";
        statusElement.innerHTML = `
                    <span class="material-icons status-icon">warning</span>
                    <span class="status-text">The path may be incorrect, please confirm</span>
                `;
      }
    }
  }

  updateConfigStatus() {
    const statusGrid = document.getElementById("configStatusGrid");
    const config = this.currentConfig;

    const statusCards = [];

    if (config.steam_path && config.steam_path_exists) {
      statusCards.push({
        type: "success",
        icon: "folder",
        title: "Steam path",
        description: `Path is valid: ${config.steam_path}`,
      });
    } else if (config.steam_path) {
      statusCards.push({
        type: "warning",
        icon: "folder_off",
        title: "Steam path",
        description: "Path is set but may be invalid",
      });
    } else {
      statusCards.push({
        type: "error",
        icon: "error",
        title: "Steam path",
        description: "Not set or auto-detection failed",
      });
    }

    if (config.debug_mode) {
      statusCards.push({
        type: "warning",
        icon: "bug_report",
        title: "Debug mode",
        description: "Enabled, detailed logs will be output",
      });
    }

    if (config.logging_files) {
      statusCards.push({
        type: "success",
        icon: "description",
        title: "Log file",
        description: "Enabled, logs will be saved to file",
      });
    }

    statusGrid.innerHTML = statusCards
      .map(
        (card) => `
            <div class="status-card ${card.type}">
                <span class="material-icons status-card-icon">${card.icon}</span>
                <div class="status-card-content">
                    <div class="status-card-title">${card.title}</div>
                    <div class="status-card-description">${card.description}</div>
                </div>
            </div>
        `,
      )
      .join("");
  }

  showConfirmDialog(title, message, confirmAction) {
    document.getElementById("dialogTitle").textContent = title;
    document.getElementById("dialogMessage").textContent = message;
    this.confirmAction = confirmAction;

    const dialog = document.getElementById("confirmDialog");
    dialog.classList.add("show");
  }

  hideConfirmDialog() {
    const dialog = document.getElementById("confirmDialog");
    dialog.classList.remove("show");
    this.confirmAction = null;
  }

  executeConfirmAction() {
    if (this.confirmAction) {
      this.confirmAction();
    }
    this.hideConfirmDialog();
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
}

function goBack() {
  window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", () => {
  new SettingsManager();
});
