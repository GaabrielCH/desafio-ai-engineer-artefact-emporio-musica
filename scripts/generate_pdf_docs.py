"""Generates the executive English PDF of the Project README & Technical Documentation for Artefact submission."""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_OUT = BASE_DIR / "docs" / "readme_documentation_en.html"
PDF_TARGETS = [
    BASE_DIR / "Documentacao_README_AI_Engineer_Artefact.pdf",
    BASE_DIR / "Documentation_README_AI_Engineer_Artefact.pdf",
    BASE_DIR.parent / "Documentacao_README_AI_Engineer_Artefact.pdf",
    BASE_DIR.parent / "Documentation_README_AI_Engineer_Artefact.pdf",
]

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Technical Documentation & README — AI Engineer Technical Challenge (Artefact)</title>
<style>
  @page {
    size: A4;
    margin: 15mm 15mm 15mm 15mm;
  }
  * {
    box-sizing: border-box;
  }
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 9.8pt;
    line-height: 1.46;
    color: #1e293b;
    margin: 0;
    padding: 0;
  }
  .header-banner {
    border-bottom: 3px solid #e11d48;
    padding-bottom: 11px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }
  .header-title h1 {
    font-size: 17.5pt;
    color: #0f172a;
    margin: 0 0 4px 0;
    letter-spacing: -0.3px;
  }
  .header-title p {
    font-size: 9.8pt;
    color: #475569;
    margin: 0;
  }
  .header-meta {
    text-align: right;
    font-size: 8.5pt;
    color: #475569;
  }
  .repo-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #0f172a;
    border-radius: 6px;
    padding: 9px 14px;
    margin-bottom: 14px;
    font-size: 9.3pt;
  }
  .repo-box a {
    color: #be123c;
    font-weight: 600;
    text-decoration: none;
  }
  h2 {
    font-size: 12.6pt;
    color: #0f172a;
    border-bottom: 1.5px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 16px;
    margin-bottom: 9px;
    page-break-after: avoid;
  }
  h3 {
    font-size: 10.5pt;
    color: #1e293b;
    margin-top: 11px;
    margin-bottom: 5px;
    page-break-after: avoid;
  }
  p {
    margin: 0 0 7px 0;
  }
  ul, ol {
    margin: 0 0 9px 0;
    padding-left: 20px;
  }
  li {
    margin-bottom: 4px;
  }
  code {
    font-family: 'Cascadia Code', Consolas, 'Courier New', monospace;
    font-size: 8.6pt;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 3px;
  }
  pre {
    background: #0f172a;
    color: #f8fafc;
    padding: 9px 12px;
    border-radius: 6px;
    font-size: 8.1pt;
    line-height: 1.38;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 6px 0 11px 0;
    page-break-inside: avoid;
  }
  pre code {
    background: transparent;
    color: inherit;
    padding: 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 7px 0 13px 0;
    font-size: 8.9pt;
    page-break-inside: avoid;
  }
  th {
    background: #0f172a;
    color: #ffffff;
    text-align: left;
    padding: 6px 9px;
    font-weight: 600;
  }
  td {
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 9px;
    vertical-align: top;
  }
  tr:nth-child(even) td {
    background: #f8fafc;
  }
  .arch-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    margin: 8px 0 13px 0;
    text-align: center;
    page-break-inside: avoid;
  }
  .card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
    margin: 7px 0 12px 0;
  }
  .card {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 11px;
    background: #ffffff;
    page-break-inside: avoid;
  }
  .card h4 {
    margin: 0 0 4px 0;
    font-size: 9.5pt;
    color: #be123c;
  }
  .card p {
    margin: 0;
    font-size: 8.6pt;
    color: #334155;
  }
  .example-box {
    border: 1px solid #cbd5e1;
    border-left: 4px solid #be123c;
    background: #fff;
    border-radius: 5px;
    padding: 7px 11px;
    margin-bottom: 8px;
    page-break-inside: avoid;
  }
  .example-box h4 {
    margin: 0 0 3px 0;
    font-size: 9.5pt;
    color: #0f172a;
  }
  .example-box p {
    margin: 0;
    font-size: 8.6pt;
    color: #334155;
  }
</style>
</head>
<body>

<div class="header-banner">
  <div class="header-title">
    <h1>Empório da Música — AI Customer Support Agent</h1>
    <p>Technical Challenge — AI Engineer (Artefact) | Project README &amp; Architecture Documentation</p>
  </div>
  <div class="header-meta">
    <strong>Author:</strong> Gabriel Camlofski Horst<br>
    <strong>Stack:</strong> Python 3.10+ | SQLite | Hybrid RAG | ReAct
  </div>
