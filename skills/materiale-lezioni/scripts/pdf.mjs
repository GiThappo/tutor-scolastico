#!/usr/bin/env node
// Stampa in PDF (A4) l'HTML di un argomento con Chrome/Chromium headless.
// Nel piè di pagina: il <title> della pagina e il numero di pagina.
//
//   node pdf.mjs <sorgente.html> <uscita.pdf>
//
// Chrome: CHROME=/percorso, altrimenti cerca google-chrome-stable, google-chrome, chromium, chromium-browser.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [sorgente, uscita] = process.argv.slice(2);
const fine = (msg) => { console.error(msg); process.exit(1); };
if (!sorgente || !uscita) fine("Uso: node pdf.mjs <sorgente.html> <uscita.pdf>");
if (!existsSync(sorgente)) fine(`Non trovo ${sorgente}`);

const chrome = [process.env.CHROME, "google-chrome-stable", "google-chrome", "chromium", "chromium-browser"]
  .filter(Boolean).find((c) => spawnSync(c, ["--version"], { stdio: "ignore" }).status === 0);
if (!chrome) fine("Non trovo Chrome o Chromium: installalo o indica il percorso con CHROME=...");

const profilo = mkdtempSync(join(tmpdir(), "pdf-argomento-"));
const porta = 9400 + Math.floor(Math.random() * 500);
const processo = spawn(chrome, ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${profilo}`,
  "--no-first-run", "--allow-file-access-from-files", "about:blank"], { stdio: "ignore" });
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
const chiudi = () => { processo.kill(); rmSync(profilo, { recursive: true, force: true }); };

try {
  let ws;
  for (let i = 0; i < 60 && !ws; i++) {
    try {
      const pagina = (await (await fetch(`http://127.0.0.1:${porta}/json`)).json()).find((t) => t.type === "page");
      if (pagina) ws = new WebSocket(pagina.webSocketDebuggerUrl);
    } catch { /* Chrome non è ancora pronto */ }
    if (!ws) await pausa(250);
  }
  if (!ws) throw new Error("Chrome non risponde");
  await new Promise((r, e) => { ws.addEventListener("open", r); ws.addEventListener("error", e); });

  let n = 0;
  const attese = new Map();
  const eventi = new Map();
  ws.addEventListener("message", (m) => {
    const d = JSON.parse(m.data);
    if (d.id && attese.has(d.id)) {
      const [ok, ko] = attese.get(d.id);
      attese.delete(d.id);
      d.error ? ko(new Error(d.error.message)) : ok(d.result);
    } else if (d.method && eventi.has(d.method)) eventi.get(d.method)(d.params);
  });
  const cdp = (method, params = {}) => new Promise((ok, ko) => { const id = ++n; attese.set(id, [ok, ko]); ws.send(JSON.stringify({ id, method, params })); });

  await cdp("Page.enable");
  const caricata = new Promise((r) => eventi.set("Page.loadEventFired", r));
  await cdp("Page.navigate", { url: pathToFileURL(resolve(sorgente)).href });
  await caricata;
  await cdp("Runtime.evaluate", { expression: "document.fonts.ready", awaitPromise: true });
  const titolo = (await cdp("Runtime.evaluate", { expression: "document.title" })).result.value ?? "";
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  const { data } = await cdp("Page.printToPDF", {
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: `<div style="font: 8pt sans-serif; color: #777; width: 100%; padding: 0 18mm; display: flex; justify-content: space-between;">
      <span>${esc(titolo)}</span><span class="pageNumber"></span></div>`,
  });
  writeFileSync(uscita, Buffer.from(data, "base64"));
  ws.close();
} catch (e) {
  chiudi();
  fine(`PDF non creato: ${e.message}`);
}
chiudi();

if (!existsSync(uscita) || statSync(uscita).size < 1000) fine(`PDF non creato: ${uscita}`);
const info = spawnSync("pdfinfo", [uscita], { encoding: "utf8" });
const pagine = info.stdout?.match(/Pages:\s+(\d+)/)?.[1];
console.log(`PDF pronto: ${uscita}${pagine ? ` (${pagine} pagine)` : ""}`);
