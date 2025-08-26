# -*- coding: utf-8 -*-
"""
卡牌系统模块 - 定义卡牌类型和效果
"""

import random
import uuid
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime

class CardType(Enum):
    """卡牌类型"""
    MARKET_NEWS = "market_news"          # 市场新闻
    EVENT_CRISIS = "event_crisis"        # 事件危机
    ROLE_INTERACTION = "role_interaction" # 角色互动
    UNDERCOVER_SPECIAL = "undercover_special" # 卧底专属
    FAMILY_SPLIT = "family_split"        # 家族撕裂
    CONSPIRACY_TRAP = "conspiracy_trap"  # 阴谋陷阱
    PUBLIC_OPINION = "public_opinion"    # 舆论风暴

class CardRarity(Enum):
    """卡牌稀有度"""
    COMMON = "common"      # 普通
    RARE = "rare"          # 稀有
    EPIC = "epic"          # 史诗
    LEGENDARY = "legendary" # 传说

class Card:
    """卡牌类"""
    
    def __init__(self, card_id: str, name: str, card_type: CardType, 
                 rarity: CardRarity, description: str, effect_func: Callable = None):
        self.card_id = card_id
        self.name = name
        self.card_type = card_type
        self.rarity = rarity
        self.description = description
        self.effect_func = effect_func
        self.created_at = datetime.now()
    
    def can_use(self, game_state, player, target_player=None) -> bool:
        """检查是否可以使用卡牌"""
        if not player.is_alive:
            return False
        
        # 卧底专属卡牌只能卧底使用
        if self.card_type == CardType.UNDERCOVER_SPECIAL and player.role != 'undercover':
            return False
        
        # 需要目标的卡牌检查目标是否有效
        if self.card_type in [CardType.ROLE_INTERACTION, CardType.CONSPIRACY_TRAP]:
            if not target_player or not target_player.is_alive or target_player.player_id == player.player_id:
                return False
        
        return True
    
    def use(self, game_state, player, target_player=None) -> Dict:
        """使用卡牌"""
        if not self.can_use(game_state, player, target_player):
            return {'success': False, 'message': '无法使用此卡牌'}
        
        if self.effect_func:
            return self.effect_func(game_state, player, target_player, self)
        
        return {'success': False, 'message': '卡牌效果未定义'}
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'card_id': self.card_id,
            'name': self.name,
            'type': self.card_type.value,
            'rarity': self.rarity.value,
            'description': self.description
        }

