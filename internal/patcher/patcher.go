package patcher

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
)

// 16-byte search pattern: the bytes preceding \x02billingtype in VDF binary format
// E8 4E 00 00 02 62 69 6C 6C 69 6E 67 74 79 70 65
var pattern = []byte{
	0xE8, 0x4E, 0x00, 0x00,
	0x02, 0x62, 0x69, 0x6C, 0x6C, 0x69, 0x6E, 0x67, 0x74, 0x79, 0x70, 0x65,
}

// 4-byte replacement: 0x12020 (73760) in little-endian
var replacement = []byte{0x20, 0x20, 0x01, 0x00}

// PatchPackageInfo patches billingtype entries in Steam's packageinfo.vdf.
// Returns the number of patches applied.
func PatchPackageInfo(steamPath string) (int, error) {
	vdfPath := filepath.Join(steamPath, "appcache", "packageinfo.vdf")

	data, err := os.ReadFile(vdfPath)
	if err != nil {
		return 0, fmt.Errorf("read packageinfo.vdf: %w", err)
	}

	// Backup
	bakPath := vdfPath + ".bak"
	os.WriteFile(bakPath, data, 0644)

	count := 0
	offset := 0
	for {
		idx := bytes.Index(data[offset:], pattern)
		if idx < 0 {
			break
		}
		pos := offset + idx
		copy(data[pos:pos+4], replacement)
		count++
		offset = pos + len(pattern)
	}

	if count == 0 {
		return 0, nil
	}

	if err := os.WriteFile(vdfPath, data, 0644); err != nil {
		return 0, fmt.Errorf("write packageinfo.vdf: %w", err)
	}
	return count, nil
}
