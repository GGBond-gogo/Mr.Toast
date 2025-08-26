# -*- coding: utf-8 -*-
"""
AI系统模块 - AI玩家行为和决策
"""

import random
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# 确保能够导入 Player 类
try:
    from .player import Player
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from player import Player

class AIPersonality:
    """AI性格类型"""
    
    def __init__(self, name: str, traits: Dict[str, float]):
        self.name = name
        self.traits = traits  # 性格特征：aggressive, cautious, social, analytical等
        
    def get_trait(self, trait_name: str) -> float:
        """获取性格特征值"""
        return self.traits.get(trait_name, 0.5)

class AIPlayer(Player):
    """AI玩家类"""
    
    def __init__(self, player_id: str, name: str, personality: AIPersonality):
        super().__init__(player_id, name, is_ai=True)
        self.personality = personality
        # 暂时注释掉这些依赖，避免循环导入
        # self.dialogue_system = AIDialogueSystem(personality)
        # self.behavior_analyzer = AIBehaviorAnalyzer()
        self.memory = []  # AI记忆
        self.suspicion_targets = {}  # 怀疑目标
        self.trust_targets = {}  # 信任目标
        self.last_action_time = datetime.now()
        
    def make_investment_decision(self, game_state, stock_market) -> Optional[Dict]:
        """AI投资决策"""
        if not self.is_alive or self.money <= 0:
            return None
            
        # 获取可用股票
        available_stocks = stock_market.get_all_stocks()
        if not available_stocks:
            return None
            
        # 根据性格特征决策
        risk_tolerance = self.personality.get_trait('risk_tolerance')
        analytical_level = self.personality.get_trait('analytical')
        
        # 分析股票
        stock_scores = {}
        for stock in available_stocks:
            score = self._analyze_stock(stock, analytical_level)
            stock_scores[stock.symbol] = score
            
        # 选择最佳股票
        if not stock_scores:
            return None
            
        best_stock = max(stock_scores.keys(), key=lambda x: stock_scores[x])
        
        # 决定投资金额
        investment_ratio = self._calculate_investment_ratio(risk_tolerance)
        investment_amount = min(self.money * investment_ratio, self.money)
        
        if investment_amount < 10:  # 最小投资额
            return None
            
        return {
            'stock_symbol': best_stock,
            'amount': investment_amount,
            'action': 'buy'
        }
        
    def _analyze_stock(self, stock, analytical_level: float) -> float:
        """分析股票得分"""
        score = 0.5  # 基础分数
        
        # 价格趋势分析
        if len(stock.price_history) >= 2:
            recent_change = (stock.current_price - stock.price_history[-2]) / stock.price_history[-2]
            score += recent_change * analytical_level
            
        # 波动率分析
        if analytical_level > 0.7:
            # 高分析能力的AI会考虑波动率
            volatility_penalty = stock.volatility * 0.1
            score -= volatility_penalty
            
        # 随机因素
        score += random.gauss(0, 0.1)
        
        return max(0, min(1, score))
        
    def _calculate_investment_ratio(self, risk_tolerance: float) -> float:
        """计算投资比例"""
        base_ratio = 0.2 + (risk_tolerance * 0.6)  # 20%-80%
        
        # 根据当前资金状况调整
        if self.money > 1000:
            base_ratio *= 1.2
        elif self.money < 200:
            base_ratio *= 0.5
            
        return min(0.8, max(0.1, base_ratio))
        
    def make_card_decision(self, game_state, available_cards: List) -> Optional[Dict]:
        """AI卡牌使用决策"""
        if not self.is_alive or not available_cards:
            return None
            
        # 根据性格和游戏状态选择卡牌
        aggressive = self.personality.get_trait('aggressive')
        social = self.personality.get_trait('social')
        
        for card in available_cards:
            if self._should_use_card(card, game_state, aggressive, social):
                target = self._select_card_target(card, game_state)
                return {
                    'card_id': card.card_id,
                    'target_player_id': target.player_id if target else None
                }
                
        return None
        
    def _should_use_card(self, card, game_state, aggressive: float, social: float) -> bool:
        """判断是否应该使用卡牌"""
        # 卧底更倾向于使用攻击性卡牌
        if self.role == 'undercover':
            if 'attack' in card.name.lower() or 'frame' in card.name.lower():
                return random.random() < 0.8
                
        # 平民更倾向于使用防御性卡牌
        if self.role == 'civilian':
            if 'trust' in card.name.lower() or 'defend' in card.name.lower():
                return random.random() < 0.7
                
        # 根据性格特征决定
        use_probability = 0.3 + (aggressive * 0.4) + (social * 0.2)
        return random.random() < use_probability
        
    def _select_card_target(self, card, game_state) -> Optional[Player]:
        """选择卡牌目标"""
        alive_players = [p for p in game_state.get_alive_players() if p.player_id != self.player_id]
        
        if not alive_players:
            return None
            
        # 根据卡牌类型和AI角色选择目标
        if self.role == 'undercover':
            # 卧底倾向于攻击最可疑的平民
            civilians = [p for p in alive_players if p.role != 'undercover']
            if civilians:
                return max(civilians, key=lambda p: p.suspicion_level)
        else:
            # 平民倾向于攻击最可疑的玩家
            return max(alive_players, key=lambda p: p.suspicion_level)
            
        return random.choice(alive_players)
        
    def make_vote_decision(self, game_state) -> Optional[str]:
        """AI投票决策"""
        if not self.is_alive:
            return None
            
        alive_players = [p for p in game_state.get_alive_players() if p.player_id != self.player_id]
        
        if not alive_players:
            return None
            
        # 根据角色和怀疑度投票
        if self.role == 'undercover':
            # 卧底投票策略：投给最不可疑的平民
            civilians = [p for p in alive_players if p.role != 'undercover']
            if civilians:
                target = min(civilians, key=lambda p: p.suspicion_level)
                return target.player_id
        else:
            # 平民投票策略：投给最可疑的玩家
            target = max(alive_players, key=lambda p: p.suspicion_level)
            return target.player_id
            
        return random.choice(alive_players).player_id
        
    def generate_message(self, game_state, context: str = "") -> str:
        """生成AI消息"""
        return self.dialogue_system.generate_message(game_state, self, context)
        
    def update_memory(self, event: Dict):
        """更新AI记忆"""
        self.memory.append({
            'timestamp': datetime.now(),
            'event': event
        })
        
        # 限制记忆长度
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
            
    def analyze_player_behavior(self, target_player, game_state) -> float:  # 移除 : Player
        """分析玩家行为可疑度"""
        return self.behavior_analyzer.analyze_suspicion(target_player, game_state)
        
    def update_suspicion_targets(self, game_state):
        """更新怀疑目标"""
        for player in game_state.get_alive_players():
            if player.player_id != self.player_id:
                suspicion = self.analyze_player_behavior(player, game_state)
                self.suspicion_targets[player.player_id] = suspicion

