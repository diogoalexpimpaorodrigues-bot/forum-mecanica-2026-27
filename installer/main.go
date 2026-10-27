// Instalador nativo: prepara Python sem depender de uma instalação do sistema.
// Código e comentários criados com auxílio de IA; consultar AI_USAGE.md.
package main

import (
	"archive/tar"
	"archive/zip"
	"bufio"
	"compress/gzip"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// As versões e os hashes fazem parte do executável, em vez de serem obtidos
// de um endereço variável cada vez que alguém instala a aplicação.
//
//go:embed bootstrap.json
var bootstrapData []byte

type asset struct {
	URL    string `json:"url"`
	SHA256 string `json:"sha256"`
	Format string `json:"format"`
}
type bootstrap struct {
	Version string           `json:"version"`
	Targets map[string]asset `json:"targets"`
}
type uvRecord struct {
	Version string `json:"version"`
	SHA256  string `json:"sha256"`
}

var network = &http.Client{Timeout: 5 * time.Minute, CheckRedirect: func(r *http.Request, via []*http.Request) error {
	if r.URL.Scheme != "https" {
		return errors.New("o download tentou abandonar HTTPS")
	}
	if len(via) > 10 {
		return errors.New("demasiados redirecionamentos")
	}
	return nil
}}

func digest(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()
	h := sha256.New()
	if _, err = io.Copy(h, file); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func fetchAsset(item asset, destination string) error {
	parsed, err := url.Parse(item.URL)
	if err != nil || parsed.Scheme != "https" {
		return errors.New("endereço de download inválido")
	}
	response, err := network.Get(item.URL)
	if err != nil {
		return fmt.Errorf("não foi possível descarregar a ferramenta: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return fmt.Errorf("download recusado: HTTP %d", response.StatusCode)
	}
	file, err := os.OpenFile(destination, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	// Um limite explícito impede que uma resposta inesperada ocupe todo o disco.
	_, copyErr := io.Copy(file, io.LimitReader(response.Body, 64*1024*1024+1))
	closeErr := file.Close()
	if copyErr != nil {
		return copyErr
	}
	if closeErr != nil {
		return closeErr
	}
	info, err := os.Stat(destination)
	if err != nil {
		return err
	}
	if info.Size() > 64*1024*1024 {
		return errors.New("download demasiado grande")
	}
	actual, err := digest(destination)
	if err != nil {
		return err
	}
	if actual != item.SHA256 {
		return errors.New("o SHA-256 do download não corresponde à versão aprovada")
	}
	return nil
}

func copyExecutable(input io.Reader, destination string) error {
	file, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0700)
	if err != nil {
		return err
	}
	count, copyErr := io.Copy(file, io.LimitReader(input, 192*1024*1024+1))
	closeErr := file.Close()
	if copyErr != nil {
		return copyErr
	}
	if closeErr != nil {
		return closeErr
	}
	if count == 0 || count > 192*1024*1024 {
		return errors.New("executável com dimensão inválida")
	}
	return nil
}

func unpack(archivePath, format, destination, expected string) error {
	// Só lemos o executável esperado. Nenhum caminho vindo do arquivo é usado
	// como destino, pelo que entradas como ../../ficheiro não podem escapar.
	if format == "zip" {
		bundle, err := zip.OpenReader(archivePath)
		if err != nil {
			return err
		}
		defer bundle.Close()
		for _, entry := range bundle.File {
			if filepath.Base(entry.Name) != expected || !entry.Mode().IsRegular() {
				continue
			}
			input, err := entry.Open()
			if err != nil {
				return err
			}
			defer input.Close()
			return copyExecutable(input, destination)
		}
	} else if format == "tar.gz" {
		file, err := os.Open(archivePath)
		if err != nil {
			return err
		}
		defer file.Close()
		compressed, err := gzip.NewReader(file)
		if err != nil {
			return err
		}
		defer compressed.Close()
		bundle := tar.NewReader(compressed)
		for {
			entry, err := bundle.Next()
			if err == io.EOF {
				break
			}
			if err != nil {
				return err
			}
			if entry.Typeflag == tar.TypeReg && filepath.Base(entry.Name) == expected {
				return copyExecutable(bundle, destination)
			}
		}
	} else {
		return errors.New("formato de arquivo não suportado")
	}
	return errors.New("o arquivo não contém o executável esperado")
}

func prepareUV(root string, config bootstrap, item asset, offline bool, out io.Writer) (string, error) {
	name := "uv"
	if runtime.GOOS == "windows" {
		name += ".exe"
	}
	destination := filepath.Join(root, "bin", name)
	recordPath := filepath.Join(root, "uv.json")
	var record uvRecord
	if data, err := os.ReadFile(recordPath); err == nil && json.Unmarshal(data, &record) == nil && record.Version == config.Version {
		if sum, err := digest(destination); err == nil && sum == record.SHA256 {
			return destination, nil
		}
	}
	if offline {
		return "", errors.New("a ferramenta ainda não está instalada; a primeira instalação necessita de Internet")
	}
	fmt.Fprintln(out, "[1/4] A descarregar e verificar a ferramenta de instalação…")
	if err := os.MkdirAll(filepath.Dir(destination), 0700); err != nil {
		return "", err
	}
	archive, err := os.CreateTemp(root, "uv-download-*")
	if err != nil {
		return "", err
	}
	archive.Close()
	defer os.Remove(archive.Name())
	if err = fetchAsset(item, archive.Name()); err != nil {
		return "", err
	}
	temporary := destination + ".new"
	os.Remove(temporary)
	defer os.Remove(temporary)
	if err = unpack(archive.Name(), item.Format, temporary, name); err != nil {
		return "", err
	}
	os.Remove(destination)
	if err = os.Rename(temporary, destination); err != nil {
		return "", err
	}
	sum, err := digest(destination)
	if err != nil {
		return "", err
	}
	data, _ := json.MarshalIndent(uvRecord{config.Version, sum}, "", "  ")
	if err = os.WriteFile(recordPath, data, 0600); err != nil {
		return "", err
	}
	return destination, nil
}

func projectRoot(explicit string) (string, error) {
	if explicit != "" {
		absolute, err := filepath.Abs(explicit)
		if err != nil {
			return "", err
		}
		if validProject(absolute) {
			return absolute, nil
		}
		return "", errors.New("a pasta indicada não contém o projeto completo")
	}
	executable, err := os.Executable()
	if err != nil {
		return "", err
	}
	for dir := filepath.Dir(executable); ; dir = filepath.Dir(dir) {
		if validProject(dir) {
			return dir, nil
		}
		if filepath.Dir(dir) == dir {
			break
		}
	}
	return "", errors.New("extrai o ZIP completo antes de abrir o instalador; mantém as pastas juntas")
}
func validProject(root string) bool {
	for _, part := range []string{"backend/requirements.txt", "frontend/dist/index.html", "installer/runner.py"} {
		if info, err := os.Stat(filepath.Join(root, filepath.FromSlash(part))); err != nil || info.IsDir() {
			return false
		}
	}
	return true
}

func childEnvironment(root string) []string {
	var env []string
	for _, entry := range os.Environ() {
		name := strings.ToUpper(strings.SplitN(entry, "=", 2)[0])
		if strings.HasPrefix(name, "UV_") || strings.HasPrefix(name, "PIP_") || name == "PYTHONHOME" || name == "PYTHONPATH" || name == "VIRTUAL_ENV" || name == "CONDA_PREFIX" {
			continue
		}
		env = append(env, entry)
	}
	values := map[string]string{"UV_NO_CONFIG": "1", "UV_MANAGED_PYTHON": "1", "UV_PYTHON_INSTALL_DIR": filepath.Join(root, "python"), "UV_PYTHON_BIN_DIR": filepath.Join(root, "python-bin"), "UV_PYTHON_INSTALL_BIN": "false", "UV_PYTHON_NO_REGISTRY": "1", "UV_CACHE_DIR": filepath.Join(root, "cache"), "UV_NO_PROGRESS": "1", "UV_SYSTEM_CERTS": "true", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
	for key, value := range values {
		env = append(env, key+"="+value)
	}
	return env
}

func command(executable string, args []string, dir string, env []string, out io.Writer) error {
	cmd := exec.Command(executable, args...)
	cmd.Dir = dir
	cmd.Env = env
	cmd.Stdin = os.Stdin
	cmd.Stdout = out
	cmd.Stderr = out
	// O filho recebe Ctrl+C na mesma consola e pode terminar o Django com ordem.
	interrupts := make(chan os.Signal, 1)
	signal.Notify(interrupts, os.Interrupt)
	defer signal.Stop(interrupts)
	return cmd.Run()
}

func existingApplication(root string, noBrowser bool) bool {
	data, err := os.ReadFile(filepath.Join(root, "server.json"))
	if err != nil {
		return false
	}
	var state struct {
		URL string `json:"url"`
	}
	if json.Unmarshal(data, &state) != nil {
		return false
	}
	parsed, err := url.Parse(state.URL)
	if err != nil || parsed.Scheme != "http" || parsed.Hostname() != "127.0.0.1" {
		return false
	}
	client := http.Client{Timeout: 2 * time.Second}
	response, err := client.Get(state.URL)
	if err != nil {
		return false
	}
	defer response.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(response.Body, 1024*1024))
	if response.StatusCode != 200 || !strings.Contains(string(body), "Passaporte Fórum") {
		return false
	}
	fmt.Println("A aplicação já está aberta:", state.URL)
	if !noBrowser {
		openBrowser(state.URL)
	}
	return true
}

func openBrowser(address string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", address)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", address)
	default:
		cmd = exec.Command("xdg-open", address)
	}
	if err := cmd.Run(); err != nil {
		fmt.Println("Abre este endereço no navegador:", address)
	}
}

func run() error {
	rootFlag := flag.String("project", "", "Pasta do projeto")
	offline := flag.Bool("offline", false, "Usar apenas a instalação existente")
	installOnly := flag.Bool("install-only", false, "Instalar sem iniciar o servidor")
	noBrowser := flag.Bool("no-browser", false, "Não abrir o navegador")
	repair := flag.Bool("repair", false, "Recriar apenas o ambiente de execução")
	port := flag.Int("port", 8000, "Porta local preferida")
	flag.Parse()
	if *port < 1 || *port > 65535 {
		return errors.New("a porta deve estar entre 1 e 65535")
	}
	var config bootstrap
	if err := json.Unmarshal(bootstrapData, &config); err != nil {
		return err
	}
	item, ok := config.Targets[runtime.GOOS+"/"+runtime.GOARCH]
	if !ok {
		return errors.New("sistema ou arquitetura não suportados; consulta INSTALAR.md")
	}
	project, err := projectRoot(*rootFlag)
	if err != nil {
		return err
	}
	runtimeRoot := filepath.Join(project, ".forum")
	if err = os.MkdirAll(runtimeRoot, 0700); err != nil {
		return fmt.Errorf("extrai o projeto para uma pasta onde possas escrever: %w", err)
	}
	release, err := installationLock(filepath.Join(runtimeRoot, "installation.lock"))
	if err != nil {
		if existingApplication(runtimeRoot, *noBrowser) {
			return nil
		}
		return errors.New("outra instalação está em curso nesta pasta; aguarda que termine")
	}
	defer release()
	os.Remove(filepath.Join(runtimeRoot, "server.json"))
	defer os.Remove(filepath.Join(runtimeRoot, "server.json"))
	log, err := os.OpenFile(filepath.Join(runtimeRoot, "installation.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer log.Close()
	out := io.MultiWriter(os.Stdout, log)
	fmt.Fprintln(out, "\nFórum Mecânica — instalar e abrir\nPasta:", project)
	uv, err := prepareUV(runtimeRoot, config, item, *offline, out)
	if err != nil {
		return err
	}
	env := childEnvironment(runtimeRoot)
	venv := filepath.Join(runtimeRoot, "env")
	python := filepath.Join(venv, "bin", "python")
	if runtime.GOOS == "windows" {
		python = filepath.Join(venv, "Scripts", "python.exe")
	}
	probe := exec.Command(python, "-c", "import sqlite3, ssl, sys; assert sys.version_info[:2] == (3, 12)")
	probe.Env = env
	healthy := probe.Run() == nil
	if !healthy || *repair {
		if _, err = os.Stat(venv); err == nil {
			if err = os.Rename(venv, venv+".previous-"+time.Now().UTC().Format("20060102T150405.000000000")); err != nil {
				return err
			}
		}
		fmt.Fprintln(out, "[2/4] A preparar Python 3.12 num ambiente próprio…")
		args := []string{"venv", "--python", "3.12", "--managed-python"}
		if *offline {
			args = append(args, "--offline")
		}
		args = append(args, venv)
		if err = command(uv, args, project, env, out); err != nil {
			return fmt.Errorf("não foi possível preparar Python; confirma a ligação e os requisitos de INSTALAR.md: %w", err)
		}
	}
	args := []string{filepath.Join(project, "installer", "runner.py"), "--project", project, "--uv", uv, "--port", fmt.Sprint(*port)}
	if *offline {
		args = append(args, "--offline")
	}
	if *installOnly {
		args = append(args, "--install-only")
	}
	if *noBrowser {
		args = append(args, "--no-browser")
	}
	if err = command(python, args, project, env, out); err != nil {
		return fmt.Errorf("a preparação não terminou; consulta .forum/installation.log: %w", err)
	}
	return nil
}

func main() {
	setupConsole()
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "\nNão foi possível concluir:", err)
		if info, e := os.Stdin.Stat(); e == nil && info.Mode()&os.ModeCharDevice != 0 {
			fmt.Println("Carrega em Enter para fechar.")
			bufio.NewReader(os.Stdin).ReadString('\n')
		}
		os.Exit(1)
	}
}
