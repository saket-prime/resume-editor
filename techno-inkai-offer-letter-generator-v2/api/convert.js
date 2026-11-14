import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Busboy from "busboy";

export const config = { api: { bodyParser: false } };

function parseMultipart(req) {
  return new Promise((resolve, reject) => {
    const bb = Busboy({ headers: req.headers });
    let fileBuffer = null;
    let filename = "offer.docx";
    bb.on("file", (_name, file, info) => {
      filename = info.filename || filename;
      const chunks = [];
      file.on("data", c => chunks.push(c));
      file.on("end", () => { fileBuffer = Buffer.concat(chunks); });
    });
    bb.on("finish", () => resolve({ fileBuffer, filename }));
    bb.on("error", reject);
  });
}

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).send("Method not allowed.");

  const { fileBuffer, filename } = await parseMultipart(req);
  if (!fileBuffer) return res.status(400).send("No DOCX file received.");

  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "offer-"));
  const docxPath = path.join(tmp, filename.replace(/[^a-z0-9._-]/gi, "_"));
  await fs.writeFile(docxPath, fileBuffer);

  try {
    const outputDir = tmp;
    await new Promise((resolve, reject) => {
      const p = spawn("libreoffice", [
        "--headless", "--convert-to", "pdf", "--outdir", outputDir, docxPath
      ]);
      let stderr = "";
      p.stderr.on("data", d => { stderr += d.toString(); });
      p.on("close", code => code === 0 ? resolve() : reject(new Error(stderr || `LibreOffice exited with ${code}`)));
      p.on("error", reject);
    });

    const pdfName = path.basename(docxPath, path.extname(docxPath)) + ".pdf";
    const pdf = await fs.readFile(path.join(outputDir, pdfName));
    res.setHeader("Content-Type", "application/pdf");
    res.setHeader("Content-Disposition", `attachment; filename="${pdfName}"`);
    res.status(200).send(pdf);
  } catch (error) {
    res.status(500).send(`PDF conversion failed: ${error.message}`);
  } finally {
    await fs.rm(tmp, { recursive: true, force: true });
  }
}