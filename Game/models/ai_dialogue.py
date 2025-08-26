# -*- coding: utf-8 -*-
"""
AI对话系统模块 - 生成AI角色的对话内容
"""

import random
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

class EmotionType(Enum):
    """情感类型"""
    CONFIDENT = "confident"      # 自信
    NERVOUS = "nervous"          # 紧张
    SUSPICIOUS = "suspicious"    # 怀疑
    FRIENDLY = "friendly"        # 友好
    AGGRESSIVE = "aggressive"    # 激进
    DEFENSIVE = "defensive"      # 防御
    ANALYTICAL = "analytical"    # 分析

class DialogueContext:
    """对话上下文"""
    
    def __init__(self, phase: str, recent_events: List[str], player_status: Dict):
        self.phase = phase
        self.recent_events = recent_events
        self.player_status = player_status
        self.timestamp = datetime.now()

class DialogueTemplate:
    """对话模板"""
    
    def __init__(self, emotion: EmotionType, templates: List[str], conditions: Dict = None):
        self.emotion = emotion
        self.templates = templates
        self.conditions = conditions or {}
        
    def can_use(self, context: DialogueContext, player) -> bool:
        """检查是否可以使用此模板"""
        for condition, value in self.conditions.items():
            if condition == 'role' and player.role != value:
                return False
            if condition == 'phase' and context.phase != value:
                return False
            if condition == 'suspicion_min' and player.suspicion_level < value:
                return False
            if condition == 'suspicion_max' and player.suspicion_level > value:
                return False
        return True

