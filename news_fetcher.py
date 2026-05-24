#!/usr/bin/env python3
"""
每日新闻抓取与推送脚本 - 权威新闻+八卦版
支持：国情、世界经济、游戏圈、娱乐圈顶流
推送方式：PushPlus (微信)
特点：
- 每天早上8点准时发送
- 权威媒体+社交平台聚合
- 只推送一周内最新、最热门
- 无链接，标题加粗方便长按复制
"""

import os
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict

# ============ 配置区域 ============
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# 分类配置
CATEGORIES = {
    "国情": {
        "keywords": ["中国", "国内", "政策", "时政", "国务院", "人大", "两会", "习近平", "外交部", "发改委", "央行", "国防部", "台湾", "香港", "澳门"],
        "exclude": ["明星", "娱乐", "游戏", "电影", "电视剧"]
    },
    "世界经济": {
        "keywords": ["美联储", "美股", "港股", "A股", "全球经济", "油价", "黄金", "汇率", "通胀", "GDP", "华尔街", "纳斯达克", "道琼斯", "比特币", "加密货币", "特斯拉", "苹果", "微软", "谷歌", "亚马逊", "马云", "马化腾", "任正非"],
        "exclude": ["游戏", "娱乐", "明星", "电影"]
    },
    "游戏圈": {
        "keywords": ["游戏", "手游", "网游", "电竞", "Steam", "原神", "王者荣耀", "LOL", "英雄联盟", "黑神话", "Switch", "PS5", "Xbox", "腾讯游戏", "网易游戏", "米哈游", "暴雪", "网易", "腾讯", "字节跳动"],
        "exclude": []
    },
    "娱乐圈": {
        "keywords": ["明星", "娱乐", "电影", "电视剧", "综艺", "顶流", "艺人", "票房", "首映", "演唱会", "八卦", "出轨", "离婚", "结婚", "恋爱", "分手", "爆料", "瓜", "塌房", "封杀", "吸毒", "偷税", "范冰冰", "郑爽", "吴亦凡", "李易峰", "邓伦", "薇娅", "李佳琦", "杨幂", "赵丽颖", "迪丽热巴", "肖战", "王一博", "易烊千玺", "王俊凯", "王源", "鹿晗", "黄子韬", "张艺兴", "蔡徐坤", "华晨宇", "周杰伦", "林俊杰", "薛之谦", "李荣浩", "邓紫棋", "张靓颖", "周深", "毛不易", "单依纯"],
        "exclude": []
    }
}


