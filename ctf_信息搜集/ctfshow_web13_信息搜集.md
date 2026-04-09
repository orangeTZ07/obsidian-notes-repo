仍然是去寻找公开信息，目标就在网站内某个链接内。
看wp说是就在页面内的一个 `Document` 里面，朝下翻就能找到，但我老年人眼力，死活找不到。
最后让AI写了个爬虫去递归爬取url(限制深度5)暴力解决了
```
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
import time


class CTFCrawler:
    def __init__(self, base_url, max_depth=5, delay=0.5):
        """
        :param base_url: 起始爬取 URL
        :param max_depth: 最大爬取深度（包含起始页，即 base_url 深度为 1）
        :param delay: 请求间隔（秒），避免过快请求
        """
        self.base_url = base_url
        self.max_depth = max_depth
        self.delay = delay
        self.domain = urlparse(base_url).netloc  # 限制只爬取同一域名下的链接
        self.visited = set()  # 已访问的 URL
        self.found_urls = set()  # 发现的所有 URL（包含外部链接，但不爬取）
        self.queue = deque()  # 待爬队列，元素为 (url, depth)

    def is_valid_url(self, url):
        """判断 URL 是否属于目标域名且为 http/https 协议"""
        parsed = urlparse(url)
        # 过滤非 http/https 协议（如 mailto:, javascript:, ftp: 等）
        if parsed.scheme not in ("http", "https"):
            return False
        # 只保留同一域名下的链接（可根据需要放宽）
        return parsed.netloc == self.domain

    def normalize_url(self, url):
        """将相对路径转为绝对 URL，并去除 fragment 部分"""
        full_url = urljoin(self.base_url, url)
        # 移除 URL 片段（# 之后的部分）
        parsed = urlparse(full_url)
        normalized = parsed._replace(fragment="")
        return normalized.geturl()

    def extract_links(self, html, current_url):
        """从 HTML 中提取所有 <a> 标签的 href 属性"""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            try:
                absolute = self.normalize_url(href)
                links.add(absolute)
            except Exception:
                continue
        return links

    def crawl(self):
        """启动爬虫"""
        start_url = self.normalize_url(self.base_url)
        self.queue.append((start_url, 1))

        print(f"[*] 开始爬取，域名限制：{self.domain}，最大深度：{self.max_depth}")

        while self.queue:
            url, depth = self.queue.popleft()
            if url in self.visited:
                continue
            if depth > self.max_depth:
                continue

            print(f"[>] 深度 {depth} 爬取: {url}")
            self.visited.add(url)

            try:
                # 设置一个常见的 User-Agent，避免被拦截
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = requests.get(
                    url, headers=headers, timeout=10, allow_redirects=True
                )
                resp.raise_for_status()

                # 仅当响应是 HTML 时才解析链接
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    print(f"   [跳过] 非 HTML 内容: {content_type}")
                    continue

                html = resp.text
                links = self.extract_links(html, url)

                for link in links:
                    self.found_urls.add(link)
                    if self.is_valid_url(link) and link not in self.visited:
                        # 检查是否已经在队列中（避免重复入队）
                        if not any(link == q_url for q_url, _ in self.queue):
                            self.queue.append((link, depth + 1))

                print(
                    f"   [+] 发现 {len(links)} 个链接，待爬队列长度：{len(self.queue)}"
                )

            except requests.exceptions.RequestException as e:
                print(f"   [-] 请求失败: {e}")

            # 礼貌性延时
            time.sleep(self.delay)

        print("\n[*] 爬取完成！")
        print(f"[*] 共访问页面：{len(self.visited)} 个")
        print(f"[*] 发现所有 URL 数量：{len(self.found_urls)} 个")

        # 输出所有发现的 URL（按字母排序便于查看）
        sorted_urls = sorted(self.found_urls)
        print("\n===== 发现的 URL 列表 =====")
        for u in sorted_urls:
            print(u)

        return sorted_urls


if __name__ == "__main__":
    base_url = "http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show"
    crawler = CTFCrawler(base_url, max_depth=5, delay=0.5)
    found = crawler.crawl()

```
结果：
```
[*] 爬取完成！
[*] 共访问页面：7 个
[*] 发现所有 URL 数量：7 个

===== 发现的 URL 列表 =====
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/Products.html
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/about.html
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/blog.html
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/contact.html
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/document.pdf
http://3e2a6194-4db2-4dc8-b644-84dda88f56f1.challenge.ctf.show/index.html
http://sc.chinaz.com/moban/
```
可见爬虫还是很重要的，非常重要。