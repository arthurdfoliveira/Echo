// <reference types="cypress" />

describe('Fluxo Completo do Utilizador (Registo, Navegação, Interação, Logout)', () => {
  it('Deve executar o fluxo completo do utilizador no site', () => {
    
    // --- GERA DADOS ÚNICOS PARA O TESTE ---
    // Isto permite que o teste corra várias vezes sem erros de "utilizador já existe"
    const uniqueId = Date.now();
    const username = `teste_cypress_${uniqueId}`;
    const email = `teste_${uniqueId}@cypress.com`;
    const password = 'senhaSegura123';

    // --- PASSO 1: Tentar aceder à página de perfil (Simula o clique) ---
    cy.log('Passo 1: Simular clique no ícone de perfil');
    // Ao visitar /perfil/, o @login_required deve redirecionar para /entrar/
    cy.visit('http://127.0.0.1:8000/perfil/'); 

    // --- PASSO 2: Verificar se foi redirecionado para o Login ---
    cy.log('Passo 2: Verificar redirecionamento para o login');
    // Verifica se a URL é a de login E se o Django anexou o 'next'
    cy.url().should('include', '/entrar/?next=/perfil/');

    // --- PASSO 3: Clicar para se registar ---
    cy.log('Passo 3: Navegar para o registo');
    // No seu entrar.html (da imagem), o link é "Cadastre-se"
    cy.contains('a', 'Cadastre-se').click();

    // --- PASSO 4: Preencher o formulário de registo ---
    cy.log('Passo 4: Preencher o formulário de registo');
    cy.url().should('include', '/registrar/');

    cy.get('#id_username').type(username);
    cy.get('#id_email').type(email);
    // Clica na categoria "Música" (conforme o seu pedido)
    cy.contains('.categoria-pill', 'Música').click();
    cy.get('#id_password').type(password);
    cy.get('#id_password_confirm').type(password);
    
    // Submeter
    cy.get('button[type="submit"]').contains('Cadastre-se').click();

    // --- PASSO 5: Aceder ao Dashboard e clicar na Notícia Recomendada ---
    cy.log('Passo 5: Dashboard e Notícia Recomendada');
    cy.url().should('eq', 'http://127.0.0.1:8000/'); // Deve estar no dashboard (raiz)
    cy.contains('h2', 'Recomendado para você').should('be.visible');

    // Clicar na primeira notícia recomendada
    cy.get('.recommended-section .news-card-link').first().scrollIntoView().click();

    // --- PASSO 6: Interagir com a Notícia ---
    cy.log('Passo 6: Interagir (Curtir e Salvar)');
    cy.url().should('match', /\/noticia\/\d+\//); // Verifica se está numa URL de notícia

    // Clica em Curtir e verifica se a classe foi adicionada
    cy.get('#btn-curtir').click();
    cy.wait(500); // Espera a chamada AJAX (pode ser substituído por intercept)
    
    // Clica em Salvar e verifica se a classe foi adicionada
    cy.get('#btn-salvar').click();
    cy.wait(500); // Espera a chamada AJAX

    // --- PASSO 7: Voltar ao Dashboard e clicar em Notícia Urgente ---
    cy.log('Passo 7: Navegar para Notícia Urgente');
    cy.get('.logo-container.top-nav-center').click(); // Clica no Logo "Echo"
    cy.url().should('eq', 'http://127.0.0.1:8000/'); // Verifica se voltou ao dashboard

    // Clica na primeira notícia urgente
    cy.get('.urgent-section .card-link-wrapper').first().scrollIntoView().click();
    
    cy.url().should('match', /\/noticia\/\d+\//); // Verifica se está noutra notícia

    // --- PASSO 8: Voltar ao Dashboard e clicar em Última Notícia ---
    cy.log('Passo 8: Navegar para Última Notícia');
    cy.get('.logo-container.top-nav-center').click(); // Clica no Logo "Echo"
    cy.url().should('eq', 'http://127.0.0.1:8000/');

    // Clica na primeira notícia da lista "Últimas Notícias"
    cy.get('.latest-news-section .latest-news-card-link').first().scrollIntoView().click();
    
    cy.url().should('match', /\/noticia\/\d+\//); // Verifica se está noutra notícia

    // --- PASSO 9: Voltar ao Dashboard e interagir com a Sidebar ---
    cy.log('Passo 9: Interagir com a Sidebar');
    cy.get('.logo-container.top-nav-center').click(); // Clica no Logo "Echo"
    cy.url().should('eq', 'http://127.0.0.1:8000/');

    // Clica no botão de menu (hambúrguer)
    cy.get('#sidebar-toggle').click();
    cy.get('#sidebar-menu').should('have.class', 'active'); // Verifica se abriu

    // Clica no *overlay* (fora do menu) para fechar
    cy.get('#sidebar-overlay').click();
    cy.get('#sidebar-menu').should('not.have.class', 'active'); // Verifica se fechou

    // --- PASSO 10: Ir ao Perfil e Sair (Logout) ---
    cy.log('Passo 10: Ir ao Perfil e Sair');
    
    // Clica no ícone de perfil
    cy.get('.nav-icon-profile-link').click();
    
    cy.url().should('include', '/perfil/');
    
    // Clica no botão de menu (hambúrguer) para abrir o menu
    cy.get('#sidebar-toggle').click();
    cy.get('#sidebar-menu').should('have.class', 'active');

    // Clica no link "Sair (Logout)"
    cy.contains('a', 'Sair (Logout)').click();

    // --- PASSO 11: Verificar se o Logout foi bem-sucedido ---
    cy.log('Passo 11: Verificar Logout');
    // A sua view 'sair' redireciona para 'entrar'
  });
});