class HotTopicsFetcher:
    """热门话题抓取器（权威媒体+社交平台）"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.all_topics = []

    def fetch_weibo_hot(self) -> List[Dict]:
        """获取微博热搜（国内最实时，瓜最多）"""
        try:
            url = "https://weibo.com/ajax/side/hotSearch"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data and 'realtime' in data['data']:
                for item in data['data']['realtime'][:30]:
                    topic = {
                        "title": item.get('word', ''),
                        "hot": item.get('raw_hot', 0),
                        "category": item.get('category', ''),
                        "source": "微博热搜",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            return topics
        except Exception as e:
            print(f"微博热搜获取失败: {e}")
            return []

    def fetch_zhihu_hot(self) -> List[Dict]:
        """获取知乎热榜（深度话题，有营养）"""
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-list-web"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data:
                for item in data['data'][:20]:
                    target = item.get('target', {})
                    topic = {
                        "title": target.get('title', ''),
                        "hot": target.get('heat', 0),
                        "source": "知乎热榜",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            return topics
        except Exception as e:
            print(f"知乎热榜获取失败: {e}")
            return []

    def fetch_baidu_hot(self) -> List[Dict]:
        """获取百度热搜（全民关注）"""
        try:
            url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data and 'cards' in data['data']:
                for card in data['data']['cards']:
                    for item in card.get('content', [])[:20]:
                        topic = {
                            "title": item.get('word', ''),
                            "hot": item.get('hotScore', 0),
                            "source": "百度热搜",
                            "time": datetime.now().strftime("%Y-%m-%d")
                        }
                        if topic['title']:
                            topics.append(topic)
            return topics
        except Exception as e:
            print(f"百度热搜获取失败: {e}")
            return []

    def fetch_douyin_hot(self) -> List[Dict]:
        """获取抖音热点（短视频热点，八卦多）"""
        try:
            url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data and 'word_list' in data['data']:
                for item in data['data']['word_list'][:15]:
                    topic = {
                        "title": item.get('word', ''),
                        "hot": item.get('hot_value', 0),
                        "source": "抖音热点",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            return topics
        except Exception as e:
            print(f"抖音热点获取失败: {e}")
            return []

    def fetch_toutiao_hot(self) -> List[Dict]:
        """获取今日头条热榜（新闻资讯）"""
        try:
            url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data:
                for item in data['data'][:15]:
                    topic = {
                        "title": item.get('Title', ''),
                        "hot": item.get('HotValue', 0),
                        "source": "今日头条",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            return topics
        except Exception as e:
            print(f"今日头条获取失败: {e}")
            return []

    def fetch_all_topics(self) -> List[Dict]:
        """获取所有平台热门话题"""
        print("正在获取全球热门话题...")
        
        # 获取各平台数据
        weibo = self.fetch_weibo_hot()
        zhihu = self.fetch_zhihu_hot()
        baidu = self.fetch_baidu_hot()
        douyin = self.fetch_douyin_hot()
        toutiao = self.fetch_toutiao_hot()
        
        # 合并所有话题
        all_topics = weibo + zhihu + baidu + douyin + toutiao
        
        # 按热度排序
        all_topics.sort(key=lambda x: x.get('hot', 0), reverse=True)
        
        # 去重（相同标题只保留一个）
        seen = set()
        unique_topics = []
        for topic in all_topics:
            title = topic['title']
            if title and title not in seen:
                seen.add(title)
                unique_topics.append(topic)
        
        print(f"共获取 {len(unique_topics)} 条热门话题")
        return unique_topics

    def classify_topics(self, topics: List[Dict]) -> Dict[str, List[Dict]]:
        """将话题分类到四个类别"""
        classified = {cat: [] for cat in CATEGORIES.keys()}
        
        for topic in topics:
            title = topic['title']
            matched = False
            
            for category, config in CATEGORIES.items():
                # 检查是否匹配关键词
                if any(kw in title for kw in config['keywords']):
                    # 检查是否包含排除词
                    if not any(exc in title for exc in config.get('exclude', [])):
                        classified[category].append(topic)
                        matched = True
                        break
            
            # 如果没有匹配到任何类别，根据内容智能判断
            if not matched:
                if any(kw in title for kw in ["游戏", "电竞", "手游", "Steam", "原神"]):
                    if len(classified['游戏圈']) < 5:
                        classified['游戏圈'].append(topic)
                elif any(kw in title for kw in ["明星", "演员", "歌手", "导演", "票房", "综艺", "电视剧", "电影", "瓜", "出轨", "离婚", "结婚"]):
                    if len(classified['娱乐圈']) < 5:
                        classified['娱乐圈'].append(topic)
                elif len(classified['国情']) < 5:
                    classified['国情'].append(topic)
        
        # 每个类别最多保留5条
        for cat in classified:
            classified[cat] = classified[cat][:5]
        
        return classified


class PushPlusNotifier:
    """PushPlus 微信推送器"""

    API_URL = "http://www.pushplus.plus/send"

    def __init__(self, token: str):
        self.token = token

    def send(self, title: str, content: str) -> bool:
        if not self.token:
            print("错误: 未设置 PUSHPLUS_TOKEN")
            return False
        try:
            data = json.dumps({
                "token": self.token,
                "title": title,
                "content": content,
                "template": "markdown"
            }).encode('utf-8')
            req = urllib.request.Request(
                self.API_URL,
                data=data,
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


def format_news_content(classified_news: Dict[str, List[Dict]]) -> str:
    """格式化新闻内容"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    content = f"# 🔥 每日热门话题早报 | {today}\n\n"
    content += "> 📱 长按标题即可复制，去百度/谷歌/知乎搜索详情\n"
    content += "> 🌍 数据来源：微博热搜、知乎热榜、百度热搜、抖音热点、今日头条\n\n"
    
    icons = {"国情": "🇨🇳", "世界经济": "💰", "游戏圈": "🎮", "娱乐圈": "🎬"}
    
    for category_name, news_list in classified_news.items():
        icon = icons.get(category_name, "📌")
        content += f"## {icon} {category_name}\n\n"
        
        if not news_list:
            content += "_暂无相关热门话题_\\n\\n"
            continue
        
        for i, news in enumerate(news_list, 1):
            title = news.get("title", "")
            source = news.get("source", "")
            hot = news.get("hot", 0)
            
            # 热度格式化
            if hot > 10000:
                hot_str = f"{hot/10000:.1f}万"
            else:
                hot_str = str(hot)
            
            # 标题加粗，方便长按复制
            content += f"**{i}. {title}**\n"
            content += f"> 🔥 热度：{hot_str} · 来源：{source}\n\n"
        
        content += "---\n\n"
    
    content += "*💡 提示：点击标题即可复制，使用搜索引擎查看详情*\\n"
    content += "*⏰ 每天早上8:00自动推送 | 数据来自国内外热门平台实时聚合*"
    
    return content


def main():
    print("=" * 60)
    print("🔥 每日热门话题早报 - 开始获取")
    print("=" * 60)
    
    if not PUSHPLUS_TOKEN:
        print("❌ 错误: 未设置 PUSHPLUS_TOKEN 环境变量")
        print("请在 GitHub Secrets 中设置 PUSHPLUS_TOKEN")
        return
    
    # 获取热门话题
    fetcher = HotTopicsFetcher()
    all_topics = fetcher.fetch_all_topics()
    
    # 分类
    print("\n正在分类话题...")
    classified = fetcher.classify_topics(all_topics)
    
    for cat, items in classified.items():
        print(f"  {cat}: {len(items)} 条")
    
    # 格式化内容
    print("\n正在格式化消息...")
    content = format_news_content(classified)
    
    # 推送
    today = datetime.now().strftime("%m月%d日")
    title = f"🔥 每日热门话题早报 | {today}"
    
    print("\n正在推送到微信...")
    notifier = PushPlusNotifier(PUSHPLUS_TOKEN)
    success = notifier.send(title, content)
    
    if success:
        print("\n✅ 今日热门话题推送完成！")
    else:
        print("\n❌ 推送失败，请检查配置")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
