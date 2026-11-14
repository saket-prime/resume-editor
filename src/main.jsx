import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Download, FileText, IndianRupee, CalendarDays, UserRound, Sparkles, CheckCircle2, RotateCcw, Eye, AlertCircle } from "lucide-react";
import "./styles.css";

const TEMPLATE_PATH = "/templates/Techno_Inkai_Template.docx";
const COMPANY = "Techno Inkai";

function ordinal(n) {
  if (n % 100 >= 11 && n % 100 <= 13) return `${n}th`;
  const suffix = ["th", "st", "nd", "rd"][Math.min(n % 10, 3)] || "th";
  return `${n}${suffix}`;
}

function formatDate(date = new Date()) {
  return `${ordinal(date.getDate())} ${date.toLocaleString("en-IN", { month: "long" })} ${date.getFullYear()}`;
}

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0
  }).format(value);
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
}

function cleanFileName(name) {
  return name.trim().replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "");
}

async function replaceDocxPlaceholders(arrayBuffer, values) {
  const zip = await JSZip.loadAsync(arrayBuffer);
  const docFile = zip.file("word/document.xml");
  if (!docFile) throw new Error("The template is not a valid Word document.");

  let xml = await docFile.async("string");

  // The supplied template has each placeholder intact in document.xml.
  // This replacement changes only the three placeholder values and leaves
  // the rest of the DOCX package untouched.
  for (const [placeholder, value] of Object.entries(values)) {
    xml = xml.split(placeholder).join(escapeXml(String(value)));
  }

  zip.file("word/document.xml", xml);
  return zip.generateAsync({
    type: "blob",
    mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    compression: "DEFLATE"
  });
}

function escapeXml(value) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

async function convertDocxToPdf(docxBlob, fileName) {
  // The frontend preserves the original DOCX exactly. For true DOCX→PDF
  // rendering, the production app sends the modified DOCX to /api/convert.
  // This keeps PDF conversion on the server where LibreOffice can render it.
  const form = new FormData();
  form.append("file", docxBlob, `${fileName}.docx`);
  const response = await fetch("/api/convert", { method: "POST", body: form });
  if (!response.ok) throw new Error(await response.text() || "PDF conversion failed.");
  return response.blob();
}

function App() {
  const [name, setName] = useState("");
  const [salary, setSalary] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const today = useMemo(() => formatDate(), []);
  const monthly = Number(salary);
  const perProject = monthly > 0 ? Math.round(monthly / 4) : 0;
  const valid = name.trim().length >= 2 && monthly > 0;

  async function createFiles() {
    if (!valid || busy) return;
    setBusy(true);
    setError("");
    setStatus("Loading your Word template…");

    try {
      const templateResponse = await fetch(TEMPLATE_PATH);
      if (!templateResponse.ok) throw new Error("Template file was not found. Check the templates folder.");

      const templateBuffer = await templateResponse.arrayBuffer();
      const values = { "{{1}}": today, "{{2}}": name.trim(), "{{3}}": formatNumber(perProject) };
      const docxBlob = await replaceDocxPlaceholders(templateBuffer, values);
      const base = cleanFileName(name);

      setStatus("Converting the completed Word document to PDF…");
      const pdfBlob = await convertDocxToPdf(docxBlob, base);

      const pdfUrl = URL.createObjectURL(pdfBlob);
      const a = document.createElement("a");
      a.href = pdfUrl;
      a.download = `${base}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(pdfUrl);

      setStatus("Offer letter generated and downloaded successfully.");
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setName("");
    setSalary("");
    setStatus("");
    setError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><FileText size={20} /></div>
          <div><div className="brand-name">{COMPANY}</div><div className="brand-sub">Offer Letter Generator</div></div>
        </div>
        <div className="secure-pill"><CheckCircle2 size={15} /> Template-based generation</div>
      </header>

      <main className="main">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow"><Sparkles size={14} /> Ready in seconds</span>
            <h1>Generate your offer letter<br /><span>without editing Word files.</span></h1>
            <p>Enter the candidate name and monthly salary. Your original Word template stays intact while only the three placeholders are replaced.</p>
          </div>
          <div className="date-card">
            <CalendarDays size={19} />
            <div><span>Today's date</span><strong>{today}</strong></div>
          </div>
        </section>

        <section className="workspace">
          <div className="form-card">
            <div className="card-heading">
              <div className="heading-left"><span className="step">01</span><div><h2>Candidate details</h2><p>Only two inputs are required.</p></div></div>
              <button className="icon-btn" onClick={reset} aria-label="Reset"><RotateCcw size={17} /></button>
            </div>

            <label htmlFor="name">Candidate name</label>
            <div className="input-wrap">
              <UserRound size={18} />
              <input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Kotha Himaja" autoComplete="off" />
            </div>

            <label htmlFor="salary">Monthly salary</label>
            <div className="input-wrap">
              <IndianRupee size={18} />
              <input id="salary" type="number" min="1" step="1" value={salary} onChange={e => setSalary(e.target.value)} placeholder="e.g. 22000" inputMode="numeric" />
            </div>
            <p className="helper">The monthly salary is automatically divided by 4 because the template specifies up to 4 projects per month.</p>

            <div className={`calculation ${monthly > 0 ? "active" : ""}`}>
              <div><span>Per project</span><strong>{perProject ? formatINR(perProject) : "—"}</strong></div>
              <span className="formula">Monthly salary ÷ 4</span>
            </div>

            <button className="primary-btn" disabled={!valid || busy} onClick={createFiles}>
              <Download size={18} /> {busy ? "Generating…" : "Generate & download PDF"}
            </button>

            <div className="template-note"><Eye size={15} /><span>Uses the DOCX stored at <code>public/templates/Techno_Inkai_Template.docx</code>.</span></div>

            {status && <div className="status"><CheckCircle2 size={16} /> {status}</div>}
            {error && <div className="error"><AlertCircle size={16} /> {error}</div>}
          </div>

          <div className="preview-card">
            <div className="preview-head">
              <div className="heading-left"><span className="step">02</span><div><h2>Live preview</h2><p>Preview of the fields being inserted into your template.</p></div></div>
              <span className="pdf-tag">TEMPLATE</span>
            </div>

            <div className="paper">
              <div className="paper-brand">{COMPANY}</div>
              <div className="paper-date">Date: {today}</div>
              <div className="paper-to">To,<br />Mr./Ms. <strong>{name.trim() || "Candidate Name"}</strong>,</div>
              <div className="highlight-line">You will receive INR <strong>{perProject ? formatNumber(perProject) : "—"}</strong> per project.</div>
              <p>All other wording, formatting, pages, and content come from your original Word template.</p>
              <div className="preview-lock"><CheckCircle2 size={15} /> Original template is used for generation</div>
            </div>
          </div>
        </section>

        <footer className="footer">
          <span>Template-driven • No OCR • No candidate document upload</span>
          <span>© {new Date().getFullYear()} {COMPANY}</span>
        </footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
