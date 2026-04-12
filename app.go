package main

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/wailsapp/wails/v2/pkg/runtime"

	"onekey/internal/config"
	"onekey/internal/i18n"
	"onekey/internal/manifest"
	"onekey/internal/models"
	"onekey/internal/steamtools"
)

type App struct {
	ctx        context.Context
	config     *config.Manager
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
	i18n.SetLanguage(a.config.AppConfig.Language)
}

func (a *App) shutdown(ctx context.Context) {}

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
	return models.SimpleResponse{Success: true, Message: i18n.T("web.config_saved")}
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
func (a *App) StartUnlock(appID string, dlc bool) models.SimpleResponse {
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

	go a.runUnlockTask(validID, dlc)
	return models.SimpleResponse{Success: true, Message: i18n.T("web.task_started")}
}

func (a *App) runUnlockTask(appID string, dlc bool) {
	emit := func(msgType, message string) {
		runtime.EventsEmit(a.ctx, "task_progress", map[string]any{
			"type":    msgType,
			"message": message,
		})
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
	appInfo, manifestInfo, err := fetchAppData(apiKey, appID, dlc)
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

	handler := manifest.NewHandler(a.config.SteamPath)
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
	emit("info", i18n.T("task.step.steamtools_done",
		"appid", appInfo.AppID,
		"depots", fmt.Sprintf("%d", len(processed)),
	))

	// 5. Done
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
