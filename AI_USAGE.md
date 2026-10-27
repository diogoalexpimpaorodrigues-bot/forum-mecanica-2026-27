# Reconhecimento transparente de auxílio de IA

Esta implementação foi **gerada e revista com o OpenAI Codex**, a pedido do utilizador. O auxílio de IA abrange a leitura do enunciado, a conceção da aplicação, o código Python/Django e React/CSS, os comentários, os testes, a execução de verificações e a documentação.

Os comentários são explicações técnicas redigidas com esse auxílio. **Não são apresentados como explicações pessoais já escritas pelo candidato, nem como prova de autoria exclusivamente humana.** Não foi inventado um nome de autor ou uma contribuição humana que não tenha sido confirmada.

A revisão visual 3.0 foi também concebida e implementada com auxílio de IA, incluindo a ilustração mecânica vetorial, a marca tipográfica demonstrativa, a composição das páginas e os textos. Não são recursos oficiais do Fórum. Não são utilizadas fotografias ou fontes descarregadas de terceiros.

Na revisão 4.0, o símbolo demonstrativo foi substituído pelo logótipo enviado pelo utilizador e a paleta passou para azuis e ciano. **O logótipo fornecido não foi gerado nem retocado pela IA**: o PNG foi copiado integralmente. A aplicação nas páginas, no ícone do separador e nos brindes ilustrativos foi feita com auxílio de IA. A origem do ficheiro e o seu hash estão em `frontend/src/assets/README.md`.

## O que o projeto faz e porquê

- Usa a autenticação do Django para reutilizar hashing, sessões, validação de palavras-passe e proteção CSRF, evitando implementar criptografia própria.
- Usa SQLite por ser suficiente para a demonstração e dispensar configuração de serviços externos.
- Guarda a carteira e o histórico no servidor. React recebe uma fotografia atualizada após cada operação, para não calcular saldo como se fosse uma fonte de verdade.
- Aceita apenas o identificador do desafio e o índice da resposta, ou o identificador do brinde. O servidor decide os montantes.
- Liga atualização de saldo e criação do movimento numa transação. Uma restrição de unicidade impede repetir o mesmo crédito/resgate, e um débito condicionado impede saldo negativo.
- Usa um catálogo pequeno, desafios autocontidos e brindes claramente ilustrativos, sem simular integrações reais com o Fórum.
- Inclui uma compilação React para permitir executar a entrega só com Python, mantendo os fontes e o lockfile para desenvolvimento.

## Antes da submissão

O candidato deve ler, executar e compreender o projeto, em especial `backend/core/views.py`, `backend/core/models.py`, `backend/core/services.py`, `frontend/src/hooks/usePassport.js` e `frontend/src/api.js`. Deve testar as regras, adaptar o que considerar apropriado e explicar pessoalmente as decisões durante a avaliação.

Se o enunciado pedir uma explicação própria em comentários, o candidato deverá acrescentar ou adaptar comentários **após compreender o código**, indicando de forma verdadeira o que alterou. A documentação atual não afirma que essa revisão pessoal já tenha ocorrido.

## Sugestão de declaração de utilização

> Recorri ao OpenAI Codex para apoiar a conceção e implementação deste projeto, incluindo código, comentários, testes e documentação. O projeto entregue identifica esse auxílio. As alterações e explicações pessoais que eu venha a acrescentar devem ser identificadas de acordo com o trabalho efetivamente realizado.

Esta sugestão não deve ser alterada para afirmar uma revisão ou contribuição que não tenha acontecido. Não existe garantia de ausência total de erros; as verificações efetivamente realizadas estão descritas em `docs/TESTES.md`.

## Instalador da revisão 5.0

O instalador nativo Go, o coordenador Python, os scripts de arranque por sistema, os testes e a documentação de instalação foram também concebidos e implementados com auxílio de IA. As ferramentas descarregadas (uv e distribuições Python) pertencem aos seus projetos de origem e não são apresentadas como criações deste trabalho. As versões e fontes são identificadas em `installer/bootstrap.json` e `INSTALAR.md`.
