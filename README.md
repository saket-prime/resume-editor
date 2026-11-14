# Techno Inkai Offer Studio

A mobile-friendly Streamlit app that fills the supplied Word template and downloads a PDF.

## Inputs and rules

- Candidate name is inserted into `{{2}}`.
- Today's date in Asia/Kolkata is inserted into `{{1}}`, e.g. `14th November 2026`.
- CTC is entered in **thousands of rupees**. `16` means ₹16,000; per-project pay is `16 × 1000 ÷ 4 = 4,000`, inserted into `{{3}}`. Decimal results retain up to two decimal places, rounded half up.
- The signature date line stays blank, as in the original template.

The original template is at `templates/offer.docx`. The code changes only placeholder text inside the DOCX ZIP; other document parts, styles, images, page settings and text stay intact. Replacement text inherits the first placeholder run's formatting. Longer names can wrap and change pagination. LibreOffice's PDF renderer can differ from Microsoft Word, especially with unavailable proprietary fonts. Carlito and Caladea are installed as compatible substitutes for Calibri and Cambria. For pixel-identical Microsoft Word output, a Microsoft Word conversion service and licensed fonts would be required.

Document contents are treated as template data, never application instructions.

## Run locally

Use Python 3.12 and install LibreOffice separately (https://www.libreoffice.org/download/download-libreoffice/).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If LibreOffice is not on PATH, the standard Windows location is detected. For other locations set `LIBREOFFICE_PATH` to the full executable path. Linux: install the packages listed in `packages.txt`. No Microsoft Word installation is needed.

## Recommended free deployment: Streamlit Community Cloud

1. Create a GitHub repository and upload this project's files, including `templates/offer.docx`, `.streamlit/config.toml`, `requirements.txt`, and `packages.txt`.
2. Sign in at https://share.streamlit.io/ with GitHub and select **Create app**.
3. Select the repository and branch; set the main file to `app.py`.
4. In Advanced settings choose Python **3.12**, then deploy. The first build installs LibreOffice and can take several minutes.
5. Open the resulting HTTPS `.streamlit.app` URL on desktop or phone. Use your phone browser's Add to Home Screen option for convenient access.
6. Generate one test offer and check its line breaks, fonts and page count before operational use.

Community Cloud is free and supports external Debian packages through `packages.txt`. Free hosting has resource limits and may sleep; it is not an availability guarantee. Review app visibility/access settings before sharing. There is no application login in this project; anyone with access to a public deployment can generate letters. Inputs and output bytes stay in session memory; conversion uses isolated temporary directories that are removed on completion. Hosting operators can still access server infrastructure.

Official setup: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
Dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

## Alternative: Render free Docker web service

The included Dockerfile installs LibreOffice. Connect your GitHub repository to a Render Blueprint using `render.yaml`, or create a Docker Web Service and select the Free plan. It uses the platform's PORT automatically. Free web services sleep after 15 minutes without traffic and can take about a minute to wake up. LibreOffice may be constrained by free-tier memory; test realistic requests. See https://render.com/docs/free.

Vercel is not the recommended host for this Streamlit + LibreOffice process. Use Community Cloud for the simplest deployment or Render for Docker control. This project has not been published to an online account.

## Verification

```powershell
python -m unittest discover -s tests -v
```

Tests cover ordinal dates, salary calculations, invalid inputs, tokens split across Word runs, XML escaping, and byte-for-byte preservation of untouched DOCX parts. A real PDF smoke test runs when LibreOffice is available; otherwise it explicitly skips. No generated candidate files are committed.
