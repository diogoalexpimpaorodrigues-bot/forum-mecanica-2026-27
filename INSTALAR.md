# Instalar e abrir o Fórum Mecânica

Extrai **todo o ZIP** para uma pasta tua, por exemplo Documentos. Mantém o projeto e a pasta `installer/` juntos.

| Sistema | Ficheiro a abrir |
|---|---|
| Windows 10/11 de 64 bits, x64 ou ARM64 | Duplo clique em **INSTALAR-WINDOWS.cmd** |
| macOS 13 ou posterior, Intel ou Apple Silicon | Duplo clique em **INSTALAR-MACOS.command** |
| Linux de 64 bits, x64 ou ARM64 | Executa **INSTALAR-LINUX.sh** num terminal |

No Linux, se o gestor de ficheiros abrir o script como texto, usa `sh INSTALAR-LINUX.sh` dentro da pasta do projeto. Os executáveis nativos estão em `installer/bin/`: há uma versão para cada sistema e arquitetura.

O instalador prepara Python 3.12, instala as dependências necessárias, cria ou atualiza a base de dados e abre o site no navegador. **Não é necessário ter Python ou Node previamente instalados.** O React segue compilado no ZIP e corre no navegador. O Node continua a ser necessário apenas para alterar e recompilar o frontend.

A primeira instalação precisa de Internet e de espaço livre para o ambiente e os downloads. A pasta tem de permitir escrita. Não são pedidos privilégios de administrador nem alterações às ferramentas globais.

## Utilizar depois de instalar

Volta a abrir o mesmo ficheiro para iniciar o site. Nas aberturas seguintes, se o ambiente estiver íntegro e os requisitos não tiverem mudado, o site pode arrancar sem Internet.

O endereço habitual é **http://127.0.0.1:8000**. Se a porta estiver ocupada, o instalador procura outra e abre o endereço correto. Mantém a consola aberta enquanto usas a aplicação e termina com **Ctrl+C**.

Se o Fórum já estiver a correr através deste instalador na mesma pasta, uma segunda abertura reutiliza o site existente. Não é criada uma segunda instalação em paralelo.

## Onde ficam os dados

- **`backend/db.sqlite3`**: contas, palavras-passe com hashing, saldos, movimentos e sessões. Não é apagado pelo instalador.
- **`.forum/`**: Python, ambiente de bibliotecas, ferramenta de instalação e cache específicos deste projeto.
- **`.forum/backups/`**: cópias SQLite criadas antes de aplicar migrações pendentes a uma base existente.
- **`.forum/installation.log`**: mensagens para diagnosticar uma falha de instalação ou arranque.

A base não contém contas pré-definidas. Cria a tua própria conta. Guarda a pasta do projeto e a base para manteres o teu progresso. Para atualizar uma instalação anterior, fecha o servidor, conserva `backend/db.sqlite3`, substitui o código e abre o novo instalador. Não copies uma base de outra pessoa por cima da tua.

## Opções de diagnóstico

Estas opções são aceites pelos três ficheiros de arranque:

- `--install-only`: instala e verifica a aplicação sem abrir o servidor.
- `--no-browser`: inicia o servidor e mostra o endereço sem abrir o navegador.
- `--port 8014`: escolhe a porta local preferida.
- `--offline`: impede novos downloads; necessita de uma instalação já preparada.
- `--repair`: recria o ambiente Python do projeto, preservando a base de dados. O ambiente anterior fica numa pasta `.forum/env.previous-*`.

Exemplo no macOS: `./INSTALAR-MACOS.command --install-only`.

## Compatibilidade e limites de verificação

Não existe um único formato de executável que funcione nativamente em todos os sistemas. Por isso esta entrega inclui **seis binários nativos** e três ficheiros de arranque que selecionam o correto. Não cobre sistemas de 32 bits, Android, iOS ou versões antigas dos sistemas operativos.

Os binários foram compilados para Windows, macOS e Linux nas arquiteturas x64 e ARM64. A instalação completa e o arranque foram efetivamente executados em **macOS ARM64**. Windows, Linux e macOS Intel necessitam ainda de validação nativa nesses ambientes; compilação não é o mesmo que teste de execução.

Em Linux, a compatibilidade final depende também da biblioteca C e da distribuição Python disponível para a máquina. A ferramenta uv usada no arranque é estática em Linux; o Python descarregado tem os seus próprios requisitos. Um ambiente sem interface gráfica pode usar `--no-browser` e abrir o endereço manualmente num navegador local.

Os executáveis deste projeto não têm assinatura comercial Microsoft nem notarização Apple. O sistema pode pedir confirmação antes de abrir um ficheiro descarregado. Respeita as regras de segurança do computador; o instalador não desativa proteções nem contorna restrições da organização.

## Origem das ferramentas

A ferramenta uv é descarregada do projeto Astral, numa versão fixada em `installer/bootstrap.json`. O executável verifica o SHA-256 do arquivo antes de o utilizar. O Python é preparado pelo uv a partir das distribuições `python-build-standalone`; as bibliotecas vêm do PyPI nas versões fixadas em `backend/requirements.txt`. O instalador não executa scripts remotos recebidos por uma sequência `curl | sh`.
