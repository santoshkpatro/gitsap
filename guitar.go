package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

type verifyResponse struct {
	Allowed bool   `json:"allowed"`
	Reason  string `json:"reason"`
}

var repoBasePath string
var applicationUrl string

func verifyWithAuthService(username, password, namespace, service string) (bool, string, error) {
	url := fmt.Sprintf("%s/api/internal/projects/verify-access/", applicationUrl)

	payload := map[string]string{
		"username":  username,
		"password":  password,
		"namespace": namespace,
		"service":   service,
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return false, "internal error", err
	}

	req, err := http.NewRequest("POST", url, strings.NewReader(string(jsonPayload)))
	if err != nil {
		return false, "request build failed", err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return false, "auth service unreachable", err
	}
	defer resp.Body.Close()

	var result verifyResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, "invalid auth service response", err
	}

	return result.Allowed, result.Reason, nil
}

func main() {
	_ = godotenv.Load()

	repoBasePath = os.Getenv("REPO_STORAGE_PATH")
	if repoBasePath == "" {
		repoBasePath = "./var/repos"
	}
	applicationUrl = os.Getenv("BASE_URL")
	if applicationUrl == "" {
		applicationUrl = "http://localhost:8000"
	}

	os.MkdirAll(repoBasePath, 0755)

	e := echo.New()
	e.Use(middleware.Recover())
	// e.Use(middleware.Logger())

	// Health check
	e.GET("/health", func(c echo.Context) error {
		return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
	})

	// info/refs (discovery)
	e.GET("/:handle/:slug/info/refs", func(c echo.Context) error {
		service := c.QueryParam("service")
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")
		namespace := fmt.Sprintf("%s/%s", handle, slug)
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		// Only authenticate for info/refs
		username, password, ok := c.Request().BasicAuth()
		if !ok {
			c.Response().Header().Set("WWW-Authenticate", `Basic realm="Git Server"`)
			return c.String(http.StatusUnauthorized, "Authentication required")
		}

		allowed, reason, err := verifyWithAuthService(username, password, namespace, service)
		if err != nil {
			return c.String(http.StatusInternalServerError, reason)
		}
		if !allowed {
			return c.String(http.StatusForbidden, reason)
		}

		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			return c.String(http.StatusNotFound, "Repository not found")
		}

		var contentType string
		var cmd *exec.Cmd

		switch service {
		case "git-upload-pack":
			contentType = "application/x-git-upload-pack-advertisement"
			cmd = exec.Command("git", "upload-pack", "--stateless-rpc", "--advertise-refs", repoPath)
		case "git-receive-pack":
			contentType = "application/x-git-receive-pack-advertisement"
			cmd = exec.Command("git", "receive-pack", "--stateless-rpc", "--advertise-refs", repoPath)
		default:
			return c.String(http.StatusBadRequest, "unsupported service")
		}

		c.Response().Header().Set("Content-Type", contentType)
		c.Response().Header().Set("Cache-Control", "no-cache")
		c.Response().WriteHeader(http.StatusOK)

		serviceRef := fmt.Sprintf("# service=%s\n", service)
		pktLen := fmt.Sprintf("%04x", len(serviceRef)+4)
		pktLine := pktLen + serviceRef + "0000"
		c.Response().Write([]byte(pktLine))
		c.Response().Flush()

		cmd.Stdout = c.Response().Writer
		cmd.Stderr = os.Stderr
		cmd.Run()

		return nil
	})

	// git-upload-pack (clone/fetch)
	e.POST("/:handle/:slug/git-upload-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			return c.String(http.StatusNotFound, "Repository not found")
		}

		c.Response().Header().Set("Content-Type", "application/x-git-upload-pack-result")
		c.Response().Header().Set("Cache-Control", "no-cache")
		c.Response().WriteHeader(http.StatusOK)

		cmd := exec.Command("git", "upload-pack", "--stateless-rpc", repoPath)
		cmd.Stdin = c.Request().Body
		cmd.Stdout = c.Response().Writer
		cmd.Stderr = os.Stderr
		cmd.Run()

		return nil
	})

	// git-receive-pack (push)
	e.POST("/:handle/:slug/git-receive-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			return c.String(http.StatusNotFound, "Repository not found")
		}

		c.Response().Header().Set("Content-Type", "application/x-git-receive-pack-result")
		c.Response().Header().Set("Cache-Control", "no-cache")
		c.Response().WriteHeader(http.StatusOK)

		cmd := exec.Command("git", "receive-pack", "--stateless-rpc", repoPath)
		cmd.Stdin = c.Request().Body
		cmd.Stdout = c.Response().Writer
		cmd.Stderr = os.Stderr
		cmd.Run()

		return nil
	})

	fmt.Println("🎸 Guitar server strumming on http://localhost:3000")
	e.Logger.Fatal(e.Start(":3000"))
}
