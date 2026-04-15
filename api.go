package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"time"

	"onekey/internal/constants"
	"onekey/internal/i18n"
	"onekey/internal/models"
)

var httpClient = &http.Client{Timeout: 60 * time.Second}

func fetchKeyInfo(key string) (*models.KeyInfo, error) {
	body, _ := json.Marshal(map[string]string{"key": key})
	resp, err := httpClient.Post(
		constants.SteamAPIBase+"/getKeyInfo",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result models.KeyInfoAPIResponse
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if result.Info == nil {
		return nil, fmt.Errorf("%s", i18n.T("api.key_not_exist"))
	}
	return result.Info, nil
}

func fetchAppData(apiKey, appID string) (*models.SteamAppInfo, *models.SteamAppManifestInfo, error) {
	// New backend expects app_id as int
	appIDInt, err := strconv.Atoi(appID)
	if err != nil {
		return nil, nil, fmt.Errorf("%s", i18n.T("web.invalid_appid"))
	}

	reqBody, _ := json.Marshal(map[string]any{
		"app_id": appIDInt,
	})

	req, err := http.NewRequest("POST", constants.SteamAPIBase+"/getGame", bytes.NewReader(reqBody))
	if err != nil {
		return nil, nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", apiKey)

	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, nil, err
	}

	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, nil, fmt.Errorf("%s", i18n.T("error.invalid_json"))
	}

	if resp.StatusCode != 200 {
		msg := getStringField(raw, "msg")
		if msg == "" {
			msg = getStringField(raw, "message")
		}
		if msg == "" {
			msg = i18n.T("error.unknown")
		}
		return nil, nil, fmt.Errorf("%s", i18n.T("error.api_response", "error", msg))
	}

	if code, ok := raw["code"].(float64); ok && int(code) != 200 {
		msg := getStringField(raw, "msg")
		return nil, nil, fmt.Errorf("%s", i18n.T("error.server_response", "error", msg))
	}

	// App info is in root-level "app" object
	appData, ok := raw["app"].(map[string]any)
	if !ok || appData == nil {
		return nil, nil, fmt.Errorf("%s", i18n.T("error.no_game_data"))
	}

	appInfo := &models.SteamAppInfo{
		AppID:                 fmt.Sprintf("%d", getIntField(appData, "appid", 0)),
		Name:                  getStringField(appData, "name"),
		HeaderImage:           getStringField(appData, "image"),
		AccessToken:           getStringField(appData, "token"),
		DLCCount:              getIntField(appData, "dlcCount", 0),
		DepotCount:            0,
		WorkshopDecryptionKey: getStringField(appData, "workshopKey"),
	}
	if appInfo.WorkshopDecryptionKey == "" {
		appInfo.WorkshopDecryptionKey = "None"
	}

	manifestInfo := &models.SteamAppManifestInfo{}

	// Game depots are at root level "gameDepots"
	if gameDepots, ok := raw["gameDepots"].([]any); ok {
		appInfo.DepotCount = len(gameDepots)
		for _, item := range gameDepots {
			if m, ok := item.(map[string]any); ok {
				manifestInfo.MainApp = append(manifestInfo.MainApp, parseManifest(m))
			}
		}
	}

	// DLC depots are at root level "dlcDepots", grouped by DLC
	if dlcDepots, ok := raw["dlcDepots"].([]any); ok {
		for _, dlcItem := range dlcDepots {
			if dlcMap, ok := dlcItem.(map[string]any); ok {
				if manifests, ok := dlcMap["manifests"].([]any); ok {
					for _, item := range manifests {
						if m, ok := item.(map[string]any); ok {
							manifestInfo.DLCs = append(manifestInfo.DLCs, parseManifest(m))
						}
					}
				}
			}
		}
	}

	// When gameManifests is null but dlcManifests has content, the input app_id
	// is itself a DLC. Treat DLC manifests as main app manifests so they get
	// processed correctly (downloaded to depotcache and included in Lua config).
	if len(manifestInfo.MainApp) == 0 && len(manifestInfo.DLCs) > 0 {
		manifestInfo.MainApp = manifestInfo.DLCs
		manifestInfo.DLCs = nil
		appInfo.DepotCount = len(manifestInfo.MainApp)
	}

	return appInfo, manifestInfo, nil
}

func parseManifest(m map[string]any) models.ManifestInfo {
	return models.ManifestInfo{
		AppID:      intFieldStr(m, "app_id"),
		DepotID:    intFieldStr(m, "depot_id"),
		DepotKey:   getStringField(m, "depot_key"),
		ManifestID: getStringField(m, "manifest_id"),
		Size:       getStringField(m, "size"),
		URL:        getStringField(m, "url"),
	}
}

