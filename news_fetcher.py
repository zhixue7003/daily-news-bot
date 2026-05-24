#!/usr/bin/env python3
"""
每日新闻抓取与推送脚本 - 优化版
支持：国情、世界经济、游戏圈、娱乐圈顶流
"""

import os
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict

# ============ 配置区域 ============
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# 分类配置（扩大关键词范围）
CATEGORIES = {
    "国情": {
        "keywords": ["中国", "国内", "政策", "时政", "国务院", "人大", "两会", "习近平", "外交部", "发改委", "央行", "国防部", "台湾", "香港", "澳门", "北京", "上海", "广州", "深圳", "疫情", "疫苗", "教育", "高考", "大学", "就业", "房价", "养老", "医保", "社保", "交通", "天气", "地震", "洪水", "火灾", "事故", "犯罪", "警察", "法院", "法律"],
        "exclude": []
    },
    "世界经济": {
        "keywords": ["美联储", "美股", "港股", "A股", "全球经济", "油价", "黄金", "汇率", "通胀", "GDP", "华尔街", "纳斯达克", "道琼斯", "比特币", "加密货币", "特斯拉", "苹果", "微软", "谷歌", "亚马逊", "马云", "马化腾", "任正非", "马斯克", "巴菲特", "贝佐斯", "扎克伯格", "经济", "金融", "银行", "股票", "基金", "期货", "房地产", "楼市", "美元", "欧元", "日元", "人民币", "加息", "降息", "央行", "财报", "营收", "利润", "破产", "裁员", "失业", "就业", "物价", "CPI", "PPI", "贸易", "关税", "进出口", "石油", "天然气", "新能源", "电动车", "芯片", "半导体", "AI", "人工智能", "ChatGPT", "OpenAI"],
        "exclude": []
    },
    "游戏圈": {
        "keywords": ["游戏", "手游", "网游", "电竞", "Steam", "原神", "王者荣耀", "LOL", "英雄联盟", "黑神话", "Switch", "PS5", "Xbox", "腾讯游戏", "网易游戏", "米哈游", "暴雪", "网易", "腾讯", "字节跳动", "B站", "哔哩哔哩", "主播", "直播", "吃鸡", "绝地求生", "和平精英", "CF", "穿越火线", "DNF", "地下城", "魔兽世界", "守望先锋", "炉石传说", "DOTA", "CSGO", "永劫无间", "蛋仔派对", "元梦之星", "崩坏", "星穹铁道", "绝区零", "鸣潮", "幻兽帕鲁", "博德之门", "塞尔达", "马里奥", "宝可梦", "GTA", "使命召唤", "战地", " FIFA", "NBA2K", "电竞", "LPL", "KPL", "TI", "S赛", "世界杯", "亚运会电竞"],
        "exclude": []
    },
    "娱乐圈": {
        "keywords": ["明星", "娱乐", "电影", "电视剧", "综艺", "顶流", "艺人", "演员", "歌手", "导演", "编剧", "制片人", "票房", "首映", "点映", "路演", "杀青", "开机", "定档", "撤档", "改档", "上映", "播出", "收官", "大结局", "演唱会", "音乐节", "演唱会", "见面会", "粉丝", "应援", "打榜", "投票", "八卦", "爆料", "瓜", "塌房", "封杀", "雪藏", "解约", "签约", "代言", "广告", "红毯", "造型", "穿搭", "妆容", "发型", "减肥", "增肥", "整容", "素颜", "生图", "精修", "路透", "花絮", "预告片", "海报", "剧照", "MV", "单曲", "专辑", "EP", "OST", "主题曲", "片尾曲", "插曲", "翻唱", "改编", "原创", "抄袭", "侵权", "诉讼", "官司", "赔偿", "出轨", "离婚", "结婚", "恋爱", "分手", "复合", "官宣", "领证", "婚礼", "蜜月", "怀孕", "生子", "二胎", "三胎", "亲子", "萌娃", "童星", "星二代", "范冰冰", "杨幂", "赵丽颖", "迪丽热巴", "杨紫", "刘亦菲", "刘诗诗", "唐嫣", "杨颖", "倪妮", "周冬雨", "关晓彤", "赵露思", "虞书欣", "白鹿", "鞠婧祎", "杨超越", "肖战", "王一博", "易烊千玺", "王俊凯", "王源", "鹿晗", "黄子韬", "张艺兴", "蔡徐坤", "华晨宇", "周杰伦", "林俊杰", "薛之谦", "李荣浩", "邓紫棋", "张靓颖", "周深", "毛不易", "单依纯", "汪苏泷", "许嵩", "陈奕迅", "张学友", "刘德华", "梁朝伟", "周星驰", "成龙", "李连杰", "甄子丹", "吴京", "沈腾", "马丽", "贾玲", "张小斐", "黄渤", "王宝强", "徐峥", "宁浩", "陈思诚", "张艺谋", "陈凯歌", "冯小刚", "贾樟柯", "王小帅", "娄烨", "毕赣", "文牧野", "郭帆", "饺子", "宫崎骏", "新海诚", "诺兰", "卡梅隆", "斯皮尔伯格"],
        "exclude": []
    }
}


