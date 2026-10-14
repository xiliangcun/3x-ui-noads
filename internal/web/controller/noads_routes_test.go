package controller

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestNoAdsSponsorEndpointsUnavailable(t *testing.T) {
	gin.SetMode(gin.TestMode)
	engine := gin.New()
	NewIndexController(engine.Group("/"))
	for _, path := range []string{"/sponsors", "/sponsors/logo/example.png"} {
		t.Run(path, func(t *testing.T) {
			response := httptest.NewRecorder()
			engine.ServeHTTP(response, httptest.NewRequest(http.MethodGet, path, nil))
			if response.Code != http.StatusNotFound {
				t.Fatalf("advertising endpoint %s returned %d; want 404", path, response.Code)
			}
		})
	}
}