class AISystem:
    """AI系统管理类"""
    
    def __init__(self):
        self.personalities = self._create_personalities()
        self.ai_players = {}
        
    def _create_personalities(self) -> List[AIPersonality]:
        """创建AI性格类型"""
        return [
            AIPersonality("激进投资者", {
                'aggressive': 0.8,
                'risk_tolerance': 0.9,
                'social': 0.6,
                'analytical': 0.7,
                'suspicious': 0.5
            }),
            AIPersonality("保守分析师", {
                'aggressive': 0.2,
                'risk_tolerance': 0.3,
                'social': 0.4,
                'analytical': 0.9,
                'suspicious': 0.7
            }),
            AIPersonality("社交达人", {
                'aggressive': 0.5,
                'risk_tolerance': 0.6,
                'social': 0.9,
                'analytical': 0.5,
                'suspicious': 0.4
            }),
            AIPersonality("神秘玩家", {
                'aggressive': 0.6,
                'risk_tolerance': 0.7,
                'social': 0.3,
                'analytical': 0.8,
                'suspicious': 0.8
            }),
            AIPersonality("平衡型", {
                'aggressive': 0.5,
                'risk_tolerance': 0.5,
                'social': 0.5,
                'analytical': 0.6,
                'suspicious': 0.5
            })
        ]
        
    def create_ai_player(self, player_id: str, name: str) -> AIPlayer:
        """创建AI玩家"""
        personality = random.choice(self.personalities)
        ai_player = AIPlayer(player_id, name, personality)
        self.ai_players[player_id] = ai_player
        return ai_player
        
    def get_ai_player(self, player_id: str) -> Optional[AIPlayer]:
        """获取AI玩家"""
        return self.ai_players.get(player_id)
        
    def process_ai_turn(self, game_state, ai_player: AIPlayer) -> List[Dict]:
        """处理AI回合"""
        actions = []
        
        # 更新怀疑目标
        ai_player.update_suspicion_targets(game_state)
        
        # 投资决策
        if game_state.current_phase == 'investment':
            investment = ai_player.make_investment_decision(game_state, game_state.stock_market)
            if investment:
                actions.append({
                    'type': 'investment',
                    'data': investment
                })
                
        # 卡牌使用决策
        if ai_player.cards:
            card_action = ai_player.make_card_decision(game_state, ai_player.cards)
            if card_action:
                actions.append({
                    'type': 'use_card',
                    'data': card_action
                })
                
        # 发言决策
        if random.random() < 0.3:  # 30%概率发言
            message = ai_player.generate_message(game_state)
            if message:
                actions.append({
                    'type': 'message',
                    'data': {'message': message}
                })
                
        return actions
        
    def process_ai_vote(self, game_state, ai_player: AIPlayer) -> Optional[str]:
        """处理AI投票"""
        return ai_player.make_vote_decision(game_state)