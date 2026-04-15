package library

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "github.com/glebarez/go-sqlite"

	"onekey/internal/models"
)

type Manager struct {
	db *sql.DB
}

// NewManager opens (or creates) %APPDATA%\Onekey\library.db.
func NewManager() *Manager {
	dir := getDataDir()
	dbPath := filepath.Join(dir, "library.db")
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		fmt.Printf("Failed to open library database: %v\n", err)
		return &Manager{}
	}
	m := &Manager{db: db}
	m.initTables()
	return m
}

func getDataDir() string {
	appData := os.Getenv("APPDATA")
	if appData == "" {
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

func (m *Manager) initTables() {
	if m.db == nil {
		return
	}
	m.db.Exec("PRAGMA foreign_keys = ON")

	m.db.Exec(`CREATE TABLE IF NOT EXISTS games (
		app_id        INTEGER PRIMARY KEY,
		name          TEXT NOT NULL DEFAULT '',
		tiny_image    TEXT DEFAULT '',
		lua_path      TEXT DEFAULT '',
		dlc_lua_paths TEXT DEFAULT '[]',
		dlc_count     INTEGER DEFAULT 0,
		depot_count   INTEGER DEFAULT 0,
		unlocked      INTEGER DEFAULT 0,
		created_at    TEXT DEFAULT (datetime('now','localtime')),
		updated_at    TEXT DEFAULT (datetime('now','localtime'))
	)`)

	m.db.Exec(`CREATE TABLE IF NOT EXISTS depots (
		id          INTEGER PRIMARY KEY AUTOINCREMENT,
		game_app_id INTEGER NOT NULL,
		app_id      TEXT NOT NULL,
		depot_id    TEXT NOT NULL,
		depot_key   TEXT DEFAULT '',
		manifest_id TEXT DEFAULT '',
		is_dlc      INTEGER DEFAULT 0,
		FOREIGN KEY (game_app_id) REFERENCES games(app_id) ON DELETE CASCADE
	)`)

	// Migration: add dlc_lua_paths column if not present
	m.db.Exec("ALTER TABLE games ADD COLUMN dlc_lua_paths TEXT DEFAULT '[]'")
}

func (m *Manager) Close() {
	if m.db != nil {
		m.db.Close()
	}
}

// AddBasic adds a game with minimal info (from search results).
// If the game already exists, it does nothing.
func (m *Manager) AddBasic(appID int, name, tinyImage string) error {
	if m.db == nil {
		return fmt.Errorf("database not available")
	}
	_, err := m.db.Exec(`INSERT OR IGNORE INTO games (app_id, name, tiny_image) VALUES (?, ?, ?)`,
		appID, name, tinyImage)
	return err
}

// SaveUnlock saves full game data after a successful unlock.
// It upserts the game row and replaces all depot entries.
func (m *Manager) SaveUnlock(appID int, name, tinyImage, luaPath string, dlcCount, depotCount int,
	mainDepots []models.ManifestInfo, dlcDepots []models.ManifestInfo) error {
	if m.db == nil {
		return fmt.Errorf("database not available")
	}

	tx, err := m.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Upsert game
	_, err = tx.Exec(`INSERT INTO games (app_id, name, tiny_image, lua_path, dlc_count, depot_count, unlocked, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now','localtime'))
		ON CONFLICT(app_id) DO UPDATE SET
			name=excluded.name, tiny_image=CASE WHEN excluded.tiny_image='' THEN games.tiny_image ELSE excluded.tiny_image END,
			lua_path=excluded.lua_path, dlc_count=excluded.dlc_count, depot_count=excluded.depot_count,
			unlocked=1, updated_at=datetime('now','localtime')`,
		appID, name, tinyImage, luaPath, dlcCount, depotCount)
	if err != nil {
		return err
	}

	// Replace depots
	tx.Exec("DELETE FROM depots WHERE game_app_id = ?", appID)

	stmt, err := tx.Prepare("INSERT INTO depots (game_app_id, app_id, depot_id, depot_key, manifest_id, is_dlc) VALUES (?, ?, ?, ?, ?, ?)")
	if err != nil {
		return err
	}
	defer stmt.Close()

	for _, d := range mainDepots {
		stmt.Exec(appID, d.AppID, d.DepotID, d.DepotKey, d.ManifestID, 0)
	}
	for _, d := range dlcDepots {
		stmt.Exec(appID, d.AppID, d.DepotID, d.DepotKey, d.ManifestID, 1)
	}

	return tx.Commit()
}

// MergeDLCUnlock saves a DLC's depot data under the parent game.
// Creates the parent entry if it doesn't exist.
func (m *Manager) MergeDLCUnlock(parentAppID int, parentName string,
	dlcLuaPath string, dlcDepots []models.ManifestInfo) error {
	if m.db == nil {
		return fmt.Errorf("database not available")
	}

	tx, err := m.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Ensure parent game exists
	tx.Exec(`INSERT OR IGNORE INTO games (app_id, name) VALUES (?, ?)`, parentAppID, parentName)

	// Update parent: mark unlocked, bump updated_at, increment dlc_count
	tx.Exec(`UPDATE games SET unlocked=1, updated_at=datetime('now','localtime') WHERE app_id=?`, parentAppID)

	// Append dlcLuaPath to the parent's dlc_lua_paths JSON array
	if dlcLuaPath != "" {
		var existing string
		tx.QueryRow("SELECT dlc_lua_paths FROM games WHERE app_id=?", parentAppID).Scan(&existing)
		var paths []string
		json.Unmarshal([]byte(existing), &paths)
		// Avoid duplicates
		found := false
		for _, p := range paths {
			if p == dlcLuaPath {
				found = true
				break
			}
		}
		if !found {
			paths = append(paths, dlcLuaPath)
		}
		data, _ := json.Marshal(paths)
		tx.Exec("UPDATE games SET dlc_lua_paths=? WHERE app_id=?", string(data), parentAppID)
	}

	// Add DLC depots (append, don't replace — parent may have its own depots)
	stmt, err := tx.Prepare("INSERT INTO depots (game_app_id, app_id, depot_id, depot_key, manifest_id, is_dlc) VALUES (?, ?, ?, ?, ?, 1)")
	if err != nil {
		return err
	}
	defer stmt.Close()

	for _, d := range dlcDepots {
		// Check if this depot already exists to avoid duplicates
		var count int
		tx.QueryRow("SELECT COUNT(*) FROM depots WHERE game_app_id=? AND depot_id=?", parentAppID, d.DepotID).Scan(&count)
		if count == 0 {
			stmt.Exec(parentAppID, d.AppID, d.DepotID, d.DepotKey, d.ManifestID)
		}
	}

	// Update dlc_count based on actual distinct DLC app_ids
	var dlcCount int
	tx.QueryRow("SELECT COUNT(DISTINCT app_id) FROM depots WHERE game_app_id=? AND is_dlc=1", parentAppID).Scan(&dlcCount)
	tx.Exec("UPDATE games SET dlc_count=? WHERE app_id=?", dlcCount, parentAppID)

	return tx.Commit()
}

// Exists checks if a game is in the library.
func (m *Manager) Exists(appID int) bool {
	if m.db == nil {
		return false
	}
	var count int
	m.db.QueryRow("SELECT COUNT(*) FROM games WHERE app_id=?", appID).Scan(&count)
	return count > 0
}

// GetAll returns all games in the library.
func (m *Manager) GetAll() []models.LibraryGame {
	if m.db == nil {
		return nil
	}

	rows, err := m.db.Query("SELECT app_id, name, tiny_image, lua_path, COALESCE(dlc_lua_paths,'[]'), dlc_count, depot_count, unlocked, created_at, updated_at FROM games ORDER BY updated_at DESC")
	if err != nil {
		return nil
	}
	defer rows.Close()

	var games []models.LibraryGame
	for rows.Next() {
		var g models.LibraryGame
		var unlocked int
		var dlcLuaPaths string
		rows.Scan(&g.AppID, &g.Name, &g.TinyImage, &g.LuaPath, &dlcLuaPaths, &g.DLCCount, &g.DepotCount, &unlocked, &g.CreatedAt, &g.UpdatedAt)
		g.Unlocked = unlocked == 1
		games = append(games, g)
	}
	return games
}

// GetGame returns a single game with its depots and DLCs.
func (m *Manager) GetGame(appID int) *models.LibraryGame {
	if m.db == nil {
		return nil
	}

	g := &models.LibraryGame{}
	var unlocked int
	var dlcLuaPaths string
	err := m.db.QueryRow("SELECT app_id, name, tiny_image, lua_path, COALESCE(dlc_lua_paths,'[]'), dlc_count, depot_count, unlocked, created_at, updated_at FROM games WHERE app_id = ?", appID).
		Scan(&g.AppID, &g.Name, &g.TinyImage, &g.LuaPath, &dlcLuaPaths, &g.DLCCount, &g.DepotCount, &unlocked, &g.CreatedAt, &g.UpdatedAt)
	if err != nil {
		return nil
	}
	g.Unlocked = unlocked == 1

	// Load depots
	rows, err := m.db.Query("SELECT app_id, depot_id, depot_key, manifest_id, is_dlc FROM depots WHERE game_app_id = ?", appID)
	if err != nil {
		return g
	}
	defer rows.Close()

	for rows.Next() {
		var d models.LibraryDepot
		var isDLC int
		rows.Scan(&d.AppID, &d.DepotID, &d.DepotKey, &d.ManifestID, &isDLC)
		if isDLC == 1 {
			g.DLCs = append(g.DLCs, d)
		} else {
			g.Depots = append(g.Depots, d)
		}
	}
	return g
}

// Remove deletes a game from the library, removes its Lua file + DLC Lua files,
// and cleans up manifest files from depotcache.
func (m *Manager) Remove(appID int, steamPath string) error {
	if m.db == nil {
		return fmt.Errorf("database not available")
	}

	// Get lua_path and dlc_lua_paths before deleting
	var luaPath, dlcLuaPathsJSON string
	m.db.QueryRow("SELECT lua_path, COALESCE(dlc_lua_paths,'[]') FROM games WHERE app_id = ?", appID).Scan(&luaPath, &dlcLuaPathsJSON)

	// Collect all depot manifest files to delete
	var manifests []string
	rows, err := m.db.Query("SELECT depot_id, manifest_id FROM depots WHERE game_app_id = ?", appID)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var depotID, manifestID string
			rows.Scan(&depotID, &manifestID)
			if depotID != "" && manifestID != "" {
				manifests = append(manifests, fmt.Sprintf("%s_%s.manifest", depotID, manifestID))
			}
		}
	}

	// Delete from DB (cascade deletes depots)
	_, err = m.db.Exec("DELETE FROM games WHERE app_id = ?", appID)
	if err != nil {
		return err
	}

	// Remove main Lua file
	if luaPath != "" {
		os.Remove(luaPath)
	}

	// Remove DLC Lua files
	var dlcPaths []string
	json.Unmarshal([]byte(dlcLuaPathsJSON), &dlcPaths)
	for _, p := range dlcPaths {
		if p != "" {
			os.Remove(p)
		}
	}

	// Remove manifest files from depotcache
	if steamPath != "" {
		depotCache := filepath.Join(steamPath, "depotcache")
		for _, name := range manifests {
			os.Remove(filepath.Join(depotCache, name))
		}
	}

	return nil
}
