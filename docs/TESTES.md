# Relatório de verificação — revisão 5.0 e histórico

Verificação realizada em 26 de outubro de 2026, em macOS ARM64: Python 3.12.14, Django 5.2.18, Node.js 24.22.1, React 19.2.0 e Playwright 1.64.1. Os resultados abaixo pertencem aos cenários executados, não a uma garantia de ausência total de erros.

## Instalador 5.0 — 27 de outubro de 2026

Foram aprovados seis testes Go e três testes Python do instalador: rejeição de hashes errados e HTTP não cifrado, download aprovado, extração limitada ao executável, bloqueio concorrente, configuração isolada, matriz de plataformas, backup de dados confirmados em WAL, porta ocupada e rejeição de versões de bibliotecas divergentes.

A instalação completa foi executada numa cópia sem ambiente, numa pasta com espaços e caracteres acentuados, em macOS ARM64. O arranque usou Python gerido **3.12.16**, descarregado automaticamente; não usou o Python 3.9 do sistema nem o ambiente de desenvolvimento anterior. Os **57 testes Django passaram também nesse Python instalado**.

O ensaio verificou: criação da base, dependências, cópia de segurança antes de uma migração pendente, preservação de uma conta com pontos, reparação e arranque sem rede, escolha de porta alternativa, segunda abertura sem duplicar servidor e paragem com Ctrl+C. O resultado está em `qa/installer-integration.json`.

Os seis binários Windows/macOS/Linux em x64/ARM64 foram compilados e os formatos PE, Mach-O e ELF inspecionados. Os binários Linux são estáticos. **Só macOS ARM64 foi executado nativamente**; não se apresenta a compilação dos restantes como teste de funcionamento nesses sistemas. Os hashes estão em `installer/BINARIOS-SHA256.json`.

A interface e a lógica do site não foram alteradas nesta revisão; as verificações React e de navegadores abaixo pertencem às revisões indicadas.

## Marca e paleta 4.0 — 27 de outubro de 2026

Após integrar o logótipo e adaptar a paleta, passaram os **37 testes React**, o percurso completo em Chromium em computador e telemóvel, as **12 auditorias axe** nas larguras 320/390/768/1440, os ensaios de teclado/rede/sessão e o teste HTTP concorrente. A verificação confirma também que a imagem do cabeçalho carrega com a resolução original e que o PNG servido no site e no favicon corresponde, byte a byte, ao ficheiro recebido.

As capturas foram atualizadas. Os testes Python, os percursos Firefox/WebKit e as medições de cobertura abaixo pertencem às revisões anteriores e não foram repetidos por esta alteração de marca; a lógica de autenticação e de pontos não mudou. O relatório específico está em `qa/branding-v4.json`. A entrega 4.0 foi também extraída e executada com uma base temporária, sem Node, conforme `qa/clean-install.json`.

## Revisão visual 3.0 — 27 de outubro de 2026

Após o redesenho foram repetidos os 57 testes Django e os 37 testes React, os percursos completos em Chromium, Firefox e WebKit (computador e telemóvel), a auditoria axe, as verificações de teclado/rede/sincronização e o teste HTTP concorrente. Todos passaram. A auditoria tem agora **12 vistas**, incluindo a página inicial em 320/390/768/1440 píxeis. ESLint, Prettier e a compilação também foram verificados.

A cobertura dos módulos carregados pela suite Vitest foi novamente medida: **90,22% de linhas, 88,52% de instruções e 78,40% de ramos**. Esta medição não inclui cobertura de CSS e não substitui a inspeção visual; as ilustrações e a apresentação são verificadas também no navegador. O resumo atual está em `qa/frontend-coverage.json`.

A entrega 3.0 foi extraída para outra pasta e executada sem Node, num ambiente Python isolado já instalado e com uma base nova. Aplicou as migrações, serviu a nova compilação e passou o teste HTTP concorrente; os hashes da entrega foram confirmados. O resultado da revisão 3.0 está em `qa/clean-install-v3.json`.

