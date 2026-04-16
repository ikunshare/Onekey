package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"golang.org/x/sys/windows/registry"
	"github.com/wailsapp/wails/v2/pkg/runtime"

	"onekey/internal/config"
	"onekey/internal/httpclient"
	"onekey/internal/i18n"
	"onekey/internal/library"
	"onekey/internal/patcher"
	"onekey/internal/manifest"
	"onekey/internal/models"
	"onekey/internal/steamtools"
)

const AppVersion = "3.0.0"

type App struct {
	ctx        context.Context
	config     *config.Manager
	library    *library.Manager
	logFile    *os.File
	taskStatus string
	taskResult *models.TaskResult
	taskMu     sync.Mutex
}

func NewApp() *App {
	return &App{
		taskStatus: "idle",
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.config = config.NewManager()
	a.library = library.NewManager()
	i18n.SetLanguage(a.config.AppConfig.Language)
	if a.config.AppConfig.ProxyURL != "" {
		httpclient.Shared().SetProxy(a.config.AppConfig.ProxyURL)
	}
	a.initLogFile()
	go a.config.InitCDNWithLatencyTest()
}

func (a *App) shutdown(ctx context.Context) {
	if a.logFile != nil {
		a.logFile.Close()
	}
	if a.config != nil {
		a.config.Close()
	}
	if a.library != nil {
		a.library.Close()
	}
}

// initLogFile opens (or creates) today's log file under %APPDATA%\Onekey\logs\.
func (a *App) initLogFile() {
	if !a.config.AppConfig.LoggingFiles {
		return
	}
	logsDir := filepath.Join(a.config.ConfigDir(), "logs")
	os.MkdirAll(logsDir, 0755)
	name := time.Now().Format("2006-01-02") + ".log"
	f, err := os.OpenFile(filepath.Join(logsDir, name), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return
	}
	a.logFile = f
}

// writeLog appends a timestamped line to the log file.
func (a *App) writeLog(level, message string) {
	if a.logFile == nil {
		return
	}
	line := fmt.Sprintf("[%s] [%s] %s\n", time.Now().Format("15:04:05"), level, message)
	a.logFile.WriteString(line)
}

// GetConfig returns basic config info for the frontend.
func (a *App) GetConfig() models.ConfigResponse {
	steamPath := ""
	if a.config.SteamPath != "" {
		steamPath = a.config.SteamPath
	}
	return models.ConfigResponse{
		Success: true,
		Config: models.BasicConfig{
			SteamPath: steamPath,
			DebugMode: a.config.AppConfig.DebugMode,
		},
	}
}

// GetDetailedConfig returns all config fields.
func (a *App) GetDetailedConfig() models.DetailedConfigResponse {
	steamPath := ""
	steamPathExists := false
	if a.config.SteamPath != "" {
		steamPath = a.config.SteamPath
		steamPathExists = config.PathExists(steamPath)
	}
	return models.DetailedConfigResponse{
		Success: true,
		Config: models.DetailedConfig{
			SteamPath:       steamPath,
			DebugMode:       a.config.AppConfig.DebugMode,
			LoggingFiles:    a.config.AppConfig.LoggingFiles,
			ShowConsole:     a.config.AppConfig.ShowConsole,
			SteamPathExists: steamPathExists,
			Key:             a.config.AppConfig.Key,
			Language:        a.config.AppConfig.Language,
			ProxyURL:        a.config.AppConfig.ProxyURL,
		},
	}
}

// UpdateConfig saves new config values.
func (a *App) UpdateConfig(req models.UpdateConfigRequest) models.SimpleResponse {
	err := a.config.Update(req)
	if err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("web.config_save_failed", "error", err.Error())}
	}
	i18n.SetLanguage(a.config.AppConfig.Language)
	httpclient.Shared().SetProxy(a.config.AppConfig.ProxyURL)
	return models.SimpleResponse{Success: true, Message: i18n.T("web.config_saved")}
}

func (a *App) TestProxy(proxyURL string) models.SimpleResponse {
	ok, msg := testProxyConnectivity(proxyURL)
	return models.SimpleResponse{Success: ok, Message: msg}
}

// ResetConfig resets to default values.
func (a *App) ResetConfig() models.SimpleResponse {
	err := a.config.Reset()
	if err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("web.config_reset_failed", "error", err.Error())}
	}
	return models.SimpleResponse{Success: true, Message: i18n.T("web.config_reset")}
}

// VerifyKey checks an API key against the remote server.
func (a *App) VerifyKey(key string) models.KeyInfoAPIResponse {
	key = strings.TrimSpace(key)
	if key == "" {
		return models.KeyInfoAPIResponse{Key: "", Info: nil}
	}
	info, err := fetchKeyInfo(key)
	if err != nil {
		return models.KeyInfoAPIResponse{Key: "", Info: nil}
	}
	return models.KeyInfoAPIResponse{Key: key, Info: info}
}

