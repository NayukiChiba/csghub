package routes

import "testing"

func TestPublicServerBaseURL(t *testing.T) {
	tests := []struct {
		name          string
		baseURL       string
		publicBaseURL string
		want          string
	}{
		{
			name:          "uses public URL for browser API requests",
			baseURL:       "http://127.0.0.1:8080",
			publicBaseURL: "http://127.0.0.1:7080",
			want:          "http://127.0.0.1:7080",
		},
		{
			name:    "falls back to internal URL",
			baseURL: "http://127.0.0.1:8080",
			want:    "http://127.0.0.1:8080",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := publicServerBaseURL(tt.baseURL, tt.publicBaseURL); got != tt.want {
				t.Fatalf("publicServerBaseURL() = %q, want %q", got, tt.want)
			}
		})
	}
}
