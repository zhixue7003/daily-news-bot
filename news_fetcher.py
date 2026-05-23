#!/usr/bin/env python3
"""
每日新闻抓取与推送脚本
支持：国情、世界经济、游戏圈、娱乐圈顶流
推送方式：PushPlus (微信)
"""

import os
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional

# ============ 配置区域 ============
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# 新闻 API 配置
NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "")

# 分类关键词配置
CATEGORIES = {
    "国情": {
        "keywords": "中国 国内 政策 时政 国务院 人大 两会",
        "category": "politics"
    },
    "世界经济": {
        "keywords": "全球经济 美股 港股 A股 美联储 央行 通胀 汇率",
        "category": "business"
    },
    "游戏圈": {
        "keywords": "游戏 手游 网游 电竞 Steam 原神 王者荣耀",
        "category": "technology"
    },
    "娱乐圈": {
        "keywords": "明星 娱乐 电影 电视剧 综艺 顶流 艺人",
        "category": "entertainment"
    }
}


class NewsFetcher:
    """新闻抓取器"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
        }

    def fetch_from_newsdata(self, category: str, keywords: str, limit: int = 5) -> List[Dict]:
        """从 NewsData.io 获取新闻"""
        if not NEWSDATA_API_KEY:
            return []
        try:
            encoded_keywords = urllib.parse.quote(keywords)
            url = (
                f"https://newsdata.io/api/1/latest?"
                f"apikey={NEWSDATA_API_KEY}&"
                f"q={encoded_keywords}&"
                f"language=zh&"
                f"size={limit}"
            )
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            if data.get("status") != "success":
                return []
            results = data.get("results", [])
            news_list = []
            for item in results[:limit]:
                news_list.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "source": item.get("source_id", "未知来源"),
                    "pub_date": item.get("pubDate", "")[:10]
                })
            return news_list
        except Exception as e:
            print(f"NewsData API 错误: {e}")
            return []

    def fetch_from_google_news_rss(self, keywords: str, limit: int = 5) -> List[Dict]:
        """从 Google News RSS 获取新闻（备用方案）"""
        try:
            import xml.etree.ElementTree as ET
            encoded_keywords = urllib.parse.quote(keywords)
            url = f"https://news.google.com/rss/search?q={encoded_keywords}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
            root = ET.fromstring(content)
            news_list = []
            for item in root.findall('.//item')[:limit]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                news_list.append({
                    "title": title.text if title is not None else "",
                    "link": link.text if link is not None else "",
                    "source": source.text if source is not None else "Google News",
                    "pub_date": self._format_date(pub_date.text if pub_date is not None else "")
                })
            return news_list
        except Exception as e:
            print(f"Google News RSS 错误: {e}")
            return []

    def _format_date(self, date_str: str) -> str:
        """格式化日期"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str[:10] if date_str else ""

    def fetch_category_news(self, category_name: str, config: Dict) -> List[Dict]:
        """获取指定分类的新闻"""
        keywords = config["keywords"]
        news = self.fetch_from_newsdata(config.get("category", ""), keywords)
        if not news:
            news = self.fetch_from_google_news_rss(keywords)
        return news[:5]


class PushPlusNotifier:
    """PushPlus 微信推送器"""

    API_URL = "http://www.pushplus.plus/send"

    def __init__(self, token: str):
        self.token = token

    def send(self, title: str, content: str) -> bool:
        """发送推送消息"""
        if not self.token:
            print("错误: 未设置 PUSHPLUS_TOKEN")
            return False
        try:
            data = {
                "token": self.token,
                "title": title,
                "content": content,
                "template": "markdown"
            }
            req = urllib.request.Request(
                self.API_URL,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
            if result.get("code") == 200:
                print(f"推送成功: {title}")
                return True
            else:
                print(f"推送失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"推送异常: {e}")
            return False


def format_news_content(all_news: Dict[str, List[Dict]]) -> str:
    """格式化新闻内容为 Markdown"""
    today = datetime.now().strftime("%Y年%m月%d日")
    content = f"# 每日新闻早报 | {today}\n\n"
    icons = {
        "国情": "🇨🇳",
        "世界经济": "💰",
        "游戏圈": "🎮",
        "娱乐圈": "🎬"
    }
    for category_name, news_list in all_news.items():
        icon = icons.get(category_name, "📌")
        content += f"## {icon} {category_name}\n\n"
        if not news_list:
            content += "_暂无相关新闻_\n\n"
            continue
        for i, news in enumerate(news_list, 1):
            title = news.get("title", "")
            link = news.get("link", "")
            source = news.get("source", "")
            pub_date = news.get("pub_date", "")
            title = re.sub(r' - [^-]+$', '', title)
            content += f"{i}. [{title}]({link})\n"
            content += f"   > 💡 {source}"
            if pub_date:
                content += f" · {pub_date}"
            content += "\n\n"
        content += "---\n\n"
    content += "*数据来源：Google News*\n"
    return content


def main():
    """主函数"""
    print("=" * 50)
    print("开始获取每日新闻")
    print("=" * 50)
    if not PUSHPLUS_TOKEN:
        print("警告: 未设置 PUSHPLUS_TOKEN 环境变量")
        print("请先在 GitHub Secrets 中设置 PUSHPLUS_TOKEN")
        return
    fetcher = NewsFetcher()
    notifier = PushPlusNotifier(PUSHPLUS_TOKEN)
    all_news = {}
    for category_name, config in CATEGORIES.items():
        print(f"\n正在获取: {category_name}...")
        news = fetcher.fetch_category_news(category_name, config)
        all_news[category_name] = news
        print(f"   获取到 {len(news)} 条新闻")
    print("\n正在格式化消息...")
    content = format_news_content(all_news)
    today = datetime.now().strftime("%m月%d日")
    title = f"每日新闻早报 | {today}"
    print("\n正在推送到微信...")
    success = notifier.send(title, content)
    if success:
        print("\n今日新闻推送完成！")
    else:
        print("\n推送失败，请检查配置")
    print("=" * 50)


if __name__ == "__main__":
    main()
