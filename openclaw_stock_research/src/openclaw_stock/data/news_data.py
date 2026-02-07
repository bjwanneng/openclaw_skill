"""
新闻数据采集模块

提供股票相关新闻的采集和分析功能。
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsDataCollector:
    """新闻数据采集器"""
    
    def __init__(self):
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_stock_news(
        self,
        symbol: str,
        stock_name: str = "",
        limit: int = 10
    ) -> Dict:
        """
        获取股票相关新闻
        
        Args:
            symbol: 股票代码（如 601127）
            stock_name: 股票名称（如 赛力斯），用于关键词搜索
            limit: 返回新闻数量限制
            
        Returns:
            包含新闻列表和摘要的字典
        """
        logger.info(f"[fetch_stock_news] 获取 {symbol} ({stock_name}) 的新闻")
        
        news_list = []
        
        # 尝试从新浪财经搜索
        try:
            search_keyword = stock_name if stock_name else symbol
            url = f"https://search.sina.com.cn/?q={search_keyword}&c=news&from=index&col=&range=all&source=&country=&size={limit}&time=&a=&page=1&pf=0&ps=0&t=0"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找新闻条目
                news_items = soup.find_all(['h2', 'h3', 'div'], class_=['box-result', 'r-info'])
                
                for item in news_items[:limit]:
                    try:
                        # 提取标题和链接
                        link_tag = item.find('a')
                        if not link_tag:
                            continue
                            
                        title = link_tag.get_text().strip()
                        href = link_tag.get('href', '')
                        
                        # 提取时间
                        time_tag = item.find('span', class_='fgray_time')
                        time_str = time_tag.get_text().strip() if time_tag else ''
                        
                        # 提取摘要
                        summary_tag = item.find('p', class_='content')
                        summary = summary_tag.get_text().strip() if summary_tag else ''
                        
                        if title and href:
                            news_list.append({
                                'title': title,
                                'url': href,
                                'time': time_str,
                                'summary': summary,
                                'source': '新浪财经'
                            })
                    except Exception as e:
                        logger.warning(f"解析新闻条目失败: {e}")
                        continue
                
                logger.info(f"成功获取 {len(news_list)} 条新闻")
        
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
        
        # 生成新闻摘要
        summary = self._generate_news_summary(news_list, stock_name or symbol)
        
        return {
            'symbol': symbol,
            'stock_name': stock_name,
            'news_count': len(news_list),
            'news_list': news_list,
            'summary': summary,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_news_summary(self, news_list: List[Dict], keyword: str) -> str:
        """
        生成新闻摘要
        
        Args:
            news_list: 新闻列表
            keyword: 关键词
            
        Returns:
            新闻摘要文本
        """
        if not news_list:
            return f"未找到关于 {keyword} 的相关新闻"
        
        summary_lines = [f"找到 {len(news_list)} 条关于 {keyword} 的新闻：\n"]
        
        for i, news in enumerate(news_list[:5], 1):  # 只摘要前5条
            time_str = f"[{news['time']}] " if news['time'] else ""
            summary_lines.append(f"{i}. {time_str}{news['title']}")
            if news['summary']:
                summary_lines.append(f"   {news['summary'][:100]}...")
        
        if len(news_list) > 5:
            summary_lines.append(f"\n... 还有 {len(news_list) - 5} 条新闻")
        
        return '\n'.join(summary_lines)


def fetch_stock_news(
    symbol: str,
    stock_name: str = "",
    limit: int = 10
) -> Dict:
    """
    获取股票相关新闻（便捷函数）
    
    Args:
        symbol: 股票代码
        stock_name: 股票名称
        limit: 返回新闻数量限制
        
    Returns:
        新闻数据字典
    """
    collector = NewsDataCollector()
    return collector.fetch_stock_news(symbol, stock_name, limit)
