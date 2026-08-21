"""Manualny tester środowiska weather dla QA — pojedynczy plik, sam stdlib.

Uruchomienie (z katalogu głównego repo):
    .venv\\Scripts\\python.exe tools\\qa_env_tester.py
    (opcjonalnie: --port 8777 --no-browser)

Serwuje lokalny interfejs WWW (domyślnie http://127.0.0.1:8777), z którego
tester wywołuje PRAWDZIWE narzędzia z polagentbench.environments.weather
i ogląda surowe odpowiedzi {ok, result/error, error_code}. Żadnych mocków,
żadnej wstępnej walidacji pól — złe wartości mają docierać do środowiska,
bo testujemy właśnie jego reakcje.

Pola liczbowe (days, value, max_distance_km) są koercjonowane na int/float
tylko jeśli da się je sparsować; inaczej lecą do env jako string — dzięki
temu tester może sprawdzić i złe ZAKRESY (days=8), i złe TYPY (days=abc).

Środowisko żyje przez cały czas działania serwera (alert_id narasta przy
kolejnych send_weather_alert); przycisk "Reset środowiska" woła env.reset({}).
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from polagentbench.environments.weather import WeatherEnvironment

DEFAULT_PORT = 8777

# Pola, które UI wysyła jako tekst, a env oczekuje liczb. Parsowalne wartości
# zamieniamy (int przed float), nieparsowalne przekazujemy surowo.
NUMERIC_FIELDS = {"days", "value", "max_distance_km"}

ENV = WeatherEnvironment()
ENV.reset({})


def coerce_argument(field: str, raw: object) -> object:
    if field not in NUMERIC_FIELDS or not isinstance(raw, str):
        return raw
    text = raw.strip()
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return raw


PAGE_HTML = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>Tester środowiska weather — PolAgentBench QA</title>
<style>
  body { font-family: "Segoe UI", system-ui, sans-serif; margin: 0; background: #f4f5f7; color: #1c2430; }
  .wrap { max-width: 920px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-size: 1.35rem; margin: 0 0 4px; }
  .sub { color: #5a6572; margin: 0 0 20px; font-size: .92rem; }
  .card { background: #fff; border: 1px solid #dde2e8; border-radius: 10px; padding: 18px; margin-bottom: 18px; }
  label { display: block; font-weight: 600; font-size: .9rem; margin: 12px 0 4px; }
  .hint { font-weight: 400; color: #5a6572; font-size: .82rem; }
  select, input[type=text] { width: 100%; box-sizing: border-box; padding: 8px 10px; font-size: 1rem;
    border: 1px solid #b9c2cd; border-radius: 6px; background: #fff; }
  select:focus, input:focus { outline: 2px solid #2563eb33; border-color: #2563eb; }
  .tool-desc { color: #374151; font-size: .9rem; margin-top: 6px; }
  .row-btn { margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; }
  button { padding: 9px 18px; font-size: .95rem; border-radius: 6px; border: 1px solid transparent; cursor: pointer; }
  #btn-call { background: #2563eb; color: #fff; font-weight: 600; }
  #btn-call:hover { background: #1d4ed8; }
  .secondary { background: #fff; border-color: #b9c2cd; color: #374151; }
  .secondary:hover { background: #f1f5f9; }
  pre { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow-x: auto;
    font-size: .85rem; line-height: 1.45; margin: 8px 0 0; }
  .entry { border-left: 5px solid #94a3b8; }
  .entry.ok { border-left-color: #16a34a; }
  .entry.err { border-left-color: #dc2626; }
  .entry-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; }
  .entry-head b { font-size: .98rem; }
  .badge { font-size: .78rem; font-weight: 700; padding: 2px 10px; border-radius: 999px; }
  .badge.ok { background: #dcfce7; color: #166534; }
  .badge.err { background: #fee2e2; color: #991b1b; }
  .meta { color: #5a6572; font-size: .8rem; }
  .section-label { font-size: .8rem; font-weight: 700; color: #5a6572; text-transform: uppercase;
    letter-spacing: .04em; margin-top: 10px; }
  h2 { font-size: 1.05rem; margin: 26px 0 10px; }
  #empty-history { color: #5a6572; font-style: italic; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Tester środowiska weather</h1>
  <p class="sub">PolAgentBench QA — wywołujesz prawdziwe narzędzia środowiska i oglądasz surowe odpowiedzi.
  Pola celowo niczego nie sprawdzają: wpisuj też wartości błędne (puste, days=0, "Atlantyda"), żeby zobaczyć reakcję środowiska.</p>

  <div class="card">
    <label for="tool">Narzędzie</label>
    <select id="tool"></select>
    <div class="tool-desc" id="tool-desc"></div>
    <div id="fields"></div>
    <div class="row-btn">
      <button id="btn-call">Wywołaj</button>
      <button id="btn-reset" class="secondary" title="Czyści stan środowiska (np. licznik wysłanych alertów)">Reset środowiska</button>
      <button id="btn-clear" class="secondary">Wyczyść historię</button>
    </div>
  </div>

  <h2>Historia wywołań (najnowsze na górze)</h2>
  <p id="empty-history">Brak wywołań — wybierz narzędzie, wypełnij pola i kliknij „Wywołaj”.</p>
  <div id="history"></div>
</div>

<script>
const TOOLS = {
  get_weather: {
    desc: "Aktualna pogoda dla miasta.",
    fields: [
      { name: "city", label: "Miasto (city)", hint: "np. Kraków, Łódź — albo celowo: Atlantyda, pusty tekst" },
    ],
  },
  get_forecast: {
    desc: "Prognoza wielodniowa dla miasta.",
    fields: [
      { name: "city", label: "Miasto (city)", hint: "np. Berlin, Gdańsk" },
      { name: "days", label: "Liczba dni (days)", hint: "środowisko akceptuje 1–7 — sprawdź też 0, 8, abc" },
    ],
  },
  send_weather_alert: {
    desc: "Wysyła alert pogodowy o zadanym poziomie.",
    fields: [
      { name: "city", label: "Miasto (city)", hint: "np. Warszawa" },
      { name: "severity", label: "Poziom alertu (severity)", hint: "środowisko akceptuje: low / medium / high — sprawdź też np. wysoka" },
      { name: "message", label: "Treść komunikatu (message)", hint: "dowolny tekst; sprawdź też pusty" },
    ],
  },
  convert_temperature: {
    desc: "Przelicza temperaturę między skalami Celsjusza i Fahrenheita.",
    fields: [
      { name: "value", label: "Wartość temperatury (value)", hint: "np. 7.76 — sprawdź też tekst zamiast liczby" },
      { name: "from_unit", label: "Jednostka źródłowa (from_unit)", hint: "środowisko akceptuje: celsius / fahrenheit" },
      { name: "to_unit", label: "Jednostka docelowa (to_unit)", hint: "środowisko akceptuje: celsius / fahrenheit" },
    ],
  },
  find_nearest_city: {
    desc: "Lista znanych miast w zadanym promieniu od miasta odniesienia.",
    fields: [
      { name: "reference_city", label: "Miasto odniesienia (reference_city)", hint: "np. Warszawa, Poznań, Katowice" },
      { name: "max_distance_km", label: "Promień w km (max_distance_km)", hint: "np. 130 — sprawdź też 0, -5, abc" },
    ],
  },
};

const elTool = document.getElementById("tool");
const elDesc = document.getElementById("tool-desc");
const elFields = document.getElementById("fields");
const elHistory = document.getElementById("history");
const elEmpty = document.getElementById("empty-history");
let counter = 0;

for (const name of Object.keys(TOOLS)) {
  const opt = document.createElement("option");
  opt.value = name;
  opt.textContent = name;
  elTool.appendChild(opt);
}

function renderFields() {
  const spec = TOOLS[elTool.value];
  elDesc.textContent = spec.desc;
  elFields.innerHTML = "";
  for (const f of spec.fields) {
    const label = document.createElement("label");
    label.htmlFor = "f-" + f.name;
    label.innerHTML = f.label + (f.hint ? ' <span class="hint">— ' + f.hint + "</span>" : "");
    const input = document.createElement("input");
    input.type = "text";           // celowo text: zero walidacji po stronie przeglądarki
    input.id = "f-" + f.name;
    input.autocomplete = "off";
    elFields.appendChild(label);
    elFields.appendChild(input);
  }
}
elTool.addEventListener("change", renderFields);
renderFields();

function addEntry(title, badgeOk, sentJson, gotJson) {
  elEmpty.style.display = "none";
  const div = document.createElement("div");
  div.className = "card entry " + (badgeOk ? "ok" : "err");
  const time = new Date().toLocaleTimeString("pl-PL");
  counter += 1;
  div.innerHTML =
    '<div class="entry-head"><b>#' + counter + " · " + title + "</b>" +
    '<span><span class="badge ' + (badgeOk ? 'ok">OK' : 'err">BŁĄD') + "</span>" +
    ' <span class="meta">' + time + "</span></span></div>" +
    (sentJson !== null ? '<div class="section-label">Wysłano</div><pre>' + sentJson + "</pre>" : "") +
    '<div class="section-label">Odpowiedź środowiska</div><pre>' + gotJson + "</pre>";
  elHistory.prepend(div);
}

document.getElementById("btn-call").addEventListener("click", async () => {
  const tool = elTool.value;
  const args = {};
  for (const f of TOOLS[tool].fields) {
    args[f.name] = document.getElementById("f-" + f.name).value;
  }
  try {
    const resp = await fetch("/api/call", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool: tool, arguments: args }),
    });
    const data = await resp.json();
    addEntry(
      tool,
      data.response && data.response.ok === true,
      JSON.stringify(data.request, null, 2),
      JSON.stringify(data.response, null, 2)
    );
  } catch (e) {
    addEntry(tool, false, null, "Brak połączenia z lokalnym serwerem testera: " + e);
  }
});

document.getElementById("btn-reset").addEventListener("click", async () => {
  try {
    const resp = await fetch("/api/reset", { method: "POST" });
    const data = await resp.json();
    addEntry("reset środowiska", true, null, JSON.stringify(data, null, 2));
  } catch (e) {
    addEntry("reset środowiska", false, null, "Brak połączenia z lokalnym serwerem testera: " + e);
  }
});

document.getElementById("btn-clear").addEventListener("click", () => {
  elHistory.innerHTML = "";
  elEmpty.style.display = "";
  counter = 0;
});
</script>
</body>
</html>
"""


class QaHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = PAGE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path == "/api/reset":
            ENV.reset({})
            self._send_json({"ok": True, "info": "Środowisko zresetowane (alerty i log wyczyszczone)."})
            return
        if self.path != "/api/call":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            tool = payload["tool"]
            raw_args = payload.get("arguments", {})
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as exc:
            self._send_json({"request": None, "response": {"ok": False, "error": f"Niepoprawne żądanie: {exc}"}}, 400)
            return
        arguments = {k: coerce_argument(k, v) for k, v in raw_args.items()}
        response = ENV.execute_tool(tool, arguments)
        self._send_json({"request": {"tool": tool, "arguments": arguments}, "response": response})

    def log_message(self, fmt: str, *args: object) -> None:
        pass  # cisza w konsoli — historia jest w przeglądarce


def main() -> None:
    parser = argparse.ArgumentParser(description="Manualny tester środowiska weather (QA).")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true", help="nie otwieraj przeglądarki automatycznie")
    opts = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    url = f"http://127.0.0.1:{opts.port}"
    server = HTTPServer(("127.0.0.1", opts.port), QaHandler)
    print("Tester środowiska weather — PolAgentBench QA")
    print(f"Serwer działa: {url}")
    print("Zatrzymanie: Ctrl+C")
    if not opts.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano.")


if __name__ == "__main__":
    main()
