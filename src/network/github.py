import time
from typing import List, Dict, Optional
from datetime import datetime

from ..constants import GITHUB_API_BASE, CN_CDN_LIST, GLOBAL_CDN_LIST
from ..models import RepoInfo
from ..logger import Logger
from .client import HttpClient


class GitHubAPI:
    """GitHub API封装"""

    def __init__(
        self,
        client: HttpClient,
        headers: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ):
        self.client = client
        self.headers = headers or {}
        self.logger = logger or Logger("GitHubAPI")
        self.is_cn = True

    async def check_rate_limit(self) -> None:
        """检查API请求限制"""
        url = f"{GITHUB_API_BASE}/rate_limit"
        try:
            r = await self.client.get(url, headers=self.headers)
            if r.status_code == 200:
                r_json = r.json()
                rate_limit = r_json.get("rate", {})
                remaining = rate_limit.get("remaining", 0)
                reset_time = rate_limit.get("reset", 0)
                reset_formatted = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(reset_time)
                )
                self.logger.info(f"剩余Github API请求次数: {remaining}")
                if remaining == 0:
                    self.logger.warning(
                        f"GitHub API 请求数已用尽, 将在 {reset_formatted} 重置"
                    )
            else:
                self.logger.error("Github请求数检查失败, 网络错误")
        except Exception as e:
            self.logger.error(f"检查Github API 请求数失败: {str(e)}")

    async def get_latest_repo_info(
        self, repos: List[str], app_id: str
    ) -> Optional[RepoInfo]:
        """获取最新的仓库信息"""
        latest_date = None
        selected_repo = None
        selected_sha = None

        for repo in repos:
            url = f"{GITHUB_API_BASE}/repos/{repo}/branches/{app_id}"
            try:
                r = await self.client.get(url, headers=self.headers)
                if r.status_code == 200:
                    r_json = r.json()
                    if "commit" in r_json:
                        date_str = r_json["commit"]["commit"]["author"]["date"]
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if latest_date is None or date > latest_date:
                            latest_date = date
                            selected_repo = repo
                            selected_sha = r_json["commit"]["sha"]
            except Exception as e:
                self.logger.warning(f"检查仓库 {repo} 失败: {str(e)}")

        if selected_repo:
            return RepoInfo(
                name=selected_repo, last_update=latest_date, sha=selected_sha
            )
        return None

    async def fetch_file(self, repo: str, sha: str, path: str) -> bytes:
        """获取文件内容"""
        cdn_list = CN_CDN_LIST if self.is_cn else GLOBAL_CDN_LIST

        for _ in range(3):
            for cdn_template in cdn_list:
                url = cdn_template.format(repo=repo, sha=sha, path=path)
                try:
                    r = await self.client.get(url, headers=self.headers)
                    if r.status_code == 200:
                        return r.content
                except Exception as e:
                    self.logger.debug(f"从 {url} 下载失败: {str(e)}")

        raise Exception(f"无法下载文件: {path}")
