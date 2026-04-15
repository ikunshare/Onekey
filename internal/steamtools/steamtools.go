package steamtools

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"onekey/internal/models"
)

// Setup generates the SteamTools Lua unlock file in Steam's stplug-in directory.
func Setup(steamPath string, appInfo *models.SteamAppInfo, manifests []models.ManifestInfo) error {
	stPath := filepath.Join(steamPath, "config", "stplug-in")
	if err := os.MkdirAll(stPath, 0755); err != nil {
		return fmt.Errorf("create stplug-in directory: %w", err)
	}

	var b strings.Builder

	fmt.Fprintf(&b, "-- Generated Lua Manifest by Onekey\n")
	fmt.Fprintf(&b, "-- Steam App %s Manifest\n", appInfo.AppID)
	fmt.Fprintf(&b, "-- Name: %s\n", appInfo.Name)
	fmt.Fprintf(&b, "-- Generated: %s\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Fprintf(&b, "-- Total Depots: %d\n", appInfo.DepotCount)
	fmt.Fprintf(&b, "-- Total DLCs: %d\n", appInfo.DLCCount)
	fmt.Fprintf(&b, "\n-- MAIN APP\n")
	fmt.Fprintf(&b, "addappid(%s, \"0\", \"%s\")\n", appInfo.AppID, appInfo.WorkshopDecryptionKey)
	if appInfo.AccessToken != "" && appInfo.AccessToken != "0" {
		fmt.Fprintf(&b, "addtoken(%s, \"%s\")\n", appInfo.AppID, appInfo.AccessToken)
	}
	fmt.Fprintf(&b, "\n-- ALL Depots\n")

	// Deduplicate depots: each depot_id should appear only once.
	seen := make(map[string]bool)
	for _, m := range manifests {
		if seen[m.DepotID] {
			continue
		}
		seen[m.DepotID] = true
		fmt.Fprintf(&b, "addappid(%s, \"1\", \"%s\")\n", m.DepotID, m.DepotKey)
	}

	luaFile := filepath.Join(stPath, appInfo.AppID+".lua")
	if err := os.WriteFile(luaFile, []byte(b.String()), 0644); err != nil {
		return fmt.Errorf("write lua file: %w", err)
	}

	return nil
}
