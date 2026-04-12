package models

// AppConfig represents the application configuration.
type AppConfig struct {
	Key             string `json:"KEY"`
	DebugMode       bool   `json:"Debug_Mode"`
	LoggingFiles    bool   `json:"Logging_Files"`
	ShowConsole     bool   `json:"Show_Console"`
	CustomSteamPath string `json:"Custom_Steam_Path"`
	Language        string `json:"Language"`
}

// ManifestInfo holds information about a single manifest from the API.
type ManifestInfo struct {
	AppID      string `json:"app_id"`
	DepotID    string `json:"depot_id"`
	DepotKey   string `json:"depot_key"`
	ManifestID string `json:"manifest_id"`
	URL        string `json:"url"`
}

// SteamAppInfo holds game metadata.
type SteamAppInfo struct {
	AppID                 string `json:"app_id"`
	Name                  string `json:"name"`
	DLCCount              int    `json:"dlc_count"`
	DepotCount            int    `json:"depot_count"`
	WorkshopDecryptionKey string `json:"workshop_decryption_key"`
}

// SteamAppManifestInfo groups main app and DLC manifests.
type SteamAppManifestInfo struct {
	MainApp []ManifestInfo `json:"mainapp"`
	DLCs    []ManifestInfo `json:"dlcs"`
}

// KeyInfo holds API key details.
type KeyInfo struct {
	Type       string `json:"type"`
	ExpiresAt  string `json:"expiresAt"`
	UsageCount int    `json:"usageCount"`
	IsActive   bool   `json:"isActive"`
}

// TaskResult holds the result of an unlock task.
type TaskResult struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// --- Frontend response types ---

type SimpleResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

type BasicConfig struct {
	SteamPath string `json:"steam_path"`
	DebugMode bool   `json:"debug_mode"`
}

type ConfigResponse struct {
	Success bool        `json:"success"`
	Config  BasicConfig `json:"config"`
}

type DetailedConfig struct {
	SteamPath       string `json:"steam_path"`
	DebugMode       bool   `json:"debug_mode"`
	LoggingFiles    bool   `json:"logging_files"`
	ShowConsole     bool   `json:"show_console"`
	SteamPathExists bool   `json:"steam_path_exists"`
	Key             string `json:"key"`
	Language        string `json:"language"`
}

type DetailedConfigResponse struct {
	Success bool           `json:"success"`
	Config  DetailedConfig `json:"config"`
}

type UpdateConfigRequest struct {
	Key          string `json:"key"`
	SteamPath    string `json:"steam_path"`
	DebugMode    bool   `json:"debug_mode"`
	LoggingFiles bool   `json:"logging_files"`
	ShowConsole  bool   `json:"show_console"`
	Language     string `json:"language"`
}

type KeyInfoAPIResponse struct {
	Key  string   `json:"key"`
	Info *KeyInfo `json:"info"`
}

type TaskStatusResponse struct {
	Status string      `json:"status"`
	Result *TaskResult `json:"result"`
}