class AIDialogueSystem:
    """AI对话系统"""
    
    def __init__(self, personality):
        self.personality = personality
        self.dialogue_templates = []
        self.recent_messages = []
        self._initialize_templates()
        
    def _initialize_templates(self):
        """初始化对话模板"""
        # 投资阶段对话
        self.dialogue_templates.extend([
            DialogueTemplate(EmotionType.CONFIDENT, [
                "我看好{stock}的前景，这是个不错的投资机会。",
                "根据我的分析，{stock}应该会有不错的表现。",
                "市场趋势很明显，{stock}是明智的选择。"
            ], {'phase': 'investment'}),
            
            DialogueTemplate(EmotionType.NERVOUS, [
                "这个市场变化太快了，我有点不确定...",
                "大家觉得现在投资{stock}怎么样？",
                "我担心市场会有大的波动。"
            ], {'phase': 'investment'}),
            
            DialogueTemplate(EmotionType.ANALYTICAL, [
                "从技术指标来看，{stock}的走势符合预期。",
                "我分析了最近的市场数据，{stock}有上涨潜力。",
                "根据历史数据，这个时候投资{stock}风险较低。"
            ], {'phase': 'investment'})
        ])
        
        # 讨论阶段对话
        self.dialogue_templates.extend([
            DialogueTemplate(EmotionType.SUSPICIOUS, [
                "{player}的投资策略很奇怪，为什么要这样做？",
                "我觉得{player}的行为有些可疑...",
                "{player}，你能解释一下你的投资逻辑吗？"
            ], {'phase': 'discussion'}),
            
            DialogueTemplate(EmotionType.DEFENSIVE, [
                "我的投资策略是基于充分分析的，没什么问题。",
                "大家不要怀疑我，我只是运气不好而已。",
                "我的每一步都有合理的理由。"
            ], {'phase': 'discussion', 'suspicion_min': 30}),
            
            DialogueTemplate(EmotionType.FRIENDLY, [
                "大家合作才能赢得游戏，不要互相怀疑。",
                "{player}的分析很有道理，我支持。",
                "我们应该团结一致，找出真正的卧底。"
            ], {'phase': 'discussion'})
        ])
        
        # 投票阶段对话
        self.dialogue_templates.extend([
            DialogueTemplate(EmotionType.CONFIDENT, [
                "我认为{player}就是卧底，大家跟我投票。",
                "证据很明显，{player}的行为最可疑。",
                "我们必须投出{player}，否则就输了。"
            ], {'phase': 'voting'}),
            
            DialogueTemplate(EmotionType.NERVOUS, [
                "我真的不知道该投谁...",
                "这个决定太难了，大家怎么看？",
                "我担心投错人..."
            ], {'phase': 'voting'})
        ])
        
        # 卧底专属对话
        self.dialogue_templates.extend([
            DialogueTemplate(EmotionType.AGGRESSIVE, [
                "你们的分析都是错的，我才是对的。",
                "市场就是这样，你们不懂。",
                "我的策略比你们都要好。"
            ], {'role': 'undercover'}),
            
            DialogueTemplate(EmotionType.DEFENSIVE, [
                "我只是投资风格不同，这不能说明什么。",
                "每个人都有自己的投资理念。",
                "你们这样怀疑我是不对的。"
            ], {'role': 'undercover', 'suspicion_min': 40})
        ])
        
        # 平民专属对话
        self.dialogue_templates.extend([
            DialogueTemplate(EmotionType.ANALYTICAL, [
                "让我们冷静分析一下每个人的行为。",
                "从投资记录来看，{player}确实有问题。",
                "我们需要更多证据来判断。"
            ], {'role': 'civilian'}),
            
            DialogueTemplate(EmotionType.FRIENDLY, [
                "我相信{player}不是卧底。",
                "我们要相信彼此，团结合作。",
                "大家都是为了赢得游戏。"
            ], {'role': 'civilian'})
        ])
        
    def generate_message(self, game_state, player, context: str = "") -> str:
        """生成AI消息"""
        # 创建对话上下文
        dialogue_context = DialogueContext(
            phase=game_state.current_phase,
            recent_events=game_state.recent_events[-5:] if hasattr(game_state, 'recent_events') else [],
            player_status={
                'money': player.money,
                'suspicion': player.suspicion_level,
                'trust': player.trust_level
            }
        )
        
        # 选择合适的情感状态
        emotion = self._determine_emotion(player, dialogue_context)
        
        # 筛选可用模板
        available_templates = [
            template for template in self.dialogue_templates
            if template.emotion == emotion and template.can_use(dialogue_context, player)
        ]
        
        if not available_templates:
            # 如果没有合适的模板，使用通用模板
            available_templates = [
                template for template in self.dialogue_templates
                if template.can_use(dialogue_context, player)
            ]
            
        if not available_templates:
            return self._generate_generic_message(player, dialogue_context)
            
        # 随机选择模板
        template = random.choice(available_templates)
        message_template = random.choice(template.templates)
        
        # 填充模板变量
        return self._fill_template(message_template, player, game_state)
        
    def _determine_emotion(self, player, context: DialogueContext) -> EmotionType:
        """确定AI当前情感状态"""
        # 根据性格特征和游戏状态确定情感
        aggressive = self.personality.get_trait('aggressive')
        social = self.personality.get_trait('social')
        suspicious = self.personality.get_trait('suspicious')
        
        # 根据怀疑度调整情感
        if player.suspicion_level > 60:
            return EmotionType.DEFENSIVE if random.random() < 0.7 else EmotionType.AGGRESSIVE
        elif player.suspicion_level > 30:
            return EmotionType.NERVOUS if random.random() < 0.6 else EmotionType.SUSPICIOUS
        
        # 根据性格特征选择情感
        if aggressive > 0.7:
            return EmotionType.AGGRESSIVE if random.random() < 0.6 else EmotionType.CONFIDENT
        elif social > 0.7:
            return EmotionType.FRIENDLY if random.random() < 0.7 else EmotionType.ANALYTICAL
        elif suspicious > 0.7:
            return EmotionType.SUSPICIOUS if random.random() < 0.8 else EmotionType.ANALYTICAL
        else:
            return random.choice([EmotionType.CONFIDENT, EmotionType.ANALYTICAL, EmotionType.FRIENDLY])
            
    def _fill_template(self, template: str, player, game_state) -> str:
        """填充模板变量"""
        # 获取其他玩家
        other_players = [p for p in game_state.get_alive_players() if p.player_id != player.player_id]
        
        # 替换变量
        if '{player}' in template and other_players:
            target_player = random.choice(other_players)
            template = template.replace('{player}', target_player.name)
            
        if '{stock}' in template:
            # 获取股票信息
            stocks = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN']  # 示例股票
            stock = random.choice(stocks)
            template = template.replace('{stock}', stock)
            
        return template
        
    def _generate_generic_message(self, player, context: DialogueContext) -> str:
        """生成通用消息"""
        generic_messages = [
            "让我想想下一步该怎么做...",
            "这个游戏真的很有挑战性。",
            "大家都很厉害啊。",
            "我需要更仔细地观察。",
            "希望我的判断是对的。"
        ]
        return random.choice(generic_messages)
        
    def add_recent_message(self, message: str):
        """添加最近消息"""
        self.recent_messages.append({
            'message': message,
            'timestamp': datetime.now()
        })
        
        # 限制消息历史长度
        if len(self.recent_messages) > 20:
            self.recent_messages = self.recent_messages[-20:]