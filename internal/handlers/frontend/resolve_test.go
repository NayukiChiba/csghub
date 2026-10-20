package frontendHandlers

import "testing"

func TestIsBinaryFormat(t *testing.T) {
	binary := []string{"jpg", "png", "webp", "mp4", "webm", "mkv", "mp3", "wav", "flac", "ogg"}
	for _, format := range binary {
		if !isBinaryFormat(format) {
			t.Errorf("expected %s to be a binary format", format)
		}
	}

	nonBinary := []string{"json", "jsonl", "csv", "txt", "md", "parquet", ""}
	for _, format := range nonBinary {
		if isBinaryFormat(format) {
			t.Errorf("expected %s to not be a binary format", format)
		}
	}
}

func TestDetermineContentType(t *testing.T) {
	cases := map[string]string{
		"videos/00001.MP4":   "video/mp4",
		"audio/clip.WAV":     "audio/wav",
		"img/cat.JPG":        "image/jpeg",
		"data/train.parquet": "application/octet-stream",
	}
	for filename, want := range cases {
		if got := determineContentType(filename); got != want {
			t.Errorf("determineContentType(%q) = %q, want %q", filename, got, want)
		}
	}
}
