package main

import (
	"os"
	"syscall"
	"unsafe"
)

var kernel = syscall.NewLazyDLL("kernel32.dll")

func installationLock(path string) (func(), error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return nil, err
	}
	overlapped := &syscall.Overlapped{}
	result, _, callErr := kernel.NewProc("LockFileEx").Call(file.Fd(), 3, 0, 1, 0, uintptr(unsafe.Pointer(overlapped)))
	if result == 0 {
		file.Close()
		return nil, callErr
	}
	return func() {
		kernel.NewProc("UnlockFileEx").Call(file.Fd(), 0, 1, 0, uintptr(unsafe.Pointer(overlapped)))
		file.Close()
	}, nil
}
func setupConsole() {
	kernel.NewProc("SetConsoleOutputCP").Call(65001)
	kernel.NewProc("SetConsoleCP").Call(65001)
}