// GetTaskStatus returns current task status.
func (a *App) GetTaskStatus() models.TaskStatusResponse {
	a.taskMu.Lock()
	defer a.taskMu.Unlock()
	return models.TaskStatusResponse{
		Status: a.taskStatus,
		Result: a.taskResult,
	}
}

// StartUnlock begins the unlock workflow via SteamTools.
func (a *App) StartUnlock(appID string) models.SimpleResponse {
	a.taskMu.Lock()
	if a.taskStatus == "running" {
		a.taskMu.Unlock()
		return models.SimpleResponse{Success: false, Message: i18n.T("web.task_running")}
	}

	appID = strings.TrimSpace(appID)
	if appID == "" {
		a.taskMu.Unlock()
		return models.SimpleResponse{Success: false, Message: i18n.T("web.invalid_appid")}
	}

	parts := strings.Split(appID, "-")
	validID := ""
	for _, p := range parts {
		if isDigits(p) {
			validID = p
			break
		}
	}
	if validID == "" {
		a.taskMu.Unlock()
		return models.SimpleResponse{Success: false, Message: i18n.T("web.invalid_format")}
	}

	a.taskStatus = "running"
	a.taskResult = nil
	a.taskMu.Unlock()

	go a.runUnlockTask(validID)
	return models.SimpleResponse{Success: true, Message: i18n.T("web.task_started")}
}

func (a *App) runUnlockTask(appID string) {
	emit := func(msgType, message string) {
		runtime.EventsEmit(a.ctx, "task_progress", map[string]any{
			"type":    msgType,
			"message": message,
		})
		a.writeLog(msgType, message)
	}

	defer func() {
		a.taskMu.Lock()
		defer a.taskMu.Unlock()
		if a.taskStatus == "running" {
			a.taskStatus = "error"
			if a.taskResult == nil {
				a.taskResult = &models.TaskResult{Success: false, Message: i18n.T("error.unknown")}
			}
		}
		runtime.EventsEmit(a.ctx, "task_done", a.taskResult)
	}()

	apiKey := a.config.AppConfig.Key

	if a.config.SteamPath == "" {
		emit("error", i18n.T("task.no_steam_path"))
		a.setTaskError(i18n.T("task.no_steam_path"))
		return
	}

	// 1. Validate key
	emit("info", i18n.T("task.step.auth"))
	_, err := fetchKeyInfo(apiKey)
	if err != nil {
		emit("warning", fmt.Sprintf("%s: %s", i18n.T("api.key_info_failed"), err.Error()))
	}

	// 2. Fetch game data from API
	emit("info", i18n.T("api.fetching_game", "app_id", appID))
	appInfo, manifestInfo, err := fetchAppData(apiKey, appID)
	if err != nil {
		emit("error", err.Error())
		a.setTaskError(err.Error())
		return
	}
	emit("info", i18n.T("api.game_name", "name", appInfo.Name))

	allManifests := append(manifestInfo.MainApp, manifestInfo.DLCs...)
	if len(allManifests) == 0 {
		emit("error", i18n.T("error.manifest_empty"))
		a.setTaskError(i18n.T("error.manifest_empty"))
		return
	}

	// 3. Download manifests to depotcache
	emit("info", i18n.T("manifest.start_batch", "count", fmt.Sprintf("%d", len(allManifests))))

	handler := manifest.NewHandler(a.config.SteamPath, a.config.GetCDNList())
	processed, err := handler.ProcessManifests(allManifests, func(msg string, current, total int) {
		emit("info", msg)
	})
	if err != nil {
		emit("error", err.Error())
		a.setTaskError(err.Error())
		return
	}

	if len(processed) == 0 {
		emit("error", i18n.T("error.manifest_process_none"))
		a.setTaskError(i18n.T("error.manifest_process_none"))
		return
	}

	// 4. Generate SteamTools Lua unlock file
	emit("info", i18n.T("task.step.steamtools_setup"))
	if err := steamtools.Setup(a.config.SteamPath, appInfo, processed); err != nil {
		emit("error", i18n.T("error.steamtools_setup", "error", err.Error()))
		a.setTaskError(i18n.T("error.steamtools_setup", "error", err.Error()))
		return
	}

	luaPath := filepath.Join(a.config.SteamPath, "config", "stplug-in", appInfo.AppID+".lua")

	emit("info", i18n.T("task.step.steamtools_done",
		"appid", appInfo.AppID,
		"depots", fmt.Sprintf("%d", len(processed)),
	))

	// 5. Save to game library (detect DLC and group under parent)
	if a.library != nil {
		appIDInt := 0
		fmt.Sscanf(appInfo.AppID, "%d", &appIDInt)

		// Check if this app is a DLC by querying Steam
		parentID, parentName := fetchParentApp(appInfo.AppID, a.config.AppConfig.Key)
		if parentID != "" && parentName != "" {
			// It's a DLC — merge under parent game
			parentIDInt := 0
			fmt.Sscanf(parentID, "%d", &parentIDInt)
			if parentIDInt > 0 {
				emit("info", i18n.T("library.dlc_grouped", "dlc", appInfo.Name, "parent", parentName))
				a.library.MergeDLCUnlock(parentIDInt, parentName, luaPath, processed)
				// Also remove the DLC's standalone entry if it was added earlier
				if a.library.Exists(appIDInt) {
					a.library.Remove(appIDInt, a.config.SteamPath)
				}
			}
		} else {
			// It's a main game — save normally
			a.library.SaveUnlock(appIDInt, appInfo.Name, appInfo.HeaderImage, luaPath,
				appInfo.DLCCount, appInfo.DepotCount, manifestInfo.MainApp, manifestInfo.DLCs)
		}
	}

	// 6. Done
	emit("info", i18n.T("task.step.finish"))

	a.taskMu.Lock()
	a.taskStatus = "completed"
	a.taskResult = &models.TaskResult{
		Success: true,
		Message: i18n.T("task.step.finish"),
	}
	a.taskMu.Unlock()
}