func getStringField(m map[string]any, key string) string {
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
		return fmt.Sprintf("%v", v)
	}
	return ""
}

// intFieldStr extracts a JSON number field as an integer string, avoiding
// scientific notation from float64 (e.g. "4.11013e+06" → "4110130").
func intFieldStr(m map[string]any, key string) string {
	if v, ok := m[key]; ok {
		switch n := v.(type) {
		case float64:
			return fmt.Sprintf("%d", int64(n))
		case string:
			return n
		}
		return fmt.Sprintf("%v", v)
	}
	return ""
}

func getIntField(m map[string]any, key string, defaultVal int) int {
	if v, ok := m[key]; ok {
		switch n := v.(type) {
		case float64:
			return int(n)
		case int:
			return n
		}
	}
	return defaultVal
}

func searchStore(term, lang string) (*models.StoreSearchResult, error) {
	u := fmt.Sprintf("https://store.steampowered.com/api/storesearch/?term=%s&l=%s&cc=CN",
		url.QueryEscape(term), url.QueryEscape(lang))
	resp, err := httpClient.Get(u)
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	var result models.StoreSearchResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	return &result, nil
}

// fetchParentApp queries Steam appdetails to check if appID is a DLC/music/etc.
// Returns (parentAppID, parentName) if it has a parent game, or ("", "") if not.
func fetchParentApp(appID string) (string, string) {
	u := fmt.Sprintf("https://store.steampowered.com/api/appdetails?appids=%s", appID)
	resp, err := httpClient.Get(u)
	if err != nil {
		return "", ""
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", ""
	}
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return "", ""
	}
	appData, ok := raw[appID].(map[string]any)
	if !ok {
		return "", ""
	}
	d, ok := appData["data"].(map[string]any)
	if !ok {
		return "", ""
	}
	// Any app with a "fullgame" field is a child (DLC, music, etc.)
	fg, ok := d["fullgame"].(map[string]any)
	if !ok {
		return "", ""
	}
	return getStringField(fg, "appid"), getStringField(fg, "name")
}

func fetchAnnouncements() ([]models.Announcement, error) {
	resp, err := httpClient.Get(constants.SteamAPIBase + "/announcements")
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result struct {
		Code int              `json:"code"`
		Data json.RawMessage  `json:"data"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if result.Code != 200 {
		return nil, fmt.Errorf("%s", i18n.T("announcement.fetch_failed"))
	}

	var announcements []models.Announcement
	if err := json.Unmarshal(result.Data, &announcements); err != nil {
		return nil, err
	}
	return announcements, nil
}

func fetchUpdateInfo(currentVersion string) (*models.UpdateInfo, error) {
	resp, err := httpClient.Get(constants.SteamAPIBase + "/version/app")
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result struct {
		Code int             `json:"code"`
		Data json.RawMessage `json:"data"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if result.Code != 200 {
		return nil, fmt.Errorf("%s", i18n.T("error.update_check_failed"))
	}

	var versionData struct {
		Version     string `json:"version"`
		DownloadURL string `json:"downloadUrl"`
		Changelog   string `json:"changelog"`
	}
	if err := json.Unmarshal(result.Data, &versionData); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}

	info := &models.UpdateInfo{
		CurrentVersion: currentVersion,
		LatestVersion:  versionData.Version,
		DownloadURL:    versionData.DownloadURL,
		Changelog:      versionData.Changelog,
	}
	info.HasUpdate = info.LatestVersion != "" && info.LatestVersion != currentVersion
	return info, nil
}

func downloadKernel() ([]byte, error) {
	// 1. Fetch kernel metadata from /version/kernel
	resp, err := httpClient.Get(constants.SteamAPIBase + "/version/kernel")
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result struct {
		Code int             `json:"code"`
		Data json.RawMessage `json:"data"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if result.Code != 200 {
		return nil, fmt.Errorf("%s", i18n.T("error.kernel_download_failed"))
	}

	var kernelInfo struct {
		DownloadURL string `json:"downloadUrl"`
	}
	if err := json.Unmarshal(result.Data, &kernelInfo); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if kernelInfo.DownloadURL == "" {
		return nil, fmt.Errorf("%s", i18n.T("error.kernel_download_failed"))
	}

	// 2. Download the actual binary from downloadUrl
	dlResp, err := httpClient.Get(kernelInfo.DownloadURL)
	if err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.network", "error", err.Error()))
	}
	defer dlResp.Body.Close()

	if dlResp.StatusCode != 200 {
		return nil, fmt.Errorf("%s", i18n.T("error.kernel_download_failed"))
	}

	return io.ReadAll(dlResp.Body)
}
