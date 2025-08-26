# -*- coding: utf-8 -*-
"""
股市系统模块 - 模拟股票市场
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum

class MarketTrend(Enum):
    """市场趋势"""
    BULL = "bull"      # 牛市
    BEAR = "bear"      # 熊市
    SIDEWAYS = "sideways"  # 震荡

class Stock:
    """股票类"""
    
    def __init__(self, symbol: str, name: str, initial_price: float, 
                 volatility: float = 0.1, sector: str = "tech"):
        self.symbol = symbol
        self.name = name
        self.current_price = initial_price
        self.initial_price = initial_price
        self.volatility = volatility  # 波动率
        self.sector = sector
        self.price_history = [initial_price]
        self.volume_history = []
        self.last_update = datetime.now()
        
    def update_price(self, market_trend: MarketTrend, news_impact: float = 0) -> float:
        """更新股票价格"""
        # 基础随机变化
        random_change = random.gauss(0, self.volatility)
        
        # 市场趋势影响
        trend_impact = {
            MarketTrend.BULL: 0.02,
            MarketTrend.BEAR: -0.02,
            MarketTrend.SIDEWAYS: 0
        }[market_trend]
        
        # 计算总变化率
        total_change = random_change + trend_impact + news_impact
        
        # 更新价格
        new_price = self.current_price * (1 + total_change)
        new_price = max(0.01, new_price)  # 价格不能为负
        
        self.current_price = new_price
        self.price_history.append(new_price)
        self.last_update = datetime.now()
        
        return total_change
    
    def get_price_change_percent(self) -> float:
        """获取价格变化百分比"""
        if len(self.price_history) < 2:
            return 0
        
        old_price = self.price_history[-2]
        return (self.current_price - old_price) / old_price * 100
    
    def get_total_return_percent(self) -> float:
        """获取总回报率"""
        return (self.current_price - self.initial_price) / self.initial_price * 100
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'current_price': round(self.current_price, 2),
            'price_change_percent': round(self.get_price_change_percent(), 2),
            'total_return_percent': round(self.get_total_return_percent(), 2),
            'volatility': self.volatility,
            'sector': self.sector,
            'last_update': self.last_update.isoformat()
        }

class MarketEvent:
    """市场事件类"""
    
    def __init__(self, event_type: str, description: str, 
                 impact: Dict[str, float], duration: int = 1):
        self.event_type = event_type
        self.description = description
        self.impact = impact  # {symbol: impact_rate}
        self.duration = duration
        self.created_at = datetime.now()
        
    def to_dict(self) -> Dict:
        return {
            'type': self.event_type,
            'description': self.description,
            'impact': self.impact,
            'duration': self.duration,
            'created_at': self.created_at.isoformat()
        }

class StockMarket:
    """股票市场类"""
    
    def __init__(self):
        self.stocks: Dict[str, Stock] = {}
        self.market_trend = MarketTrend.SIDEWAYS
        self.market_events: List[MarketEvent] = []
        self.round_number = 0
        self._initialize_stocks()
        
    def _initialize_stocks(self):
        """初始化股票"""
        stock_data = [
            ('AAPL', '苹果公司', 150.0, 0.12, 'tech'),
            ('GOOGL', '谷歌', 2800.0, 0.15, 'tech'),
            ('TSLA', '特斯拉', 800.0, 0.25, 'auto'),
            ('AMZN', '亚马逊', 3300.0, 0.18, 'retail'),
            ('MSFT', '微软', 300.0, 0.10, 'tech'),
            ('NVDA', '英伟达', 220.0, 0.20, 'tech'),
            ('META', 'Meta', 320.0, 0.22, 'social'),
            ('NFLX', '奈飞', 400.0, 0.16, 'media'),
            ('BTC', '比特币', 45000.0, 0.30, 'crypto'),
            ('ETH', '以太坊', 3000.0, 0.28, 'crypto')
        ]
        
        for symbol, name, price, volatility, sector in stock_data:
            self.stocks[symbol] = Stock(symbol, name, price, volatility, sector)
    
    def update_market_trend(self):
        """更新市场趋势"""
        # 随机改变市场趋势
        trends = list(MarketTrend)
        weights = [0.3, 0.3, 0.4]  # 牛市、熊市、震荡的概率
        self.market_trend = random.choices(trends, weights=weights)[0]
    
    def generate_market_event(self) -> Optional[MarketEvent]:
        """生成市场事件"""
        # 30%概率生成事件
        if random.random() > 0.3:
            return None
        
        events = [
            {
                'type': 'tech_boom',
                'description': '科技股大涨！AI技术突破带动科技板块上涨',
                'impact': {symbol: 0.08 for symbol, stock in self.stocks.items() 
                          if stock.sector == 'tech'}
            },
            {
                'type': 'market_crash',
                'description': '市场恐慌！全球经济担忧导致股市下跌',
                'impact': {symbol: -0.05 for symbol in self.stocks.keys()}
            },
            {
                'type': 'crypto_surge',
                'description': '加密货币暴涨！机构投资者大量买入',
                'impact': {symbol: 0.15 for symbol, stock in self.stocks.items() 
                          if stock.sector == 'crypto'}
            },
            {
                'type': 'auto_recall',
                'description': '汽车召回事件！安全问题影响汽车股',
                'impact': {symbol: -0.12 for symbol, stock in self.stocks.items() 
                          if stock.sector == 'auto'}
            },
            {
                'type': 'earnings_beat',
                'description': '财报季超预期！多家公司业绩亮眼',
                'impact': {random.choice(list(self.stocks.keys())): 0.10}
            }
        ]
        
        event_data = random.choice(events)
        event = MarketEvent(
            event_type=event_data['type'],
            description=event_data['description'],
            impact=event_data['impact']
        )
        
        self.market_events.append(event)
        return event
    
    def update_prices(self) -> Dict:
        """更新所有股票价格"""
        self.round_number += 1
        
        # 更新市场趋势
        self.update_market_trend()
        
        # 生成市场事件
        new_event = self.generate_market_event()
        
        # 计算事件影响
        event_impacts = {}
        for event in self.market_events:
            for symbol, impact in event.impact.items():
                if symbol in event_impacts:
                    event_impacts[symbol] += impact
                else:
                    event_impacts[symbol] = impact
        
        # 更新股票价格
        price_changes = {}
        for symbol, stock in self.stocks.items():
            news_impact = event_impacts.get(symbol, 0)
            change_rate = stock.update_price(self.market_trend, news_impact)
            price_changes[symbol] = change_rate
        
        # 清理过期事件
        self.market_events = [event for event in self.market_events 
                             if (datetime.now() - event.created_at).days < event.duration]
        
        return {
            'round': self.round_number,
            'market_trend': self.market_trend.value,
            'new_event': new_event.to_dict() if new_event else None,
            'price_changes': price_changes,
            'stocks': {symbol: stock.to_dict() for symbol, stock in self.stocks.items()}
        }
    
    def get_stock_price(self, symbol: str) -> float:
        """获取股票价格"""
        if symbol in self.stocks:
            return self.stocks[symbol].current_price
        return 0
    
    def get_all_stocks(self) -> Dict[str, Dict]:
        """获取所有股票信息"""
        return {symbol: stock.to_dict() for symbol, stock in self.stocks.items()}
    
    def get_market_summary(self) -> Dict:
        """获取市场摘要"""
        total_stocks = len(self.stocks)
        rising_stocks = sum(1 for stock in self.stocks.values() 
                           if stock.get_price_change_percent() > 0)
        falling_stocks = sum(1 for stock in self.stocks.values() 
                            if stock.get_price_change_percent() < 0)
        
        avg_change = sum(stock.get_price_change_percent() 
                        for stock in self.stocks.values()) / total_stocks
        
        return {
            'market_trend': self.market_trend.value,
            'total_stocks': total_stocks,
            'rising_stocks': rising_stocks,
            'falling_stocks': falling_stocks,
            'unchanged_stocks': total_stocks - rising_stocks - falling_stocks,
            'average_change': round(avg_change, 2),
            'active_events': len(self.market_events),
            'round_number': self.round_number
        }
    
    def calculate_portfolio_value(self, portfolio: Dict[str, float]) -> float:
        """计算投资组合价值"""
        total_value = 0
        for symbol, amount in portfolio.items():
            if symbol in self.stocks:
                total_value += amount * self.stocks[symbol].current_price
        return total_value
    
    def get_top_performers(self, count: int = 3) -> List[Dict]:
        """获取表现最佳的股票"""
        stocks_with_change = [(symbol, stock.get_price_change_percent(), stock) 
                             for symbol, stock in self.stocks.items()]
        stocks_with_change.sort(key=lambda x: x[1], reverse=True)
        
        return [{
            'symbol': symbol,
            'name': stock.name,
            'change_percent': round(change, 2),
            'current_price': round(stock.current_price, 2)
        } for symbol, change, stock in stocks_with_change[:count]]
    
    def get_worst_performers(self, count: int = 3) -> List[Dict]:
        """获取表现最差的股票"""
        stocks_with_change = [(symbol, stock.get_price_change_percent(), stock) 
                             for symbol, stock in self.stocks.items()]
        stocks_with_change.sort(key=lambda x: x[1])
        
        return [{
            'symbol': symbol,
            'name': stock.name,
            'change_percent': round(change, 2),
            'current_price': round(stock.current_price, 2)
        } for symbol, change, stock in stocks_with_change[:count]]