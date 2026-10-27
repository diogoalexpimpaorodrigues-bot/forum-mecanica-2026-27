# Passaporte · Fórum Mecânica 2026/27

Uma WebApp de recrutamento com Django, React e SQLite. Cria uma conta sem email, resolve desafios de engenharia, recebe pontos e troca-os por brindes ilustrativos. A carteira, o histórico e a identificação da conta persistem no servidor.

![Página inicial](docs/screenshots/desktop-inicio.png)

## Instalação automática

Clona o repositório ou extrai todo o ZIP e abre **INSTALAR-WINDOWS.cmd**, **INSTALAR-MACOS.command** ou **INSTALAR-LINUX.sh**, consoante o sistema. O arranque nativo prepara Python e as bibliotecas numa pasta própria e abre o site. A primeira instalação necessita de Internet; não é necessário instalar Python ou Node manualmente. Consulta [INSTALAR.md](INSTALAR.md) para os sistemas suportados, funcionamento, dados e limites de verificação.

### Ao obter apenas o código pelo GitHub

O ZIP distribuído em **Releases** preserva as permissões dos instaladores. Se usares `git clone` ou **Code → Download ZIP**, prepara as permissões de execução antes do primeiro arranque em macOS ou Linux. Abre um terminal na raiz do projeto e executa:

```sh
chmod +x INSTALAR-MACOS.command INSTALAR-LINUX.sh installer/bin/forum-darwin-* installer/bin/forum-linux-*
```

No Windows, abre `INSTALAR-WINDOWS.cmd` depois de extrair todos os ficheiros.

## Base de dados e repositório

A estrutura da base de dados está no código dos modelos e nas migrações de `backend/core/migrations/`. Na primeira execução, o Django cria `backend/db.sqlite3` com as tabelas necessárias. Cada pessoa cria as suas próprias contas; os dados de uma instalação não são publicados no GitHub.

Os ambientes locais, as dependências instaladas, os ficheiros `.env` e as bases SQLite estão excluídos pelo `.gitignore`.

## Arranque manual — sem precisar de Node

Requisitos: **Python 3.10 a 3.14** (recomendado: 3.12), com `pip` e `venv`. Testado com Python 3.12.14. É necessária ligação à Internet para a instalação inicial de dependências. O funcionamento local não depende de serviços externos, imagens ou fontes remotas.

Extrai o ZIP e abre o terminal **dentro da pasta `forum-mecanica`**, onde está este README.

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python start.py
```

### Windows — PowerShell

Não é necessário alterar a política de execução do PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe start.py
```

Nos comandos seguintes, se estiveres no Windows sem ativar o ambiente, substitui `python` por `.\.venv\Scripts\python.exe`.

Abre **http://127.0.0.1:8000**. O script cria a base de dados e aplica as migrações automaticamente. Termina com `Ctrl+C`. Para voltar a executar, basta ativar o ambiente e executar `python start.py` (ou o último comando de Windows).

O ZIP inclui o frontend já compilado em `frontend/dist/` e o respetivo código-fonte. Não inclui contas reais, credenciais pessoais nem uma base de dados pré-preenchida. As palavras-passe dos testes são fictícias. Cria a tua própria conta na primeira utilização. O nome de utilizador funciona como identificador único (3 a 30 caracteres; as maiúsculas e minúsculas são diferentes); a palavra-passe exige pelo menos 10 caracteres e passa pelos validadores do Django. Não existe recuperação de conta por email.

Se a porta 8000 estiver ocupada, usa `python start.py --port 8001` e abre http://127.0.0.1:8001. Ajusta também o proxy do Vite se estiveres a desenvolver o frontend nessa porta.

**Atualizar uma instalação anterior:** termina o servidor, guarda uma cópia de `backend/db.sqlite3`, substitui o código e executa `python start.py`. As migrações preservam as contas, carteiras e movimentos. Os antigos contadores de login são substituídos pelo novo mecanismo de limitação. Nunca substituas a tua base de dados pela de outra pessoa.


## Percurso de demonstração — cerca de 3 minutos

1. Na página inicial, usa **Começar o meu percurso** e escolhe **Criar conta**, preenche o nome e confirma a palavra-passe. A entrada é automática.
2. No dashboard, confirma que o teu nome e o saldo de **0 pontos** estão visíveis.
3. No desafio de energia, experimenta responder “Carvão”: surge feedback e o saldo mantém-se. Escolhe “Vento”: recebes **80 pontos**.
4. Responde “Newton” no desafio de mecânica: o saldo passa a **180 pontos**. Cada desafio só pode creditar uma vez.
5. Na **Loja de brindes**, seleciona o pack de autocolantes. Podes cancelar sem alterar o saldo; ao confirmar, são debitados **80 pontos** e ficam **100 pontos**.
6. Em **Histórico**, consulta os créditos, o débito e o código único do resgate.
7. Atualiza a página, sai e volta a entrar: os pontos e movimentos continuam guardados.

Os três desafios atribuem no total 300 pontos. Os brindes custam 80, 180 e 250 pontos. Cada conta pode resgatar cada brinde uma vez e tem de escolher como gastar o saldo finito. Os desafios são educativos e repetíveis em caso de resposta errada; não comprovam presença num evento.

**Catálogo demonstrativo:** os brindes e códigos não dão direito a entrega física. Não existe stock real, compra, pagamento ou integração com serviços do Fórum.

