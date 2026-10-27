# Interface — revisão 4.0

A direção visual aproxima o projeto de um site de evento e dá continuidade entre a página pública e a área pessoal. Não inventa patrocinadores, datas de sessões, testemunhos ou números de participantes.

## Identidade

Azul profundo (`#123652`) para estrutura e ações, branco azulado (`#f4f8fb`) para leitura e ciano claro (`#83dcfa`) para destaque. As cores acompanham o logótipo fornecido pelo utilizador. A tipografia combina a família sans-serif do sistema com Georgia em apontamentos editoriais. Não são necessárias fontes ou imagens remotas.

O símbolo da marca é o PNG enviado pelo utilizador, sem redesenho, filtros, recoloração ou remoção de fundo. O fundo branco é preservado num suporte próprio; as dimensões mantêm a proporção original. O ficheiro também é usado no ícone do separador e aplicado aos brindes demonstrativos. Não depende de recursos remotos. A origem e o hash estão em `frontend/src/assets/README.md`.

`MechanismArt.jsx` desenha uma vista explodida com SVG, incluindo anéis, dentes, gradientes e linhas de chamada. `useId` evita colisões entre os identificadores dos gradientes. A peça não é um desenho técnico de fabrico. O cartão de passaporte e os objetos dos brindes são ilustrações próprias, criadas com auxílio de IA e descritas em `AI_USAGE.md`. O logótipo aplicado não foi criado pela IA.

## Percurso

A página inicial apresenta a experiência, explica as três etapas e conduz ao formulário através de ligações para secções existentes. A autenticação conserva a validação e o feedback junto dos campos.

Na área pessoal, a carteira recebe mais destaque, os indicadores resumem o progresso e a navegação agrupa desafios, brindes e histórico. O catálogo usa fundos ligeiramente diferentes para distinguir os produtos. As explicações dos desafios e a confirmação de saldo continuam disponíveis.

## Responsividade e acessibilidade

A composição passa de duas colunas para uma; a área pessoal reorganiza os indicadores e os cartões. A ilustração é fluida e decorativa. As animações são breves e desativadas quando o sistema pede movimento reduzido. Os controlos mantêm estados visíveis e alvos de toque confortáveis.

Mantêm-se títulos semânticos, legendas, ligação para saltar conteúdo, foco visível e gestão de foco nos formulários e no diálogo. A auditoria axe verifica regras selecionadas WCAG 2 A/AA e 2.1 AA. Isto não equivale a certificação WCAG.

As capturas de computador e telemóvel estão em `screenshots/`. Os resultados e os limites da verificação estão em `TESTES.md`.
