# -*- coding: utf-8 -*-
"""
游戏引擎模块 - 游戏核心逻辑控制
"""

import random
from typing import Dict, List, Optional
from datetime import datetime

# 修改这些导入语句，移除相对导入
# from .game_state import GameState
# from .player import Player  
# from .ai_system import AISystem
# from .card_system import CardSystem
# from .stock_market import StockMarket

# 改为绝对导入或在运行时动态导入
class GameEngine:
    """游戏引擎"""
    
    def __init__(self, game_id: str, max_players: int = 6):
        self.game_id = game_id
        self.game_state = GameState(game_id, max_players)
        self.ai_system = AISystem()
        self.card_system = CardSystem()
        self.stock_market = StockMarket()
        self.phase_duration = {
            'investment': 120,  # 2分钟
            'discussion': 180,  # 3分钟
            'voting': 60       # 1分钟
        }
        
    def add_player(self, player_name: str, is_ai: bool = False) -> Optional[Player]:
        """添加玩家"""
        if self.game_state.can_add_player():
            if is_ai:
                player = self.ai_system.create_ai_player(
                    f"ai_{len(self.game_state.players)}",
                    player_name
                )
            else:
                player = Player(f"player_{len(self.game_state.players)}", player_name)
                
            self.game_state.add_player(player)
            return player
        return None
        
    def start_game(self) -> bool:
        """开始游戏"""
        if self.game_state.can_start_game():
            # 分配角色
            self.game_state.assign_roles()
            
            # 给每个玩家发卡牌
            for player in self.game_state.players:
                cards = self.card_system.draw_cards(3)  # 每人3张卡
                for card in cards:
                    player.add_card(card)
                    
            # 开始游戏
            self.game_state.start_game()
            
            # 开始第一轮
            self._start_investment_phase()
            return True
        return False
        
    def _start_investment_phase(self):
        """开始投资阶段"""
        self.game_state.advance_phase('investment', self.phase_duration['investment'])
        
        # AI自动投资
        self._process_ai_investments()
        
    def _start_discussion_phase(self):
        """开始讨论阶段"""
        self.game_state.advance_phase('discussion', self.phase_duration['discussion'])
        
        # AI自动发言
        self._process_ai_discussions()
        
    def _start_voting_phase(self):
        """开始投票阶段"""
        self.game_state.advance_phase('voting', self.phase_duration['voting'])
        
        # AI自动投票
        self._process_ai_votes()
        
    def _process_ai_investments(self):
        """处理AI投资"""
        for player in self.game_state.get_alive_players():
            if player.is_ai:
                ai_player = self.ai_system.get_ai_player(player.player_id)
                if ai_player:
                    investment = ai_player.make_investment_decision(self.game_state, self.stock_market)
                    if investment:
                        self.process_investment(player.player_id, investment)
                        
    def _process_ai_discussions(self):
        """处理AI讨论"""
        for player in self.game_state.get_alive_players():
            if player.is_ai and random.random() < 0.7:  # 70%概率发言
                ai_player = self.ai_system.get_ai_player(player.player_id)
                if ai_player:
                    message = ai_player.generate_message(self.game_state)
                    if message:
                        self.add_message(player.player_id, message)
                        
    def _process_ai_votes(self):
        """处理AI投票"""
        for player in self.game_state.get_alive_players():
            if player.is_ai:
                ai_player = self.ai_system.get_ai_player(player.player_id)
                if ai_player:
                    vote_target = ai_player.make_vote_decision(self.game_state)
                    if vote_target:
                        self.process_vote(player.player_id, vote_target)
                        
    def process_investment(self, player_id: str, investment_data: Dict) -> Dict:
        """处理投资"""
        player = self.game_state.get_player(player_id)
        if not player or not player.is_alive:
            return {'success': False, 'message': '玩家不存在或已被淘汰'}
            
        if self.game_state.current_phase != 'investment':
            return {'success': False, 'message': '当前不是投资阶段'}
            
        stock_symbol = investment_data.get('stock_symbol')
        amount = investment_data.get('amount', 0)
        action = investment_data.get('action', 'buy')
        
        if action == 'buy':
            result = self.stock_market.buy_stock(player, stock_symbol, amount)
        else:
            result = self.stock_market.sell_stock(player, stock_symbol, amount)
            
        if result['success']:
            # 记录投资历史
            player.add_investment_record({
                'action': action,
                'stock': stock_symbol,
                'amount': amount,
                'price': result.get('price', 0),
                'timestamp': datetime.now()
            })
            
        return result
        
    def process_card_use(self, player_id: str, card_data: Dict) -> Dict:
        """处理卡牌使用"""
        player = self.game_state.get_player(player_id)
        if not player or not player.is_alive:
            return {'success': False, 'message': '玩家不存在或已被淘汰'}
            
        card_id = card_data.get('card_id')
        target_player_id = card_data.get('target_player_id')
        
        # 找到卡牌
        card = None
        for c in player.cards:
            if c.card_id == card_id:
                card = c
                break
                
        if not card:
            return {'success': False, 'message': '卡牌不存在'}
            
        # 获取目标玩家
        target_player = None
        if target_player_id:
            target_player = self.game_state.get_player(target_player_id)
            
        # 使用卡牌
        result = card.use(self.game_state, player, target_player)
        
        if result['success']:
            # 移除已使用的卡牌
            player.remove_card(card)
            
            # 添加游戏事件
            self.game_state.add_message({
                'type': 'card_use',
                'player': player.name,
                'card': card.name,
                'message': result['message'],
                'timestamp': datetime.now()
            })
            
        return result
        
    def process_vote(self, voter_id: str, target_id: str) -> Dict:
        """处理投票"""
        if self.game_state.current_phase != 'voting':
            return {'success': False, 'message': '当前不是投票阶段'}
            
        voter = self.game_state.get_player(voter_id)
        target = self.game_state.get_player(target_id)
        
        if not voter or not voter.is_alive:
            return {'success': False, 'message': '投票者不存在或已被淘汰'}
            
        if not target or not target.is_alive:
            return {'success': False, 'message': '投票目标不存在或已被淘汰'}
            
        if voter_id == target_id:
            return {'success': False, 'message': '不能投票给自己'}
            
        # 添加投票
        self.game_state.add_vote(voter_id, target_id)
        
        # 记录投票历史
        voter.add_vote_record({
            'target': target_id,
            'round': self.game_state.round_number,
            'timestamp': datetime.now()
        })
        
        return {'success': True, 'message': f'{voter.name} 投票给了 {target.name}'}
        
    def add_message(self, player_id: str, message: str) -> Dict:
        """添加消息"""
        player = self.game_state.get_player(player_id)
        if not player or not player.is_alive:
            return {'success': False, 'message': '玩家不存在或已被淘汰'}
            
        # 添加消息到游戏状态
        self.game_state.add_message({
            'type': 'chat',
            'player_id': player_id,
            'player_name': player.name,
            'message': message,
            'timestamp': datetime.now()
        })
        
        # 记录到玩家消息历史
        player.add_message_record({
            'content': message,
            'timestamp': datetime.now()
        })
        
        return {'success': True}
        
    def advance_to_next_phase(self) -> Dict:
        """推进到下一阶段"""
        current_phase = self.game_state.current_phase
        
        if current_phase == 'investment':
            # 更新股票价格
            self.stock_market.update_all_prices()
            
            # 进入讨论阶段
            self._start_discussion_phase()
            
        elif current_phase == 'discussion':
            # 进入投票阶段
            self._start_voting_phase()
            
        elif current_phase == 'voting':
            # 处理投票结果
            eliminated_player = self.game_state.process_vote_results()
            
            # 检查游戏是否结束
            if self.game_state.check_game_end():
                winner = self.game_state.get_winner()
                return {
                    'phase': 'game_end',
                    'winner': winner,
                    'eliminated': eliminated_player.name if eliminated_player else None
                }
            else:
                # 开始新一轮
                self.game_state.round_number += 1
                
                # 给存活玩家发新卡牌
                for player in self.game_state.get_alive_players():
                    new_cards = self.card_system.draw_cards(1)
                    for card in new_cards:
                        player.add_card(card)
                        
                # 开始新的投资阶段
                self._start_investment_phase()
                
                return {
                    'phase': 'investment',
                    'round': self.game_state.round_number,
                    'eliminated': eliminated_player.name if eliminated_player else None
                }
                
        return {'phase': self.game_state.current_phase}
        
    def get_game_status(self) -> Dict:
        """获取游戏状态"""
        return {
            'game_id': self.game_id,
            'phase': self.game_state.current_phase,
            'round': self.game_state.round_number,
            'players': [{
                'id': p.player_id,
                'name': p.name,
                'is_alive': p.is_alive,
                'is_ai': p.is_ai,
                'money': p.money,
                'stocks': p.stocks,
                'cards_count': len(p.cards),
                'suspicion_level': p.suspicion_level,
                'trust_level': p.trust_level
            } for p in self.game_state.players],
            'stock_market': self.stock_market.get_market_status(),
            'messages': self.game_state.messages[-20:],  # 最近20条消息
            'votes': self.game_state.votes,
            'time_remaining': self.game_state.get_phase_time_remaining(),
            'eliminated_players': [p.name for p in self.game_state.eliminated_players]
        }