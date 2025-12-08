// --- Echo_app/static/Echo_app/js/jogo_da_forca.js ---

document.addEventListener('DOMContentLoaded', () => {
    // =====================================
    // DADOS DO JOGO
    // =====================================
    const palavrasPorTema = {
        'Esportes': [
            { palavra: 'FUTEBOL', dica: 'O esporte mais popular do Brasil.' },
            { palavra: 'VÔLEI', dica: 'Jogado em quadra ou na areia, a bola não pode cair.' },
            { palavra: 'NATAÇÃO', dica: 'Modalidade de piscina.' },
            { palavra: 'ATLETISMO', dica: 'Conjunto de corridas, saltos e arremessos.' },
        ],
        'Cultura Pop': [
            { palavra: 'CINEMA', dica: 'A sétima arte.' },
            { palavra: 'NOVEMBRO', dica: 'Um mês frio, uma série de sucesso.' },
            { palavra: 'PIZZA', dica: 'Comida de filme de herói.' },
            { palavra: 'ROCK', dica: 'Gênero musical de guitarras distorcidas.' },
        ],
        'Tecnologia': [
            { palavra: 'ALGORITMO', dica: 'Sequência de passos para resolver um problema.' },
            { palavra: 'INTERNET', dica: 'Rede mundial de computadores.' },
            { palavra: 'JAVASCRIPT', dica: 'Linguagem de script usada neste jogo.' },
            { palavra: 'CELULAR', dica: 'Dispositivo móvel que você provavelmente está usando.' },
        ],
        'Cidades PE': [
            { palavra: 'RECIFE', dica: 'A capital pernambucana.' },
            { palavra: 'OLINDA', dica: 'Cidade conhecida pelo carnaval histórico.' },
            { palavra: 'CARUARU', dica: 'Capital do Forró e do Agreste.' },
            { palavra: 'PETROLINA', dica: 'Famosa pela produção de frutas no sertão.' },
        ]
    };

    const letrasAlfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
    const partesDaForca = [
        'forca-base-1', 'forca-base-2', 'forca-base-3', 'forca-laco', 
        'forca-cabeca', 'forca-tronco', 'forca-braco-e', 'forca-braco-d', 
        'forca-perna-e', 'forca-perna-d' // 10 erros no total
    ];

    // Variáveis de Estado
    let palavraSecreta = '';
    let temaAtual = '';
    let letrasAdivinhadas = [];
    let erros = 0;
    let maxErros = partesDaForca.length;
    let jogoAtivo = true;

    // Elementos DOM
    const wordDisplay = document.getElementById('word-display');
    const keyboardContainer = document.getElementById('keyboard-container');
    const forcaGabarito = document.getElementById('forca-gabarito');
    const messageDisplay = document.getElementById('message-display');
    const temaDisplay = document.querySelector('#tema-display span');
    const incorrectGuessesTable = document.getElementById('incorrect-guesses');
    const correctGuessesTable = document.getElementById('correct-guesses-table');
    const restartButton = document.getElementById('restart-button');

    // =====================================
    // FUNÇÕES DE LÓGICA
    // =====================================

    /**
     * 1. Inicializa um novo jogo: seleciona palavra, reseta estado e monta UI.
     */
    function initializeGame() {
        // 1. Resetar Estado
        letrasAdivinhadas = [];
        erros = 0;
        jogoAtivo = true;
        forcaGabarito.innerHTML = '';
        messageDisplay.textContent = '';
        
        // 2. Selecionar Palavra e Tema
        const temas = Object.keys(palavrasPorTema);
        temaAtual = temas[Math.floor(Math.random() * temas.length)];
        const palavrasDoTema = palavrasPorTema[temaAtual];
        const palavraObj = palavrasDoTema[Math.floor(Math.random() * palavrasDoTema.length)];
        
        palavraSecreta = palavraObj.palavra;
        
        // 3. Atualizar UI
        temaDisplay.textContent = `${temaAtual} (Dica: ${palavraObj.dica})`;
        renderWordDisplay();
        renderKeyboard();
        updateHistoryTable();
    }

    /**
     * 2. Renderiza a palavra oculta no DOM.
     */
    function renderWordDisplay() {
        wordDisplay.innerHTML = palavraSecreta.split('').map(letra => {
            const displayLetra = letrasAdivinhadas.includes(letra) ? letra : '_';
            return `<span>${displayLetra}</span>`;
        }).join('');
    }

    /**
     * 3. Cria os botões do teclado virtual.
     */
    function renderKeyboard() {
        keyboardContainer.innerHTML = '';
        letrasAlfabeto.forEach(letra => {
            const button = document.createElement('button');
            button.classList.add('key-button');
            button.textContent = letra;
            button.setAttribute('data-letra', letra);
            button.addEventListener('click', () => handleGuess(letra, button));
            keyboardContainer.appendChild(button);
        });
    }

    /**
     * 4. Lida com o palpite de uma letra.
     */
    function handleGuess(letra, button) {
        if (!jogoAtivo || letrasAdivinhadas.includes(letra)) return;

        letrasAdivinhadas.push(letra);
        button.disabled = true;

        if (palavraSecreta.includes(letra)) {
            // Acertou
            button.classList.add('correct');
            renderWordDisplay();
            updateHistoryTable();
            checkGameStatus();
        } else {
            // Errou
            button.classList.add('incorrect');
            erros++;
            drawHangmanPart();
            updateHistoryTable();
            checkGameStatus();
        }
    }

    /**
     * 5. Adiciona uma parte do desenho da forca.
     */
    function drawHangmanPart() {
        if (erros > 0 && erros <= maxErros) {
            const partClass = partesDaForca[erros - 1];
            const partDiv = document.createElement('div');
            partDiv.classList.add(partClass);
            forcaGabarito.appendChild(partDiv);
        }
    }

    /**
     * 6. Atualiza a tabela de tentativas anteriores.
     */
    function updateHistoryTable() {
        // Filtra as letras erradas
        const letrasErradas = letrasAdivinhadas.filter(letra => !palavraSecreta.includes(letra));
        incorrectGuessesTable.textContent = letrasErradas.join(', ');

        // Filtra as letras corretas que JÁ FORAM exibidas na palavra
        const letrasCorretas = letrasAdivinhadas.filter(letra => palavraSecreta.includes(letra));
        correctGuessesTable.textContent = letrasCorretas.join(', ');
    }

    /**
     * 7. Verifica se o jogo terminou (vitória ou derrota).
     */
    function checkGameStatus() {
        const palavraAtual = palavraSecreta.split('').map(letra => letrasAdivinhadas.includes(letra) ? letra : '_').join('');

        if (palavraAtual === palavraSecreta) {
            // Vitória
            jogoAtivo = false;
            messageDisplay.textContent = '🎉 Parabéns! Você salvou o boneco!';
            messageDisplay.classList.remove('game-over');
            messageDisplay.classList.add('game-win');
            disableKeyboard();
        } else if (erros >= maxErros) {
            // Derrota
            jogoAtivo = false;
            messageDisplay.innerHTML = `💀 Fim de jogo! A palavra era: <strong>${palavraSecreta}</strong>`;
            messageDisplay.classList.remove('game-win');
            messageDisplay.classList.add('game-over');
            disableKeyboard();
        }
    }

    /**
     * 8. Desabilita todos os botões do teclado.
     */
    function disableKeyboard() {
        document.querySelectorAll('.key-button').forEach(button => {
            button.disabled = true;
        });
    }

    // =====================================
    // EVENT LISTENERS
    // =====================================

    restartButton.addEventListener('click', initializeGame);

    // Inicia o jogo quando a página carrega
    initializeGame();
});