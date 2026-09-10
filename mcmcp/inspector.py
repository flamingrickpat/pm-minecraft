"""A small browser UI that makes independent MCP client calls.

The inspector has no Minecraft runtime. Each request creates an MCP client,
uses the public HTTP transport, and closes the client when the request ends.
"""

from __future__ import annotations

import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Any

from fastmcp import Client

from .config import Configuration

PATH = "/mcp"


PAGE = """<!doctype html><title>Minecraft MCP inspector</title><style>
*{box-sizing:border-box}body{margin:0;background:#151515;color:#ddd;font:14px system-ui;display:grid;grid-template-columns:25% 45% 30%;grid-template-rows:1fr 180px;height:100vh}section{padding:12px;border:1px solid #444;overflow:auto}#tools{grid-column:1}#call{grid-column:2}#result{grid-column:3}#log{grid-column:1/4}button{display:block;width:100%;margin:4px 0;padding:8px;background:#333;color:#ddd;border:1px solid #666;text-align:left}button:hover{background:#555}textarea{width:100%;height:45%;background:#111;color:#ddd;border:1px solid #666;padding:8px;font-family:ui-monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere}img{max-width:100%;height:auto}</style>
<section id=tools><h3>Tools</h3><div id=list>Loading...</div></section><section id=call><h3 id=name>Select a tool</h3><pre id=description></pre><textarea id=args>{}</textarea><button id=send>Send</button></section><section id=result><h3>State and screenshot</h3><pre id=state></pre><img id=screen></section><section id=log><h3>Log</h3><pre id=events></pre></section><script>
let selected='';const out=document.querySelector('#events');const name=document.querySelector('#name');const description=document.querySelector('#description');const args=document.querySelector('#args');const send=document.querySelector('#send');const state=document.querySelector('#state');const screen=document.querySelector('#screen');function log(s){out.textContent+=new Date().toLocaleTimeString()+' '+s+'\\n';out.scrollTop=out.scrollHeight}async function load(){try{let tools=await fetch('/api/tools').then(r=>r.json());let list=document.querySelector('#list');list.textContent='';for(let tool of tools){let b=document.createElement('button');b.textContent=tool.name;b.onclick=()=>{selected=tool.name;name.textContent=tool.name;description.textContent=tool.description||'';args.value='{}';};list.append(b)}}catch(e){log('Tool list error: '+e)}}send.onclick=async()=>{if(!selected)return log('Select a tool first.');let arguments;try{arguments=JSON.parse(args.value)}catch(e){return log('Argument JSON error: '+e)}log('Calling '+selected);try{let data=await fetch('/api/call',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name:selected,arguments})}).then(async r=>{let d=await r.json();if(!r.ok)throw Error(d.error);return d});state.textContent=JSON.stringify(data.structuredContent||data.content,null,2);screen.src=data.image?'data:image/png;base64,'+data.image:'';log(selected+' complete')}catch(e){log(selected+' error: '+e)}};load();</script>"""


def _mcp_url(configuration: Configuration) -> str:
    return f"http://127.0.0.1:{configuration.mcp_port}{PATH}"


async def _list_tools(url: str) -> list[dict[str, Any]]:
    async with Client(url) as client:
        return [tool.model_dump(by_alias=True, mode="json") for tool in await client.list_tools()]


async def _call_tool(url: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async with Client(url) as client:
        result = await client.call_tool(name, arguments)
    content = [item.model_dump(by_alias=True, mode="json") for item in result.content]
    image = next((item["data"] for item in content if item["type"] == "image"), None)
    return {"content": content, "structuredContent": result.structured_content, "image": image}


class InspectorRequestHandler(BaseHTTPRequestHandler):
    mcp_url = ""

    def _reply(self, code: int, body: Any) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/":
            data = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/api/tools":
            try:
                self._reply(200, asyncio.run(_list_tools(self.mcp_url)))
            except Exception as error:
                self._reply(502, {"error": str(error)})
            return
        self._reply(404, {"error": "Not found."})

    def do_POST(self) -> None:
        if self.path != "/api/call":
            self._reply(404, {"error": "Not found."})
            return
        try:
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._reply(200, asyncio.run(_call_tool(self.mcp_url, request["name"], request["arguments"])))
        except Exception as error:
            self._reply(502, {"error": str(error)})

    def log_message(self, format: str, *args: Any) -> None:
        return


def start_inspector(configuration: Configuration) -> str:
    """Start the independent browser inspector and return its browser URL."""
    InspectorRequestHandler.mcp_url = _mcp_url(configuration)
    httpd = ThreadingHTTPServer((configuration.inspector_host, configuration.inspector_port), InspectorRequestHandler)
    threading.Thread(target=httpd.serve_forever, name="mcp-inspector", daemon=True).start()
    return f"http://{configuration.inspector_host}:{httpd.server_port}"
