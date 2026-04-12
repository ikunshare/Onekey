//go:build !windows

package config

func getSteamPathFromRegistry() string {
	return ""
}
