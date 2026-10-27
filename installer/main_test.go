package main

import (
	"archive/tar"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDownloadRejectsWrongChecksum(t *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("ficheiro inesperado")) }))
	defer server.Close()
	previous := network
	network = server.Client()
	defer func() { network = previous }()
	err := fetchAsset(asset{URL: server.URL, SHA256: strings.Repeat("0", 64)}, filepath.Join(t.TempDir(), "download"))
	if err == nil || !strings.Contains(err.Error(), "SHA-256") {
		t.Fatalf("checksum incorreto aceite: %v", err)
	}
}
func TestVerifiedDownloadAndHTTPS(t *testing.T) {
	content := []byte("arquivo aprovado")
	sum := sha256.Sum256(content)
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write(content) }))
	defer server.Close()
	previous := network
	network = server.Client()
	defer func() { network = previous }()
	destination := filepath.Join(t.TempDir(), "download")
	if err := fetchAsset(asset{URL: server.URL, SHA256: hex.EncodeToString(sum[:])}, destination); err != nil {
		t.Fatal(err)
	}
	if err := fetchAsset(asset{URL: "http://example.invalid/file"}, destination); err == nil {
		t.Fatal("HTTP inseguro aceite")
	}
}
func TestArchiveCannotChooseDestination(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "bundle.tar.gz")
	file, _ := os.Create(path)
	compressed := gzip.NewWriter(file)
	bundle := tar.NewWriter(compressed)
	for _, entry := range []struct{ name, content string }{{"../../outside", "não escrever"}, {"uv-target/uv", "executável esperado"}} {
		data := []byte(entry.content)
		bundle.WriteHeader(&tar.Header{Name: entry.name, Mode: 0755, Size: int64(len(data)), Typeflag: tar.TypeReg})
		bundle.Write(data)
	}
	bundle.Close()
	compressed.Close()
	file.Close()
	target := filepath.Join(dir, "uv")
	if err := unpack(path, "tar.gz", target, "uv"); err != nil {
		t.Fatal(err)
	}
	data, _ := os.ReadFile(target)
	if string(data) != "executável esperado" {
		t.Fatal("ficheiro errado extraído")
	}
	if _, err := os.Stat(filepath.Join(dir, "outside")); !os.IsNotExist(err) {
		t.Fatal("o arquivo escreveu um destino próprio")
	}
	if err := unpack(path, "tar.gz", filepath.Join(dir, "missing"), "outro"); err == nil {
		t.Fatal("ausência de executável aceite")
	}
}
func TestLockReleasesWithoutDeletingFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "lock")
	release, err := installationLock(path)
	if err != nil {
		t.Fatal(err)
	}
	if second, err := installationLock(path); err == nil {
		second()
		release()
		t.Fatal("duas instalações simultâneas aceites")
	}
	release()
	next, err := installationLock(path)
	if err != nil {
		t.Fatal(err)
	}
	next()
}
func TestEnvironmentIsLocal(t *testing.T) {
	t.Setenv("UV_SYSTEM_PYTHON", "true")
	t.Setenv("UV_INDEX_URL", "https://example.invalid")
	t.Setenv("PYTHONHOME", "outra pasta")
	env := strings.Join(childEnvironment(t.TempDir()), "\n")
	if strings.Contains(env, "UV_SYSTEM_PYTHON=") || strings.Contains(env, "UV_INDEX_URL=") || strings.Contains(env, "PYTHONHOME=") {
		t.Fatal("configuração externa herdada")
	}
	if !strings.Contains(env, "UV_MANAGED_PYTHON=1") || !strings.Contains(env, "UV_NO_CONFIG=1") {
		t.Fatal("isolamento em falta")
	}
}
func TestAllSixTargetsArePinned(t *testing.T) {
	var config bootstrap
	if err := json.Unmarshal(bootstrapData, &config); err != nil {
		t.Fatal(err)
	}
	if len(config.Targets) != 6 {
		t.Fatal("matriz de sistemas incompleta")
	}
	for target, item := range config.Targets {
		if !strings.HasPrefix(item.URL, "https://github.com/astral-sh/uv/releases/download/"+config.Version+"/") || len(item.SHA256) != 64 {
			t.Fatal("download não fixado", target)
		}
	}
}
