package manifest

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"onekey/internal/httpclient"
	"onekey/internal/i18n"
	"onekey/internal/models"
)

var client = httpclient.Shared()

// ProgressFunc is called with a status message and current/total counts.
type ProgressFunc func(msg string, current, total int)

// Handler downloads and processes Steam manifest files.
type Handler struct {
	steamPath  string
	depotCache string
	cdnList    []string
	cdnMu      sync.Mutex
}

// NewHandler creates a manifest handler for the given Steam path and CDN list.
func NewHandler(steamPath string, cdnList []string) *Handler {
	cache := filepath.Join(steamPath, "depotcache")
	os.MkdirAll(cache, 0755)
	return &Handler{
		steamPath:  steamPath,
		depotCache: cache,
		cdnList:    cdnList,
	}
}

// ProcessManifests downloads and saves all manifests concurrently.
func (h *Handler) ProcessManifests(manifests []models.ManifestInfo, onProgress ProgressFunc) ([]models.ManifestInfo, error) {
	total := len(manifests)
	results := make([]models.ManifestInfo, total)
	success := make([]bool, total)

	sem := make(chan struct{}, 10) // max 10 concurrent
	var wg sync.WaitGroup
	var mu sync.Mutex
	current := 0

	for i, m := range manifests {
		wg.Add(1)
		go func(idx int, info models.ManifestInfo) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			ok := h.processSingle(info)

			mu.Lock()
			current++
			c := current
			if ok {
				results[idx] = info
				success[idx] = true
				if onProgress != nil {
					if h.manifestExists(info) {
						onProgress(i18n.T("manifest.status.exists", "depot_id", info.DepotID), c, total)
					} else {
						onProgress(i18n.T("manifest.status.downloaded", "depot_id", info.DepotID), c, total)
					}
				}
			} else {
				if onProgress != nil {
					onProgress(i18n.T("manifest.status.failed", "depot_id", info.DepotID), c, total)
				}
			}
			mu.Unlock()
		}(i, m)
	}

	wg.Wait()

	var processed []models.ManifestInfo
	for i, ok := range success {
		if ok {
			processed = append(processed, results[i])
		}
	}
	return processed, nil
}

func (h *Handler) manifestPath(info models.ManifestInfo) string {
	return filepath.Join(h.depotCache, fmt.Sprintf("%s_%s.manifest", info.DepotID, info.ManifestID))
}

func (h *Handler) manifestExists(info models.ManifestInfo) bool {
	_, err := os.Stat(h.manifestPath(info))
	return err == nil
}

func (h *Handler) processSingle(info models.ManifestInfo) bool {
	if h.manifestExists(info) {
		return true
	}

	data := h.download(info)
	if data == nil {
		return false
	}

	payload := extractManifestPayload(data)
	h.removeOldManifests(info.DepotID, info.ManifestID)

	path := h.manifestPath(info)
	if err := os.WriteFile(path, payload, 0644); err != nil {
		return false
	}
	return true
}

func (h *Handler) download(info models.ManifestInfo) []byte {
	for retry := 0; retry < 3; retry++ {
		h.cdnMu.Lock()
		cdns := make([]string, len(h.cdnList))
		copy(cdns, h.cdnList)
		h.cdnMu.Unlock()

		for i, cdn := range cdns {
			url := cdn + info.URL
			resp, err := client.Get(url)
			if err != nil {
				h.demoteCDN(i)
				continue
			}
			if resp.StatusCode == 200 {
				data, err := io.ReadAll(resp.Body)
				resp.Body.Close()
				if err == nil {
					return data
				}
			} else {
				resp.Body.Close()
				h.demoteCDN(i)
			}
		}
	}
	return nil
}

// demoteCDN moves the CDN at index i to the end of the list so that
// subsequent downloads prefer other nodes first.
func (h *Handler) demoteCDN(i int) {
	h.cdnMu.Lock()
	defer h.cdnMu.Unlock()
	if i < 0 || i >= len(h.cdnList)-1 {
		return
	}
	bad := h.cdnList[i]
	h.cdnList = append(h.cdnList[:i], h.cdnList[i+1:]...)
	h.cdnList = append(h.cdnList, bad)
}

func (h *Handler) removeOldManifests(depotID, currentManifestID string) {
	entries, err := os.ReadDir(h.depotCache)
	if err != nil {
		return
	}
	prefix := depotID + "_"
	currentName := fmt.Sprintf("%s_%s.manifest", depotID, currentManifestID)
	for _, e := range entries {
		name := e.Name()
		if strings.HasPrefix(name, prefix) && strings.HasSuffix(name, ".manifest") && name != currentName {
			os.Remove(filepath.Join(h.depotCache, name))
		}
	}
}

func extractManifestPayload(content []byte) []byte {
	reader, err := zip.NewReader(bytes.NewReader(content), int64(len(content)))
	if err != nil {
		return content
	}
	for _, f := range reader.File {
		if f.Name == "z" {
			rc, err := f.Open()
			if err != nil {
				return content
			}
			data, err := io.ReadAll(rc)
			rc.Close()
			if err != nil {
				return content
			}
			return data
		}
	}
	return content
}
