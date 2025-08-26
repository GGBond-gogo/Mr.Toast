// 游戏页面JavaScript逻辑
class StockUndercoverGame {
    constructor(gameId) {
        this.gameId = gameId;
        this.socket = io();
        this.playerId = null;
        this.playerName = null;
        this.gameState = null;
        this.selectedStock = null;
        this.selectedCard = null;
        this.selectedTarget = null;
        
        this.initializeSocket();
        this.initializeUI();
        this.loadGameState();
    }
    
    initializeSocket() {
        // 连接到游戏房间
        this.socket.emit('join_game', { game_id: this.gameId });
        
        // 监听游戏状态更新
        this.socket.on('game_state_update', (data) => {
            this.gameState = data;
            this.updateUI();
        });
        
        // 监听新消息
        this.socket.on('new_message', (data) => {
            this.addMessage(data);
        });
        
        // 监听投资结果
        this.socket.on('investment_result', (data) => {
            this.showNotification(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                this.clearInvestmentForm();
            }
        });
        
        // 监听卡牌使用结果
        this.socket.on('card_use_result', (data) => {
            this.showNotification(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                this.clearCardSelection();
            }
        });
        
        // 监听投票结果
        this.socket.on('vote_result', (data) => {
            this.showNotification(data.message, data.success ? 'success' : 'error');
        });
        
        // 监听阶段变化
        this.socket.on('phase_change', (data) => {
            this.showNotification(`游戏进入${this.getPhaseText(data.phase)}阶段`, 'info');
            this.updatePhaseUI(data.phase);
        });
        
        // 监听游戏结束
        this.socket.on('game_end', (data) => {
            this.showGameEndModal(data);
        });
    }
    
