# -*- coding: utf-8 -*-
# 股市卧底游戏 - Flask主应用
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import json
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入模块，绕过 __init__.py
try:
    # 方法1：直接从文件导入
    import importlib.util
    
    def load_module_from_file(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    # 加载所有模块
    game_state_module = load_module_from_file("game_state", os.path.join(current_dir, "models", "game_state.py"))
    player_module = load_module_from_file("player", os.path.join(current_dir, "models", "player.py"))
    ai_system_module = load_module_from_file("ai_system", os.path.join(current_dir, "models", "ai_system.py"))
    card_system_module = load_module_from_file("card_system", os.path.join(current_dir, "models", "card_system.py"))
    stock_market_module = load_module_from_file("stock_market", os.path.join(current_dir, "models", "stock_market.py"))
    game_engine_module = load_module_from_file("game_engine", os.path.join(current_dir, "models", "game_engine.py"))
    
    # 获取类
    GameState = game_state_module.GameState
    Player = player_module.Player
    AISystem = ai_system_module.AISystem
    CardSystem = card_system_module.CardSystem
    StockMarket = stock_market_module.StockMarket
    GameEngine = game_engine_module.GameEngine
    
    print("✅ 模块导入成功！")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    # 备用方案：尝试常规导入
    try:
        from models.game_state import GameState
        from models.player import Player
        from models.ai_system import AISystem
        from models.card_system import CardSystem
        from models.stock_market import StockMarket
        from models.game_engine import GameEngine
        print("✅ 备用导入成功！")
    except Exception as e2:
        print(f"❌ 备用导入也失败: {e2}")
        exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock_undercover_game_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局游戏状态
games = {}
ai_system = AISystem()
card_system = CardSystem()
stock_market = StockMarket()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<game_id>')
def game(game_id):
    if game_id not in games:
        return "游戏不存在", 404
    return render_template('game.html', game_id=game_id)

@app.route('/api/create_game', methods=['POST'])
def create_game():
    try:
        data = request.json
        player_name = data.get('player_name', '').strip()
        max_players = int(data.get('max_players', 6))
        
        if not player_name:
            return jsonify({'error': '玩家名称不能为空'}), 400
        
        if max_players < 3 or max_players > 8:
            return jsonify({'error': '玩家数量必须在3-8人之间'}), 400
        
        # 创建游戏
        game_id = str(uuid.uuid4())[:8]
        game_state = GameState(game_id, max_players)
        
        # 创建游戏引擎
        game_engine = GameEngine(game_state, ai_system, card_system, stock_market)
        
        # 创建玩家
        player = Player(str(uuid.uuid4())[:8], player_name, is_ai=False)
        game_state.add_player(player)
        
        games[game_id] = {
            'state': game_state,
            'engine': game_engine,
            'created_at': datetime.now()
        }
        
        return jsonify({
            'game_id': game_id,
            'player_id': player.player_id,
            'message': f'游戏 {game_id} 创建成功！'
        })
        
    except Exception as e:
        return jsonify({'error': f'创建游戏失败: {str(e)}'}), 500

@app.route('/api/join_game', methods=['POST'])
def join_game():
    try:
        data = request.json
        game_id = data.get('game_id', '').strip()
        player_name = data.get('player_name', '').strip()
        
        if not game_id or not player_name:
            return jsonify({'error': '游戏ID和玩家名称不能为空'}), 400
        
        if game_id not in games:
            return jsonify({'error': '游戏不存在'}), 404
        
        game_state = games[game_id]['state']
        
        if game_state.phase != 'waiting':
            return jsonify({'error': '游戏已开始，无法加入'}), 400
        
        if len(game_state.players) >= game_state.max_players:
            return jsonify({'error': '游戏人数已满'}), 400
        
        # 检查玩家名称是否重复
        for player in game_state.players.values():
            if player.name == player_name:
                return jsonify({'error': '玩家名称已存在'}), 400
        
        # 创建玩家
        player = Player(str(uuid.uuid4())[:8], player_name, is_ai=False)
        game_state.add_player(player)
        
        return jsonify({
            'game_id': game_id,
            'player_id': player.player_id,
            'message': f'成功加入游戏 {game_id}！'
        })
        
    except Exception as e:
        return jsonify({'error': f'加入游戏失败: {str(e)}'}), 500

@app.route('/api/game_state/<game_id>')
def get_game_state(game_id):
    if game_id not in games:
        return jsonify({'error': '游戏不存在'}), 404
    
    game_state = games[game_id]['state']
    return jsonify(game_state.to_dict())

# WebSocket事件处理
@socketio.on('connect')
def on_connect():
    print(f'客户端连接: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    print(f'客户端断开: {request.sid}')

@socketio.on('join_game')
def on_join_game(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    
    if game_id in games:
        join_room(game_id)
        emit('game_update', games[game_id]['state'].to_dict(), room=game_id)

@socketio.on('start_game')
def on_start_game(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    game_engine = games[game_id]['engine']
    
    try:
        result = game_engine.start_game()
        if result['success']:
            emit('game_update', games[game_id]['state'].to_dict(), room=game_id)
            emit('message', {'message': '游戏开始！', 'type': 'system'}, room=game_id)
        else:
            emit('error', {'message': result['message']})
    except Exception as e:
        emit('error', {'message': f'开始游戏失败: {str(e)}'})

@socketio.on('invest')
def on_invest(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    stock_symbol = data.get('stock_symbol')
    amount = data.get('amount')
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    game_engine = games[game_id]['engine']
    
    try:
        result = game_engine.handle_investment(player_id, stock_symbol, amount)
        if result['success']:
            emit('game_update', games[game_id]['state'].to_dict(), room=game_id)
            emit('message', {
                'message': f'{result["player_name"]} 投资了 {amount} 元到 {stock_symbol}',
                'type': 'investment'
            }, room=game_id)
        else:
            emit('error', {'message': result['message']})
    except Exception as e:
        emit('error', {'message': f'投资失败: {str(e)}'})

@socketio.on('use_card')
def on_use_card(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    card_id = data.get('card_id')
    target_player_id = data.get('target_player_id')
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    game_engine = games[game_id]['engine']
    
    try:
        result = game_engine.handle_card_use(player_id, card_id, target_player_id)
        if result['success']:
            emit('game_update', games[game_id]['state'].to_dict(), room=game_id)
            emit('message', {
                'message': result['message'],
                'type': 'card'
            }, room=game_id)
        else:
            emit('error', {'message': result['message']})
    except Exception as e:
        emit('error', {'message': f'使用卡牌失败: {str(e)}'})

@socketio.on('send_message')
def on_send_message(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    message = data.get('message', '').strip()
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    if not message:
        emit('error', {'message': '消息不能为空'})
        return
    
    game_state = games[game_id]['state']
    
    if player_id not in game_state.players:
        emit('error', {'message': '玩家不存在'})
        return
    
    player = game_state.players[player_id]
    
    # 添加消息到游戏状态
    game_state.add_message(player_id, message)
    
    emit('message', {
        'player_name': player.name,
        'message': message,
        'type': 'player',
        'timestamp': datetime.now().isoformat()
    }, room=game_id)

@socketio.on('vote')
def on_vote(data):
    game_id = data.get('game_id')
    voter_id = data.get('voter_id')
    target_id = data.get('target_id')
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    game_engine = games[game_id]['engine']
    
    try:
        result = game_engine.handle_vote(voter_id, target_id)
        if result['success']:
            emit('game_update', games[game_id]['state'].to_dict(), room=game_id)
            emit('message', {
                'message': result['message'],
                'type': 'vote'
            }, room=game_id)
        else:
            emit('error', {'message': result['message']})
    except Exception as e:
        emit('error', {'message': f'投票失败: {str(e)}'})

@socketio.on('next_phase')
def on_next_phase(data):
    game_id = data.get('game_id')
    
    if game_id not in games:
        emit('error', {'message': '游戏不存在'})
        return
    
    game_engine = games[game_id]['engine']
    
    try:
        result = game_engine.advance_phase()
        if result['success']:
            emit('game_update', games[game_id]['state'].to_dict(), room=game_id)
            emit('message', {
                'message': result['message'],
                'type': 'system'
            }, room=game_id)
        else:
            emit('error', {'message': result['message']})
    except Exception as e:
        emit('error', {'message': f'推进阶段失败: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)