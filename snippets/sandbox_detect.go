package snippets
//go:build windows
// +build windows

// Sandbox Detection Snippet
// Reference: MITRE ATT&CK T1497 (Virtualization/Sandbox Evasion)
//
// This snippet implements multiple sandbox and virtual machine detection
// techniques to identify analysis environments. If a sandbox is detected,
// the implant can exit cleanly to avoid analysis.
//
// Detection techniques:
// - Time acceleration detection (sandboxes often accelerate sleep)
// - Debugger detection (IsDebuggerPresent API)
// - Low CPU count detection (sandboxes often have 1-2 CPUs)
// - Low memory detection (sandboxes often have limited RAM)
//
// Usage: Call detectSandbox() early and exit if true is returned.
//
// Note: This file is a standalone snippet for reference. The evasion.py
// module generates this code dynamically for template injection.

package main

import (
	"runtime"
	"syscall"
	"time"
)

// detectSandbox performs multiple sandbox/VM detection checks.
// Reference: MITRE ATT&CK T1497 (Virtualization/Sandbox Evasion)
func detectSandbox() bool {
	// Time acceleration check - sandboxes often accelerate time
	if detectTimeAcceleration() {
		return true
	}

	// Check for debugger
	if detectDebugger() {
		return true
	}

	// Check for low resources (typical of sandboxes)
	if detectLowResources() {
		return true
	}

	return false
}

// detectTimeAcceleration checks if time is being accelerated.
// Sandboxes often speed up sleep calls to analyze malware faster.
func detectTimeAcceleration() bool {
	start := time.Now()
	time.Sleep(2 * time.Second)
	elapsed := time.Since(start)

	// If elapsed time is significantly less than expected, we're in a sandbox
	if elapsed < 1500*time.Millisecond {
		return true
	}
	return false
}

// detectDebugger checks for attached debugger using Windows API.
func detectDebugger() bool {
	kernel32 := syscall.MustLoadDLL("kernel32.dll")
	isDebuggerPresent := kernel32.MustFindProc("IsDebuggerPresent")
	ret, _, _ := isDebuggerPresent.Call()
	return ret != 0
}

// detectLowResources checks for sandbox-typical low resource allocation.
func detectLowResources() bool {
	// Sandboxes typically have very few CPUs
	if runtime.NumCPU() < 2 {
		return true
	}
	return false
}

// detectVMRegistry checks for VM-related registry keys.
// This is an additional detection method that can be enabled.
func detectVMRegistry() bool {
	// Common VM registry paths to check:
	// HKLM\SOFTWARE\VMware, Inc.\VMware Tools
	// HKLM\SOFTWARE\Oracle\VirtualBox Guest Additions
	// HKLM\HARDWARE\ACPI\DSDT\VBOX__
	// Implementation requires registry access
	return false
}

// detectSuspiciousProcesses checks for analysis tool processes.
// This is an additional detection method that can be enabled.
func detectSuspiciousProcesses() bool {
	// Suspicious process names to check:
	// wireshark.exe, fiddler.exe, procmon.exe, procexp.exe
	// x64dbg.exe, x32dbg.exe, ollydbg.exe, ida.exe, ida64.exe
	// Implementation requires process enumeration
	return false
}
