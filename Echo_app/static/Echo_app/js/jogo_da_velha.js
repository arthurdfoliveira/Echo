// --- Echo_app/static/Echo_app/js/jogo_da_velha.js ---

const cells = document.querySelectorAll('.cell');
const statusDisplay = document.getElementById('status');
const restartButton = document.getElementById('restart-button');

// Variáveis de estado do jogo
let gameActive = true;
let currentPlayer = 'X';
let gameState = ['', '', '', '', '', '', '', '', '']; // Representa as 9 células
let jogoAcabou = false; // Flag para controlar o estado do jogo

// Condições de vitória (índices das células que formam uma linha)
const winningConditions = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // Linhas
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // Colunas
    [0, 4, 8], [2, 4, 6]             // Diagonais
];

// 1. Funções de Mensagens
const statusMessages = {
    win: (player) => `Jogador ${player} Venceu!`,
    draw: 'Empate!',
    turn: (player) => `Vez do Jogador ${player}`
};

function handleStatusDisplay(message) {
    statusDisplay.innerHTML = message;
}

// 2. Funções de Marcação e Troca de Jogador
function handleCellPlayed(clickedCellIndex) {
    // Marca a célula no estado interno
    gameState[clickedCellIndex] = currentPlayer;
    
    // Atualiza o DOM
    const clickedCell = cells[clickedCellIndex];
    clickedCell.innerHTML = currentPlayer;
    clickedCell.classList.add(currentPlayer); 
}

function handlePlayerChange() {
    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
    handleStatusDisplay(statusMessages.turn(currentPlayer));
}

// 3. Função de Verificação de Resultado
function handleResultValidation() {
    let roundWon = false;
    for (let i = 0; i < winningConditions.length; i++) {
        const winCondition = winningConditions[i];
        let a = gameState[winCondition[0]];
        let b = gameState[winCondition[1]];
        let c = gameState[winCondition[2]];

        if (a === '' || b === '' || c === '') {
            continue; 
        }
        if (a === b && b === c) {
            roundWon = true;
            // Adiciona estilo para a linha vencedora
            winCondition.forEach(index => cells[index].style.backgroundColor = 'lightgreen');
            break;
        }
    }

    if (roundWon) {
        handleStatusDisplay(statusMessages.win(currentPlayer));
        gameActive = false;
        jogoAcabou = true;
        return true; // Vitória
    }

    // Verifica Empate
    let roundDraw = !gameState.includes('');
    if (roundDraw) {
        handleStatusDisplay(statusMessages.draw);
        gameActive = false;
        jogoAcabou = true;
        return true; // Empate
    }

    // Se ninguém ganhou nem empatou, troca o jogador
    handlePlayerChange();
    return false; // Jogo continua
}

// ===========================================
// 4. LÓGICA DO BOT (JOGADOR 'O')
// ===========================================

/**
 * Função auxiliar para verificar se o movimento em 'indice' garante a vitória para 'jogador'
 */
function checarVitoriaSimulada(tab, jog, indice) {
    const tempTab = [...tab];
    tempTab[indice] = jog;

    for (const [a, b, c] of winningConditions) {
        if (tempTab[a] === jog && tempTab[b] === jog && tempTab[c] === jog) {
            return true;
        }
    }
    return false;
}


/**
 * Determina o índice da jogada ideal para o Bot ('O').
 */
function fazerJogadaBot(tabuleiro) {
    const movimentosDisponiveis = tabuleiro
        .map((cell, index) => cell === '' ? index : null)
        .filter(index => index !== null);
    
    if (movimentosDisponiveis.length === 0) return -1;
    
    // 1. Vencer (Se 'O' pode ganhar)
    for (const i of movimentosDisponiveis) {
        if (checarVitoriaSimulada(tabuleiro, "O", i)) {
            return i;
        }
    }

    // 2. Bloquear (Se 'X' pode ganhar)
    for (const i of movimentosDisponiveis) {
        if (checarVitoriaSimulada(tabuleiro, "X", i)) {
            return i;
        }
    }

    // 3. Centro
    if (movimentosDisponiveis.includes(4)) {
        return 4;
    }

    // 4. Cantos (0, 2, 6, 8)
    const cantos = [0, 2, 6, 8];
    for (const i of cantos) {
        if (movimentosDisponiveis.includes(i)) {
            return i;
        }
    }

    // 5. Laterais (1, 3, 5, 7) - Escolhe o primeiro disponível
    for (const i of movimentosDisponiveis) {
        // Como 'i' está na lista de disponíveis, ele é uma lateral ou um canto
        // Se a lógica chegou aqui, é o primeiro slot disponível restante.
        return i;
    }

    return -1;
}

function processarJogadaBot() {
    // Garante que o jogo está ativo e é a vez do Bot ('O')
    if (gameActive && !jogoAcabou && currentPlayer === 'O') {
        const botIndex = fazerJogadaBot(gameState);

        if (botIndex !== -1) {
            handleCellPlayed(botIndex);
            
            // Valida o resultado da jogada do Bot (e troca para 'X' se o jogo continua)
            handleResultValidation();
        } else {
            // Se o botIndex for -1, significa que não há movimentos, mas o jogo não acabou,
            // o que implicaria um erro de lógica em 'handleResultValidation'.
            // Para segurança, trocamos de volta para 'X' se o bot falhar.
            if (gameState.includes('')) {
                // Caso extremo: o bot falhou em encontrar a jogada.
                handlePlayerChange(); 
            }
        }
    }
}

// 5. Função Principal de Clique (Humano 'X')
function handleCellClick(event) {
    const clickedCellIndex = parseInt(event.target.getAttribute('data-index'));

    // 1. Condição: A célula deve estar vazia E o jogo ativo E deve ser a vez do 'X'
    if (gameState[clickedCellIndex] !== '' || !gameActive || currentPlayer === 'O') {
        // Se for a vez do O (bot) ou se a célula estiver ocupada, a ação é bloqueada.
        return;
    }

    // 2. Processa o movimento do Humano ('X')
    handleCellPlayed(clickedCellIndex);
    
    // 3. Valida o resultado (Se for vitória/empate, retorna true e gameActive é false. 
    // Se continua, troca para 'O'.)
    const gameOver = handleResultValidation(); 

    // 4. Se o jogo não acabou (gameOver é false), agora é a vez do 'O'. Chama o bot.
    if (!gameOver) {
        // Pequeno delay para melhor UX
        setTimeout(processarJogadaBot, 500); 
    }
}

// 6. Função de Reinício do Jogo
function handleRestartGame() {
    gameActive = true;
    jogoAcabou = false;
    currentPlayer = 'X';
    gameState = ['', '', '', '', '', '', '', '', ''];
    handleStatusDisplay(statusMessages.turn(currentPlayer));

    cells.forEach(cell => {
        cell.innerHTML = '';
        cell.classList.remove('X', 'O');
        cell.style.backgroundColor = ''; 
    });
}

// 7. Adiciona Listeners
cells.forEach(cell => cell.addEventListener('click', handleCellClick));
restartButton.addEventListener('click', handleRestartGame);

// Inicializa a mensagem
handleStatusDisplay(statusMessages.turn(currentPlayer));