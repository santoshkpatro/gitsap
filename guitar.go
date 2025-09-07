package main

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/labstack/echo/v4"
)

func main() {
	e := echo.New()

	// Discovery for fetch/clone
	e.GET("/:handle/:slug/info/refs", func(c echo.Context) error {
		service := c.QueryParam("service")
		handle := c.Param("handle") // e.g. santoshkpatro
		slug := c.Param("slug")     // e.g. gitsap.git

		// Strip ".git" if present
		slug = strings.TrimSuffix(slug, ".git")

		namespace := fmt.Sprintf("%s/%s", handle, slug)

		fmt.Println("🎸 Git discovery request received!")
		fmt.Printf("➡️  Namespace: %s, Service=%s\n", namespace, service)

		return c.String(http.StatusOK,
			fmt.Sprintf("Hello from Guitar 🎶 [info/refs] namespace=%s, service=%s\n",
				namespace, service))
	})

	// Upload-pack (fetch/clone)
	e.POST("/:handle/:slug/git-upload-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")

		namespace := fmt.Sprintf("%s/%s", handle, slug)

		return c.String(http.StatusOK,
			fmt.Sprintf("Stub: git-upload-pack for %s\n", namespace))
	})

	// Receive-pack (push)
	e.POST("/:handle/:slug/git-receive-pack", func(c echo.Context) error {
		handle := c.Param("handle")
		slug := strings.TrimSuffix(c.Param("slug"), ".git")

		namespace := fmt.Sprintf("%s/%s", handle, slug)

		return c.String(http.StatusOK,
			fmt.Sprintf("Stub: git-receive-pack for %s\n", namespace))
	})

	e.Logger.Print("🎸 Guitar server strumming on http://localhost:3000 ...")
	e.Logger.Fatal(e.Start(":3000"))
}
