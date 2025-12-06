// --- Echo_app/static/Echo_app/js/jogo_da_memoria.js ---

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('game-grid');
    const movesCounter = document.getElementById('moves-counter');
    const restartButton = document.getElementById('restart-button');

    // =========================================================
    // 🆕 NOVO CONTEÚDO: Caminhos para 8 Avatares
    // Assumindo que a pasta raiz 'static/avatars/' é acessível.
    // Usaremos os avatares de 1 a 8 como os pares.
    // =========================================================
    const avatarFiles = [
        'avatars1.png', 'avatars2.png', 'avatars3.png', 'avatars4.png', 
        'avatars5.png', 'avatars6.png', 'avatars7.png', 'avatars8.png'
    ];
    
    // Mapeia os nomes dos arquivos para os caminhos estáticos
    const imagePaths = avatarFiles.map(file => {
        // Usa o caminho relativo ao STATIC_ROOT/STATICFILES_DIRS
        return `/static/avatars/${file}`;
    });

    let cardsArray = [];
    let firstCard = null;
    let secondCard = null;
    let lockBoard = false;
    let moves = 0;
    let matches = 0;

    // Função para embaralhar um array (Algoritmo de Fisher-Yates)
    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // 1. Inicializa o Jogo
    function initializeGame() {
        // Cria 8 pares de caminhos de imagem e embaralha
        cardsArray = shuffle([...imagePaths, ...imagePaths]);
        
        // Limpa a grade e o contador
        grid.innerHTML = '';
        moves = 0;
        matches = 0;
        movesCounter.textContent = moves;

        // Cria e injeta as cartas no DOM
        cardsArray.forEach((imagePath, index) => {
            const cardElement = document.createElement('div');
            cardElement.classList.add('card');
            
            // Usamos o caminho da imagem como o atributo de comparação
            cardElement.setAttribute('data-image', imagePath);
            cardElement.setAttribute('data-index', index);

            // 🆕 ALTERAÇÃO AQUI: Usa <img> em vez de texto no card-front
            cardElement.innerHTML = `
                <div class="card-face card-front">
                    <img src="${imagePath}" alt="Avatar" style="width: 90%; height: 90%; object-fit: contain;">
                </div>
                <div class="card-face card-back"></div>
            `;

            cardElement.addEventListener('click', flipCard);
            grid.appendChild(cardElement);
        });
    }

    // 2. Lógica de Virar a Carta
    function flipCard() {
        if (lockBoard || this === firstCard || this.classList.contains('matched')) return;

        this.classList.add('flipped');

        if (!firstCard) {
            firstCard = this;
            return;
        }

        secondCard = this;
        lockBoard = true;
        
        moves++;
        movesCounter.textContent = moves;

        checkForMatch();
    }

    // 3. Verifica se as duas cartas viradas são um par
    function checkForMatch() {
        // 🆕 ALTERAÇÃO AQUI: Compara 'data-image' em vez de 'data-emoji'
        const isMatch = firstCard.getAttribute('data-image') === secondCard.getAttribute('data-image');
    
        isMatch ? disableCards() : unflipCards();
    }

    // 4. Ação: Par Encontrado (MANTÉM VIRADA + OPACIDADE REDUZIDA)
   function disableCards() {
        firstCard.removeEventListener('click', flipCard);
        secondCard.removeEventListener('click', flipCard);
    
        firstCard.classList.add('matched');
        secondCard.classList.add('matched');
    
        matches++;

        if (matches === imagePaths.length) {
            alert(`Parabéns! Você completou o jogo em ${moves} movimentos.`);
        }
    
        resetBoard(); 
    }

    // 5. Ação: Não é um Par
    function unflipCards() {
        grid.classList.add('locked'); 
    
        setTimeout(() => {
            firstCard.classList.remove('flipped');
            secondCard.classList.remove('flipped');
            
            grid.classList.remove('locked');
            resetBoard();
        }, 1500);
    }

    // 6. Reseta as Variáveis de Controle de Turno
    function resetBoard() {
        [firstCard, secondCard, lockBoard] = [null, null, false];
    }

    // 7. Event Listener para o Botão de Reiniciar
    restartButton.addEventListener('click', () => {
        grid.style.opacity = '0'; 
        setTimeout(() => {
            initializeGame();
            grid.style.opacity = '1';
        }, 300);
    });

    // Inicia o jogo quando a página carrega
    initializeGame();
});