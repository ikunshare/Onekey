package httpclient

import (
	"context"
	"encoding/base64"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

var dohProviders = []string{
	"https://dns.alidns.com/dns-query",
	"https://doh.pub/dns-query",
}

// shouldUseDoH returns true for hostnames that are commonly affected by DNS
// pollution in mainland China. For other hosts we defer to the system resolver
// to avoid interfering with VPN/proxy setups.
var dohHostSuffixes = []string{
	".steampowered.com",
	".steamcontent.com",
	".steamcommunity.com",
	".steamstatic.com",
	"steampowered.com",
	"steamcontent.com",
	"steamcommunity.com",
	"steamstatic.com",
}

func shouldUseDoH(host string) bool {
	h := strings.ToLower(host)
	for _, s := range dohHostSuffixes {
		if h == s || strings.HasSuffix(h, s) {
			return true
		}
	}
	return false
}

type dohCacheEntry struct {
	ips    []string
	expire time.Time
}

var (
	dohCache   = make(map[string]dohCacheEntry)
	dohCacheMu sync.RWMutex

	// dohClient is a minimal HTTP client used only for DoH lookups. It must not
	// recurse through the resolving transport.
	dohClient = &http.Client{
		Timeout: 5 * time.Second,
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout:   3 * time.Second,
				KeepAlive: 15 * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   3 * time.Second,
			ResponseHeaderTimeout: 3 * time.Second,
			MaxIdleConns:          4,
			IdleConnTimeout:       30 * time.Second,
		},
	}
)

func cachedLookup(host string) []string {
	dohCacheMu.RLock()
	defer dohCacheMu.RUnlock()
	if e, ok := dohCache[host]; ok && time.Now().Before(e.expire) {
		return append([]string(nil), e.ips...)
	}
	return nil
}

func storeLookup(host string, ips []string, ttl time.Duration) {
	if len(ips) == 0 {
		return
	}
	if ttl < 30*time.Second {
		ttl = 30 * time.Second
	}
	dohCacheMu.Lock()
	dohCache[host] = dohCacheEntry{ips: ips, expire: time.Now().Add(ttl)}
	dohCacheMu.Unlock()
}

// resolveDoH resolves host to one or more IPv4 addresses by racing multiple
// DoH providers. Returns the first non-empty answer. TTL is clamped between
// 30s and 10min.
func resolveDoH(ctx context.Context, host string) ([]string, error) {
	if ips := cachedLookup(host); len(ips) > 0 {
		return ips, nil
	}

	type res struct {
		ips []string
		ttl time.Duration
		err error
	}

	ctx, cancel := context.WithTimeout(ctx, 4*time.Second)
	defer cancel()

	ch := make(chan res, len(dohProviders))
	for _, p := range dohProviders {
		go func(endpoint string) {
			ips, ttl, err := queryDoH(ctx, endpoint, host)
			ch <- res{ips, ttl, err}
		}(p)
	}

	var lastErr error
	for i := 0; i < len(dohProviders); i++ {
		r := <-ch
		if r.err == nil && len(r.ips) > 0 {
			storeLookup(host, r.ips, r.ttl)
			return r.ips, nil
		}
		if r.err != nil {
			lastErr = r.err
		}
	}
	if lastErr == nil {
		lastErr = fmt.Errorf("doh: no answer for %s", host)
	}
	return nil, lastErr
}

// queryDoH sends a DNS A query to a DoH endpoint using GET + RFC 8484 wire
// format and returns the IPv4 addresses from the answer section.
func queryDoH(ctx context.Context, endpoint, host string) ([]string, time.Duration, error) {
	msg, err := buildDNSQuery(host)
	if err != nil {
		return nil, 0, err
	}
	q := base64.RawURLEncoding.EncodeToString(msg)

	url := endpoint + "?dns=" + q
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("Accept", "application/dns-message")

	resp, err := dohClient.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, 0, fmt.Errorf("doh: status %d", resp.StatusCode)
	}
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, err
	}
	return parseDNSAnswer(data)
}

// buildDNSQuery constructs a minimal DNS query packet (A record, ID=0, RD=1)
// in RFC 1035 wire format.
func buildDNSQuery(host string) ([]byte, error) {
	host = strings.TrimSuffix(host, ".")
	buf := make([]byte, 0, 32+len(host))
	// Header: ID=0, flags=0x0100 (RD), QDCOUNT=1, rest=0
	buf = append(buf, 0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
	// QNAME: sequence of labels, each prefixed with its length
	for _, label := range strings.Split(host, ".") {
		if len(label) == 0 || len(label) > 63 {
			return nil, fmt.Errorf("doh: invalid label %q", label)
		}
		buf = append(buf, byte(len(label)))
		buf = append(buf, []byte(label)...)
	}
	buf = append(buf, 0x00)             // end of QNAME
	buf = append(buf, 0x00, 0x01)        // QTYPE=A
	buf = append(buf, 0x00, 0x01)        // QCLASS=IN
	return buf, nil
}

// parseDNSAnswer extracts A-record IPv4 addresses and the minimum TTL from a
// DNS response packet.
func parseDNSAnswer(msg []byte) ([]string, time.Duration, error) {
	if len(msg) < 12 {
		return nil, 0, fmt.Errorf("doh: short response")
	}
	qd := int(msg[4])<<8 | int(msg[5])
	an := int(msg[6])<<8 | int(msg[7])
	if an == 0 {
		return nil, 0, fmt.Errorf("doh: empty answer")
	}

	pos := 12
	// Skip question section
	for i := 0; i < qd; i++ {
		n, err := skipName(msg, pos)
		if err != nil {
			return nil, 0, err
		}
		pos = n + 4 // QTYPE + QCLASS
		if pos > len(msg) {
			return nil, 0, fmt.Errorf("doh: truncated question")
		}
	}

	var ips []string
	var minTTL uint32 = 600
	for i := 0; i < an; i++ {
		n, err := skipName(msg, pos)
		if err != nil {
			return nil, 0, err
		}
		pos = n
		if pos+10 > len(msg) {
			return nil, 0, fmt.Errorf("doh: truncated answer")
		}
		rrType := uint16(msg[pos])<<8 | uint16(msg[pos+1])
		ttl := uint32(msg[pos+4])<<24 | uint32(msg[pos+5])<<16 | uint32(msg[pos+6])<<8 | uint32(msg[pos+7])
		rdLen := int(msg[pos+8])<<8 | int(msg[pos+9])
		pos += 10
		if pos+rdLen > len(msg) {
			return nil, 0, fmt.Errorf("doh: truncated rdata")
		}
		if rrType == 1 && rdLen == 4 {
			ip := net.IPv4(msg[pos], msg[pos+1], msg[pos+2], msg[pos+3]).String()
			ips = append(ips, ip)
			if ttl < minTTL {
				minTTL = ttl
			}
		}
		pos += rdLen
	}
	if len(ips) == 0 {
		return nil, 0, fmt.Errorf("doh: no A record")
	}
	return ips, time.Duration(minTTL) * time.Second, nil
}

// skipName advances past a DNS name (supports pointer compression) and
// returns the new offset.
func skipName(msg []byte, pos int) (int, error) {
	for {
		if pos >= len(msg) {
			return 0, fmt.Errorf("doh: name out of bounds")
		}
		b := msg[pos]
		if b == 0 {
			return pos + 1, nil
		}
		if b&0xC0 == 0xC0 {
			// Compressed pointer: 2 bytes
			if pos+1 >= len(msg) {
				return 0, fmt.Errorf("doh: bad pointer")
			}
			return pos + 2, nil
		}
		pos += int(b) + 1
	}
}
