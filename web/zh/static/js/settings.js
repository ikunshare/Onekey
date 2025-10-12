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
        "重置配置",
        "确定要重置所有配置为默认值吗？此操作不可恢复。",
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
        "更换卡密",
        "确定要更换为新的卡密吗？更换后需要重新验证。",
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
        this.showSnackbar("加载配置失败: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar("无法连接到服务器", "error");
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
                            <strong>未设置卡密</strong><br>
                            请在下方输入您的授权卡密
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
                            <strong>卡密验证失败</strong><br>
                            当前卡密无效或已过期，请更换新的卡密
                        </div>
                    </div>
                `;
      }
    } catch (error) {
      keyInfoSection.innerHTML = `
                <div class="expiry-warning">
                    <span class="material-icons">error</span>
                    <div>
                        <strong>获取卡密信息失败</strong><br>
                        请检查网络连接或联系客服
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
      day: "日卡",
      week: "周卡",
      month: "月卡",
      year: "年卡",
      permanent: "永久卡",
    };

    let statusBadge = "";
    if (isExpired && keyInfo.type != "permanent") {
      statusBadge =
        '<span class="key-status-badge expired"><span class="material-icons" style="font-size: 14px;">cancel</span>已过期</span>';
    } else if (!keyInfo.isActive) {
      statusBadge =
        '<span class="key-status-badge inactive"><span class="material-icons" style="font-size: 14px;">pause</span>未激活</span>';
    } else {
      statusBadge =
        '<span class="key-status-badge active"><span class="material-icons" style="font-size: 14px;">check_circle</span>正常</span>';
    }

    let warningSection = "";
    if (isExpiringSoon) {
      warningSection = `
                <div class="expiry-warning">
                    <span class="material-icons">schedule</span>
                    <div>
                        <strong>即将到期提醒</strong><br>
                        您的卡密将在 ${daysLeft} 天后到期，请及时续费
                    </div>
                </div>
            `;
    }

    keyInfoSection.innerHTML = `
            <div class="key-info-grid">
                <div class="key-info-card">
                    <span class="material-icons key-info-icon">fingerprint</span>
                    <div class="key-info-content">
                        <div class="key-info-label">卡密</div>
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
                        <div class="key-info-label">类型</div>
                        <div class="key-info-value">${
                          typeNames[keyInfo.type] || keyInfo.type
                        }</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">toggle_on</span>
                    <div class="key-info-content">
                        <div class="key-info-label">状态</div>
                        <div class="key-info-value">${statusBadge}</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">event</span>
                    <div class="key-info-content">
                        <div class="key-info-label">到期时间</div>
                        <div class="key-info-value">${expiresAt.toLocaleDateString()} ${expiresAt
                          .toLocaleTimeString()
                          .substring(0, 5)}</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">analytics</span>
                    <div class="key-info-content">
                        <div class="key-info-label">使用次数</div>
                        <div class="key-info-value">${keyInfo.usageCount} / ${
                          keyInfo.totalUsage || "∞"
                        }</div>
                    </div>
                </div>

                <div class="key-info-card">
                    <span class="material-icons key-info-icon">schedule</span>
                    <div class="key-info-content">
                        <div class="key-info-label">创建时间</div>
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
      this.showSnackbar("请输入新卡密", "error");
      return;
    }

    if (!key.match(/^[A-Z0-9_-]+$/)) {
      this.showSnackbar("卡密格式不正确", "error");
      return;
    }

    const verifyBtn = document.getElementById("verifyNewKey");
    const changeBtn = document.getElementById("changeKey");

    verifyBtn.disabled = true;
    verifyBtn.innerHTML =
      '<span class="material-icons">hourglass_empty</span>验证中...';

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
        this.showSnackbar("新卡密验证成功！", "success");

        changeBtn.style.display = "flex";
        verifyBtn.style.display = "none";

        const typeNames = {
          day: "日卡",
          week: "周卡",
          month: "月卡",
          year: "年卡",
          permanent: "永久卡",
        };

        const expiresAt = new Date(data.info.expiresAt);
        this.showSnackbar(
          `验证成功！新卡密类型：${
            typeNames[data.info.type]
          }，有效期至：${expiresAt.toLocaleDateString()}`,
          "success",
        );
      } else {
        this.showSnackbar("新卡密无效或已过期", "error");
        this.newKeyData = null;
      }
    } catch (error) {
      this.showSnackbar("验证失败，请检查网络连接", "error");
      console.error("New key verification error:", error);
    } finally {
      verifyBtn.disabled = false;
      verifyBtn.innerHTML = '<span class="material-icons">check</span>验证';
    }
  }

  async changeKey() {
    if (!this.newKeyData) {
      this.showSnackbar("请先验证新卡密", "error");
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
        this.showSnackbar("卡密更换成功！", "success");

        await this.loadKeyInfo();

        this.resetNewKeyStatus();
        document.getElementById("newKey").value = "";
      } else {
        this.showSnackbar("更换失败: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar("更换卡密时发生错误", "error");
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
        this.showSnackbar("配置已保存", "success");
        await this.loadConfig();
      } else {
        this.showSnackbar("保存失败: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar("保存配置时发生错误", "error");
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
        this.showSnackbar("配置已重置（卡密保持不变）", "success");
        await this.loadConfig();
      } else {
        this.showSnackbar("重置失败: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar("重置配置时发生错误", "error");
      console.error("Reset config error:", error);
    }

    this.hideConfirmDialog();
  }

  async testConfig() {
    this.showSnackbar("正在测试配置...", "info");

    try {
      const response = await fetch("/api/config");
      const data = await response.json();

      if (data.success) {
        let messages = [];

        if (data.config.steam_path) {
          messages.push("✓ Steam 路径配置正常");
        } else {
          messages.push("✗ Steam 路径配置异常");
        }

        if (this.currentKeyInfo) {
          const expiresAt = new Date(this.currentKeyInfo.expiresAt);
          let isExpired = expiresAt < new Date();

          if ((this.currentKeyInfo.type = "permanent")) {
            isExpired = false;
          }

          if (this.currentKeyInfo.isActive && !isExpired) {
            messages.push("✓ 卡密状态正常");
          } else {
            messages.push("✗ 卡密状态异常");
          }
        }

        this.showSnackbar(`配置测试完成: ${messages.join(", ")}`, "success");
      } else {
        this.showSnackbar("配置测试失败: " + data.message, "error");
      }
    } catch (error) {
      this.showSnackbar("配置测试时发生错误", "error");
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
    this.showSnackbar("已设置为常见路径，请确认是否正确", "info");
  }

  validateSteamPath() {
    const steamPath = document.getElementById("steamPath").value.trim();
    const statusElement = document.getElementById("steamPathStatus");

    if (!steamPath) {
      statusElement.className = "status-indicator";
      statusElement.innerHTML = `
                <span class="material-icons status-icon">info</span>
                <span class="status-text">将使用自动检测的路径</span>
            `;
    } else {
      if (steamPath.toLowerCase().includes("steam")) {
        statusElement.className = "status-indicator success";
        statusElement.innerHTML = `
                    <span class="material-icons status-icon">check_circle</span>
                    <span class="status-text">路径格式看起来正确</span>
                `;
      } else {
        statusElement.className = "status-indicator warning";
        statusElement.innerHTML = `
                    <span class="material-icons status-icon">warning</span>
                    <span class="status-text">路径可能不正确，请确认</span>
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
        title: "Steam 路径",
        description: `路径有效: ${config.steam_path}`,
      });
    } else if (config.steam_path) {
      statusCards.push({
        type: "warning",
        icon: "folder_off",
        title: "Steam 路径",
        description: "路径已设置但可能无效",
      });
    } else {
      statusCards.push({
        type: "error",
        icon: "error",
        title: "Steam 路径",
        description: "未设置或自动检测失败",
      });
    }

    if (config.debug_mode) {
      statusCards.push({
        type: "warning",
        icon: "bug_report",
        title: "调试模式",
        description: "已启用，会输出详细日志",
      });
    }

    if (config.logging_files) {
      statusCards.push({
        type: "success",
        icon: "description",
        title: "日志文件",
        description: "已启用，日志将保存到文件",
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