</div>

<div class="repo-box">
  <strong>🔗 Public GitHub Repository:</strong>
  <a href="https://github.com/GaabrielCH/desafio-ai-engineer-artefact-emporio-musica">
    https://github.com/GaabrielCH/desafio-ai-engineer-artefact-emporio-musica
  </a><br>
  <span>Includes modular source code (<code>src/</code>), automated test suite (<code>tests/</code>), 5 full multi-turn conversation transcripts (<code>examples/</code>), and a progressive Git commit history.</span>
</div>

<h2>1. Overview &amp; System Architecture</h2>
<p>
  <strong>Empório da Música</strong> (a musical instrument store located in Campo Grande/MS, Brazil) requires an AI assistant capable of handling two fundamentally different information retrieval paradigms:
  <strong>(1) Structured Transactional Data (<code>data/*.csv</code>)</strong> — product catalog, live stock levels, pricing, active vs. expired promotions, and customer orders — which require zero numerical hallucination; and
  <strong>(2) Unstructured Normative Policies (<code>data/políticas_da_loja.pdf</code>)</strong> — return/exchange rules, consumer warranty (CDC), shipping modalities, business hours, and store scope guardrails.
</p>
<p>
  To solve both requirements with production-grade reliability, we implemented a <strong>Hybrid Agent Architecture combining Function Calling (ReAct) + Sanitized Relational SQLite Store + Tri-Modal Policy RAG with Reciprocal Rank Fusion (RRF)</strong>:
</p>

<div class="arch-container">
  <svg width="680" height="210" viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
      </marker>
    </defs>
    <!-- Customer -->
    <rect x="10" y="72" width="115" height="60" rx="6" fill="#0f172a" />
    <text x="67" y="99" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">Customer (CLI/API)</text>
    <text x="67" y="115" fill="#cbd5e1" font-size="9" text-anchor="middle">Text Messages</text>

    <!-- Agent + Memory -->
    <rect x="155" y="52" width="160" height="100" rx="6" fill="#fff1f2" stroke="#e11d48" stroke-width="1.8" />
    <text x="235" y="77" fill="#9f1239" font-size="11" font-weight="bold" text-anchor="middle">EmporioMusicaAgent</text>
    <text x="235" y="93" fill="#334155" font-size="9" text-anchor="middle">ReAct Loop + Store Persona</text>
    <text x="235" y="109" fill="#334155" font-size="9" text-anchor="middle">Multi-LLM (Gemini/OpenAI/</text>
    <text x="235" y="122" fill="#334155" font-size="9" text-anchor="middle">Groq/Ollama + Local Engine)</text>
    <text x="235" y="139" fill="#0f172a" font-size="8.5" font-weight="bold" text-anchor="middle">SQLite Session Memory</text>

    <!-- AgentToolkit -->
    <rect x="350" y="62" width="125" height="80" rx="6" fill="#f1f5f9" stroke="#475569" stroke-width="1.5" />
    <text x="412" y="89" fill="#0f172a" font-size="10.5" font-weight="bold" text-anchor="middle">AgentToolkit</text>
    <text x="412" y="105" fill="#334155" font-size="8.8" text-anchor="middle">8 Function Calling</text>
    <text x="412" y="119" fill="#334155" font-size="8.8" text-anchor="middle">Tools + Guardrails</text>

    <!-- SQLite Store -->
    <rect x="510" y="12" width="160" height="88" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5" />
    <text x="590" y="33" fill="#1d4ed8" font-size="10" font-weight="bold" text-anchor="middle">Operational SQLite (CSVs)</text>
    <text x="590" y="49" fill="#334155" font-size="8.5" text-anchor="middle">products, promotions, orders</text>
    <text x="590" y="62" fill="#334155" font-size="8.5" text-anchor="middle">customers, order_items</text>
    <text x="590" y="75" fill="#1e40af" font-size="8.5" font-weight="bold" text-anchor="middle">+ return_requests (Reverse)</text>
    <text x="590" y="88" fill="#1e40af" font-size="8.5" font-weight="bold" text-anchor="middle">+ complaint_tickets (SAC)</text>

    <!-- Policy RAG -->
    <rect x="510" y="115" width="160" height="82" rx="6" fill="#ecfdf5" stroke="#059669" stroke-width="1.5" />
    <text x="590" y="136" fill="#047857" font-size="10" font-weight="bold" text-anchor="middle">PolicyRAG (PDF Manual)</text>
    <text x="590" y="152" fill="#334155" font-size="8.5" text-anchor="middle">10 Semantic Sections</text>
    <text x="590" y="165" fill="#334155" font-size="8.5" text-anchor="middle">TF-IDF + Char N-Gram + SVD</text>
    <text x="590" y="179" fill="#065f46" font-size="8.5" font-weight="bold" text-anchor="middle">Reciprocal Rank Fusion (RRF)</text>

    <!-- Arrows -->
    <line x1="125" y1="102" x2="153" y2="102" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" marker-start="url(#arrow)" />
    <line x1="315" y1="102" x2="348" y2="102" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)" marker-start="url(#arrow)" />
    <line x1="475" y1="85" x2="508" y2="59" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)" />
    <line x1="475" y1="119" x2="508" y2="152" stroke="#059669" stroke-width="1.5" marker-end="url(#arrow)" />
  </svg>
</div>

<h2>2. Technical Decisions &amp; Justification</h2>
<table>
  <thead>
    <tr>
      <th style="width:22%;">Decision Area</th>
      <th style="width:26%;">Chosen Approach</th>
      <th style="width:52%;">Technical Justification</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Agent Architecture</strong></td>
      <td><strong>Hybrid: Function Calling (ReAct) + Relational SQL + Policy RAG</strong></td>
      <td>Tabular data (<code>products.csv</code>, <code>orders.csv</code>, <code>promotions.csv</code>) requires exact numerical filtering (<code>price &lt;= 1000</code>, <code>stock &gt; 0</code>, <code>is_active == 1</code>) and relational joins, where pure vector RAG would hallucinate figures. Conversely, the PDF policy manual is best served by structural section-based RAG.</td>
    </tr>
    <tr>
      <td><strong>Policy Retrieval (PDF RAG)</strong></td>
      <td><strong>Section Chunking + Tri-Modal (Word TF-IDF + Char N-Grams + LSA/SVD Dense) + RRF</strong></td>
      <td>The 8-page PDF is segmented into its 10 numbered semantic sections (preserving payment/shipping tables intact). Retrieval fuses lexical word n-grams, character n-grams (typo-resilient), and L2-normalized dense semantic vectors (<code>TruncatedSVD</code>) via <em>Reciprocal Rank Fusion (RRF)</em>.</td>
    </tr>
    <tr>
      <td><strong>Deterministic Business Logic</strong></td>
      <td><strong>8 Specialized Python Tools with Built-in Calculators</strong></td>
      <td>Critical financial and legal rules — 5% PIX discount non-cumulativity with active promos (Sec. 6.2), tiered interest-free installments (min. R$ 50 for 1–3x; R$ 80 for 4–6x; R$ 100 for 7–12x — Sec. 3.1), and calendar-day windows for Buyer's Remorse (7 days) and Warranty (30/90 days) — are computed deterministically in Python.</td>
    </tr>
    <tr>
      <td><strong>LLM Provider &amp; Model</strong></td>
      <td><strong>Multi-Provider (Gemini, OpenAI, Groq, Ollama) + Local ReAct Fallback</strong></td>
      <td>Supports native API Function Calling (<code>gemini-2.5-flash</code>, <code>gpt-4o-mini</code>, <code>llama-3.3-70b</code>) and includes a zero-config deterministic local ReAct engine (<code>LLM_PROVIDER=auto</code>) so evaluators can run and test the entire system out-of-the-box after <code>git clone</code> even without external API keys.</td>
    </tr>
    <tr>
      <td><strong>Conversation Persistence</strong></td>
      <td><strong>SQLite (<code>data/chat_history.db</code>)</strong></td>
      <td>Persists sessions, user/assistant turns, and full JSON tool call traces, enabling multi-turn coreference resolution (e.g., <em>"What about its installments?"</em>) and auditability.</td>
    </tr>
  </tbody>
</table>

<h2>3. Data Sanitization, Detected Anomalies &amp; Documented Assumptions</h2>
<p>During exploratory data analysis of <code>data/*.csv</code> and <code>data/políticas_da_loja.pdf</code>, we identified and programmatically handled (<code>src/database.py</code>, <code>src/policy_rag.py</code>) the following edge cases:</p>
<ul>
  <li><strong>Active Product with Zero Stock (<code>out_of_stock</code>):</strong> Acoustic guitar <em>Giannini GF-3D Dreadnought Sunburst</em> (<code>product_id=96</code>) has <code>status='active'</code> but <code>stock_quantity=0</code>. Per Section 7.3, it is excluded from available searches and, when queried directly, the tool flags unavailability and automatically recommends 3 in-stock alternatives.</li>
  <li><strong>Discontinued Products with Residual Stock (<code>discontinued</code>):</strong> Bass <em>Ibanez Bass 2X</em> (<code>product_id=136</code>) has <code>stock_quantity=13</code> but <code>status='discontinued'</code> (along with 7-string guitar <em>Shelby SN-7C</em>, ID 113). The <code>discontinued</code> status takes precedence and the agent suggests active equivalents (Section 7.3).</li>
  <li><strong>Active vs. Expired Promotions &amp; PIX Non-Cumulativity:</strong> Out of 25 rows in <code>promotions.csv</code>, only <strong>4 are active (<code>is_active=1</code>)</strong>: <em>Kalani KAL-700T</em> (-10%), <em>Ohana CK-20</em> (-20%), <em>Crafter HT-100</em> (-18%), and <em>Taylor 110e</em> (-8%). The remaining 21 (including <em>Takamine GD20</em> at 12%) are expired (<code>is_active=0</code>). The agent transparently informs when a past promotion has ended (Section 7.3) and prevents stacking the 5% PIX discount on already discounted items (Section 6.2).</li>
  <li><strong>Title vs. Description Mismatches (IDs 135–144) &amp; Empty Categories (IDs 6, 7, 8):</strong> Synthetic items where the description mentions a different brand than the title are flagged with a <code>data_anomaly</code> prioritizing the canonical <code>name</code>. Categories <em>Wind Instruments (Woodwinds/Brass)</em> and <em>Orchestral Strings</em> (0 rows in <code>products.csv</code>) return a transparent stock notice.</li>
  <li><strong>PDF Internal Ambiguities Reconciled:</strong> (a) Section 1.2 lists phone/WhatsApp <code>(67) 3341-4444</code> while Section 7 lists <code>(67) 3321-4500</code>; the agent provides both (physical store vs. remote WhatsApp central). (b) Table 3 summarizes a R$ 100 minimum installment, while Section 3.1 details the exact tiers: R$ 50 (1–3x), R$ 80 (4–6x), and R$ 100 (7–12x), which we enforced in the payment calculator.</li>
</ul>

<h2>4. Production Evolutions Implemented Beyond Base Scope</h2>
<div class="card-grid">
  <div class="card">
    <h4>🔒 1. LGPD 2-Factor Verification &amp; PII Masking</h4>
    <p>Compliant with Section 9 (LGPD): querying an order by ID alone (e.g., <code>#7</code>) masks customer PII (<code>le***a@jmail.com</code>, <code>(67) *****-0123</code>). Providing a matching 2nd factor (name, email, or phone) unlocks <code>verificado_2_fatores</code>.</p>
  </div>
  <div class="card">
    <h4>🚚 2. Weight/Cubage &amp; Regional Tariff Shipping Engine</h4>
    <p>Estimates package weight/dimensions by category (Ukulele 1.2 kg; Acoustic Guitar 3.2 kg; Electric Guitar 4.8 kg; Drums 28 kg) + regional tariff calculation (MS Interior vs. Other States) + 1.5% <em>ad valorem</em> insurance for PAC, Jadlog, and SEDEX.</p>
  </div>
  <div class="card">
    <h4>🎫 3. Reverse Logistics &amp; SAC Escalation Write Tools</h4>
    <p>Transactional tools <code>registrar_solicitacao_troca_devolucao</code> (issues protocol <code>TROCA-2026-XXXX</code> and prepaid Correios reverse code <code>LOG-REV-BR...</code>) and <code>abrir_chamado_reclamacao</code> (protocol <code>SAC-2026-XXXX</code> with 24-business-hour SLA — Sec. 7.3).</p>
  </div>
  <div class="card">
    <h4>🧠 4. Dense Semantic RAG (LSA/SVD) + RRF</h4>
    <p>Upgraded <code>PolicyRAG</code> combining 3 retrieval signals (sublinear word TF-IDF, char_wb 3..5 n-grams, and L2-normalized <code>TruncatedSVD</code> dense semantic embeddings) fused via <em>Reciprocal Rank Fusion (RRF)</em>.</p>
  </div>
</div>

<h2>5. Setup &amp; Execution Instructions</h2>
<pre><code># 1. Clone the repository and install dependencies
git clone https://github.com/GaabrielCH/desafio-ai-engineer-artefact-emporio-musica.git
cd desafio-ai-engineer-artefact-emporio-musica
pip install -r requirements.txt

# 2. Configure environment variables (.env is optional: works out-of-the-box with the local ReAct
#    engine, or connects natively to GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, OPENAI_BASE_URL)
cp .env.example .env

# 3. Start the interactive CLI chat or run the automated 5-scenario terminal demonstration
python main.py
python main.py --demo

# 4. Run the automated test suite (8 unit &amp; integration tests via pytest)
python -m pytest -v</code></pre>

<h2>6. Conversation Examples Included in the Repository (<code>examples/</code>)</h2>
<div class="example-box">
  <h4>📄 01_catalogo_violoes_ate_1000.md — Catalog Search &amp; Out-of-Stock / Discontinued Handling</h4>
  <p>Lists the 12 available acoustic guitars up to R$ 1,000.00 (grouped into nylon and steel strings with PIX and installment pricing). In Turn 2, handles queries for <em>Giannini GF-3D</em> (0 stock) and <em>Shelby SN-7C</em> (discontinued), applying Section 7.3 and recommending in-stock alternatives.</p>
</div>
<div class="example-box">
  <h4>📄 02_preco_promocoes_e_pagamento_takamine.md — Pricing, Expired vs. Active Promotions &amp; PIX Rules</h4>
  <p>Details the <em>Takamine GD20</em> (R$ 2,199.00 | PIX R$ 2,089.05 | 12x of R$ 183.25 | combined payment &gt; R$ 2,000), transparently informs that its past 12% promo expired (<code>is_active=0</code>), and explains PIX non-cumulativity on the actively discounted <em>Taylor 110e</em> (-8%).</p>
</div>
<div class="example-box">
  <h4>📄 03_devolucao_arrependimento_e_rastreio_pedidos.md — Non-Trivial Scenario: CDC Policies + Live Order + Reverse Logistics</h4>
  <p>Explains Section 4 return rules, verifies <strong>Order #7</strong> for customer <em>Letícia Gonçalves Rocha</em> (2FA LGPD verification), confirms eligibility within the 7-calendar-day delivery window, automatically issues protocol <code>TROCA-2026-0007</code> + prepaid reverse code <code>LOG-REV-BR0007EMP26BR</code>, and tracks <strong>Order #8</strong> (<code>BRJL5544332BR</code>).</p>
</div>
<div class="example-box">
  <h4>📄 04_informacoes_gerais_frete_e_horario.md — Store Info, Opening Hours &amp; Regional Shipping Quotes</h4>
  <p>Provides store address, hours (Mon–Fri 09:00–18:00, Sat 09:00–13:00), and compares shipping for a R$ 600 guitar to <strong>Campo Grande/MS</strong> (Free &gt; R$ 500 via own courier in 1–3 business days) vs. <strong>Dourados/MS</strong> (PAC R$ 55.10, Jadlog R$ 67.34, SEDEX R$ 87.46 with insurance included).</p>
</div>
<div class="example-box">
  <h4>📄 05_fora_de_escopo_acessorios_e_off_topic.md — Scope Guardrails (Accessories &amp; Off-Topic Requests)</h4>
  <p>Politely declines accessory requests (Elixir strings, picks, and guitar amplifier — Sections 1 &amp; 7.1, as the store sells exclusively musical instruments) and redirects off-topic questions (carrot cake recipe) while maintaining the store persona.</p>
</div>

<h2>7. Known Limitations, Next Steps &amp; AI Assistant Workflow</h2>
<ul>
  <li><strong>Known Limitations &amp; Production Next Steps:</strong> (1) Bind the 2FA LGPD verification automatically to the authenticated WhatsApp Business Cloud API phone token or SMS/Email OTP; (2) Connect shipping and reverse-logistics tools to live Correios/Melhor Envio REST APIs and ERP inventory webhooks; (3) Expose a web dashboard for human agents to manage the 24-hour SLA queue in <code>complaint_tickets</code>.</li>
  <li><strong>AI Coding Assistant Workflow:</strong> Developed using <strong>Antigravity (Google DeepMind)</strong> in an agentic pair-programming workflow: (1) automated exploratory audit of all CSVs and OCR of the PDF manual to map data anomalies prior to coding; (2) architectural separation between relational SQLite tools and section-based Policy RAG; (3) modular implementation validated by 8 automated <code>pytest</code> tests; and (4) reproducible generation of the 5 conversation transcripts in <code>examples/</code>.</li>
</ul>

</body>
</html>
"""


def main() -> None:
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(HTML_CONTENT, encoding="utf-8")

    browsers = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    browser_exe = next((b for b in browsers if b.exists()), None)
    if not browser_exe:
        raise RuntimeError("No Chromium browser (Chrome/Edge) found for PDF generation.")

    for target_pdf in PDF_TARGETS:
        cmd = [
            str(browser_exe),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={target_pdf}",
            HTML_OUT.resolve().as_uri(),
        ]
        subprocess.run(cmd, check=True)
        print(f"Generated English PDF: {target_pdf} ({target_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