class CardSystem:
    """卡牌系统管理类"""
    
    def __init__(self):
        self.card_templates = []
        self._initialize_cards()
    
    def _initialize_cards(self):
        """初始化卡牌模板"""
        # 市场新闻卡
        self.card_templates.extend([
            {
                'name': '利好消息',
                'type': CardType.MARKET_NEWS,
                'rarity': CardRarity.COMMON,
                'description': '选择一只股票，其价格上涨10%',
                'effect': self._effect_good_news
            },
            {
                'name': '市场崩盘',
                'type': CardType.MARKET_NEWS,
                'rarity': CardRarity.RARE,
                'description': '所有股票价格下跌15%',
                'effect': self._effect_market_crash
            },
            {
                'name': '内幕消息',
                'type': CardType.MARKET_NEWS,
                'rarity': CardRarity.EPIC,
                'description': '查看下一轮的股票价格变化',
                'effect': self._effect_insider_info
            }
        ])
        
        # 事件危机卡
        self.card_templates.extend([
            {
                'name': '资金冻结',
                'type': CardType.EVENT_CRISIS,
                'rarity': CardRarity.COMMON,
                'description': '目标玩家下一轮无法投资',
                'effect': self._effect_freeze_funds
            },
            {
                'name': '审计风暴',
                'type': CardType.EVENT_CRISIS,
                'rarity': CardRarity.RARE,
                'description': '所有玩家的投资记录公开',
                'effect': self._effect_audit_storm
            }
        ])
        
        # 角色互动卡
        self.card_templates.extend([
            {
                'name': '信任建立',
                'type': CardType.ROLE_INTERACTION,
                'rarity': CardRarity.COMMON,
                'description': '增加目标玩家对你的信任度',
                'effect': self._effect_build_trust
            },
            {
                'name': '散布谣言',
                'type': CardType.ROLE_INTERACTION,
                'rarity': CardRarity.COMMON,
                'description': '增加目标玩家的怀疑度',
                'effect': self._effect_spread_rumor
            }
        ])
        
        # 卧底专属卡
        self.card_templates.extend([
            {
                'name': '伪装身份',
                'type': CardType.UNDERCOVER_SPECIAL,
                'rarity': CardRarity.RARE,
                'description': '降低自己的怀疑度',
                'effect': self._effect_disguise
            },
            {
                'name': '栽赃陷害',
                'type': CardType.UNDERCOVER_SPECIAL,
                'rarity': CardRarity.EPIC,
                'description': '大幅增加目标玩家的怀疑度',
                'effect': self._effect_frame_up
            }
        ])
        
        # 家族撕裂卡
        self.card_templates.extend([
            {
                'name': '利益冲突',
                'type': CardType.FAMILY_SPLIT,
                'rarity': CardRarity.RARE,
                'description': '两名玩家互相增加怀疑度',
                'effect': self._effect_conflict
            }
        ])
        
        # 阴谋陷阱卡
        self.card_templates.extend([
            {
                'name': '投票操控',
                'type': CardType.CONSPIRACY_TRAP,
                'rarity': CardRarity.EPIC,
                'description': '强制目标玩家投票给指定对象',
                'effect': self._effect_vote_control
            }
        ])
        
        # 舆论风暴卡
        self.card_templates.extend([
            {
                'name': '媒体曝光',
                'type': CardType.PUBLIC_OPINION,
                'rarity': CardRarity.LEGENDARY,
                'description': '公开一名玩家的角色信息',
                'effect': self._effect_media_exposure
            }
        ])
    
    def create_card(self, template: Dict) -> Card:
        """根据模板创建卡牌"""
        card_id = str(uuid.uuid4())[:8]
        return Card(
            card_id=card_id,
            name=template['name'],
            card_type=template['type'],
            rarity=template['rarity'],
            description=template['description'],
            effect_func=template['effect']
        )
    
    def draw_cards(self, count: int = 1) -> List[Card]:
        """抽取卡牌"""
        cards = []
        for _ in range(count):
            # 根据稀有度权重随机选择
            weights = {
                CardRarity.COMMON: 50,
                CardRarity.RARE: 30,
                CardRarity.EPIC: 15,
                CardRarity.LEGENDARY: 5
            }
            
            # 按稀有度分组模板
            rarity_groups = {}
            for template in self.card_templates:
                rarity = template['rarity']
                if rarity not in rarity_groups:
                    rarity_groups[rarity] = []
                rarity_groups[rarity].append(template)
            
            # 随机选择稀有度
            rarities = list(weights.keys())
            rarity_weights = list(weights.values())
            selected_rarity = random.choices(rarities, weights=rarity_weights)[0]
            
            # 从选中稀有度中随机选择模板
            if selected_rarity in rarity_groups:
                template = random.choice(rarity_groups[selected_rarity])
                cards.append(self.create_card(template))
        
        return cards
    
    # 卡牌效果函数
    def _effect_good_news(self, game_state, player, target_player, card):
        """利好消息效果"""
        # 这里需要股市系统配合
        return {
            'success': True,
            'message': f'{player.name} 使用了 {card.name}，某只股票价格上涨！'
        }
    
    def _effect_market_crash(self, game_state, player, target_player, card):
        """市场崩盘效果"""
        return {
            'success': True,
            'message': f'{player.name} 使用了 {card.name}，市场崩盘！所有股票下跌！'
        }
    
    def _effect_insider_info(self, game_state, player, target_player, card):
        """内幕消息效果"""
        return {
            'success': True,
            'message': f'{player.name} 使用了 {card.name}，获得了内幕消息！'
        }
    
    def _effect_freeze_funds(self, game_state, player, target_player, card):
        """资金冻结效果"""
        if target_player:
            # 添加冻结状态（需要在游戏状态中实现）
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}！'
            }
        return {'success': False, 'message': '需要选择目标玩家'}
    
    def _effect_audit_storm(self, game_state, player, target_player, card):
        """审计风暴效果"""
        return {
            'success': True,
            'message': f'{player.name} 使用了 {card.name}，所有投资记录公开！'
        }
    
    def _effect_build_trust(self, game_state, player, target_player, card):
        """建立信任效果"""
        if target_player:
            target_player.update_trust(20)
            player.update_trust(10)
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}，增加了信任度！'
            }
        return {'success': False, 'message': '需要选择目标玩家'}
    
    def _effect_spread_rumor(self, game_state, player, target_player, card):
        """散布谣言效果"""
        if target_player:
            target_player.update_suspicion(15)
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}，散布了谣言！'
            }
        return {'success': False, 'message': '需要选择目标玩家'}
    
    def _effect_disguise(self, game_state, player, target_player, card):
        """伪装身份效果"""
        player.update_suspicion(-25)
        return {
            'success': True,
            'message': f'{player.name} 使用了 {card.name}，降低了怀疑度！'
        }
    
    def _effect_frame_up(self, game_state, player, target_player, card):
        """栽赃陷害效果"""
        if target_player:
            target_player.update_suspicion(30)
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}，进行了栽赃陷害！'
            }
        return {'success': False, 'message': '需要选择目标玩家'}
    
    def _effect_conflict(self, game_state, player, target_player, card):
        """利益冲突效果"""
        # 随机选择两名其他玩家
        alive_players = [p for p in game_state.get_alive_players() if p.player_id != player.player_id]
        if len(alive_players) >= 2:
            targets = random.sample(alive_players, 2)
            targets[0].update_suspicion(10)
            targets[1].update_suspicion(10)
            return {
                'success': True,
                'message': f'{player.name} 使用了 {card.name}，{targets[0].name} 和 {targets[1].name} 产生了利益冲突！'
            }
        return {'success': False, 'message': '存活玩家不足'}
    
    def _effect_vote_control(self, game_state, player, target_player, card):
        """投票操控效果"""
        if target_player:
            # 需要在游戏状态中实现投票控制
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}，操控了投票！'
            }
        return {'success': False, 'message': '需要选择目标玩家'}
    
    def _effect_media_exposure(self, game_state, player, target_player, card):
        """媒体曝光效果"""
        if target_player:
            return {
                'success': True,
                'message': f'{player.name} 对 {target_player.name} 使用了 {card.name}，曝光了其角色：{target_player.role}！',
                'revealed_role': target_player.role
            }
        return {'success': False, 'message': '需要选择目标玩家'}