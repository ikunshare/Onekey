export namespace models {
	
	export class Announcement {
	    id: number;
	    author: string;
	    title: string;
	    content: string;
	    createdAt: string;
	    updatedAt: string;
	
	    static createFrom(source: any = {}) {
	        return new Announcement(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.author = source["author"];
	        this.title = source["title"];
	        this.content = source["content"];
	        this.createdAt = source["createdAt"];
	        this.updatedAt = source["updatedAt"];
	    }
	}
	export class AnnouncementResponse {
	    success: boolean;
	    announcements: Announcement[];
	
	    static createFrom(source: any = {}) {
	        return new AnnouncementResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.announcements = this.convertValues(source["announcements"], Announcement);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class BasicConfig {
	    steam_path: string;
	    debug_mode: boolean;
	
	    static createFrom(source: any = {}) {
	        return new BasicConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.steam_path = source["steam_path"];
	        this.debug_mode = source["debug_mode"];
	    }
	}
	export class ConfigResponse {
	    success: boolean;
	    config: BasicConfig;
	
	    static createFrom(source: any = {}) {
	        return new ConfigResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.config = this.convertValues(source["config"], BasicConfig);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class DetailedConfig {
	    steam_path: string;
	    debug_mode: boolean;
	    logging_files: boolean;
	    show_console: boolean;
	    steam_path_exists: boolean;
	    key: string;
	    language: string;
	
	    static createFrom(source: any = {}) {
	        return new DetailedConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.steam_path = source["steam_path"];
	        this.debug_mode = source["debug_mode"];
	        this.logging_files = source["logging_files"];
	        this.show_console = source["show_console"];
	        this.steam_path_exists = source["steam_path_exists"];
	        this.key = source["key"];
	        this.language = source["language"];
	    }
	}
	export class DetailedConfigResponse {
	    success: boolean;
	    config: DetailedConfig;
	
	    static createFrom(source: any = {}) {
	        return new DetailedConfigResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.config = this.convertValues(source["config"], DetailedConfig);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class KernelSettings {
	    activate_unlock_mode: boolean;
	    always_stay_unlocked: boolean;
	    not_unlock_depot: boolean;
	
	    static createFrom(source: any = {}) {
	        return new KernelSettings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.activate_unlock_mode = source["activate_unlock_mode"];
	        this.always_stay_unlocked = source["always_stay_unlocked"];
	        this.not_unlock_depot = source["not_unlock_depot"];
	    }
	}
	export class KernelSettingsResponse {
	    success: boolean;
	    settings: KernelSettings;
	    message?: string;
	
	    static createFrom(source: any = {}) {
	        return new KernelSettingsResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.settings = this.convertValues(source["settings"], KernelSettings);
	        this.message = source["message"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class KeyInfo {
	    key: string;
	    type: string;
	    createdAt: string;
	    firstUsedAt?: string;
	    expiresAt?: string;
	    isActive: boolean;
	    usageCount: number;
	    totalUsage: number;
	
	    static createFrom(source: any = {}) {
	        return new KeyInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.key = source["key"];
	        this.type = source["type"];
	        this.createdAt = source["createdAt"];
	        this.firstUsedAt = source["firstUsedAt"];
	        this.expiresAt = source["expiresAt"];
	        this.isActive = source["isActive"];
	        this.usageCount = source["usageCount"];
	        this.totalUsage = source["totalUsage"];
	    }
	}
	export class KeyInfoAPIResponse {
	    code: number;
	    key: string;
	    info?: KeyInfo;
	
	    static createFrom(source: any = {}) {
	        return new KeyInfoAPIResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.code = source["code"];
	        this.key = source["key"];
	        this.info = this.convertValues(source["info"], KeyInfo);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class LibraryDepot {
	    app_id: string;
	    depot_id: string;
	    depot_key: string;
	    manifest_id: string;
	
	    static createFrom(source: any = {}) {
	        return new LibraryDepot(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.app_id = source["app_id"];
	        this.depot_id = source["depot_id"];
	        this.depot_key = source["depot_key"];
	        this.manifest_id = source["manifest_id"];
	    }
	}
	export class LibraryGame {
	    app_id: number;
	    name: string;
	    tiny_image: string;
	    lua_path: string;
	    dlc_count: number;
	    depot_count: number;
	    unlocked: boolean;
	    created_at: string;
	    updated_at: string;
	    depots: LibraryDepot[];
	    dlcs: LibraryDepot[];
	
	    static createFrom(source: any = {}) {
	        return new LibraryGame(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.app_id = source["app_id"];
	        this.name = source["name"];
	        this.tiny_image = source["tiny_image"];
	        this.lua_path = source["lua_path"];
	        this.dlc_count = source["dlc_count"];
	        this.depot_count = source["depot_count"];
	        this.unlocked = source["unlocked"];
	        this.created_at = source["created_at"];
	        this.updated_at = source["updated_at"];
	        this.depots = this.convertValues(source["depots"], LibraryDepot);
	        this.dlcs = this.convertValues(source["dlcs"], LibraryDepot);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class SimpleResponse {
	    success: boolean;
	    message: string;
	
	    static createFrom(source: any = {}) {
	        return new SimpleResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.message = source["message"];
	    }
	}
	export class StoreSearchPrice {
	    currency: string;
	    initial: number;
	    final: number;
	    discount_percent: number;
	
	    static createFrom(source: any = {}) {
	        return new StoreSearchPrice(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.currency = source["currency"];
	        this.initial = source["initial"];
	        this.final = source["final"];
	        this.discount_percent = source["discount_percent"];
	    }
	}
	export class StoreSearchPlatforms {
	    windows: boolean;
	    mac: boolean;
	    linux: boolean;
	
	    static createFrom(source: any = {}) {
	        return new StoreSearchPlatforms(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.windows = source["windows"];
	        this.mac = source["mac"];
	        this.linux = source["linux"];
	    }
	}
	export class StoreSearchItem {
	    type: string;
	    name: string;
	    id: number;
	    tiny_image: string;
	    platforms?: StoreSearchPlatforms;
	    price?: StoreSearchPrice;
	
	    static createFrom(source: any = {}) {
	        return new StoreSearchItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.type = source["type"];
	        this.name = source["name"];
	        this.id = source["id"];
	        this.tiny_image = source["tiny_image"];
	        this.platforms = this.convertValues(source["platforms"], StoreSearchPlatforms);
	        this.price = this.convertValues(source["price"], StoreSearchPrice);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	
	export class StoreSearchResult {
	    total: number;
	    items: StoreSearchItem[];
	
	    static createFrom(source: any = {}) {
	        return new StoreSearchResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.total = source["total"];
	        this.items = this.convertValues(source["items"], StoreSearchItem);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class TaskResult {
	    success: boolean;
	    message: string;
	
	    static createFrom(source: any = {}) {
	        return new TaskResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.message = source["message"];
	    }
	}
	export class TaskStatusResponse {
	    status: string;
	    result?: TaskResult;
	
	    static createFrom(source: any = {}) {
	        return new TaskStatusResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.status = source["status"];
	        this.result = this.convertValues(source["result"], TaskResult);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class UpdateConfigRequest {
	    key: string;
	    steam_path: string;
	    debug_mode: boolean;
	    logging_files: boolean;
	    show_console: boolean;
	    language: string;
	
	    static createFrom(source: any = {}) {
	        return new UpdateConfigRequest(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.key = source["key"];
	        this.steam_path = source["steam_path"];
	        this.debug_mode = source["debug_mode"];
	        this.logging_files = source["logging_files"];
	        this.show_console = source["show_console"];
	        this.language = source["language"];
	    }
	}
	export class UpdateInfo {
	    has_update: boolean;
	    latest_version: string;
	    current_version: string;
	    download_url: string;
	    changelog: string;
	
	    static createFrom(source: any = {}) {
	        return new UpdateInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.has_update = source["has_update"];
	        this.latest_version = source["latest_version"];
	        this.current_version = source["current_version"];
	        this.download_url = source["download_url"];
	        this.changelog = source["changelog"];
	    }
	}

}

