from __future__ import annotations

import argparse
import json
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from multi_agent_system import MultiAgentSystem
from terminal_chat import ChatResponder


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Multiagents Web Chat</title>
  <style>
    :root{
      --bg0:#f4f7fb;
      --bg1:#eaf1ff;
      --ink:#0f1b33;
      --muted:#51617a;
      --card:#ffffff;
      --line:#d3dcef;
      --accent:#2166d9;
      --accent2:#00a8c6;
      --ok:#2f8f46;
      --user:#eef5ff;
      --bot:#f8fbff;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      min-height:100vh;
      font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial;
      color:var(--ink);
      background:radial-gradient(1200px 600px at 15% -10%, #ffffff 0%, var(--bg1) 45%, var(--bg0) 100%);
      display:flex;
      align-items:center;
      justify-content:center;
      padding:24px;
    }
    .app{
      width:min(1040px, 100%);
      height:min(86vh, 900px);
      background:var(--card);
      border:1px solid var(--line);
      border-radius:22px;
      box-shadow:0 20px 60px rgba(20,40,80,.14);
      overflow:hidden;
      display:grid;
      grid-template-rows:auto 1fr auto;
    }
    .head{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:16px;
      padding:18px 22px;
      border-bottom:1px solid var(--line);
      background:linear-gradient(135deg,#fdfefe 0%,#f4f8ff 100%);
    }
    .brand{
      display:flex;
      align-items:center;
      gap:10px;
      font-weight:800;
      letter-spacing:.2px;
      font-size:20px;
    }
    .dot{
      width:11px;height:11px;border-radius:999px;background:linear-gradient(135deg,var(--accent),var(--accent2));
      box-shadow:0 0 0 4px rgba(33,102,217,.12);
    }
    .meta{color:var(--muted);font-size:13px}
    .chat{
      padding:20px;
      overflow:auto;
      display:flex;
      flex-direction:column;
      gap:12px;
      background:linear-gradient(180deg,#ffffff 0%,#fcfdff 100%);
    }
    .msg{
      max-width:84%;
      border:1px solid var(--line);
      border-radius:16px;
      padding:12px 14px;
      line-height:1.45;
      white-space:pre-wrap;
      box-shadow:0 3px 10px rgba(15,27,51,.05);
    }
    .msg.user{
      align-self:flex-end;
      background:var(--user);
      border-color:#c7d9ff;
    }
    .msg.bot{
      align-self:flex-start;
      background:var(--bot);
    }
    .msg .label{
      display:block;
      font-size:11px;
      color:var(--muted);
      margin-bottom:6px;
      text-transform:uppercase;
      letter-spacing:.4px;
      font-weight:700;
    }
    .composer{
      border-top:1px solid var(--line);
      padding:14px;
      display:grid;
      grid-template-columns:1fr auto;
      gap:10px;
      background:#fff;
    }
    textarea{
      resize:none;
      min-height:56px;
      max-height:160px;
      border-radius:14px;
      border:1px solid var(--line);
      padding:12px 14px;
      outline:none;
      font:inherit;
      color:var(--ink);
      background:#fff;
    }
    textarea:focus{border-color:#9fb7ea; box-shadow:0 0 0 3px rgba(33,102,217,.1)}
    button{
      border:none;
      border-radius:14px;
      padding:0 22px;
      font-weight:700;
      font-size:15px;
      color:white;
      background:linear-gradient(135deg,var(--accent),#1b84d8);
      cursor:pointer;
      transition:transform .06s ease, opacity .2s ease;
    }
    button:active{transform:translateY(1px)}
    button:disabled{opacity:.55;cursor:not-allowed}
    .hint{
      color:var(--muted);
      font-size:12px;
      margin-top:6px;
    }
    @media (max-width: 720px){
      body{padding:8px}
      .app{height:95vh;border-radius:16px}
      .msg{max-width:92%}
      .head{padding:14px}
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="head">
      <div>
        <div class="brand"><span class="dot"></span>Multiagents Web Chat</div>
        <div class="meta">Ask questions without terminal. Same runtime, same tools.</div>
      </div>
      <div class="meta" id="status">ready</div>
    </div>
    <div class="chat" id="chat"></div>
    <div class="composer">
      <div>
        <textarea id="input" placeholder="Ask anything about your workspace..."></textarea>
        <div class="hint">Enter to send, Shift+Enter for newline.</div>
      </div>
      <button id="send">Send</button>
    </div>
  </div>
  <script>
    const chat = document.getElementById("chat");
    const input = document.getElementById("input");
    const sendBtn = document.getElementById("send");
    const statusEl = document.getElementById("status");
    const SESSION_KEY = "multiagents_web_session";
    let sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
      sessionId = "web_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(SESSION_KEY, sessionId);
    }

    function appendMsg(role, text){
      const el = document.createElement("div");
      el.className = "msg " + role;
      const label = document.createElement("span");
      label.className = "label";
      label.textContent = role === "user" ? "You" : "Assistant";
      el.appendChild(label);
      el.appendChild(document.createTextNode(text));
      chat.appendChild(el);
      chat.scrollTop = chat.scrollHeight;
    }

    async function send(){
      const q = input.value.trim();
      if (!q) return;
      appendMsg("user", q);
      input.value = "";
      input.style.height = "56px";
      sendBtn.disabled = true;
      statusEl.textContent = "thinking...";
      try{
        const resp = await fetch("/api/chat", {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({message: q, session_id: sessionId})
        });
        const data = await resp.json();
        if (!resp.ok) {
          appendMsg("bot", "Request failed: " + (data.error || resp.statusText));
        } else {
          appendMsg("bot", data.reply || "(empty reply)");
          statusEl.textContent = "trace: " + (data.trace_id || "n/a");
        }
      } catch(err){
        appendMsg("bot", "Network error: " + err);
      } finally {
        sendBtn.disabled = false;
        statusEl.textContent = statusEl.textContent === "thinking..." ? "ready" : statusEl.textContent;
      }
    }

    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        send();
      }
    });
    input.addEventListener("input", () => {
      input.style.height = "56px";
      input.style.height = Math.min(input.scrollHeight, 160) + "px";
    });

    appendMsg("bot", "Web chat is ready. Ask your first question.");
  </script>
</body>
</html>
"""


def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def build_handler(app: MultiAgentSystem, responder: ChatResponder):
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path in {"/", "/index.html"}:
                body = HTML_PAGE.encode("utf-8")
                self._send(200, body, "text/html; charset=utf-8")
                return
            self._send(404, _json_bytes({"ok": False, "error": "not found"}))

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                self._send(404, _json_bytes({"ok": False, "error": "not found"}))
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
            except Exception:
                length = 0
            raw = self.rfile.read(max(0, length))
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send(400, _json_bytes({"ok": False, "error": "invalid JSON body"}))
                return

            message = str(data.get("message", "")).strip()
            if not message:
                self._send(400, _json_bytes({"ok": False, "error": "message is required"}))
                return
            session_id = str(data.get("session_id", "")).strip() or f"web_{uuid.uuid4().hex[:12]}"

            try:
                with lock:
                    msg, _state = app.run(message, session_id=session_id)
                content = msg.get("content", {}) if isinstance(msg, dict) else {}
                trace = ""
                if isinstance(content, dict):
                    trace = str(content.get("trace_id") or "")
                if not trace:
                    trace = str((msg or {}).get("metadata", {}).get("trace_id", ""))
                reply = responder.render(user_input=message, result=content if isinstance(content, dict) else {}, trace=trace)
                self._send(
                    200,
                    _json_bytes(
                        {
                            "ok": True,
                            "reply": reply,
                            "trace_id": trace,
                            "structured": content,
                            "session_id": session_id,
                        }
                    ),
                )
            except Exception as e:
                self._send(500, _json_bytes({"ok": False, "error": f"internal error: {e}"}))

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Web chatbot for MultiAgentSystem")
    parser.add_argument("--workspace", default=".", help="workspace root path")
    parser.add_argument("--model", default="gpt-4o", help="LLM model used by responder")
    parser.add_argument("--host", default="127.0.0.1", help="bind host")
    parser.add_argument("--port", type=int, default=7860, help="bind port")
    parser.add_argument("--open", action="store_true", help="open browser automatically")
    args = parser.parse_args()

    app = MultiAgentSystem(workspace=args.workspace)
    responder = ChatResponder(model=args.model)
    handler = build_handler(app=app, responder=responder)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"[web_chat] running at {url}")
    print(f"[web_chat] workspace={args.workspace}")
    if args.open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    server.serve_forever()


if __name__ == "__main__":
    main()

