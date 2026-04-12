package config

import (
	"encoding/json"
	"os"
	"path/filepath"

	"onekey/internal/models"
)

var DefaultConfig = models.AppConfig{
	Key:             "",
	DebugMode:       false,
	LoggingFiles:    true,
	ShowConsole:     false,
	CustomSteamPath: "",
	Language:        "zh",
}

type Manager struct {
	AppConfig  models.AppConfig
	SteamPath  string
	configPath string
}

func NewManager() *Manager {
	m := &Manager{
		configPath: "config.json",
	}
	m.load()
	return m
}

func (m *Manager) load() {
	data, err := os.ReadFile(m.configPath)
	if err != nil {
		m.AppConfig = DefaultConfig
		m.save()
	} else {
		if err := json.Unmarshal(data, &m.AppConfig); err != nil {
			m.AppConfig = DefaultConfig
			m.save()
		}
	}
	m.SteamPath = m.getSteamPath()
}

func (m *Manager) save() error {
	data, err := json.MarshalIndent(m.AppConfig, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(m.configPath, data, 0644)
}

func (m *Manager) Update(req models.UpdateConfigRequest) error {
	m.AppConfig.Key = req.Key
	m.AppConfig.CustomSteamPath = req.SteamPath
	m.AppConfig.DebugMode = req.DebugMode
	m.AppConfig.LoggingFiles = req.LoggingFiles
	m.AppConfig.ShowConsole = req.ShowConsole
	if req.Language != "" {
		m.AppConfig.Language = req.Language
	}
	err := m.save()
	if err != nil {
		return err
	}
	m.SteamPath = m.getSteamPath()
	return nil
}

func (m *Manager) Reset() error {
	m.AppConfig = DefaultConfig
	err := m.save()
	if err != nil {
		return err
	}
	m.SteamPath = m.getSteamPath()
	return nil
}

func (m *Manager) getSteamPath() string {
	if m.AppConfig.CustomSteamPath != "" {
		return filepath.Clean(m.AppConfig.CustomSteamPath)
	}
	return getSteamPathFromRegistry()
}

// PathExists checks if a given path exists on disk.
func PathExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}
