# -*- coding: utf-8 -*-
"""
AI行为分析器模块 - 分析玩家行为模式
"""

import math
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class BehaviorPattern:
    """行为模式"""
    risk_preference: float      # 风险偏好 (0-1)
    investment_consistency: float  # 投资一致性 (0-1)
    social_activity: float      # 社交活跃度 (0-1)
    suspicion_tendency: float   # 怀疑倾向 (0-1)
    defensive_frequency: float  # 防御频率 (0-1)
    voting_pattern: float       # 投票模式 (0-1)

class AIBehaviorAnalyzer:
    """AI行为分析器"""
    
    def __init__(self):
        self.behavior_history = {}
        self.suspicion_weights = {
            'risk_preference': 0.15,
            'investment_consistency': 0.25,
            'social_activity': 0.15,
            'suspicion_tendency': 0.20,
            'defensive_frequency': 0.15,
            'voting_pattern': 0.10
        }
        
    def analyze_player_behavior(self, player, game_state) -> BehaviorPattern:
        """分析玩家行为模式"""
        # 分析风险偏好
        risk_preference = self._analyze_risk_preference(player)
        
        # 分析投资一致性
        investment_consistency = self._analyze_investment_consistency(player)
        
        # 分析社交活跃度
        social_activity = self._analyze_social_activity(player, game_state)
        
        # 分析怀疑倾向
        suspicion_tendency = self._analyze_suspicion_tendency(player)
        
        # 分析防御频率
        defensive_frequency = self._analyze_defensive_frequency(player)
        
        # 分析投票模式
        voting_pattern = self._analyze_voting_pattern(player, game_state)
        
        return BehaviorPattern(
            risk_preference=risk_preference,
            investment_consistency=investment_consistency,
            social_activity=social_activity,
            suspicion_tendency=suspicion_tendency,
            defensive_frequency=defensive_frequency,
            voting_pattern=voting_pattern
        )
        
    def _analyze_risk_preference(self, player) -> float:
        """分析风险偏好"""
        if not player.investment_history:
            return 0.5  # 默认中等风险偏好
            
        total_investments = len(player.investment_history)
        high_risk_investments = 0
        
        for investment in player.investment_history:
            # 假设投资金额占总资金比例超过30%为高风险
            if investment.get('amount', 0) > player.money * 0.3:
                high_risk_investments += 1
                
        return high_risk_investments / total_investments if total_investments > 0 else 0.5
        
    def _analyze_investment_consistency(self, player) -> float:
        """分析投资一致性"""
        if len(player.investment_history) < 2:
            return 0.5
            
        # 分析投资策略的一致性
        strategies = []
        for investment in player.investment_history:
            # 简化的策略分类
            if investment.get('amount', 0) > player.money * 0.5:
                strategies.append('aggressive')
            elif investment.get('amount', 0) < player.money * 0.2:
                strategies.append('conservative')
            else:
                strategies.append('moderate')
                
        # 计算策略一致性
        if not strategies:
            return 0.5
            
        most_common = max(set(strategies), key=strategies.count)
        consistency = strategies.count(most_common) / len(strategies)
        
        return consistency
        
    def _analyze_social_activity(self, player, game_state) -> float:
        """分析社交活跃度"""
        if not hasattr(player, 'message_history'):
            return 0.5
            
        total_messages = len(player.message_history)
        total_rounds = game_state.round_number if game_state.round_number > 0 else 1
        
        # 计算每轮平均消息数
        messages_per_round = total_messages / total_rounds
        
        # 标准化到0-1范围
        return min(1.0, messages_per_round / 3.0)  # 假设每轮3条消息为高活跃度
        
    def _analyze_suspicion_tendency(self, player) -> float:
        """分析怀疑倾向"""
        if not hasattr(player, 'message_history'):
            return 0.5
            
        suspicious_keywords = ['怀疑', '可疑', '奇怪', '问题', '不对']
        total_messages = len(player.message_history)
        
        if total_messages == 0:
            return 0.5
            
        suspicious_messages = 0
        for message in player.message_history:
            content = message.get('content', '').lower()
            if any(keyword in content for keyword in suspicious_keywords):
                suspicious_messages += 1
                
        return suspicious_messages / total_messages
        
    def _analyze_defensive_frequency(self, player) -> float:
        """分析防御频率"""
        if not hasattr(player, 'message_history'):
            return 0.5
            
        defensive_keywords = ['不是', '没有', '误会', '解释', '澄清']
        total_messages = len(player.message_history)
        
        if total_messages == 0:
            return 0.5
            
        defensive_messages = 0
        for message in player.message_history:
            content = message.get('content', '').lower()
            if any(keyword in content for keyword in defensive_keywords):
                defensive_messages += 1
                
        return defensive_messages / total_messages
        
    def _analyze_voting_pattern(self, player, game_state) -> float:
        """分析投票模式"""
        if not hasattr(player, 'vote_history') or not player.vote_history:
            return 0.5
            
        # 分析投票是否跟随大众
        following_majority = 0
        total_votes = len(player.vote_history)
        
        for vote in player.vote_history:
            # 检查是否投票给了最终被淘汰的玩家
            if vote.get('target') in [p.player_id for p in game_state.eliminated_players]:
                following_majority += 1
                
        return following_majority / total_votes if total_votes > 0 else 0.5
        
    def calculate_overall_suspicion(self, behavior_pattern: BehaviorPattern, player_role: str = None) -> float:
        """计算总体可疑度"""
        suspicion_score = 0.0
        
        # 根据行为模式计算可疑度
        # 极端的风险偏好可能表示卧底
        risk_suspicion = abs(behavior_pattern.risk_preference - 0.5) * 2
        suspicion_score += risk_suspicion * self.suspicion_weights['risk_preference']
        
        # 低投资一致性可能表示卧底
        consistency_suspicion = 1 - behavior_pattern.investment_consistency
        suspicion_score += consistency_suspicion * self.suspicion_weights['investment_consistency']
        
        # 极低或极高的社交活跃度都可疑
        social_suspicion = abs(behavior_pattern.social_activity - 0.5) * 2
        suspicion_score += social_suspicion * self.suspicion_weights['social_activity']
        
        # 高怀疑倾向可能是平民，低怀疑倾向可能是卧底
        suspicion_tendency_suspicion = 1 - behavior_pattern.suspicion_tendency
        suspicion_score += suspicion_tendency_suspicion * self.suspicion_weights['suspicion_tendency']
        
        # 高防御频率可疑
        defensive_suspicion = behavior_pattern.defensive_frequency
        suspicion_score += defensive_suspicion * self.suspicion_weights['defensive_frequency']
        
        # 不跟随大众投票可疑
        voting_suspicion = 1 - behavior_pattern.voting_pattern
        suspicion_score += voting_suspicion * self.suspicion_weights['voting_pattern']
        
        return min(1.0, max(0.0, suspicion_score))
        
    def get_most_suspicious_player(self, game_state) -> Optional[str]:
        """获取最可疑的玩家"""
        max_suspicion = 0
        most_suspicious = None
        
        for player in game_state.get_alive_players():
            behavior = self.analyze_player_behavior(player, game_state)
            suspicion = self.calculate_overall_suspicion(behavior)
            
            if suspicion > max_suspicion:
                max_suspicion = suspicion
                most_suspicious = player.player_id
                
        return most_suspicious
        
    def update_suspicion_scores(self, game_state):
        """更新所有玩家的怀疑得分"""
        for player in game_state.get_alive_players():
            behavior = self.analyze_player_behavior(player, game_state)
            suspicion = self.calculate_overall_suspicion(behavior)
            player.suspicion_level = suspicion * 100  # 转换为0-100分
            
    def analyze_suspicion(self, player, game_state) -> float:
        """分析单个玩家的可疑度"""
        behavior = self.analyze_player_behavior(player, game_state)
        return self.calculate_overall_suspicion(behavior)