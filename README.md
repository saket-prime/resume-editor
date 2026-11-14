# Techno Inkai Offer Letter Generator — Template-Preserving Version

## Template location

Place your Word template here:

`public/templates/Techno_Inkai_Template.docx`

The app expects these exact placeholders in the DOCX:

- `{{1}}` → current date
- `{{2}}` → candidate name
- `{{3}}` → per-project amount

Your supplied template contains all three placeholders.

## Important deployment note

The frontend intentionally edits the original DOCX package rather than rebuilding the letter. This preserves the existing Word document content and formatting as closely as possible.

The PDF conversion endpoint uses LibreOffice. This works on a normal Node server/container, but **Vercel serverless functions do not provide LibreOffice as a native runtime**. Therefore:

### Recommended production deployment

Use:
- **Frontend:** Vercel
- **PDF conversion API:** Render

Or deploy the whole project to a Render service/container where LibreOffice can be installed.

### Vercel-only option

For a Vercel-only deployment, replace `/api/convert` with a hosted DOCX→PDF conversion provider. The frontend/template replacement code does not need to change.

## Local development

Install:

```bash
npm install
```

Run frontend:

```bash
npm run dev
```

The template must exist at:

```text
public/templates/Techno_Inkai_Template.docx
```

## Production PDF conversion on Render

Create a Docker service using the included `Dockerfile` (if you choose a containerized Node service), or install LibreOffice in the Render environment.

## GitHub deployment

```bash
git init
git add .
git commit -m "Add template-preserving offer letter generator"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```

## Security/privacy

No candidate documents are uploaded. The browser sends only the generated DOCX to the PDF conversion endpoint when the user clicks Generate PDF.
