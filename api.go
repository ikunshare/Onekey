package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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

	var result struct {
		Key  string          `json:"key"`
		Info *models.KeyInfo `json:"info"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("%s", i18n.T("error.invalid_response", "error", err.Error()))
	}
	if result.Info == nil {
		return nil, fmt.Errorf("%s", i18n.T("api.key_not_exist"))
	}
	return result.Info, nil
}

func fetchAppData(apiKey, appID string, dlc bool) (*models.SteamAppInfo, *models.SteamAppManifestInfo, error) {
	reqBody, _ := json.Marshal(map[string]any{
		"app_id": appID,
		"dlc":    dlc,
	})

	req, err := http.NewRequest("POST", constants.SteamAPIBase+"/getGame", bytes.NewReader(reqBody))
	if err != nil {
		return nil, nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Api-Key", apiKey)

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
			msg = getStringField(raw, "detail")
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

	appData, ok := raw["data"].(map[string]any)
	if !ok {
		appData = raw
	}
	if appData == nil {
		return nil, nil, fmt.Errorf("%s", i18n.T("error.no_game_data"))
	}

	appInfo := &models.SteamAppInfo{
		AppID:                 appID,
		Name:                  getStringField(appData, "name"),
		DLCCount:              getIntField(appData, "totalDLCCount", getIntField(appData, "dlcCount", 0)),
		DepotCount:            getIntField(appData, "depotCount", 0),
		WorkshopDecryptionKey: getStringField(appData, "workshopDecryptionKey"),
	}
	if appInfo.WorkshopDecryptionKey == "" {
		appInfo.WorkshopDecryptionKey = "None"
	}

	manifestInfo := &models.SteamAppManifestInfo{}

	if gameManifests, ok := appData["gameManifests"].([]any); ok {
		for _, item := range gameManifests {
			if m, ok := item.(map[string]any); ok {
				manifestInfo.MainApp = append(manifestInfo.MainApp, parseManifest(m))
			}
		}
	}

	if dlc {
		if dlcManifests, ok := appData["dlcManifests"].([]any); ok {
			for _, dlcItem := range dlcManifests {
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
	}

	return appInfo, manifestInfo, nil
}

func parseManifest(m map[string]any) models.ManifestInfo {
	return models.ManifestInfo{
		AppID:      fmt.Sprintf("%v", m["app_id"]),
		DepotID:    fmt.Sprintf("%v", m["depot_id"]),
		DepotKey:   getStringField(m, "depot_key"),
		ManifestID: fmt.Sprintf("%v", m["manifest_id"]),
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