## Desenvolvimento do frontend

Para alterar React ou voltar a compilar, instala **Node.js 24 LTS** (também é compatível com Node 22.12+) e npm.

```sh
cd frontend
npm ci
npm run dev
```

Num segundo terminal, mantém o backend em `127.0.0.1:8000`. Abre o endereço indicado pelo Vite, normalmente `http://127.0.0.1:5173`. O proxy encaminha `/api` para Django e mantém autenticação e CSRF na mesma origem.

Depois de alterar o frontend:

```sh
npm run build
```

O novo `dist/` substitui a versão servida por Django. Não edites os ficheiros compilados diretamente. O lockfile fixa as versões efetivas; usa `npm ci` para as reproduzir.

## Organização

```text
backend/
  config/           Configuração, rotas e WSGI
  core/
    catalog.py      Desafios, respostas e preços controlados pelo servidor
    models.py       Carteira, movimentos e orçamentos de pedidos
    views.py        Adaptação HTTP e autenticação
    services.py     Créditos, resgates e fotografia transacional
    http.py         Erros JSON, métodos e validação de pedidos
    throttling.py   Limites persistentes e atómicos
    middleware.py   Cache e cabeçalhos de segurança
    migrations/     Esquema reproduzível da base de dados
    tests.py        Testes de regras, validação e segurança
frontend/
  src/components/   Entrada, desafios, dashboard e confirmação
  src/api.js        HTTP, timeout e renovação segura de CSRF
  src/hooks/        Sessão, sincronização e reconciliação
  src/*.test.*      Testes da interface e do cliente HTTP
  dist/             Aplicação React compilada, pronta a servir
  package-lock.json Dependências reproduzíveis
start.py            Migrações e arranque local portátil
tests/              Executor isolado, três motores de navegador e ensaio prolongado
docs/               Arquitetura, testes e capturas reais
AI_USAGE.md         Reconhecimento e explicação do auxílio de IA
```

## Segurança e âmbito

As palavras-passe são guardadas com o mecanismo de hashing do Django; a sessão usa um cookie HttpOnly com SameSite=Lax e o Django valida CSRF em todas as mutações. Valores de pontos, preços, conta e saldo não são aceites como autoridade a partir do cliente. Créditos e resgates são transacionais, têm restrições de unicidade e não permitem saldo negativo. Os limites incluem todas as tentativas: cinco logins por combinação IP/nome, 60 logins por IP e dez registos por IP, numa janela de dez minutos. O orçamento é consumido antes do hashing e partilhado entre processos através de SQLite. A API não ativa CORS e os dados da sessão não ficam em localStorage. As respostas usam `no-store`; a página inclui CSP e bloqueia enquadramento em páginas de terceiros.

O arranque fornecido serve **uma demonstração local**, ligada apenas a `127.0.0.1`. Para exposição pública é necessário configurar HTTPS, um segredo aleatório no ambiente, `DJANGO_DEBUG=0`, hosts explícitos, um servidor WSGI e assets estáticos próprios, além de limites de tráfego no proxy. Com DEBUG desligado, o projeto recusa a chave local e marca os cookies como Secure. Não basta desligar DEBUG para transformar o servidor de desenvolvimento numa instalação de produção.

Limites deliberados: SQLite serializa escritas; o protótipo usa um catálogo pequeno e não tem administração, paginação, recuperação de palavras-passe, verificação de presenças nem entrega de brindes. Em carga elevada, um conflito de escrita pode devolver 503 para o utilizador tentar novamente. A limitação de login não substitui uma proteção global contra abuso ou ataques distribuídos; os contadores antigos e sessões expiradas podem ser removidos com `python backend/manage.py cleanup_expired`. Detalhes em [ARQUITETURA.md](docs/ARQUITETURA.md).

## Correspondência ao enunciado

| Requisito | Implementação |
|---|---|
| Python e Django | Backend Django 5.2 LTS |
| React nas páginas | Interface React 19 com componentes e estados |
| Registo/login/logout sem email | Username + palavra-passe, sessões Django |
| Contas persistentes | Modelos de autenticação Django e SQLite |
| Identificar conta autenticada | Nome no cabeçalho e saudação; `GET /api/session/` |
| Página inicial | `/`, com entrada e registo |
| Página de utilizador | `/dashboard`, protegida pela sessão da API |
| Funcionalidade útil | Desafios que creditam pontos, resgates que debitam e histórico |
| Aparência cuidada | Layout responsivo, confirmação, feedback e estados vazios |
| Identificar auxílio de IA e explicar código | AI_USAGE.md, comentários e identificação no rodapé |

O símbolo do Fórum é o PNG fornecido pelo utilizador, preservado sem alterações e identificado em `frontend/src/assets/README.md`. A composição tipográfica, os elementos geométricos e os objetos ilustrados foram construídos para esta demonstração com auxílio de IA. O logótipo recebido não é apresentado como criação da IA.

## Documentação complementar

- [Instalação automática e sistemas suportados](INSTALAR.md)
- [Código do instalador](installer/README.md)

- [Histórico das revisões](docs/ALTERACOES.md)
- [Arquitetura e decisões](docs/ARQUITETURA.md)
- [Guia para compreender o código](docs/GUIA_DE_LEITURA.md)
- [Relatório de testes](docs/TESTES.md)