    initializeUI() {
        // 投资按钮事件
        document.getElementById('invest-btn').addEventListener('click', () => {
            this.makeInvestment();
        });
        
        // 卖出按钮事件
        document.getElementById('sell-btn').addEventListener('click', () => {
            this.sellStock();
        });
        
        // 使用卡牌按钮事件
        document.getElementById('use-card-btn').addEventListener('click', () => {
            this.useCard();
        });
        
        // 发送消息按钮事件
        document.getElementById('send-message-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 投票按钮事件
        document.getElementById('vote-btn').addEventListener('click', () => {
            this.vote();
        });
        
        // 下一阶段按钮事件
        document.getElementById('next-phase-btn').addEventListener('click', () => {
            this.nextPhase();
        });
        
        // 消息输入框回车事件
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // 股票选择事件
        document.addEventListener('change', (e) => {
            if (e.target.name === 'stock-select') {
                this.selectedStock = e.target.value;
                this.updateStockInfo();
            }
        });
        
        // 卡牌选择事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('card-item')) {
                this.selectCard(e.target);
            }
        });
        
        // 玩家选择事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('player-item')) {
                this.selectPlayer(e.target);
            }
        });
    }
    
    async loadGameState() {
        try {
            const response = await fetch(`/api/game_state/${this.gameId}`);
            const data = await response.json();
            
            if (data.error) {
                this.showNotification(data.error, 'error');
                return;
            }
            
            this.gameState = data;
            this.updateUI();
        } catch (error) {
            console.error('加载游戏状态失败:', error);
            this.showNotification('加载游戏状态失败', 'error');
        }
    }
    
    updateUI() {
        if (!this.gameState) return;
        
        this.updatePlayerList();
        this.updateStockMarket();
        this.updatePlayerInfo();
        this.updateCards();
        this.updateMessages();
        this.updatePhaseInfo();
        this.updateVotes();
    }
    
    updatePlayerList() {
        const playerList = document.getElementById('player-list');
        playerList.innerHTML = '';
        
        this.gameState.players.forEach(player => {
            const playerDiv = document.createElement('div');
            playerDiv.className = `player-item ${!player.is_alive ? 'eliminated' : ''}`;
            playerDiv.dataset.playerId = player.id;
            
            const suspicionBar = this.createSuspicionBar(player.suspicion_level);
            const trustBar = this.createTrustBar(player.trust_level);
            
            playerDiv.innerHTML = `
                <div class="player-name">${player.name} ${player.is_ai ? '(AI)' : ''}</div>
                <div class="player-money">资金: ¥${player.money.toLocaleString()}</div>
                <div class="player-stocks">持股: ${Object.keys(player.stocks).length}</div>
                <div class="suspicion-level">
                    <span>怀疑度:</span>
                    ${suspicionBar}
                </div>
                <div class="trust-level">
                    <span>信任度:</span>
                    ${trustBar}
                </div>
                ${!player.is_alive ? '<div class="eliminated-tag">已淘汰</div>' : ''}
            `;
            
            playerList.appendChild(playerDiv);
        });
    }
    
    updateStockMarket() {
        const stockList = document.getElementById('stock-list');
        const stockSelect = document.getElementById('stock-select');
        
        if (!this.gameState.stock_market || !this.gameState.stock_market.stocks) {
            return;
        }
        
        stockList.innerHTML = '';
        stockSelect.innerHTML = '<option value="">选择股票</option>';
        
        Object.values(this.gameState.stock_market.stocks).forEach(stock => {
            // 更新股票列表显示
            const stockDiv = document.createElement('div');
            stockDiv.className = 'stock-item';
            
            const priceChange = this.calculatePriceChange(stock);
            const changeClass = priceChange > 0 ? 'positive' : priceChange < 0 ? 'negative' : 'neutral';
            
            stockDiv.innerHTML = `
                <div class="stock-symbol">${stock.symbol}</div>
                <div class="stock-name">${stock.name}</div>
                <div class="stock-price">¥${stock.current_price.toFixed(2)}</div>
                <div class="stock-change ${changeClass}">
                    ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%
                </div>
                <div class="stock-volume">成交量: ${stock.volume || 0}</div>
            `;
            
            stockList.appendChild(stockDiv);
            
            // 更新股票选择下拉框
            const option = document.createElement('option');
            option.value = stock.symbol;
            option.textContent = `${stock.symbol} - ${stock.name} (¥${stock.current_price.toFixed(2)})`;
            stockSelect.appendChild(option);
        });
    }
    
    updatePlayerInfo() {
        const currentPlayer = this.getCurrentPlayer();
        if (!currentPlayer) return;
        
        document.getElementById('player-money').textContent = `¥${currentPlayer.money.toLocaleString()}`;
        document.getElementById('player-role').textContent = currentPlayer.role || '未知';
        
        // 更新持股信息
        const holdingsDiv = document.getElementById('player-holdings');
        holdingsDiv.innerHTML = '';
        
        Object.entries(currentPlayer.stocks || {}).forEach(([symbol, amount]) => {
            const stock = this.gameState.stock_market.stocks[symbol];
            if (stock && amount > 0) {
                const holdingDiv = document.createElement('div');
                holdingDiv.className = 'holding-item';
                holdingDiv.innerHTML = `
                    <span>${symbol}: ${amount}股</span>
                    <span>价值: ¥${(stock.current_price * amount).toFixed(2)}</span>
                `;
                holdingsDiv.appendChild(holdingDiv);
            }
        });
    }
    
    updateCards() {
        const cardsDiv = document.getElementById('player-cards');
        const currentPlayer = this.getCurrentPlayer();
        
        if (!currentPlayer || !currentPlayer.cards) {
            cardsDiv.innerHTML = '<div class="no-cards">暂无卡牌</div>';
            return;
        }
        
        cardsDiv.innerHTML = '';
        
        currentPlayer.cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card-item';
            cardDiv.dataset.cardId = card.card_id;
            
            cardDiv.innerHTML = `
                <div class="card-name">${card.name}</div>
                <div class="card-type">${this.getCardTypeText(card.type)}</div>
                <div class="card-rarity ${card.rarity}">${this.getCardRarityText(card.rarity)}</div>
                <div class="card-description">${card.description}</div>
            `;
            
            cardsDiv.appendChild(cardDiv);
        });
    }
    
    updateMessages() {
        const messagesDiv = document.getElementById('messages');
        
        if (!this.gameState.messages) return;
        
        messagesDiv.innerHTML = '';
        
        this.gameState.messages.forEach(message => {
            this.addMessage(message, false);
        });
        
        // 滚动到底部
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    updatePhaseInfo() {
        const phaseDiv = document.getElementById('current-phase');
        const timerDiv = document.getElementById('phase-timer');
        const roundDiv = document.getElementById('current-round');
        
        phaseDiv.textContent = this.getPhaseText(this.gameState.phase);
        roundDiv.textContent = `第 ${this.gameState.round} 轮`;
        
        if (this.gameState.time_remaining) {
            this.startTimer(this.gameState.time_remaining);
        }
        
        this.updatePhaseUI(this.gameState.phase);
    }
    
    updateVotes() {
        const votesDiv = document.getElementById('vote-results');
        
        if (!this.gameState.votes || Object.keys(this.gameState.votes).length === 0) {
            votesDiv.innerHTML = '<div class="no-votes">暂无投票</div>';
            return;
        }
        
        votesDiv.innerHTML = '';
        
        Object.entries(this.gameState.votes).forEach(([targetId, voters]) => {
            const targetPlayer = this.gameState.players.find(p => p.id === targetId);
            if (targetPlayer) {
                const voteDiv = document.createElement('div');
                voteDiv.className = 'vote-item';
                voteDiv.innerHTML = `
                    <span class="vote-target">${targetPlayer.name}</span>
                    <span class="vote-count">${voters.length} 票</span>
                `;
                votesDiv.appendChild(voteDiv);
            }
        });
    }
    
    // 游戏操作方法
    makeInvestment() {
        const stockSymbol = document.getElementById('stock-select').value;
        const amount = parseFloat(document.getElementById('invest-amount').value);
        
        if (!stockSymbol) {
            this.showNotification('请选择股票', 'warning');
            return;
        }
        
        if (!amount || amount <= 0) {
            this.showNotification('请输入有效的投资金额', 'warning');
            return;
        }
        
        this.socket.emit('invest', {
            game_id: this.gameId,
            stock_symbol: stockSymbol,
            amount: amount,
            action: 'buy'
        });
    }
    
    sellStock() {
        const stockSymbol = document.getElementById('stock-select').value;
        const amount = parseFloat(document.getElementById('sell-amount').value);
        
        if (!stockSymbol) {
            this.showNotification('请选择股票', 'warning');
            return;
        }
        
        if (!amount || amount <= 0) {
            this.showNotification('请输入有效的卖出数量', 'warning');
            return;
        }
        
        this.socket.emit('invest', {
            game_id: this.gameId,
            stock_symbol: stockSymbol,
            amount: amount,
            action: 'sell'
        });
    }
    
    useCard() {
        if (!this.selectedCard) {
            this.showNotification('请选择要使用的卡牌', 'warning');
            return;
        }
        
        this.socket.emit('use_card', {
            game_id: this.gameId,
            card_id: this.selectedCard,
            target_player_id: this.selectedTarget
        });
    }
    
    sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) {
            return;
        }
        
        this.socket.emit('send_message', {
            game_id: this.gameId,
            message: message
        });
        
        messageInput.value = '';
    }
    
    vote() {
        if (!this.selectedTarget) {
            this.showNotification('请选择投票目标', 'warning');
            return;
        }
        
        this.socket.emit('vote', {
            game_id: this.gameId,
            target_player_id: this.selectedTarget
        });
    }
    
    nextPhase() {
        this.socket.emit('next_phase', {
            game_id: this.gameId
        });
    }
    
    // 辅助方法
    getCurrentPlayer() {
        if (!this.gameState || !this.playerId) return null;
        return this.gameState.players.find(p => p.id === this.playerId);
    }
    
    selectCard(cardElement) {
        // 清除之前的选择
        document.querySelectorAll('.card-item').forEach(card => {
            card.classList.remove('selected');
        });
        
        // 选择新卡牌
        cardElement.classList.add('selected');
        this.selectedCard = cardElement.dataset.cardId;
    }
    
    selectPlayer(playerElement) {
        // 清除之前的选择
        document.querySelectorAll('.player-item').forEach(player => {
            player.classList.remove('selected');
        });
        
        // 选择新玩家
        playerElement.classList.add('selected');
        this.selectedTarget = playerElement.dataset.playerId;
    }
    
    addMessage(message, scroll = true) {
        const messagesDiv = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type || 'chat'}`;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        if (message.type === 'system') {
            messageDiv.innerHTML = `
                <div class="message-time">${timestamp}</div>
                <div class="message-content system">${message.message}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="message-player">${message.player_name || '系统'}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-content">${message.message}</div>
            `;
        }
        
        messagesDiv.appendChild(messageDiv);
        
        if (scroll) {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
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
    
    startTimer(seconds) {
        const timerDiv = document.getElementById('phase-timer');
        
        const updateTimer = () => {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            timerDiv.textContent = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
            
            if (seconds > 0) {
                seconds--;
                setTimeout(updateTimer, 1000);
            } else {
                timerDiv.textContent = '00:00';
            }
        };
        
        updateTimer();
    }
    
    updatePhaseUI(phase) {
        // 隐藏所有阶段面板
        document.querySelectorAll('.phase-panel').forEach(panel => {
            panel.style.display = 'none';
        });
        
        // 显示当前阶段面板
        const currentPanel = document.getElementById(`${phase}-panel`);
        if (currentPanel) {
            currentPanel.style.display = 'block';
        }
    }
    
    clearInvestmentForm() {
        document.getElementById('invest-amount').value = '';
        document.getElementById('sell-amount').value = '';
    }
    
    clearCardSelection() {
        document.querySelectorAll('.card-item').forEach(card => {
            card.classList.remove('selected');
        });
        this.selectedCard = null;
    }
    
    calculatePriceChange(stock) {
        if (!stock.price_history || stock.price_history.length < 2) {
            return 0;
        }
        
        const currentPrice = stock.current_price;
        const previousPrice = stock.price_history[stock.price_history.length - 2];
        
        return ((currentPrice - previousPrice) / previousPrice) * 100;
    }
    
    createSuspicionBar(level) {
        const percentage = Math.min(100, Math.max(0, level));
        return `<div class="progress-bar suspicion"><div class="progress-fill" style="width: ${percentage}%"></div></div>`;
    }
    
    createTrustBar(level) {
        const percentage = Math.min(100, Math.max(0, level));
        return `<div class="progress-bar trust"><div class="progress-fill" style="width: ${percentage}%"></div></div>`;
    }
    
    getPhaseText(phase) {
        const phaseTexts = {
            'waiting': '等待开始',
            'investment': '投资阶段',
            'discussion': '讨论阶段',
            'voting': '投票阶段',
            'game_end': '游戏结束'
        };
        return phaseTexts[phase] || phase;
    }
    
    getCardTypeText(type) {
        const typeTexts = {
            'market_news': '市场新闻',
            'event_crisis': '事件危机',
            'role_interaction': '角色互动',
            'undercover_special': '卧底专属',
            'family_split': '家族撕裂',
            'conspiracy_trap': '阴谋陷阱',
            'public_opinion': '舆论风暴'
        };
        return typeTexts[type] || type;
    }
    
    getCardRarityText(rarity) {
        const rarityTexts = {
            'common': '普通',
            'rare': '稀有',
            'epic': '史诗',
            'legendary': '传说'
        };
        return rarityTexts[rarity] || rarity;
    }
    
    showGameEndModal(data) {
        const modal = document.createElement('div');
        modal.className = 'game-end-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>游戏结束</h2>
                <div class="winner-info">
                    <h3>获胜方: ${data.winner}</h3>
                    ${data.eliminated ? `<p>被淘汰: ${data.eliminated}</p>` : ''}
                </div>
                <div class="final-scores">
                    <h4>最终得分:</h4>
                    <div id="final-player-list"></div>
                </div>
                <button onclick="location.href='/'" class="btn btn-primary">返回首页</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 显示最终玩家列表
        const finalPlayerList = document.getElementById('final-player-list');
        this.gameState.players.forEach(player => {
            const playerDiv = document.createElement('div');
            playerDiv.className = 'final-player';
            playerDiv.innerHTML = `
                <span class="player-name">${player.name}</span>
                <span class="player-role">${player.role}</span>
                <span class="player-money">¥${player.money.toLocaleString()}</span>
            `;
            finalPlayerList.appendChild(playerDiv);
        });
    }
}

// 页面加载完成后初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    const gameId = window.location.pathname.split('/').pop();
    window.game = new StockUndercoverGame(gameId);
});