Os ensaios prolongados, as regressões deliberadas, a cobertura Python e as auditorias de dependências abaixo pertencem à revisão 2.0. Não foram repetidos por esta alteração de apresentação; as dependências e a lógica Python mantêm-se. As capturas e os relatórios dos navegadores foram atualizados.

## Resultado resumido da revisão 2.0

| Verificação | Resultado |
|---|---|
| Django: regras, autenticação, segurança, invariantes e migração | **57 testes aprovados** |
| React/Vitest: interação, formulários, HTTP e recuperação | **37 testes aprovados** |
| Sequências pseudoaleatórias | 20 sequências de 100 operações, com registo esperado independente |
| Percurso completo em Chromium | Computador e telemóvel aprovados |
| Percurso completo em Firefox | Computador e telemóvel aprovados |
| Percurso completo em WebKit | Computador e telemóvel aprovados |
| axe-core: regras WCAG 2 A/AA e 2.1 AA selecionadas | 9 vistas sem violações detetadas |
| Ensaio de estabilidade de pontos | 20 minutos, 4 trabalhadores, 16 contas, **34 862 pedidos** |
| Regressões deliberadas em cópias descartáveis | As 4 foram detetadas pelos testes |
| Auditoria de dependências npm e Python de execução | Nenhuma vulnerabilidade conhecida reportada na execução |
| Ruff, ESLint, Prettier e compilação Vite | Aprovados |
| Migrações e atualização a partir da versão inicial | Aprovadas |
| Instalação limpa a partir do ZIP | Python novo, migrações, assets e API aprovados |

São **94 casos automatizados nas suites unitárias/integradas**, além dos percursos reais de navegador, sequências e ensaios descritos. Não se somam os 2 000 passos pseudoaleatórios ou os pedidos de estabilidade como se fossem casos unitários independentes.

## Cobertura medida

A lógica Python de `core` medida pelo coverage.py atingiu 100% de instruções e ramos no conjunto executado. Esta medição exclui migrações, ficheiros de teste e comandos de gestão; os testes de migração e limpeza foram executados separadamente dentro da suite.

Na revisão 2.0, o frontend atingiu 89,70% de linhas, 87,96% de instruções e 77,74% de ramos na suite Vitest. O resumo frontend foi substituído pela medição da revisão 3.0 indicada acima. O percurso de navegador exercita ainda fluxos visuais, como a loja, sem ser somado à medição unitária. As métricas estão em `qa/backend-coverage.json` e `qa/frontend-coverage.json`.

Cobertura diz que código foi executado. Não demonstra que todas as condições possíveis ou todos os erros foram descobertos.

## Regras e segurança

Os testes cobrem registo sem email, hashing, validação e confirmação de palavra-passe, rejeição de palavras-passe só com espaços, normalização consistente de nomes, conta inativa, sessão, logout idempotente, rotação de sessão e orçamentos de pedidos.

Também verificam CSRF/origem, formato e dimensão do corpo, JSON inválido ou excessivamente aninhado, tipos incorretos, ausência de campos, respostas ocultas, métodos HTTP, rotas incompletas, proteção do caminho dos assets, cache e indisponibilidade temporária da base.

Para os pontos, verificam resposta errada, crédito, repetição, preços controlados pelo servidor, saldo insuficiente, débito, rollback se o movimento falhar, sinais impostos pela base, isolamento entre contas, guarda contra troca de conta e revisão monotónica.

As 20 sequências pseudoaleatórias com sementes fixas executam 2 000 operações. Depois de cada passo, comparam saldo, revisão e histórico com um registo esperado independente. O teste de atualização cria uma conta na versão inicial, migra-a e confirma palavra-passe, saldo, movimentos e código de resgate.

## Navegadores e acessibilidade

