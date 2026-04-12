package config

import (
	"golang.org/x/sys/windows/registry"
)

func getSteamPathFromRegistry() string {
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\Valve\Steam`, registry.QUERY_VALUE)
	if err != nil {
		return ""
	}
	defer key.Close()

	val, _, err := key.GetStringValue("SteamPath")
	if err != nil {
		return ""
	}
	return val
}
