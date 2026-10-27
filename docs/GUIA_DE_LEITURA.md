# Guia para compreender e apresentar o projeto

Este guia ajuda a estudar a implementação gerada com auxílio de IA. Não afirma que essa leitura pessoal já tenha sido feita.

## 1. Começar pelo comportamento

Executa a aplicação e percorre registo, entrada, um desafio, um resgate e o histórico. Experimenta também uma resposta errada e um brinde sem saldo. Depois atualiza a página e volta a entrar. A diferença entre estado local e dados persistidos fica mais clara quando se observa o comportamento.

## 2. Seguir um pedido de crédito

1. `Challenge.jsx` guarda o índice da resposta selecionada, sem alterar pontos.
2. `Dashboard.jsx` pede a operação ao hook `usePassport`.
3. `api.js` envia JSON e o token CSRF; a sessão segue num cookie HttpOnly.
4. `views.claim` verifica sessão, formato e eventual troca de conta.
5. `claim_points`, em `services.py`, verifica a resposta e abre uma transação.
6. A base atualiza saldo/revisão e cria o movimento. Se algo falhar, reverte ambos.
7. `snapshot` lê uma fotografia consistente; React apresenta o resultado recebido.

O mesmo desenho aplica-se ao resgate, com a condição adicional `balance >= cost` na própria atualização SQL.

## 3. Conseguir explicar as decisões

- **Porquê Django auth?** Para reutilizar hashing, sessões e validação mantidos pelo framework.
- **Porquê não calcular o saldo no React?** O navegador pode ser alterado pelo utilizador; só o servidor pode autorizar uma operação.
- **Porquê uma transação se há restrições?** A unicidade impede repetir o movimento, mas é a transação que impede deixar o saldo alterado quando a inserção falha.
- **Porquê uma expressão `F`?** A base faz o cálculo sobre o valor atual, em vez de guardar um resultado calculado a partir de uma leitura antiga.
- **Porquê revisão além de saldo?** O saldo pode voltar ao mesmo valor depois de crédito e débito; a revisão identifica a ordem das mudanças.
- **Porquê não repetir um pedido com erro de rede?** O servidor pode já ter confirmado a operação. Primeiro consulta-se o estado real.
- **Porquê SQLite?** Simplifica a instalação local; as escritas são serializadas e a solução tem limites de carga explícitos.
- **Porquê não JWT/localStorage?** Uma sessão de mesma origem resolve o requisito com menos mecanismos e sem guardar um token de autenticação acessível ao JavaScript.

## 4. Ler os testes como exemplos de regras

`tests.py` mostra o contrato principal. `test_security.py` cobre entradas adversas e proteção HTTP. `test_invariants.py` executa 2 000 operações pseudoaleatórias com um registo esperado independente. `test_migrations.py` verifica uma atualização com dados existentes. Os scripts em `tests/` acrescentam um navegador real, acessibilidade e concorrência HTTP.

Cobertura mede código executado; não demonstra ausência de erros. A documentação distingue testes unitários, percursos no navegador e ensaio de estabilidade.

## 5. Fazer uma alteração própria verificável

Uma forma de estudar o desenho é acrescentar um desafio com identificador novo em `catalog.py`, atualizar as instruções e criar um teste do seu crédito/repetição. Outra é mudar um brinde e verificar saldo insuficiente, confirmação e histórico. Mantém estáveis os identificadores de itens que já têm movimentos, para não transformar uma alteração de catálogo num segundo crédito.

Antes da submissão, descreve apenas as alterações e a revisão que efetivamente realizaste. Mantém o reconhecimento do auxílio de IA e adapta os comentários com uma explicação tua depois de compreender o código.
