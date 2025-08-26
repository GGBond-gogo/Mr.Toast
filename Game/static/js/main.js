// 主页JavaScript代码
class GameLobby {
    constructor() {
        this.initializeUI();
    }
    
    initializeUI() {
        // 创建游戏按钮事件
        document.getElementById('create-game-btn').addEventListener('click', () => {
            this.createGame();
        });
        
        // 加入游戏按钮事件
        document.getElementById('join-game-btn').addEventListener('click', () => {
            this.joinGame();
        });
        
        // 表单提交事件
        document.getElementById('create-game-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createGame();
        });
        
        document.getElementById('join-game-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.joinGame();
        });
    }
    
    async createGame() {
        const playerName = document.getElementById('create-player-name').value.trim();
        const maxPlayers = parseInt(document.getElementById('max-players').value);
        
        if (!playerName) {
            this.showNotification('请输入玩家名称', 'warning');
            return;
        }
        
        if (maxPlayers < 3 || maxPlayers > 8) {
            this.showNotification('玩家数量必须在3-8人之间', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/create_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_name: playerName,
                    max_players: maxPlayers
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showNotification(data.error, 'error');
                return;
            }
            
            // 跳转到游戏页面
            window.location.href = `/game/${data.game_id}`;
            
        } catch (error) {
            console.error('创建游戏失败:', error);
            this.showNotification('创建游戏失败，请重试', 'error');
        }
    }
    
    async joinGame() {
        const playerName = document.getElementById('join-player-name').value.trim();
        const gameId = document.getElementById('game-id').value.trim();
        
        if (!playerName) {
            this.showNotification('请输入玩家名称', 'warning');
            return;
        }
        
        if (!gameId) {
            this.showNotification('请输入游戏ID', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/join_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_name: playerName,
                    game_id: gameId
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showNotification(data.error, 'error');
                return;
            }
            
            // 跳转到游戏页面
            window.location.href = `/game/${gameId}`;
            
        } catch (error) {
            console.error('加入游戏失败:', error);
            this.showNotification('加入游戏失败，请重试', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 3秒后自动消失
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new GameLobby();
});