func (a *App) setTaskError(msg string) {
	a.taskMu.Lock()
	a.taskStatus = "error"
	a.taskResult = &models.TaskResult{Success: false, Message: msg}
	a.taskMu.Unlock()
}

func isDigits(s string) bool {
	if s == "" {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

// SearchStore searches the Steam store for games matching the given term.
func (a *App) SearchStore(term string) models.StoreSearchResult {
	term = strings.TrimSpace(term)
	if term == "" {
		return models.StoreSearchResult{}
	}
	lang := "schinese"
	if a.config.AppConfig.Language == "en" {
		lang = "english"
	}
	result, err := searchStore(term, lang, a.config.AppConfig.Key)
	if err != nil {
		return models.StoreSearchResult{}
	}
	return *result
}

// --- Game Library ---

// GetLibrary returns all games in the library.
func (a *App) GetLibrary() []models.LibraryGame {
	if a.library == nil {
		return nil
	}
	games := a.library.GetAll()
	if games == nil {
		return []models.LibraryGame{}
	}
	return games
}

// GetGameDetail returns a game with its depots and DLCs.
func (a *App) GetGameDetail(appID int) *models.LibraryGame {
	if a.library == nil {
		return nil
	}
	return a.library.GetGame(appID)
}

// AddToLibrary adds a game from search results.
// If it's a DLC, it auto-groups under the parent game.
func (a *App) AddToLibrary(appID int, name, tinyImage, appType string) models.SimpleResponse {
	if a.library == nil {
		return models.SimpleResponse{Success: false, Message: "library not available"}
	}

	if appType != "app" && appType != "" {
		parentID, parentName := fetchParentApp(fmt.Sprintf("%d", appID), a.config.AppConfig.Key)
		if parentID != "" && parentName != "" {
			parentIDInt := 0
			fmt.Sscanf(parentID, "%d", &parentIDInt)
			if parentIDInt > 0 {
				a.library.AddBasic(parentIDInt, parentName, "")
				return models.SimpleResponse{Success: true, Message: i18n.T("library.dlc_added_to_parent", "parent", parentName)}
			}
		}
	}

	err := a.library.AddBasic(appID, name, tinyImage)
	if err != nil {
		return models.SimpleResponse{Success: false, Message: err.Error()}
	}
	return models.SimpleResponse{Success: true, Message: i18n.T("library.added")}
}

// RemoveFromLibrary removes a game and deletes its Lua file.
func (a *App) RemoveFromLibrary(appID int) models.SimpleResponse {
	if a.library == nil {
		return models.SimpleResponse{Success: false, Message: "library not available"}
	}
	err := a.library.Remove(appID, a.config.SteamPath)
	if err != nil {
		return models.SimpleResponse{Success: false, Message: err.Error()}
	}
	return models.SimpleResponse{Success: true, Message: i18n.T("library.removed")}
}

// GetAnnouncements fetches announcements from the server.
func (a *App) GetAnnouncements() models.AnnouncementResponse {
	list, err := fetchAnnouncements()
	if err != nil {
		return models.AnnouncementResponse{Success: false}
	}
	return models.AnnouncementResponse{Success: true, Announcements: list}
}

// CheckUpdate checks for a new version from the server.
func (a *App) CheckUpdate() *models.UpdateInfo {
	info, err := fetchUpdateInfo(AppVersion)
	if err != nil {
		return &models.UpdateInfo{
			HasUpdate:      false,
			CurrentVersion: AppVersion,
		}
	}
	return info
}

// LoadKernel downloads the kernel file and saves it as xinput1_4.dll in the Steam root directory.
func (a *App) LoadKernel() models.SimpleResponse {
	if a.config.SteamPath == "" {
		return models.SimpleResponse{Success: false, Message: i18n.T("kernel.no_steam_path")}
	}

	data, err := downloadKernel()
	if err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("kernel.download_failed", "error", err.Error())}
	}

	dstPath := filepath.Join(a.config.SteamPath, "xinput1_4.dll")
	if err := os.WriteFile(dstPath, data, 0644); err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("kernel.save_failed", "error", err.Error())}
	}

	return models.SimpleResponse{Success: true, Message: i18n.T("kernel.download_success")}
}

