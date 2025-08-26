# -*- coding: utf-8 -*-
"""
简化版股市卧底游戏启动文件
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import json
import uuid
import time
from threading import Timer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock_undercover_game_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储所有游戏房间
games = {}

# 股票数据
STOCKS = {
    'AAPL': {'name': 'Apple Inc.', 'price': 150.0, 'change': 0},
    'GOOGL': {'name': 'Alphabet Inc.', 'price': 2500.0, 'change': 0},
    'TSLA': {'name': 'Tesla Inc.', 'price': 800.0, 'change': 0},
    'MSFT': {'name': 'Microsoft Corp.', 'price': 300.0, 'change': 0},
    'AMZN': {'name': 'Amazon.com Inc.', 'price': 3200.0, 'change': 0}
}

# 角色配置
ROLES = {
    'investor': {'name': '投资者', 'description': '通过投资获利，找出卧底'},
    'undercover': {'name': '卧底', 'description': '隐藏身份，误导其他玩家'}
}

# AI玩家名字池
AI_NAMES = [
    '智能投资者小王', '股神小李', '分析师小张', '交易员小陈', 
    '基金经理小刘', '证券分析师小赵', '投资顾问小孙', '金融专家小周'
]

class GameEngine:
    def __init__(self, game_id):
        self.game_id = game_id
        self.phase = 'waiting'  # waiting, discussion, voting, result
        self.round = 1
        self.phase_timer = None
        
    def add_ai_players(self, count=4):
        """添加AI玩家"""
        game = games[self.game_id]
        current_count = len(game['players'])
        
        # 确保总玩家数不超过最大限制
        max_ai = min(count, game['max_players'] - current_count)
        
        available_names = [name for name in AI_NAMES if name not in [p['name'] for p in game['players']]]
        
        for i in range(max_ai):
            if available_names:
                ai_name = available_names.pop(0)
                game['players'].append({
                    'name': ai_name,
                    'id': str(uuid.uuid4())[:8],
                    'socket_id': 'AI',
                    'is_host': False,
                    'is_ai': True
                })
        
        return len(game['players'])
        
    def start_game(self, auto_start=False):
        game = games[self.game_id]
        
        # 如果是自动开始且玩家不足，添加AI玩家
        if auto_start and len(game['players']) < 4:
            self.add_ai_players(4 - len(game['players']))
            
        if len(game['players']) < 3:
            return False, '至少需要3名玩家才能开始游戏'
            
        # 分配角色
        self.assign_roles()
        
        # 初始化玩家状态
        for player in game['players']:
            player['money'] = 1000
            player['stocks'] = {}
            player['alive'] = True
            player['votes'] = 0
            
        game['status'] = 'playing'
        self.phase = 'discussion'
        
        # 更新股票价格
        self.update_stock_prices()
        
        # 通知所有玩家游戏开始
        socketio.emit('game_started', {
            'message': '游戏开始！',
            'phase': self.phase,
            'round': self.round,
            'stocks': STOCKS,
            'players': game['players']
        }, room=self.game_id)
        
        # 发送角色信息给每个玩家（只发给真实玩家）
        for player in game['players']:
            if not player.get('is_ai', False):
                socketio.emit('role_assigned', {
                    'role': player['role'],
                    'role_info': ROLES[player['role']]
                }, room=player['socket_id'])
            
        # 开始讨论阶段
        self.start_discussion_phase()
        return True, '游戏开始成功'
        
    def assign_roles(self):
        game = games[self.game_id]
        players = game['players']
        player_count = len(players)
        
        # 计算卧底数量（约1/3）
        undercover_count = max(1, player_count // 3)
        
        # 随机分配角色
        roles = ['undercover'] * undercover_count + ['investor'] * (player_count - undercover_count)
        random.shuffle(roles)
        
        for i, player in enumerate(players):
            player['role'] = roles[i]
            
    def update_stock_prices(self):
        for symbol in STOCKS:
            # 随机价格变动 -5% 到 +5%
            change_percent = random.uniform(-0.05, 0.05)
            old_price = STOCKS[symbol]['price']
            new_price = old_price * (1 + change_percent)
            STOCKS[symbol]['price'] = round(new_price, 2)
            STOCKS[symbol]['change'] = round(((new_price - old_price) / old_price) * 100, 2)
            
    def start_discussion_phase(self):
        self.phase = 'discussion'
        socketio.emit('phase_changed', {
            'phase': 'discussion',
            'message': '讨论阶段开始！分析股票走势，寻找可疑行为',
            'duration': 30  # 缩短为30秒
        }, room=self.game_id)
        
        # AI玩家自动进行股票交易
        self.ai_auto_trade()
        
        # 30秒后进入投票阶段
        self.phase_timer = Timer(30.0, self.start_voting_phase)
        self.phase_timer.start()
        
    def ai_auto_trade(self):
        """AI玩家自动交易"""
        game = games[self.game_id]
        
        for player in game['players']:
            if player.get('is_ai', False) and player['alive']:
                # AI随机选择股票进行交易
                if random.random() < 0.7:  # 70%概率进行交易
                    symbol = random.choice(list(STOCKS.keys()))
                    max_affordable = int(player['money'] // STOCKS[symbol]['price'])
                    
                    if max_affordable > 0:
                        amount = random.randint(1, min(3, max_affordable))
                        cost = STOCKS[symbol]['price'] * amount
                        
                        player['money'] -= cost
                        if 'stocks' not in player:
                            player['stocks'] = {}
                        player['stocks'][symbol] = player['stocks'].get(symbol, 0) + amount
                        
                        # 通知其他玩家AI的交易行为
                        socketio.emit('player_action', {
                            'player': player['name'],
                            'action': f'购买了 {amount} 股 {symbol}',
                            'is_ai': True
                        }, room=self.game_id)
        
    def start_voting_phase(self):
        self.phase = 'voting'
        game = games[self.game_id]
        
        # 重置投票
        for player in game['players']:
            player['votes'] = 0
            player['voted'] = False
            
        alive_players = [p for p in game['players'] if p['alive']]
        
        socketio.emit('phase_changed', {
            'phase': 'voting',
            'message': '投票阶段！选择你认为的卧底',
            'duration': 20,  # 缩短为20秒
            'players': [{'id': p['id'], 'name': p['name'], 'is_ai': p.get('is_ai', False)} for p in alive_players]
        }, room=self.game_id)
        
        # AI自动投票
        self.ai_auto_vote()
        
        # 20秒后统计投票结果
        self.phase_timer = Timer(20.0, self.count_votes)
        self.phase_timer.start()
        
    def ai_auto_vote(self):
        """AI玩家自动投票"""
        game = games[self.game_id]
        alive_players = [p for p in game['players'] if p['alive']]
        
        for player in game['players']:
            if player.get('is_ai', False) and player['alive'] and not player.get('voted', False):
                # AI随机选择一个其他玩家投票
                possible_targets = [p for p in alive_players if p['id'] != player['id']]
                if possible_targets:
                    target = random.choice(possible_targets)
                    target['votes'] = target.get('votes', 0) + 1
                    player['voted'] = True
                    
                    socketio.emit('vote_cast', {
                        'voter': player['name'],
                        'target': target['name'],
                        'is_ai': True
                    }, room=self.game_id)
        
    def count_votes(self):
        game = games[self.game_id]
        
        # 找出得票最多的玩家
        max_votes = 0
        eliminated_players = []
        
        for player in game['players']:
            if player['alive'] and player['votes'] > max_votes:
                max_votes = player['votes']
                eliminated_players = [player]
            elif player['alive'] and player['votes'] == max_votes and max_votes > 0:
                eliminated_players.append(player)
                
        # 如果有平票，随机选择一个
        if eliminated_players:
            eliminated = random.choice(eliminated_players)
            eliminated['alive'] = False
            
            socketio.emit('player_eliminated', {
                'player': eliminated['name'],
                'role': eliminated['role'],
                'votes': eliminated['votes'],
                'is_ai': eliminated.get('is_ai', False)
            }, room=self.game_id)
            
        # 检查游戏是否结束
        if self.check_game_end():
            return
            
        # 进入下一轮
        self.round += 1
        self.update_stock_prices()
        
        socketio.emit('round_ended', {
            'round': self.round,
            'stocks': STOCKS
        }, room=self.game_id)
        
        # 开始新的讨论阶段
        Timer(3.0, self.start_discussion_phase).start()
        
    def check_game_end(self):
        game = games[self.game_id]
        alive_players = [p for p in game['players'] if p['alive']]
        alive_investors = [p for p in alive_players if p['role'] == 'investor']
        alive_undercovers = [p for p in alive_players if p['role'] == 'undercover']
        
        winner = None
        
        if len(alive_undercovers) == 0:
            winner = 'investors'
        elif len(alive_undercovers) >= len(alive_investors):
            winner = 'undercovers'
            
        if winner:
            socketio.emit('game_ended', {
                'winner': winner,
                'message': f'游戏结束！{"投资者" if winner == "investors" else "卧底"}获胜！',
                'final_scores': self.calculate_scores()
            }, room=self.game_id)
            
            game['status'] = 'ended'
            return True
            
        return False
        
    def calculate_scores(self):
        game = games[self.game_id]
        scores = []
        
        for player in game['players']:
            # 计算股票总价值
            stock_value = sum(STOCKS[symbol]['price'] * amount 
                            for symbol, amount in player.get('stocks', {}).items())
            total_value = player['money'] + stock_value
            
            scores.append({
                'name': player['name'],
                'role': player['role'],
                'money': player['money'],
                'stock_value': round(stock_value, 2),
                'total_value': round(total_value, 2),
                'alive': player['alive'],
                'is_ai': player.get('is_ai', False)
            })
            
        return sorted(scores, key=lambda x: x['total_value'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_game', methods=['POST'])
def create_game():
    try:
        data = request.get_json()
        player_name = data.get('player_name')
        max_players = data.get('max_players', 6)
        
        if not player_name:
            return jsonify({'error': '玩家名称不能为空'}), 400
            
        # 生成游戏ID
        game_id = str(uuid.uuid4())[:8]
        
        # 创建新游戏
        games[game_id] = {
            'id': game_id,
            'players': [{
                'name': player_name, 
                'id': str(uuid.uuid4())[:8],
                'socket_id': None,
                'is_host': True,
                'is_ai': False
            }],
            'max_players': max_players,
            'status': 'waiting',
            'engine': GameEngine(game_id),
            'created_at': time.time()
        }
        
        return jsonify({
            'success': True,
            'game_id': game_id,
            'message': f'游戏创建成功！游戏ID: {game_id}'
        })
        
    except Exception as e:
        return jsonify({'error': f'创建游戏失败: {str(e)}'}), 500

@app.route('/api/join_game', methods=['POST'])
def join_game():
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
            
        player_name = data.get('player_name')
        game_id = data.get('game_id')
        
        print(f"收到加入游戏请求: player_name={player_name}, game_id={game_id}")  # 调试信息
        
        if not player_name or not game_id:
            return jsonify({'error': '玩家名称和游戏ID不能为空'}), 400
            
        if game_id not in games:
            return jsonify({'error': '游戏不存在'}), 404
            
        game = games[game_id]
        
        if game['status'] != 'waiting':
            return jsonify({'error': '游戏已开始，无法加入'}), 400
            
        if len(game['players']) >= game['max_players']:
            return jsonify({'error': '游戏人数已满'}), 400
            
        # 检查玩家名是否重复
        for player in game['players']:
            if player['name'] == player_name:
                return jsonify({'error': '玩家名称已存在'}), 400
        
        # 添加玩家
        new_player = {
            'name': player_name, 
            'id': str(uuid.uuid4())[:8],
            'socket_id': None,
            'is_host': len(game['players']) == 0,  # 第一个玩家是房主
            'is_ai': False
        }
        game['players'].append(new_player)
        
        print(f"玩家 {player_name} 成功加入游戏 {game_id}，当前玩家数: {len(game['players'])}")
        
        return jsonify({
            'success': True,
            'message': f'成功加入游戏！当前玩家数: {len(game["players"])}/{game["max_players"]}',
            'redirect_url': f'/game/{game_id}'
        })
        
    except Exception as e:
        print(f"加入游戏错误: {str(e)}")  # 调试信息
        return jsonify({'error': f'加入游戏失败: {str(e)}'}), 500

@socketio.on('join_game')
def on_join_game(data):
    game_id = data.get('game_id')
    player_name = data.get('player_name')
    
    print(f"SocketIO加入游戏: player_name={player_name}, game_id={game_id}")  # 调试信息
    
    if game_id in games:
        game = games[game_id]
        
        # 找到对应玩家并更新socket_id
        for player in game['players']:
            if player['name'] == player_name:
                player['socket_id'] = request.sid
                break
                
        join_room(game_id)
        
        # 发送游戏状态
        emit('game_state', {
            'game_id': game_id,
            'players': game['players'],
            'status': game['status'],
            'stocks': STOCKS
        })
        
        # 通知其他玩家
        emit('player_joined', {
            'player_name': player_name,
            'player_count': len(game['players'])
        }, room=game_id, include_self=False)
        
        # 检查是否需要自动开始（单人游戏）
        real_players = [p for p in game['players'] if not p.get('is_ai', False)]
        print(f"当前真实玩家数: {len(real_players)}, 游戏状态: {game['status']}")
        
        if len(real_players) == 1 and game['status'] == 'waiting':
            print("检测到单人游戏，2秒后自动添加AI并开始游戏")
            # 延迟2秒自动开始，给前端时间加载
            def auto_start_game():
                try:
                    print("开始自动添加AI玩家并启动游戏")
                    success, message = game['engine'].start_game(auto_start=True)
                    print(f"自动开始游戏结果: {success}, {message}")
                    if success:
                        emit('auto_game_started', {
                            'message': '检测到单人游戏，已自动添加AI玩家并开始游戏！'
                        }, room=game_id)
                except Exception as e:
                    print(f"自动开始游戏错误: {str(e)}")
                    
            Timer(2.0, auto_start_game).start()

@socketio.on('start_game')
def on_start_game(data):
    game_id = data.get('game_id')
    
    if game_id in games:
        game = games[game_id]
        success, message = game['engine'].start_game(auto_start=True)
        
        emit('start_game_response', {
            'success': success,
            'message': message
        })

@socketio.on('vote_player')
def on_vote_player(data):
    game_id = data.get('game_id')
    voter_name = data.get('voter_name')
    target_id = data.get('target_id')
    
    if game_id in games:
        game = games[game_id]
        
        # 找到投票者
        voter = None
        for player in game['players']:
            if player['name'] == voter_name:
                voter = player
                break
                
        if voter and not voter.get('voted', False) and not voter.get('is_ai', False):
            # 找到被投票者
            for player in game['players']:
                if player['id'] == target_id:
                    player['votes'] = player.get('votes', 0) + 1
                    voter['voted'] = True
                    
                    emit('vote_cast', {
                        'voter': voter_name,
                        'target': player['name']
                    }, room=game_id)
                    break

@socketio.on('buy_stock')
def on_buy_stock(data):
    game_id = data.get('game_id')
    player_name = data.get('player_name')
    symbol = data.get('symbol')
    amount = data.get('amount', 1)
    
    if game_id in games and symbol in STOCKS:
        game = games[game_id]
        
        for player in game['players']:
            if player['name'] == player_name and not player.get('is_ai', False):
                cost = STOCKS[symbol]['price'] * amount
                
                if player['money'] >= cost:
                    player['money'] -= cost
                    if 'stocks' not in player:
                        player['stocks'] = {}
                    player['stocks'][symbol] = player['stocks'].get(symbol, 0) + amount
                    
                    emit('stock_purchased', {
                        'symbol': symbol,
                        'amount': amount,
                        'cost': cost,
                        'remaining_money': player['money']
                    })
                    
                    # 通知其他玩家有人买了股票
                    emit('player_action', {
                        'player': player_name,
                        'action': f'购买了 {amount} 股 {symbol}'
                    }, room=game_id, include_self=False)
                else:
                    emit('error', {'message': '资金不足'})
                break

@socketio.on('disconnect')
def on_disconnect():
    print(f'客户端已断开连接: {request.sid}')

if __name__ == '__main__':
    print("🎮 股市卧底游戏服务器启动中...")
    print("📊 游戏地址: http://127.0.0.1:8080")
    print("🔧 调试模式: 开启")
    print("✅ 服务器准备就绪！")
    print("🤖 单人模式：一个人进入游戏将自动添加AI玩家并开始！")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)