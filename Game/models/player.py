# -*- coding: utf-8 -*-
"""
玩家模块 - 定义玩家类和相关功能
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime

class Player:
    """玩家类"""
    
    def __init__(self, player_id: str = None, name: str = "", is_ai: bool = False):
        self.player_id = player_id or str(uuid.uuid4())[:8]
        self.name = name
        self.is_ai = is_ai
        self.role = None  # 'undercover' 或 'civilian'
        self.is_alive = True
        self.money = 10000  # 初始资金
        self.stocks = {}  # 持有的股票 {symbol: amount}
        self.cards = []  # 手牌
        self.trust_level = 0  # 信任度 (-100 到 100)
        self.suspicion_level = 0  # 怀疑度 (0 到 100)
        self.investment_history = []  # 投资历史
        self.vote_history = []  # 投票历史
        self.messages = []  # 发言历史
        self.ai_personality = None  # AI性格特征
        self.created_at = datetime.now()
        
    def calculate_total_assets(self, stock_prices: Dict[str, float]) -> float:
        """计算总资产"""
        total = self.money
        for symbol, amount in self.stocks.items():
            if symbol in stock_prices:
                total += amount * stock_prices[symbol]
        return total
    
    def can_invest(self, amount: float) -> bool:
        """检查是否有足够资金投资"""
        return self.money >= amount
    
    def invest(self, symbol: str, amount: float, price: float) -> bool:
        """进行投资"""
        cost = amount * price
        if not self.can_invest(cost):
            return False
        
        self.money -= cost
        if symbol in self.stocks:
            self.stocks[symbol] += amount
        else:
            self.stocks[symbol] = amount
        
        # 记录投资历史
        self.investment_history.append({
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'cost': cost,
            'timestamp': datetime.now()
        })
        
        return True
    
    def sell_stock(self, symbol: str, amount: float, price: float) -> bool:
        """卖出股票"""
        if symbol not in self.stocks or self.stocks[symbol] < amount:
            return False
        
        self.stocks[symbol] -= amount
        if self.stocks[symbol] == 0:
            del self.stocks[symbol]
        
        revenue = amount * price
        self.money += revenue
        
        # 记录投资历史
        self.investment_history.append({
            'symbol': symbol,
            'amount': -amount,
            'price': price,
            'revenue': revenue,
            'timestamp': datetime.now()
        })
        
        return True
    
    def add_card(self, card):
        """添加卡牌"""
        self.cards.append(card)
    
    def remove_card(self, card_id: str) -> bool:
        """移除卡牌"""
        for i, card in enumerate(self.cards):
            if card.card_id == card_id:
                self.cards.pop(i)
                return True
        return False
    
    def get_card(self, card_id: str):
        """获取指定卡牌"""
        for card in self.cards:
            if card.card_id == card_id:
                return card
        return None
    
    def update_trust(self, change: int):
        """更新信任度"""
        self.trust_level = max(-100, min(100, self.trust_level + change))
    
    def update_suspicion(self, change: int):
        """更新怀疑度"""
        self.suspicion_level = max(0, min(100, self.suspicion_level + change))
    
    def add_message(self, message: str):
        """添加发言记录"""
        self.messages.append({
            'message': message,
            'timestamp': datetime.now()
        })
    
    def add_vote(self, target_id: str, round_num: int):
        """添加投票记录"""
        self.vote_history.append({
            'target_id': target_id,
            'round': round_num,
            'timestamp': datetime.now()
        })
    
    def get_role_description(self) -> str:
        """获取角色描述"""
        if self.role == 'undercover':
            return "你是卧底！目标是隐藏身份并存活到最后。"
        elif self.role == 'civilian':
            return "你是平民！目标是找出并投票淘汰所有卧底。"
        else:
            return "角色未分配"
    
    def get_investment_summary(self) -> Dict:
        """获取投资摘要"""
        total_invested = sum(inv['cost'] for inv in self.investment_history if inv.get('cost', 0) > 0)
        total_revenue = sum(inv['revenue'] for inv in self.investment_history if inv.get('revenue', 0) > 0)
        
        return {
            'total_invested': total_invested,
            'total_revenue': total_revenue,
            'net_profit': total_revenue - total_invested,
            'investment_count': len(self.investment_history)
        }
    
    def to_dict(self, include_private: bool = False) -> Dict:
        """转换为字典格式"""
        data = {
            'player_id': self.player_id,
            'name': self.name,
            'is_ai': self.is_ai,
            'is_alive': self.is_alive,
            'money': self.money,
            'stocks': self.stocks,
            'trust_level': self.trust_level,
            'suspicion_level': self.suspicion_level,
            'card_count': len(self.cards),
            'investment_summary': self.get_investment_summary()
        }
        
        if include_private:
            data.update({
                'role': self.role,
                'cards': [card.to_dict() for card in self.cards],
                'investment_history': self.investment_history,
                'vote_history': self.vote_history,
                'messages': self.messages,
                'ai_personality': self.ai_personality,
                'role_description': self.get_role_description()
            })
        
        return data
    
    def __str__(self):
        return f"Player({self.name}, {self.role}, ${self.money:.2f})"