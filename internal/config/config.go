package config

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"time"

	_ "github.com/glebarez/go-sqlite"

	"onekey/internal/httpclient"
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
	AppConfig models.AppConfig
	SteamPath string
	db        *sql.DB
	configDir string
}

// NewManager creates a config manager backed by SQLite3 at %APPDATA%\Onekey\onekey.db.
func NewManager() *Manager {
	configDir := getConfigDir()
	m := &Manager{
		configDir: configDir,
	}
	m.initDB()
	m.load()
	return m
}

// getConfigDir returns %APPDATA%\Onekey, creating it if needed.
func getConfigDir() string {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		// Fallback: use executable directory
		exe, err := os.Executable()
		if err == nil {
			appData = filepath.Dir(exe)
		} else {
			appData = "."
		}
	}
	dir := filepath.Join(appData, "Onekey")
	os.MkdirAll(dir, 0755)
	return dir
}

func (m *Manager) initDB() {
	dbPath := filepath.Join(m.configDir, "onekey.db")
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		fmt.Printf("Failed to open database: %v\n", err)
		m.AppConfig = DefaultConfig
		return
	}
	m.db = db

	// Create config table if not exists
	_, err = m.db.Exec(`
		CREATE TABLE IF NOT EXISTS config (
			key   TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)
	`)
	if err != nil {
		fmt.Printf("Failed to create config table: %v\n", err)
	}

	// Create cdn_cache table if not exists
	_, err = m.db.Exec(`
		CREATE TABLE IF NOT EXISTS cdn_cache (
			url       TEXT PRIMARY KEY,
			weight    INTEGER NOT NULL,
			updated_at TEXT NOT NULL
		)
	`)
	if err != nil {
		fmt.Printf("Failed to create cdn_cache table: %v\n", err)
	}
}

func (m *Manager) load() {
	// Start with defaults
	m.AppConfig = DefaultConfig

	if m.db == nil {
		m.SteamPath = m.getSteamPath()
		return
	}

	// Try migrating from old config.json if database is empty
	m.migrateFromJSON()

	// Load all config keys from SQLite
	rows, err := m.db.Query("SELECT key, value FROM config")
	if err != nil {
		m.SteamPath = m.getSteamPath()
		return
	}
	defer rows.Close()

	found := make(map[string]string)
	for rows.Next() {
		var k, v string
		if err := rows.Scan(&k, &v); err == nil {
			found[k] = v
		}
	}

	// Apply found values to config (auto-complete: missing keys keep defaults)
	if v, ok := found["KEY"]; ok {
		m.AppConfig.Key = v
	}
	if v, ok := found["Debug_Mode"]; ok {
		m.AppConfig.DebugMode = v == "true"
	}
	if v, ok := found["Logging_Files"]; ok {
		m.AppConfig.LoggingFiles = v == "true"
	}
	if v, ok := found["Show_Console"]; ok {
		m.AppConfig.ShowConsole = v == "true"
	}
	if v, ok := found["Custom_Steam_Path"]; ok {
		m.AppConfig.CustomSteamPath = v
	}
	if v, ok := found["Language"]; ok && v != "" {
		m.AppConfig.Language = v
	}
	if v, ok := found["Proxy_URL"]; ok {
		m.AppConfig.ProxyURL = v
	}

	// Auto-complete: ensure all default keys exist in DB
	m.autoComplete(found)

	m.SteamPath = m.getSteamPath()
}

// autoComplete writes default values for any config keys not yet in the database.
func (m *Manager) autoComplete(existing map[string]string) {
	defaults := m.configMap(DefaultConfig)
	for k, v := range defaults {
		if _, ok := existing[k]; !ok {
			m.setKey(k, v)
		}
	}
}

