package main

import (
	"fmt"
	"net/http"

	"github.com/labstack/echo/v4"
)

func main() {
	e := echo.New()

	e.GET("/:namespace/:handle.git/info/refs", func(c echo.Context) error {
		namespace := c.Param("namespace")
		handle := c.Param("handle")

		fmt.Println("🎸 Git request received!")
		fmt.Printf("➡️  Namespace: %s, Handle: %s\n", namespace, handle)

		return c.String(http.StatusOK,
			fmt.Sprintf("Hello from Guitar 🎶 namespace=%s, handle=%s\n", namespace, handle))
	})

	e.Logger.Print("🎸 Guitar server strumming on http://localhost:8080 ...")
	e.Logger.Fatal(e.Start(":3000"))
}
