# Código do instalador

O arranque nativo está em `main.go`. Não depende de Python ou de um interpretador de scripts no Windows. As entradas macOS e Linux só escolhem o binário correspondente. O bloqueio de ficheiro é fornecido pelo sistema operativo e é libertado mesmo que o processo termine inesperadamente.

`bootstrap.json` fixa a versão, os endereços e os hashes oficiais do uv. O arquivo é limitado em dimensão, verificado e apenas o executável esperado é extraído. O ambiente do filho não herda configurações uv/pip que possam redirecionar a instalação para outro Python. Os ambientes ficam em `.forum/`; não são alterados perfis de shell, registo Windows ou instalações globais.

Depois de preparar Python 3.12, o programa executa `runner.py`. Este verifica os requisitos, instala as versões em falta, consulta o plano de migração do Django e usa a API de backup SQLite antes de uma migração pendente. Em seguida abre o servidor apenas em loopback. O Python e o servidor são terminados de forma coordenada através da consola.

## Reproduzir a compilação

É necessário Go 1.25 ou superior para desenvolver o instalador. A entrega foi compilada com Go 1.27.3 e `CGO_ENABLED=0`, sem módulos Go externos.

Dentro desta pasta, por exemplo:

```sh
go test ./...
CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -trimpath -buildvcs=false -ldflags="-s -w" -o bin/forum-windows-amd64.exe .
CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -trimpath -buildvcs=false -ldflags="-s -w" -o bin/forum-darwin-arm64 .
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -buildvcs=false -ldflags="-s -w" -o bin/forum-linux-amd64 .
python test_runner.py -v
```

Repete a compilação para as seis combinações de `darwin/windows/linux` e `amd64/arm64`. Atualiza `BINARIOS-SHA256.json` depois de compilar. A licença do runtime Go está em `GO-LICENSE.txt`. O uv e o Python são descarregados dos respetivos projetos e conservam as suas licenças.

Os testes Go verificam hashes, HTTPS, extração, isolamento de configuração e bloqueio concorrente. Os testes Python verificam backup com WAL, portas ocupadas e versões de dependências. O relatório de instalação real está em `../docs/qa/installer-integration.json` e os limites em `../INSTALAR.md`.

Todo o código deste instalador foi criado com auxílio de IA; não é atribuído a uma contribuição humana não confirmada.