// migrateFromJSON migrates from old config.json if it exists and DB is empty.
func (m *Manager) migrateFromJSON() {
	// Check if DB already has config data
	var count int
	m.db.QueryRow("SELECT COUNT(*) FROM config").Scan(&count)
	if count > 0 {
		return
	}

	// Try reading old config.json from several locations
	searchPaths := []string{
		"config.json",
	}
	if exe, err := os.Executable(); err == nil {
		searchPaths = append(searchPaths, filepath.Join(filepath.Dir(exe), "config.json"))
	}

	for _, p := range searchPaths {
		data, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		var oldCfg models.AppConfig
		if err := json.Unmarshal(data, &oldCfg); err != nil {
			continue
		}
		// Migrate to SQLite
		m.AppConfig = oldCfg
		m.save()
		fmt.Printf("Migrated config from %s to SQLite\n", p)
		return
	}
}

func (m *Manager) save() error {
	if m.db == nil {
		return fmt.Errorf("database not initialized")
	}

	pairs := m.configMap(m.AppConfig)
	for k, v := range pairs {
		if err := m.setKey(k, v); err != nil {
			return err
		}
	}
	return nil
}

func (m *Manager) setKey(key, value string) error {
	_, err := m.db.Exec(
		"INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
		key, value,
	)
	return err
}

func (m *Manager) configMap(cfg models.AppConfig) map[string]string {
	return map[string]string{
		"KEY":               cfg.Key,
		"Debug_Mode":        boolStr(cfg.DebugMode),
		"Logging_Files":     boolStr(cfg.LoggingFiles),
		"Show_Console":      boolStr(cfg.ShowConsole),
		"Custom_Steam_Path": cfg.CustomSteamPath,
		"Language":          cfg.Language,
		"Proxy_URL":         cfg.ProxyURL,
	}
}