// PatchVDF patches Steam's packageinfo.vdf to modify billingtype entries.
func (a *App) PatchVDF() models.SimpleResponse {
	if a.config.SteamPath == "" {
		return models.SimpleResponse{Success: false, Message: i18n.T("kernel.no_steam_path")}
	}

	count, err := patcher.PatchPackageInfo(a.config.SteamPath)
	if err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("patch.failed", "error", err.Error())}
	}
	if count == 0 {
		return models.SimpleResponse{Success: true, Message: i18n.T("patch.no_match")}
	}
	return models.SimpleResponse{Success: true, Message: i18n.T("patch.success", "count", fmt.Sprintf("%d", count))}
}

// RestartSteam kills the Steam process and relaunches it.
func (a *App) RestartSteam() models.SimpleResponse {
	killCmd := exec.Command("taskkill", "/F", "/IM", "steam.exe")
	_ = killCmd.Run()

	steamPath := a.config.SteamPath
	if steamPath == "" {
		return models.SimpleResponse{Success: false, Message: i18n.T("task.no_steam_path")}
	}
	steamExe := filepath.Join(steamPath, "steam.exe")
	if !config.PathExists(steamExe) {
		return models.SimpleResponse{Success: false, Message: i18n.T("steam.exe_not_found")}
	}
	cmd := exec.Command(steamExe)
	cmd.Dir = steamPath
	if err := cmd.Start(); err != nil {
		return models.SimpleResponse{Success: false, Message: i18n.T("steam.restart_failed", "error", err.Error())}
	}
	return models.SimpleResponse{Success: true, Message: i18n.T("steam.restart_success")}
}

const steamtoolsRegPath = `Software\Valve\Steamtools`

// GetKernelSettings reads SteamTools settings from the registry.
func (a *App) GetKernelSettings() models.KernelSettingsResponse {
	k, err := registry.OpenKey(registry.CURRENT_USER, steamtoolsRegPath, registry.QUERY_VALUE)
	if err != nil {
		// Key doesn't exist yet — return defaults (all false)
		return models.KernelSettingsResponse{Success: true, Settings: models.KernelSettings{}}
	}
	defer k.Close()

	readBool := func(name string) bool {
		v, _, err := k.GetStringValue(name)
		if err != nil {
			return false
		}
		return v == "1" || strings.EqualFold(v, "true")
	}

	return models.KernelSettingsResponse{
		Success: true,
		Settings: models.KernelSettings{
			ActivateUnlockMode: readBool("ActivateUnlockMode"),
			AlwaysStayUnlocked: readBool("AlwaysStayUnlocked"),
			NotUnlockDepot:     readBool("notUnlockDepot"),
		},
	}
}

// SetKernelSettings writes SteamTools settings to the registry.
func (a *App) SetKernelSettings(settings models.KernelSettings) models.SimpleResponse {
	k, _, err := registry.CreateKey(registry.CURRENT_USER, steamtoolsRegPath, registry.SET_VALUE)
	if err != nil {
		return models.SimpleResponse{Success: false, Message: err.Error()}
	}
	defer k.Close()

	boolStr := func(b bool) string {
		if b {
			return "1"
		}
		return "0"
	}

	k.SetStringValue("ActivateUnlockMode", boolStr(settings.ActivateUnlockMode))
	k.SetStringValue("AlwaysStayUnlocked", boolStr(settings.AlwaysStayUnlocked))
	k.SetStringValue("notUnlockDepot", boolStr(settings.NotUnlockDepot))

	return models.SimpleResponse{Success: true, Message: i18n.T("kernel_settings.saved")}
}
