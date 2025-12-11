// --- Echo_app/static/Echo_app/js/jogo_da_forca.js ---

document.addEventListener('DOMContentLoaded', () => {
    // =====================================
    // FUNÇÃO DE NORMALIZAÇÃO CRÍTICA (CORREÇÃO)
    // =====================================

    /**
     * Remove acentos e substitui Ç por C para fins de comparação no jogo.
     * @param {string} str - A string a ser normalizada.
     * @returns {string} A string normalizada em MAIÚSCULAS.
     */
    function normalizarString(str) {
        if (!str) return '';
        // 1. Garante que está em maiúsculas
        str = str.toUpperCase();
        
        // 2. Remove acentos e diacríticos (caracteres especiais como ^, ~, `)
        // Isso transforma Á em A, Ã em A, etc.
        str = str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

        // 3. Trata o Ç, pois o NFD não o transforma em C
        str = str.replace(/Ç/g, "C");
        
        return str;
    }

    // =====================================
    // DADOS DO JOGO
    // =====================================
    const palavrasPorTema = {
        'Esportes': [
            // Agora com acentos (VÔLEI) e cedilha (NATAÇÃO) para teste!
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

    // =====================================
    // ELEMENTOS DO DOM E ESTADO
    // =====================================
    let palavraSecreta = '';
    let palavraNormalizada = ''; // Novo: Versão normalizada para comparação rápida
    let temaAtual = '';
    let dicaAtual = '';
    let letrasAdivinhadas = []; // Armazena as letras clicadas (sempre normais: A, C, O, etc.)
    let erros = 0;
    const maxErros = 8;
    let jogoAtivo = true;

    // Elementos DOM
    const wordDisplay = document.getElementById('word-display');
    const keyboardContainer = document.getElementById('keyboard-container');
    const hangmanImage = document.getElementById('hangman-image'); 
    const messageDisplay = document.getElementById('message-display');
    const incorrectGuessesTable = document.getElementById('incorrect-guesses');
    const correctGuessesTable = document.getElementById('correct-guesses-table');
    const errosCountDisplay = document.getElementById('erros-count'); 
    const restartButton = document.getElementById('restart-button');
    
    // NOVOS ELEMENTOS PARA TEMA E DICA
    const showHintButton = document.getElementById('show-hint-button');
    const hintTextContainer = document.getElementById('hint-text');
    const temaDisplayWord = document.getElementById('tema-display-word');
    const temaDisplayHint = document.getElementById('tema-display-hint');
    
    // Verifica se a variável STATIC_IMAGE_PATH (definida no HTML) existe
    if (typeof STATIC_IMAGE_PATH === 'undefined') {
        console.error("A variável STATIC_IMAGE_PATH não está definida no HTML. O jogo não funcionará corretamente.");
        return; 
    }

    // =====================================
    // FUNÇÕES DE LÓGICA
    // =====================================

    /**
     * Inicializa um novo jogo.
     */
    function initializeGame() {
        letrasAdivinhadas = [];
        erros = 0;
        jogoAtivo = true;
        messageDisplay.textContent = '';
        messageDisplay.classList.remove('game-over', 'game-win');

        hangmanImage.src = `${STATIC_IMAGE_PATH}forca1.jpeg`;

        // Seleciona tema e palavra aleatória
        const temas = Object.keys(palavrasPorTema);
        temaAtual = temas[Math.floor(Math.random() * temas.length)];
        const palavrasDoTema = palavrasPorTema[temaAtual];
        const palavraObj = palavrasDoTema[Math.floor(Math.random() * palavrasDoTema.length)];

        palavraSecreta = palavraObj.palavra; // Ex: 'NATAÇÃO'
        palavraNormalizada = normalizarString(palavraSecreta); // Ex: 'NATACAO'
        dicaAtual = palavraObj.dica;

        // Atualiza UI
        temaDisplayWord.textContent = temaAtual;
        temaDisplayHint.textContent = dicaAtual;
        hintTextContainer.classList.remove('visible');
        showHintButton.disabled = false;
        
        renderWordDisplay();
        renderKeyboard();
        updateHistoryTable();
    }

    /**
     * Renderiza a palavra oculta no DOM.
     */
    function renderWordDisplay() {
        // Itera sobre a PALAVRA SECRETA ORIGINAL ('NATAÇÃO')
        wordDisplay.innerHTML = palavraSecreta.split('').map(letra => {
            // Verifica se a letra original, quando normalizada, já foi adivinhada
            const letraNormalizada = normalizarString(letra);
            
            // Se a letra normalizada (A, C, O) estiver entre as adivinhadas (letrasAdivinhadas),
            // exibe a letra original ('Ã', 'Ç', 'Õ').
            const displayLetra = letrasAdivinhadas.includes(letraNormalizada) ? letra : '_';
            
            return `<span>${displayLetra}</span>`;
        }).join('');
    }

    /**
     * Cria os botões do teclado virtual.
     */
    function renderKeyboard() {
        keyboardContainer.innerHTML = '';
        letrasAlfabeto.forEach(letra => {
            const button = document.createElement('button');
            button.classList.add('key-button');
            button.textContent = letra;
            button.setAttribute('data-letra', letra);
            button.addEventListener('click', () => handleGuess(letra, button));
            
            // O botão é desabilitado se a letra (normalizada) já foi clicada
            button.disabled = letrasAdivinhadas.includes(letra);
            
            keyboardContainer.appendChild(button);
        });
    }

    /**
     * Lida com o palpite de uma letra.
     */
    function handleGuess(letra, button) {
        // A letra é a tentativa (sempre A-Z), ex: 'C'
        if (!jogoAtivo || letrasAdivinhadas.includes(letra)) return;

        letrasAdivinhadas.push(letra); // Adiciona a letra normal (C) às adivinhadas
        button.disabled = true;

        // ✅ CORREÇÃO: Verifica se a PALAVRA NORMALIZADA contém a letra normal (C)
        if (palavraNormalizada.includes(letra)) {
            // Acertou
            button.classList.add('correct');
            renderWordDisplay(); // Redesenha a palavra
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
     * Desenha as partes da forca conforme número de erros (Muda a imagem JPEG).
     */
    function drawHangmanPart() {
        if (erros > 0 && erros <= maxErros) {
             hangmanImage.src = `${STATIC_IMAGE_PATH}forca${erros}.jpeg`;
        }
        
        errosCountDisplay.textContent = `${erros}`;
    }

    /**
     * Exibe a dica e desabilita o botão de lâmpada.
     */
    function showHint() {
        if (!showHintButton.disabled) {
            hintTextContainer.classList.add('visible');
            showHintButton.disabled = true;
        }
    }

    /**
     * Atualiza a tabela de tentativas anteriores.
     */
    function updateHistoryTable() {
        // ✅ CORREÇÃO: Filtra as letras erradas e corretas com base na PALAVRA NORMALIZADA
        const letrasErradas = letrasAdivinhadas.filter(letra => !palavraNormalizada.includes(letra));
        incorrectGuessesTable.textContent = letrasErradas.join(', ');

        const letrasCorretas = letrasAdivinhadas.filter(letra => palavraNormalizada.includes(letra));
        correctGuessesTable.textContent = letrasCorretas.join(', ');
        
        errosCountDisplay.textContent = `${erros}`; 
    }

    /**
     * Verifica se o jogo terminou (vitória ou derrota).
     */
    function checkGameStatus() {
        // ✅ CORREÇÃO: Verifica a vitória comparando a PALAVRA NORMALIZADA
        const palavraAdivinhadaNormalizada = palavraNormalizada.split('').map(letraNormal => {
            return letrasAdivinhadas.includes(letraNormal) ? letraNormal : '_';
        }).join('');

        if (palavraAdivinhadaNormalizada === palavraNormalizada) {
            jogoAtivo = false;
            messageDisplay.textContent = '🎉 Parabéns! Você salvou o boneco!';
            messageDisplay.classList.remove('game-over');
            messageDisplay.classList.add('game-win');
            disableKeyboard();
            showHintButton.disabled = true;
            hintTextContainer.classList.add('visible');
        } else if (erros >= maxErros) {
            jogoAtivo = false;
            messageDisplay.innerHTML = `Fim de jogo! A palavra era: <strong>${palavraSecreta}</strong>`;
            messageDisplay.classList.remove('game-win');
            messageDisplay.classList.add('game-over');
            disableKeyboard();
            showHintButton.disabled = true;
            hintTextContainer.classList.add('visible');

            hangmanImage.src = `${STATIC_IMAGE_PATH}forca${maxErros}.jpeg`;
        }
    }

    /**
     * Desabilita todos os botões do teclado.
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
    showHintButton.addEventListener('click', showHint);

    // Adiciona listener para teclado físico
    document.addEventListener('keydown', (event) => {
        const key = event.key.toUpperCase();
        if (letrasAlfabeto.includes(key) && jogoAtivo) {
            const button = document.querySelector(`.key-button[data-letra="${key}"]`);
            if (button && !button.disabled) {
                // Simula o clique do botão para acionar a mesma lógica
                handleGuess(key, button);
            }
        }
    });

    // Inicia o jogo
    initializeGame();
});