func boolStr(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

func (m *Manager) Update(req models.UpdateConfigRequest) error {
	m.AppConfig.Key = req.Key
	m.AppConfig.CustomSteamPath = req.SteamPath
	m.AppConfig.DebugMode = req.DebugMode
	m.AppConfig.LoggingFiles = req.LoggingFiles
	m.AppConfig.ShowConsole = req.ShowConsole
	m.AppConfig.ProxyURL = req.ProxyURL
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

// ConfigDir returns the application config directory path.
func (m *Manager) ConfigDir() string {
	return m.configDir
}

// Close closes the database connection.
func (m *Manager) Close() {
	if m.db != nil {
		m.db.Close()
	}
}

// --- CDN List Management ---

// steamPipeAPI is the Steam CDN directory endpoint.
const steamPipeAPI = "https://api.steampowered.com/IContentServerDirectoryService/GetServersForSteamPipe/v1"

// fallbackCDNList is used when both API fetch and DB cache fail.
// Covers HKG, SHA (Shanghai), SGP, LAX for geographic diversity.
var fallbackCDNList = []string{
	"https://cache1-hkg1.steamcontent.com",
	"https://cache2-hkg1.steamcontent.com",
	"https://cache3-hkg1.steamcontent.com",
	"https://cache1-sgp1.steamcontent.com",
	"https://cache2-sgp1.steamcontent.com",
	"https://cache1-lax1.steamcontent.com",
}

type cdnEntry struct {
	URL    string
	Weight int
}

// GetCDNList returns an ordered CDN list: fetch from Steam API → save to DB.
// On failure, try DB cache. On cache miss, use hardcoded fallback.
func (m *Manager) GetCDNList() []string {
	// 1. Try fetching from Steam API
	if list := m.fetchCDNListFromAPI(); len(list) > 0 {
		m.saveCDNCache(list)
		return cdnURLs(list)
	}

	// 2. Try loading from DB cache
	if list := m.loadCDNCache(); len(list) > 0 {
		return cdnURLs(list)
	}

	// 3. Hardcoded fallback
	return fallbackCDNList
}

func (m *Manager) fetchCDNListFromAPI() []cdnEntry {
	resp, err := httpclient.Shared().Get(steamPipeAPI)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil
	}

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil
	}

	var result struct {
		Response struct {
			Servers []struct {
				Type         string `json:"type"`
				Host         string `json:"host"`
				WeightedLoad int    `json:"weighted_load"`
				HTTPSSupport string `json:"https_support"`
			} `json:"servers"`
		} `json:"response"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil
	}

	var entries []cdnEntry
	for _, s := range result.Response.Servers {
		// Only use SteamCache and CDN types
		if s.Type != "SteamCache" && s.Type != "CDN" {
			continue
		}
		if s.Host == "" {
			continue
		}

		scheme := "https"
		if s.HTTPSSupport == "unavailable" {
			scheme = "http"
		}
		url := fmt.Sprintf("%s://%s", scheme, s.Host)
		entries = append(entries, cdnEntry{URL: url, Weight: s.WeightedLoad})
	}

	// Sort by weighted_load ascending (lower = better)
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].Weight < entries[j].Weight
	})

	return entries
}

func (m *Manager) saveCDNCache(entries []cdnEntry) {
	if m.db == nil {
		return
	}

	now := time.Now().UTC().Format(time.RFC3339)

	tx, err := m.db.Begin()
	if err != nil {
		return
	}

	// Clear old cache
	tx.Exec("DELETE FROM cdn_cache")

	stmt, err := tx.Prepare("INSERT INTO cdn_cache (url, weight, updated_at) VALUES (?, ?, ?)")
	if err != nil {
		tx.Rollback()
		return
	}
	defer stmt.Close()

	for _, e := range entries {
		stmt.Exec(e.URL, e.Weight, now)
	}
	tx.Commit()
}

func (m *Manager) loadCDNCache() []cdnEntry {
	if m.db == nil {
		return nil
	}

	rows, err := m.db.Query("SELECT url, weight FROM cdn_cache ORDER BY weight ASC")
	if err != nil {
		return nil
	}
	defer rows.Close()

	var entries []cdnEntry
	for rows.Next() {
		var e cdnEntry
		if err := rows.Scan(&e.URL, &e.Weight); err == nil {
			entries = append(entries, e)
		}
	}
	return entries
}

func cdnURLs(entries []cdnEntry) []string {
	urls := make([]string, len(entries))
	for i, e := range entries {
		urls[i] = e.URL
	}
	return urls
}

// PathExists checks if a given path exists on disk.
func PathExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

// InitCDNWithLatencyTest fetches the CDN list, probes each endpoint's latency
// concurrently, sorts by response time, and persists the ranked list to DB.
// Designed to be called once at startup in a goroutine.
func (m *Manager) InitCDNWithLatencyTest() {
	candidates := m.fetchCDNListFromAPI()
	if len(candidates) == 0 {
		candidates = m.loadCDNCache()
	}
	if len(candidates) == 0 {
		candidates = make([]cdnEntry, len(fallbackCDNList))
		for i, u := range fallbackCDNList {
			candidates[i] = cdnEntry{URL: u, Weight: 999}
		}
	}

	type probeResult struct {
		idx     int
		latency time.Duration
		ok      bool
	}

	ch := make(chan probeResult, len(candidates))
	for i, c := range candidates {
		go func(idx int, cdnURL string) {
			lat, ok := probeCDN(cdnURL)
			ch <- probeResult{idx, lat, ok}
		}(i, c.URL)
	}

	latencies := make([]time.Duration, len(candidates))
	for i := 0; i < len(candidates); i++ {
		r := <-ch
		if r.ok {
			latencies[r.idx] = r.latency
		} else {
			latencies[r.idx] = 999 * time.Second
		}
	}

	type ranked struct {
		entry   cdnEntry
		latency time.Duration
	}
	items := make([]ranked, len(candidates))
	for i, c := range candidates {
		items[i] = ranked{entry: c, latency: latencies[i]}
	}
	sort.Slice(items, func(i, j int) bool {
		return items[i].latency < items[j].latency
	})

	sorted := make([]cdnEntry, len(items))
	for i, it := range items {
		sorted[i] = cdnEntry{URL: it.entry.URL, Weight: i}
	}
	m.saveCDNCache(sorted)
}

// probeCDN sends a small HEAD request to the CDN and returns the round-trip
// latency. Returns false if the probe fails.
func probeCDN(cdnURL string) (time.Duration, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	start := time.Now()
	resp, err := httpclient.Shared().GetCtx(ctx, cdnURL)
	if err != nil {
		return 0, false
	}
	resp.Body.Close()
	return time.Since(start), true
}
