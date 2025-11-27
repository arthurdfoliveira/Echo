// --- Echo_app/static/Echo_app/js/jogo_da_velha.js ---

const cells = document.querySelectorAll('.cell');
const statusDisplay = document.getElementById('status');
const restartButton = document.getElementById('restart-button');

// Variáveis de estado do jogo
let gameActive = true;
let currentPlayer = 'X';
let gameState = ['', '', '', '', '', '', '', '', '']; // Representa as 9 células

// Condições de vitória (índices das células que formam uma linha)
const winningConditions = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
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
function handleCellPlayed(clickedCell, clickedCellIndex) {
    // Atualiza o estado interno e o DOM
    gameState[clickedCellIndex] = currentPlayer;
    clickedCell.innerHTML = currentPlayer;
    clickedCell.classList.add(currentPlayer); // Adiciona classe para estilização de cor
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
            continue; // Continua se a linha não estiver completa
        }
        if (a === b && b === c) {
            roundWon = true;
            // Opcional: Adicionar estilo para a linha vencedora (ex: mudar cor de fundo)
            winCondition.forEach(index => cells[index].style.backgroundColor = 'lightgreen');
            break;
        }
    }

    if (roundWon) {
        handleStatusDisplay(statusMessages.win(currentPlayer));
        gameActive = false;
        return;
    }

    // Verifica Empate: Se não há mais espaços vazios (e ninguém ganhou)
    let roundDraw = !gameState.includes('');
    if (roundDraw) {
        handleStatusDisplay(statusMessages.draw);
        gameActive = false;
        return;
    }

    // Se ninguém ganhou nem empatou, troca o jogador
    handlePlayerChange();
}

// 4. Função Principal de Clique
function handleCellClick(event) {
    const clickedCell = event.target;
    const clickedCellIndex = parseInt(clickedCell.getAttribute('data-index'));

    // 1. Checa se a célula já está preenchida ou se o jogo acabou
    if (gameState[clickedCellIndex] !== '' || !gameActive) {
        return;
    }

    // 2. Processa o movimento
    handleCellPlayed(clickedCell, clickedCellIndex);
    
    // 3. Valida o resultado
    handleResultValidation();
}

// 5. Função de Reinício do Jogo
function handleRestartGame() {
    gameActive = true;
    currentPlayer = 'X';
    gameState = ['', '', '', '', '', '', '', '', ''];
    handleStatusDisplay(statusMessages.turn(currentPlayer));

    cells.forEach(cell => {
        cell.innerHTML = '';
        cell.classList.remove('X', 'O');
        cell.style.backgroundColor = ''; // Remove o estilo de vitória
    });
}

// 6. Adiciona Listeners
cells.forEach(cell => cell.addEventListener('click', handleCellClick));
restartButton.addEventListener('click', handleRestartGame);

// Inicializa a mensagem
handleStatusDisplay(statusMessages.turn(currentPlayer));