class HotTopicsFetcher:
    """热门话题抓取器"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }

    def safe_get_hot(self, value) -> int:
        """安全获取热度值"""
        try:
            if value is None:
                return 0
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                value = value.replace('万', '').replace('亿', '').replace(',', '')
                return int(float(value))
            return int(value)
        except:
            return 0

    def fetch_zhihu_hot(self) -> List[Dict]:
        """获取知乎热榜"""
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-list-web"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data:
                for item in data['data'][:30]:
                    target = item.get('target', {})
                    topic = {
                        "title": target.get('title', ''),
                        "hot": self.safe_get_hot(target.get('heat', 0)),
                        "source": "知乎热榜",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            print(f"知乎热榜: {len(topics)} 条")
            return topics
        except Exception as e:
            print(f"知乎热榜获取失败: {e}")
            return []

    def fetch_baidu_hot(self) -> List[Dict]:
        """获取百度热搜"""
        try:
            url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data and 'cards' in data['data']:
                for card in data['data']['cards']:
                    for item in card.get('content', [])[:30]:
                        topic = {
                            "title": item.get('word', ''),
                            "hot": self.safe_get_hot(item.get('hotScore', 0)),
                            "source": "百度热搜",
                            "time": datetime.now().strftime("%Y-%m-%d")
                        }
                        if topic['title']:
                            topics.append(topic)
            print(f"百度热搜: {len(topics)} 条")
            return topics
        except Exception as e:
            print(f"百度热搜获取失败: {e}")
            return []

    def fetch_toutiao_hot(self) -> List[Dict]:
        """获取今日头条热榜"""
        try:
            url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if 'data' in data:
                for item in data['data'][:25]:
                    topic = {
                        "title": item.get('Title', ''),
                        "hot": self.safe_get_hot(item.get('HotValue', 0)),
                        "source": "今日头条",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            print(f"今日头条: {len(topics)} 条")
            return topics
        except Exception as e:
            print(f"今日头条获取失败: {e}")
            return []

    def fetch_weibo_hot(self) -> List[Dict]:
        """获取微博热搜"""
        try:
            url = "https://api.oioweb.cn/api/common/weiboHot"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            if data.get('code') == 200 and 'result' in data:
                for item in data['result'][:30]:
                    topic = {
                        "title": item.get('word', ''),
                        "hot": self.safe_get_hot(item.get('hot', 0)),
                        "source": "微博热搜",
                        "time": datetime.now().strftime("%Y-%m-%d")
                    }
                    if topic['title']:
                        topics.append(topic)
            print(f"微博热搜: {len(topics)} 条")
            return topics
        except Exception as e:
            print(f"微博热搜获取失败: {e}")
            return []

    def fetch_all_topics(self) -> List[Dict]:
        """获取所有平台热门话题"""
        print("正在获取全球热门话题...")
        
        zhihu = self.fetch_zhihu_hot()
        baidu = self.fetch_baidu_hot()
        toutiao = self.fetch_toutiao_hot()
        weibo = self.fetch_weibo_hot()
        
        all_topics = zhihu + baidu + toutiao + weibo
        
        # 按热度排序
        all_topics.sort(key=lambda x: x.get('hot', 0), reverse=True)
        
        # 去重
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
        """智能分类话题"""
        classified = {cat: [] for cat in CATEGORIES.keys()}
        unclassified = []
        
        # 第一轮：按关键词分类
        for topic in topics:
            title = topic['title']
            matched = False
            
            for category, config in CATEGORIES.items():
                if any(kw in title for kw in config['keywords']):
                    if not any(exc in title for exc in config.get('exclude', [])):
                        classified[category].append(topic)
                        matched = True
                        break
            
            if not matched:
                unclassified.append(topic)
        
        print(f"\n分类结果（第一轮）：")
        for cat, items in classified.items():
            print(f"  {cat}: {len(items)} 条")
        print(f"  未分类: {len(unclassified)} 条")
        
        # 第二轮：智能分配未分类话题
        # 根据话题内容智能判断
        for topic in unclassified[:20]:  # 只处理前20条未分类
            title = topic['title']
            
            # 娱乐相关
            if any(kw in title for kw in ["新剧", "新片", "上映", "播出", "杀青", "开机", "红毯", "造型", "演唱会", "音乐节", "粉丝", "应援"]):
                if len(classified['娱乐圈']) < 5:
                    classified['娱乐圈'].append(topic)
                    continue
            
            # 游戏相关
            if any(kw in title for kw in ["上线", "公测", "内测", "版本更新", "新赛季", "新英雄", "新皮肤", "职业选手", "战队", "比赛"]):
                if len(classified['游戏圈']) < 5:
                    classified['游戏圈'].append(topic)
                    continue
            
            # 经济相关
            if any(kw in title for kw in ["涨价", "降价", "销量", "市值", "股价", "暴跌", "暴涨", "创新高", "跌破", "收购", "合并", "投资", "融资", "上市", "退市"]):
                if len(classified['世界经济']) < 5:
                    classified['世界经济'].append(topic)
                    continue
            
            # 其他放入国情
            if len(classified['国情']) < 5:
                classified['国情'].append(topic)
        
        # 第三轮：确保每个分类至少有内容
        # 如果某个分类为空，从其他分类借调
        min_items = 3  # 每个分类最少3条
        
        for cat in ['世界经济', '游戏圈', '娱乐圈']:
            if len(classified[cat]) < min_items:
                # 从国情借调
                while len(classified[cat]) < min_items and len(classified['国情']) > min_items:
                    classified[cat].append(classified['国情'].pop())
        
        # 每个分类最多保留5条
        for cat in classified:
            classified[cat] = classified[cat][:5]
        
        print(f"\n分类结果（最终）：")
        for cat, items in classified.items():
            print(f"  {cat}: {len(items)} 条")
        
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
    content += "> 🌍 数据来源：微博热搜、知乎热榜、百度热搜、今日头条\n\n"
    
    icons = {"国情": "🇨🇳", "世界经济": "💰", "游戏圈": "🎮", "娱乐圈": "🎬"}
    
    for category_name, news_list in classified_news.items():
        icon = icons.get(category_name, "📌")
        content += f"## {icon} {category_name}\n\n"
        
        if not news_list:
            content += "_暂无相关热门话题_\n\n"
            continue
        
        for i, news in enumerate(news_list, 1):
            title = news.get("title", "")
            source = news.get("source", "")
            hot = news.get("hot", 0)
            
            if hot > 10000:
                hot_str = f"{hot/10000:.1f}万"
            else:
                hot_str = str(hot)
            
            content += f"**{i}. {title}**\n"
            content += f"> 🔥 热度：{hot_str} · 来源：{source}\n\n"
        
        content += "---\n\n"
    
    content += "*💡 提示：点击标题即可复制，使用搜索引擎查看详情*\n"
    content += "*⏰ 每天早上8:00自动推送*"
    
    return content


def main():
    print("=" * 60)
    print("🔥 每日热门话题早报 - 开始获取")
    print("=" * 60)
    
    if not PUSHPLUS_TOKEN:
        print("❌ 错误: 未设置 PUSHPLUS_TOKEN 环境变量")
        return
    
    fetcher = HotTopicsFetcher()
    all_topics = fetcher.fetch_all_topics()
    
    if not all_topics:
        print("❌ 未获取到任何话题，请检查网络连接")
        return
    
    classified = fetcher.classify_topics(all_topics)
    
    print("\n正在格式化消息...")
    content = format_news_content(classified)
    
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
