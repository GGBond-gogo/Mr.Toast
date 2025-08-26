# -*- coding: utf-8 -*-
"""
游戏状态模块 - 管理游戏的整体状态
"""

import random
from typing import Dict, List, Optional
from datetime import datetime

# 修改这一行：移除相对导入，改为在需要时导入
# from .player import Player  # 删除这行

class GameState:
    """游戏状态类"""
    
    def __init__(self, game_id: str, max_players: int = 6):
        self.game_id = game_id
        self.max_players = max_players
        self.players: Dict[str, 'Player'] = {}  # 使用字符串类型注解
        self.phase = 'waiting'  # waiting, investment, discussion, voting, ended
        self.round_number = 0
        self.phase_start_time = datetime.now()
        self.phase_duration = 60  # 秒
        self.votes = {}  # {voter_id: target_id}
        self.eliminated_players = []
        self.winner = None
        self.market_events = []
        self.messages = []
        self.created_at = datetime.now()
        
    def add_player(self, player) -> bool:  # 移除类型注解中的 Player
        """添加玩家"""
        if len(self.players) >= self.max_players:
            return False
        
        if self.phase != 'waiting':
            return False
        
        self.players[player.player_id] = player
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """移除玩家"""
        if player_id in self.players:
            del self.players[player_id]
            return True
        return False
    
    def get_player(self, player_id: str):
        """获取玩家"""
        return self.players.get(player_id)
    
    def get_alive_players(self):  # 移除 -> List[Player]
        """获取存活玩家"""
        return [player for player in self.players.values() if player.is_alive]
    
    def get_undercover_players(self):  # 移除 -> List[Player]
        """获取卧底玩家"""
        return [player for player in self.players.values() 
                if player.role == 'undercover' and player.is_alive]
    
    def get_civilian_players(self):  # 移除 -> List[Player]
        """获取平民玩家"""
        return [player for player in self.players.values() 
                if player.role == 'civilian' and player.is_alive]
    
    def can_start_game(self) -> bool:
        """检查是否可以开始游戏"""
        return len(self.players) >= 3 and self.phase == 'waiting'
    
    def assign_roles(self):
        """分配角色"""
        player_list = list(self.players.values())
        random.shuffle(player_list)
        
        # 计算卧底数量 (约1/3的玩家)
        undercover_count = max(1, len(player_list) // 3)
        
        # 分配卧底角色
        for i in range(undercover_count):
            player_list[i].role = 'undercover'
        
        # 其余为平民
        for i in range(undercover_count, len(player_list)):
            player_list[i].role = 'civilian'
    
    def start_game(self) -> bool:
        """开始游戏"""
        if not self.can_start_game():
            return False
        
        self.assign_roles()
        self.phase = 'investment'
        self.round_number = 1
        self.phase_start_time = datetime.now()
        return True
    
    def advance_phase(self) -> str:
        """推进游戏阶段"""
        if self.phase == 'investment':
            self.phase = 'discussion'
        elif self.phase == 'discussion':
            self.phase = 'voting'
        elif self.phase == 'voting':
            # 处理投票结果
            self._process_votes()
            
            # 检查游戏是否结束
            if self.check_game_end():
                self.phase = 'ended'
            else:
                self.round_number += 1
                self.phase = 'investment'
                self.votes.clear()
        
        self.phase_start_time = datetime.now()
        return self.phase
    
    def _process_votes(self):
        """处理投票结果"""
        if not self.votes:
            return
        
        # 统计票数
        vote_counts = {}
        for target_id in self.votes.values():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        # 找出得票最多的玩家
        max_votes = max(vote_counts.values())
        candidates = [player_id for player_id, votes in vote_counts.items() 
                     if votes == max_votes]
        
        # 如果有平票，随机选择一个
        if candidates:
            eliminated_id = random.choice(candidates)
            if eliminated_id in self.players:
                self.players[eliminated_id].is_alive = False
                self.eliminated_players.append(eliminated_id)
    
    def add_vote(self, voter_id: str, target_id: str) -> bool:
        """添加投票"""
        if self.phase != 'voting':
            return False
        
        if voter_id not in self.players or target_id not in self.players:
            return False
        
        if not self.players[voter_id].is_alive or not self.players[target_id].is_alive:
            return False
        
        self.votes[voter_id] = target_id
        self.players[voter_id].add_vote(target_id, self.round_number)
        return True
    
    def check_game_end(self) -> bool:
        """检查游戏是否结束"""
        undercover_alive = len(self.get_undercover_players())
        civilian_alive = len(self.get_civilian_players())
        
        if undercover_alive == 0:
            self.winner = 'civilian'
            return True
        elif undercover_alive >= civilian_alive:
            self.winner = 'undercover'
            return True
        
        return False
    
    def get_winner(self) -> Optional[str]:
        """获取胜者"""
        return self.winner
    
    def add_market_event(self, event: Dict):
        """添加市场事件"""
        event['timestamp'] = datetime.now()
        self.market_events.append(event)
    
    def add_message(self, player_id: str, message: str, message_type: str = 'player'):
        """添加消息"""
        msg = {
            'player_id': player_id,
            'message': message,
            'type': message_type,
            'timestamp': datetime.now()
        }
        self.messages.append(msg)
        
        if player_id in self.players:
            self.players[player_id].add_message(message)
    
    def get_phase_time_remaining(self) -> int:
        """获取当前阶段剩余时间"""
        elapsed = (datetime.now() - self.phase_start_time).total_seconds()
        return max(0, int(self.phase_duration - elapsed))
    
    def to_dict(self, player_id: str = None) -> Dict:
        """转换为字典格式"""
        data = {
            'game_id': self.game_id,
            'max_players': self.max_players,
            'phase': self.phase,
            'round_number': self.round_number,
            'phase_time_remaining': self.get_phase_time_remaining(),
            'players': {pid: player.to_dict(include_private=(pid == player_id)) 
                       for pid, player in self.players.items()},
            'eliminated_players': self.eliminated_players,
            'winner': self.winner,
            'market_events': self.market_events[-10:],  # 最近10个事件
            'messages': self.messages[-50:],  # 最近50条消息
            'vote_counts': self._get_vote_counts() if self.phase == 'voting' else {},
            'alive_count': len(self.get_alive_players()),
            'undercover_count': len(self.get_undercover_players()),
            'civilian_count': len(self.get_civilian_players())
        }
        
        return data
    
    def _get_vote_counts(self) -> Dict:
        """获取投票统计"""
        vote_counts = {}
        for target_id in self.votes.values():
            if target_id in vote_counts:
                vote_counts[target_id] += 1
            else:
                vote_counts[target_id] = 1
        return vote_counts
    
    def __str__(self):
        return f"Game({self.game_id}, {self.phase}, Round {self.round_number})"