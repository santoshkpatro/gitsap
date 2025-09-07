package main

import (
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

var repoBasePath string

func main() {
	// Load .env file if present
	_ = godotenv.Load()

	// Get REPO_STORAGE_PATH (default ./var/repos)
	repoBasePath = os.Getenv("REPO_STORAGE_PATH")
	if repoBasePath == "" {
		repoBasePath = "./var/repos"
	}

	// Create repos directory if it doesn't exist
	if err := os.MkdirAll(repoBasePath, 0755); err != nil {
		fmt.Printf("Error creating repos directory: %v\n", err)
		os.Exit(1)
	}

	e := echo.New()

	// Add middleware for better debugging
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())

	// Discovery for fetch/clone
	e.GET("/:handle/:slug/info/refs", func(c echo.Context) error {
		service := c.QueryParam("service")
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")

		namespace := fmt.Sprintf("%s/%s", handle, slug)
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		fmt.Println("🎸 Git discovery request received!")
		fmt.Printf("➡️  Namespace: %s, Service=%s, RepoPath=%s\n", namespace, service, repoPath)

		// Check if repository exists
		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			return c.String(http.StatusNotFound, "Repository not found")
		}

		var cmd *exec.Cmd
		switch service {
		case "git-upload-pack":
			c.Response().Header().Set("Content-Type", "application/x-git-upload-pack-advertisement")
			c.Response().Header().Set("Cache-Control", "no-cache")
			cmd = exec.Command("git", "upload-pack", "--stateless-rpc", "--advertise-refs", repoPath)
		case "git-receive-pack":
			c.Response().Header().Set("Content-Type", "application/x-git-receive-pack-advertisement")
			c.Response().Header().Set("Cache-Control", "no-cache")
			cmd = exec.Command("git", "receive-pack", "--stateless-rpc", "--advertise-refs", repoPath)
		default:
			return c.String(http.StatusBadRequest, "unsupported service")
		}

		// Write required pkt-line header before Git's output
		c.Response().WriteHeader(http.StatusOK)
		fmt.Fprintf(c.Response(), "001e# service=%s\n0000", service)
		c.Response().Flush()

		cmd.Stdout = c.Response()
		cmd.Stderr = os.Stderr

		if err := cmd.Run(); err != nil {
			fmt.Printf("Error running git command: %v\n", err)
			return echo.NewHTTPError(http.StatusInternalServerError, "Git command failed")
		}
		return nil
	})

	// Upload-pack (fetch/clone)
	e.POST("/:handle/:slug/git-upload-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")
		namespace := fmt.Sprintf("%s/%s", handle, slug)
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		fmt.Println("📦 Git upload-pack request received!")
		fmt.Printf("➡️  Namespace: %s, RepoPath: %s\n", namespace, repoPath)

		// Check if repository exists
		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			return c.String(http.StatusNotFound, "Repository not found")
		}

		// Set correct content type and headers
		c.Response().Header().Set("Content-Type", "application/x-git-upload-pack-result")
		c.Response().Header().Set("Cache-Control", "no-cache")

		cmd := exec.Command("git", "upload-pack", "--stateless-rpc", repoPath)
		cmd.Stdin = c.Request().Body // client request → git stdin
		cmd.Stdout = c.Response()    // git stdout → client response
		cmd.Stderr = os.Stderr       // debug

		if err := cmd.Run(); err != nil {
			fmt.Printf("Error running git upload-pack: %v\n", err)
			return echo.NewHTTPError(http.StatusInternalServerError, "Git upload-pack failed")
		}
		return nil
	})

	// Receive-pack (push)
	e.POST("/:handle/:slug/git-receive-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")
		namespace := fmt.Sprintf("%s/%s", handle, slug)
		repoPath := filepath.Join(repoBasePath, handle, slug+".git")

		fmt.Println("📤 Git receive-pack request received!")
		fmt.Printf("➡️  Namespace: %s, RepoPath: %s\n", namespace, repoPath)

		// Check if repository exists, create if it doesn't
		if _, err := os.Stat(repoPath); os.IsNotExist(err) {
			// Create the directory structure
			if err := os.MkdirAll(filepath.Dir(repoPath), 0755); err != nil {
				return echo.NewHTTPError(http.StatusInternalServerError, "Failed to create repository directory")
			}

			// Initialize bare repository
			initCmd := exec.Command("git", "init", "--bare", repoPath)
			if err := initCmd.Run(); err != nil {
				fmt.Printf("Error initializing bare repository: %v\n", err)
				return echo.NewHTTPError(http.StatusInternalServerError, "Failed to initialize repository")
			}
		}

		// Set correct content type and headers
		c.Response().Header().Set("Content-Type", "application/x-git-receive-pack-result")
		c.Response().Header().Set("Cache-Control", "no-cache")

		cmd := exec.Command("git", "receive-pack", "--stateless-rpc", repoPath)
		cmd.Stdin = c.Request().Body // client request → git stdin
		cmd.Stdout = c.Response()    // git stdout → client response
		cmd.Stderr = os.Stderr       // debug

		if err := cmd.Run(); err != nil {
			fmt.Printf("Error running git receive-pack: %v\n", err)
			return echo.NewHTTPError(http.StatusInternalServerError, "Git receive-pack failed")
		}
		return nil
	})

	fmt.Println("🎸 Guitar server strumming on http://localhost:3000 ...")
	e.Logger.Fatal(e.Start(":3000"))
}
