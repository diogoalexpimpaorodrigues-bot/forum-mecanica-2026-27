# Revisão 5.0 — instalador multiplataforma

- Seis executáveis nativos para Windows, macOS e Linux, em x64 e ARM64.
- Arranque sem Python previamente instalado, com downloads fixados e verificados.
- Ambiente de execução isolado em `.forum/`, sem alterações a ferramentas globais.
- Instalação de requisitos, migrações, backup SQLite antes de migrações pendentes e abertura do navegador.
- Reutilização do ambiente sem Internet e escolha de outra porta quando necessário.
- Código-fonte, testes, hashes e instruções incluídos; a execução efetivamente verificada foi macOS ARM64.

# Correção 4.0.1 — nome da marca

- O nome visível passa a “Fórum Mecânica”, com as iniciais maiúsculas, no cabeçalho e nos elementos de apresentação.
- A instalação local conserva a base SQLite existente; não existem alterações ao esquema nem aos dados.

# Revisão 4.0 — logótipo do Fórum

- Integra o PNG fornecido pelo utilizador, preservando todos os seus bytes, proporção, cores e fundo branco.
- Substitui o símbolo demonstrativo no cabeçalho e no ícone do separador; aplica a imagem também no passaporte, rodapé e brindes ilustrativos.
- Harmoniza página inicial, dashboard, estados e ilustrações com azul profundo e ciano.
- Identifica a origem do logótipo separadamente dos elementos criados com auxílio de IA.
- Atualiza fontes, compilação, capturas e documentação. A lógica de autenticação e pontos mantém-se.

# Revisão 3.0 — interface

- Nova página inicial com apresentação editorial, percurso em três etapas e área de acesso própria.
- Ilustração SVG original de uma vista explodida, com gradientes e anotações inspiradas em desenho técnico. É decorativa, sem pretensão de precisão para fabrico.
- Paleta de verde profundo, marfim e lima; hierarquia tipográfica e espaçamentos revistos.
- Cabeçalho com navegação real entre secções e rodapé com identidade consistente.
- Carteira, indicadores, navegação, catálogo e histórico alinhados com a nova direção visual.
- Composição adaptada a telemóvel, movimento reduzido respeitado e blocos sem deslocamento horizontal nas larguras verificadas.
- Auditoria da página inicial alargada às larguras 320, 390, 768 e 1440; agora são 12 vistas auditadas.
- Código React, estilos, compilação pronta a executar, capturas e documentação atualizados. As regras de autenticação, créditos e resgates mantêm a implementação da revisão 2.

# Revisão 2.0

Esta revisão corrige falhas encontradas depois da primeira entrega e aprofunda a verificação.

## Comportamento e segurança

- Limites de pedidos passam a ser persistentes e atómicos, antes do hashing, incluindo um orçamento global por IP.
- Pedidos malformados, tipos errados, JSON patológico, tamanho excessivo, CSRF e métodos errados têm respostas previsíveis.
- Erros de qualidade da palavra-passe são associados ao campo certo; palavras-passe apenas com espaços são rejeitadas.
- Uma troca de conta noutro separador é detetada antes de movimentar pontos.
- Fotografias consistentes e revisões monotónicas impedem que uma resposta antiga faça a interface regredir.
- Respostas perdidas são reconciliadas com o servidor; um débito não é reenviado automaticamente por falha de rede.
- Erros de resgate ficam dentro da confirmação, onde podem ser lidos e corrigidos.
- A recompilação do frontend com Django ligado deixa de servir referências a assets removidos.

## Experiência

- Tipografia maior, melhor contraste, foco visível e alvos de interação mais confortáveis.
- Ilustrações vetoriais próprias para os brindes.
- Explicações educativas guardadas nos desafios concluídos.
- Histórico com filtros, cópia de códigos completos e exportação CSV protegida contra interpretação de fórmulas.
- Confirmação mostra saldo atual, custo e saldo final.
- Navegação preserva a secção no URL e suporta voltar/avançar.
- Sincronização entre separadores e recuperação ao voltar a ter ligação.

## Execução e manutenção

- Arranque portátil com seleção de porta e erros mais úteis.
- Executor de testes que cria servidor e base descartáveis, sem alterar contas locais.
- Testes reais em Chromium, Firefox e WebKit; auditoria axe e ensaio prolongado de concorrência.
- Migração e teste de atualização a partir da primeira versão, preservando pontos e códigos.
- Documentação revista, reconhecimento explícito da utilização de IA e relatório com resultados medidos.
