export namespace models {
	
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
	export class KeyInfo {
	    type: string;
	    expiresAt: string;
	    usageCount: number;
	    isActive: boolean;
	
	    static createFrom(source: any = {}) {
	        return new KeyInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.type = source["type"];
	        this.expiresAt = source["expiresAt"];
	        this.usageCount = source["usageCount"];
	        this.isActive = source["isActive"];
	    }
	}
	export class KeyInfoAPIResponse {
	    key: string;
	    info?: KeyInfo;
	
	    static createFrom(source: any = {}) {
	        return new KeyInfoAPIResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
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

}

