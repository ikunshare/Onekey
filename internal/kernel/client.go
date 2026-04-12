package kernel

import (
	"encoding/json"
	"fmt"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	DefaultAddr      = "127.0.0.1:6754"
	handshakeTimeout = 10 * time.Second
	writeTimeout     = 10 * time.Second
	readTimeout      = 30 * time.Second
)

// Request is the JSON command sent to the kernel.
type Request struct {
	Cmd  string      `json:"cmd"`
	Data any `json:"data,omitempty"`
}

// Response is the JSON reply from the kernel.
type Response struct {
	OK   bool            `json:"ok"`
	Msg  string          `json:"msg,omitempty"`
	Data json.RawMessage `json:"data,omitempty"`
}

// Client manages a WebSocket connection to the kernel.
type Client struct {
	addr string
	key  string
	conn *websocket.Conn
	mu   sync.Mutex
}

// NewClient creates a kernel client (does not connect yet).
func NewClient(addr, key string) *Client {
	if addr == "" {
		addr = DefaultAddr
	}
	return &Client{addr: addr, key: key}
}

// Connect establishes the WebSocket connection with key authentication.
func (c *Client) Connect() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		return nil // already connected
	}

	u := url.URL{
		Scheme:   "ws",
		Host:     c.addr,
		Path:     "/",
		RawQuery: "key=" + url.QueryEscape(c.key),
	}

	dialer := websocket.Dialer{
		HandshakeTimeout: handshakeTimeout,
	}

	conn, _, err := dialer.Dial(u.String(), nil)
	if err != nil {
		return fmt.Errorf("kernel connect failed: %w", err)
	}
	c.conn = conn
	return nil
}

// Close shuts down the connection.
func (c *Client) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.conn != nil {
		c.conn.WriteMessage(
			websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""),
		)
		c.conn.Close()
		c.conn = nil
	}
}

// Send sends a command and waits for the response.
func (c *Client) Send(cmd string, data any) (*Response, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn == nil {
		return nil, fmt.Errorf("not connected to kernel")
	}

	req := Request{Cmd: cmd, Data: data}
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
	if err := c.conn.WriteMessage(websocket.TextMessage, payload); err != nil {
		return nil, fmt.Errorf("send to kernel: %w", err)
	}

	c.conn.SetReadDeadline(time.Now().Add(readTimeout))
	_, msg, err := c.conn.ReadMessage()
	if err != nil {
		return nil, fmt.Errorf("read from kernel: %w", err)
	}

	var resp Response
	if err := json.Unmarshal(msg, &resp); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}
	return &resp, nil
}

// --- Convenience command wrappers ---

// ClearApps sends the clear_apps command.
func (c *Client) ClearApps() error {
	resp, err := c.Send("clear_apps", nil)
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("clear_apps: %s", resp.Msg)
	}
	return nil
}

// AddApp sends the add_app command.
func (c *Client) AddApp(appid uint32, mode uint32) error {
	resp, err := c.Send("add_app", map[string]any{
		"appid": appid,
		"mode":  mode,
	})
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("add_app: %s", resp.Msg)
	}
	return nil
}

// SetToken sends the set_token command.
func (c *Client) SetToken(appid uint32, value uint64) error {
	resp, err := c.Send("set_token", map[string]any{
		"appid": appid,
		"value": value,
	})
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("set_token: %s", resp.Msg)
	}
	return nil
}

// SetTicket sends the set_ticket command.
func (c *Client) SetTicket(appid uint32, ticket string) error {
	resp, err := c.Send("set_ticket", map[string]any{
		"appid":  appid,
		"ticket": ticket,
	})
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("set_ticket: %s", resp.Msg)
	}
	return nil
}

// SetCDN sends the set_cdn command.
func (c *Client) SetCDN(cdnURL string) error {
	resp, err := c.Send("set_cdn", map[string]any{
		"url": cdnURL,
	})
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("set_cdn: %s", resp.Msg)
	}
	return nil
}

// SetUnlockMode sends the set_unlock_mode command.
func (c *Client) SetUnlockMode(enabled bool) error {
	resp, err := c.Send("set_unlock_mode", map[string]any{
		"enabled": enabled,
	})
	if err != nil {
		return err
	}
	if !resp.OK {
		return fmt.Errorf("set_unlock_mode: %s", resp.Msg)
	}
	return nil
}

// DispatchResult holds the dispatch response data.
type DispatchResult struct {
	UnlockApps int `json:"unlock_apps"`
	Manifests  int `json:"manifests"`
	Tokens     int `json:"tokens"`
}

// Dispatch sends the dispatch command and returns the result.
func (c *Client) Dispatch() (*DispatchResult, error) {
	resp, err := c.Send("dispatch", nil)
	if err != nil {
		return nil, err
	}
	if !resp.OK {
		return nil, fmt.Errorf("dispatch: %s", resp.Msg)
	}
	var result DispatchResult
	if resp.Data != nil {
		if err := json.Unmarshal(resp.Data, &result); err != nil {
			return nil, fmt.Errorf("parse dispatch result: %w", err)
		}
	}
	return &result, nil
}

// StatusResult holds the get_status response data.
type StatusResult struct {
	Version       string `json:"version"`
	SteamID3      int64  `json:"steamid3"`
	SessionID     int64  `json:"session_id"`
	UnlockEnabled bool   `json:"unlock_enabled"`
	UnlockApps    int    `json:"unlock_apps"`
	Manifests     int    `json:"manifests"`
	Tokens        int    `json:"tokens"`
	PackageReady  bool   `json:"package_ready"`
}

// GetStatus sends the get_status command and returns kernel status.
func (c *Client) GetStatus() (*StatusResult, error) {
	resp, err := c.Send("get_status", nil)
	if err != nil {
		return nil, err
	}
	if !resp.OK {
		return nil, fmt.Errorf("get_status: %s", resp.Msg)
	}
	var result StatusResult
	if resp.Data != nil {
		if err := json.Unmarshal(resp.Data, &result); err != nil {
			return nil, fmt.Errorf("parse status result: %w", err)
		}
	}
	return &result, nil
}
