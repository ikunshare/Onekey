package httpclient

import (
	"context"
	"io"
	"net"
	"strings"
	"time"
)

var ipServices = []string{
	"https://api.ipify.org",
	"https://ifconfig.me/ip",
	"https://icanhazip.com",
}

// GetPublicIP returns the client's public IPv4 address by querying external
// services. Returns empty string on failure.
func GetPublicIP() string {
	ctx, cancel := context.WithTimeout(context.Background(), 6*time.Second)
	defer cancel()

	type result struct {
		ip string
	}
	ch := make(chan result, len(ipServices))

	for _, svc := range ipServices {
		go func(url string) {
			resp, err := Shared().GetCtx(ctx, url)
			if err != nil {
				ch <- result{}
				return
			}
			defer resp.Body.Close()
			if resp.StatusCode != 200 {
				ch <- result{}
				return
			}
			data, err := io.ReadAll(io.LimitReader(resp.Body, 64))
			if err != nil {
				ch <- result{}
				return
			}
			ip := strings.TrimSpace(string(data))
			if net.ParseIP(ip) != nil {
				ch <- result{ip: ip}
				return
			}
			ch <- result{}
		}(svc)
	}

	for i := 0; i < len(ipServices); i++ {
		r := <-ch
		if r.ip != "" {
			return r.ip
		}
	}
	return ""
}
