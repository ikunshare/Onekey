package i18n

import (
	"fmt"
	"strings"
	"sync"
)

var (
	currentLang string = "zh"
	mu          sync.RWMutex
)

var translations = map[string]map[string]string{
	"zh": {
		// 系统托盘
		"tray.show_window":  "显示程序",
		"tray.show_console": "显示控制台",
		"tray.exit":         "退出程序",
		// 配置
		"config.generated":         "配置文件已生成",
		"config.create_failed":     "配置文件创建失败: {error}",
		"config.corrupted":         "配置文件损坏，正在重新生成...",
		"config.steam_path_failed": "Steam路径获取失败: {error}",
		// API
		"api.key_not_exist":   "卡密不存在",
		"api.key_type":        "卡密类型: {type}",
		"api.key_expires":     "卡密过期时间: {time}",
		"api.key_info_failed": "获取卡密信息失败",
		"api.fetching_game":   "正在获取游戏 {app_id} 的信息...",
		"api.request_failed":  "API请求失败，状态码: {code}",
		"api.no_manifest":     "未找到此游戏的清单信息",
		"api.game_name":       "游戏名称: {name}",
		// 任务
		"task.no_steam_path": "Steam路径未配置或无效，无法继续",
		"task.run_error":     "运行错误: {error}",
		"task.step.auth":           "正在验证卡密...",
		"task.step.steamtools_setup": "正在生成 SteamTools 解锁配置...",
		"task.step.steamtools_done":  "SteamTools 配置完成: 应用 {appid}, 共 {depots} 个仓库",
		"task.step.finish":         "操作成功！游戏已解锁，重启Steam后生效。",
		// Web
		"web.task_running":   "已有任务正在运行",
		"web.invalid_appid":  "请输入有效的App ID",
		"web.invalid_format": "App ID格式无效",
		"web.task_started":   "任务已开始",
		// 卡密类型
		"key_type.week":      "周卡",
		"key_type.month":     "月卡",
		"key_type.year":      "年卡",
		"key_type.permanent": "永久卡",
		// SteamTools
		"steamtools.setup_done":     "SteamTools 解锁配置已写入: {appid}",
		// 清单
		"manifest.start_batch":        "开始批量处理 {count} 个清单任务...",
		"manifest.download.failed":    "从 {url} 下载失败: {error}",
		"manifest.delete_old":         "删除旧清单: {name}",
		"manifest.process.success":    "清单处理成功: {depot_id}_{manifest_id}.manifest",
		"manifest.downloading.failed": "下载清单失败: {depot_id}_{manifest_id}",
		"manifest.status.exists":      "已缓存: 仓库 {depot_id}",
		"manifest.status.downloaded":  "已下载: 仓库 {depot_id}",
		"manifest.status.failed":      "失败: 仓库 {depot_id}",
		// 错误
		"error.network":          "网络连接错误: {error}",
		"error.invalid_response": "无效的响应数据: {error}",
		"error.invalid_json":     "API 返回了无效的数据格式",
		"error.api_response":     "API 请求被拒绝: {error}",
		"error.server_response":  "服务器业务错误: {error}",
		"error.no_game_data":     "未在响应中找到有效的游戏数据",
		"error.unknown":          "未知错误",
		"error.manifest_empty":        "游戏清单列表为空，无法继续",
		"error.manifest_process_none": "没有成功处理任何清单文件",
		"error.steamtools_setup":      "SteamTools 配置写入失败: {error}",
		// Web 配置
		"web.config_saved":        "配置已保存",
		"web.config_save_failed":  "保存配置失败: {error}",
		"web.config_reset":        "配置已重置为默认值",
		"web.config_reset_failed": "重置配置失败: {error}",
	},
	"en": {
		"tray.show_window":  "Show Window",
		"tray.show_console": "Show Console",
		"tray.exit":         "Exit",
		"config.generated":         "Configuration file generated",
		"config.create_failed":     "Failed to create configuration file: {error}",
		"config.corrupted":         "Configuration file corrupted, regenerating...",
		"config.steam_path_failed": "Failed to get Steam path: {error}",
		"api.key_not_exist":   "Key does not exist",
		"api.key_type":        "Key type: {type}",
		"api.key_expires":     "Key expires at: {time}",
		"api.key_info_failed": "Failed to get key info",
		"api.fetching_game":   "Fetching game {app_id} information...",
		"api.request_failed":  "API request failed with status code: {code}",
		"api.no_manifest":     "No manifest found for this game",
		"api.game_name":       "Game name: {name}",
		"task.no_steam_path": "Steam path not configured or invalid",
		"task.run_error":     "Run error: {error}",
		"task.step.auth":           "Verifying API Key...",
		"task.step.steamtools_setup": "Generating SteamTools unlock configuration...",
		"task.step.steamtools_done":  "SteamTools config done: App {appid}, {depots} depots",
		"task.step.finish":         "Success! Game has been unlocked. Restart Steam to take effect.",
		"web.task_running":   "A task is already running",
		"web.invalid_appid":  "Please enter a valid App ID",
		"web.invalid_format": "Invalid App ID format",
		"web.task_started":   "Task started",
		"key_type.week":      "Weekly",
		"key_type.month":     "Monthly",
		"key_type.year":      "Yearly",
		"key_type.permanent": "Permanent",
		"steamtools.setup_done":     "SteamTools unlock config written: {appid}",
		"manifest.start_batch":        "Starting batch processing for {count} manifests...",
		"manifest.download.failed":    "Downloading from {url} failed: {error}",
		"manifest.delete_old":         "Delete old manifest: {name}",
		"manifest.process.success":    "Manifest processed: {depot_id}_{manifest_id}.manifest",
		"manifest.downloading.failed": "Manifest download failed: {depot_id}_{manifest_id}",
		"manifest.status.exists":      "Cached: Depot {depot_id}",
		"manifest.status.downloaded":  "Downloaded: Depot {depot_id}",
		"manifest.status.failed":      "Failed: Depot {depot_id}",
		"error.network":          "Network Error: {error}",
		"error.invalid_response": "Invalid response: {error}",
		"error.invalid_json":     "API returned invalid data format",
		"error.api_response":     "API Request Denied: {error}",
		"error.server_response":  "Server Business Error: {error}",
		"error.no_game_data":     "No valid game data found in response",
		"error.unknown":          "Unknown error",
		"error.manifest_empty":        "Manifest list is empty, cannot proceed",
		"error.manifest_process_none": "No manifests were successfully processed",
		"error.steamtools_setup":      "SteamTools config failed: {error}",
		"web.config_saved":        "Configuration saved",
		"web.config_save_failed":  "Failed to save configuration: {error}",
		"web.config_reset":        "Configuration reset to default",
		"web.config_reset_failed": "Failed to reset configuration: {error}",
	},
}

// SetLanguage sets the current language.
func SetLanguage(lang string) {
	mu.Lock()
	defer mu.Unlock()
	if _, ok := translations[lang]; ok {
		currentLang = lang
	}
}

// T returns a translated string, replacing {key} placeholders with provided values.
// Usage: T("api.fetching_game", "app_id", "730")
func T(key string, args ...string) string {
	mu.RLock()
	lang := currentLang
	mu.RUnlock()

	dict, ok := translations[lang]
	if !ok {
		return key
	}
	text, ok := dict[key]
	if !ok {
		return key
	}

	if len(args) >= 2 {
		for i := 0; i+1 < len(args); i += 2 {
			text = strings.ReplaceAll(text, fmt.Sprintf("{%s}", args[i]), args[i+1])
		}
	}
	return text
}