Os motores automatizados foram Chromium, Firefox e WebKit, em 1440 × 1000 e 390 × 844. O WebKit automatizado não é uma execução da aplicação Safari instalada, nem substitui testes em dispositivos físicos.

O percurso inclui registo, erro/correção de resposta, dois créditos, cancelamento de resgate, confirmação, débito, código, atualização da página, concorrência, logout e novo login. Não ocorreram erros JavaScript de página nesses percursos.

A auditoria adicional em Chromium cobre entrada, registo com erros, desafios a 320/390/768/1440 píxeis, loja, confirmação e histórico filtrado. Verifica atalho de conteúdo, foco de campos, navegação no diálogo e devolução de foco. A interface foi também inspecionada visualmente nas capturas em `screenshots/`.

O ensaio simula uma resposta de resgate perdida **depois** da confirmação no servidor: o cliente reconcilia o estado, mostra um único débito e não repete o POST. Simula também ausência de ligação, erro visível dentro do modal, cópia de código, exportação CSV e logout propagado entre separadores. `qa/accessibility.json` contém o resultado das nove vistas.

Isto não é uma certificação WCAG nem uma auditoria completa de utilização com leitores de ecrã.

## Estabilidade e concorrência

O ensaio prolongado correu 1 201,09 segundos numa base SQLite descartável, com quatro trabalhadores e 16 contas. Foram efetuados 34 862 pedidos: 8 789 respostas 200 e 26 073 conflitos 409 esperados em operações repetidas ou sem saldo. Não houve respostas 500, violações de saldo, movimentos duplicados ou mistura de contas.

Em cada resposta de estado aceita, foram verificadas as invariantes: saldo não negativo, saldo igual à soma do histórico, referências únicas por tipo e carteira, revisão igual ao número de movimentos e identificação correta da conta. No fim, todas as carteiras foram reconciliadas de novo.

O relatório regista latência mediana de 7,11 ms e percentil 95 de 11,78 ms. Estes valores descrevem este computador, este tráfego controlado e um perfil com muitos conflitos esperados. **Não são uma estimativa de capacidade em produção.** O ensaio usa sessões de teste já criadas e não mede throughput de hashing/registo/login.

O teste HTTP curto envia ainda quatro créditos simultâneos para o mesmo desafio e dois resgates cujo custo conjunto excede o saldo: aceita exatamente um crédito e um resgate, preservando o histórico. Os resultados estão em `qa/soak.json` e nos relatórios dos executores.

## Testes que falham quando devem

Em quatro cópias descartáveis, introduziram-se regressões deliberadas: aceitar uma resposta errada, retirar as transações, ignorar a troca de conta e inflacionar um crédito. Os testes selecionados detetaram as quatro regressões. A entrega não inclui essas alterações; `qa/mutations.json` regista os testes usados.

## Reproduzir e interpretar os limites

Segue os comandos no README ou usa `python verify.py --browser`, depois de instalar as dependências de desenvolvimento e os browsers. O executor de navegador cria uma porta e uma base temporárias, terminando o servidor e removendo os dados no fim.

Não houve ensaio nativo de Windows/Linux, teste em dispositivos móveis físicos, auditoria externa de segurança ou integração com serviços reais. As instruções e os scripts usam APIs portáveis, mas só o ambiente acima foi executado. As auditorias de dependências refletem o resultado à data da verificação.

## Entrega limpa

O ZIP foi extraído para outra pasta e as dependências de execução foram instaladas num ambiente Python novo. O arranque foi verificado antes de existir `frontend/node_modules`: criou a base, aplicou migrações, serviu HTML/JS/CSS e passou o teste HTTP concorrente. Os hashes dos ficheiros originais da entrega foram confirmados. O resultado dessa instalação da revisão 2.0 está em `qa/clean-install-v2.json`. Depois foi instalada a árvore Node pelo lockfile e repetida a verificação geral nessa cópia.
