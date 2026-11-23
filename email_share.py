"""Open blank email drafts and copy a formatted email message.

No SMTP connection, mailbox password, or backend sending is used.
"""

import html
import json
import re
import base64
from urllib.parse import quote, urlencode


def validate_email(value):
    """Accept one plain email address."""
    value = value.strip()

    pattern = (
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?"
        r"\.[A-Za-z]{2,63}"
    )

    if len(value) > 254 or not re.fullmatch(pattern, value):
        raise ValueError("Enter one valid email address.")

    local, domain = value.rsplit("@", 1)

    invalid_local = (
        len(local) > 64
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
    )

    invalid_domain = any(
        not label
        or label.startswith("-")
        or label.endswith("-")
        or len(label) > 63
        for label in domain.split(".")
    )

    if invalid_local or invalid_domain:
        raise ValueError("Enter one valid email address.")

    return value


def default_body(name):
    """Return the predefined message.

    The name argument is retained for compatibility with app.py.
    """
    return (
        "Dear Candidate,\n\n"
        "Greetings from Techno Inkai.\n\n"
        "Please carefully review the following instructions "
        "to ensure smooth onboarding.\n\n"
        "Employment Process\n\n"
        "To commence work, kindly print the offer letter, "
        "sign it manually, and email the scanned copy to "
        "the official email ID provided "
        "(hr@technoinkai.com). Digital signatures are not permitted.\n\n"
        "Along with the signed offer letter, please submit:\n\n"
        "- Aadhaar Card copy\n"
        "- PAN Card copy\n"
        "- Higher Qualification Certificate\n"
        "- Passport-size Photograph\n"
        "- Bank Details\n\n"
        "All documents must also be shared on WhatsApp "
        "at 90523 02759 .\n\n"
        "Working Guidelines\n\n"
        "- Working hours are flexible (Monday–Friday).\n"
        "- Technical support hours: 11:00 AM – 03:00 PM "
        "(Lunch: 1:00 PM – 2:00 PM).\n"
        "- Contact support at 90523 02759 for technical assistance "
        "(Calls only for technical issues; otherwise, WhatsApp text).\n"
        "- Copy-paste and use of auto-correction/auto-spacing "
        "software is strictly prohibited.\n"
        "- No refund policy upon resignation.\n"
        "- Registration validity: 1 months "
        "(no break exceeding 3 months allowed).\n\n"
        "We look forward to your cooperation.\n\n"
        "Regards,\n"
        "Technical Support Team\n"
        "Techno Inkai\n"
        "Contact: 90523 02759"
    )


def formatted_body(body):
    """Create an escaped HTML message with selected phrases bolded."""
    bold_phrases = [
        "Techno Inkai",
        "Employment Process",
        "Working Guidelines",
        "90523 02759",
        "Monday–Friday",
        "11:00 AM – 03:00 PM",
        "1:00 PM – 2:00 PM",
    ]

    pattern = re.compile(
        "|".join(re.escape(phrase) for phrase in bold_phrases)
    )

    chunks = []
    cursor = 0

    for match in pattern.finditer(body):
        chunks.append(html.escape(body[cursor:match.start()]))
        chunks.append(
            "<strong>"
            + html.escape(match.group())
            + "</strong>"
        )
        cursor = match.end()

    chunks.append(html.escape(body[cursor:]))

    content = "".join(chunks).replace("\n", "<br>")

    return (
        '<div style="font-family:Arial,sans-serif;'
        'font-size:14px;line-height:1.5;color:#162c28">'
        + content
        + "</div>"
    )


def share_html(recipient, subject, body, pdf, filename):
    """Compact download and email controls without a preview."""
    recipient = validate_email(recipient)

    payload = json.dumps(
        {
            "recipient": recipient,
            "text": body,
            "html": formatted_body(body),
        },
        ensure_ascii=True,
    ).replace("<", "\\u003c")

    # Recipient and subject only. Email body remains blank.
    mailto = (
        "mailto:"
        + quote(recipient, safe="@")
        + "?"
        + urlencode(
            {"subject": subject},
            quote_via=quote,
        )
    )

    pdf_url = (
        "data:application/pdf;base64,"
        + base64.b64encode(pdf).decode("ascii")
    )

    template = """
<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: system-ui, sans-serif;
            color: #162c28;
        }

        .actions {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 6px;
        }

        button,
        a {
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 0;
            min-height: 40px;
            margin: 0;
            padding: 8px 5px;
            border: 1px solid #b8cec3;
            border-radius: 8px;
            background: #ffffff;
            color: #195b46;
            font: 600 12px system-ui, sans-serif;
            line-height: 1.2;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            overflow-wrap: anywhere;
        }

        .primary {
            background: #19755d;
            border-color: #19755d;
            color: #ffffff;
        }

        button:hover,
        a:hover {
            filter: brightness(.96);
        }

        button:focus-visible,
        a:focus-visible {
            outline: 2px solid #19755d;
            outline-offset: 2px;
        }

        #status {
            margin: 5px 0 0;
            font-size: 11px;
            line-height: 1.3;
            color: #526b61;
            overflow-wrap: anywhere;
        }

        #status:empty {
            display: none;
        }

        @media (max-width: 420px) {
            .actions {
                gap: 4px;
            }

            button,
            a {
                font-size: 10px;
                min-height: 42px;
                padding: 6px 3px;
            }
        }
    </style>
</head>

<body>
    <div class="actions">
        <a
            href="__PDF_URL__"
            download="__FILENAME__"
            aria-label="Download candidate offer PDF"
        >
            Download PDF
        </a>

        <button
            id="formatted"
            class="primary"
            type="button"
            aria-label="Copy formatted email message"
        >
            Copy message
        </button>

        <a
            href="__MAILTO__"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open email draft with recipient and subject"
        >
            Open draft
        </a>

        <button
            id="recipient"
            type="button"
            aria-label="Copy candidate email address"
        >
            Copy recipient
        </button>
    </div>

    <p id="status" role="status" aria-live="polite"></p>

    <script>
        const data = __PAYLOAD__;
        const status = document.getElementById("status");

        document.getElementById("formatted").onclick = async () => {
            try {
                if (
                    !navigator.clipboard ||
                    !navigator.clipboard.write ||
                    !window.ClipboardItem
                ) {
                    throw new Error("Formatted clipboard unavailable");
                }

                await navigator.clipboard.write([
                    new ClipboardItem({
                        "text/html": new Blob(
                            [data.html],
                            {type: "text/html"}
                        ),
                        "text/plain": new Blob(
                            [data.text],
                            {type: "text/plain"}
                        )
                    })
                ]);

                status.textContent =
                    "Message copied. Open draft and paste.";

            } catch (error) {
                status.textContent =
                    "Formatted copy was blocked. Try opening " +
                    "the app directly in Safari or Chrome.";
            }
        };

        document.getElementById("recipient").onclick = async () => {
            try {
                await navigator.clipboard.writeText(data.recipient);

                status.textContent =
                    "Recipient copied. Copy message again " +
                    "before pasting the email body.";

            } catch (error) {
                status.textContent = data.recipient;
            }
        };
    </script>
</body>
</html>
"""

    replacements = {
        "__PDF_URL__": pdf_url,
        "__FILENAME__": html.escape(filename, quote=True),
        "__MAILTO__": html.escape(mailto, quote=True),
        "__PAYLOAD__": payload,
    }

    return re.sub(
        r"__PDF_URL__|__FILENAME__|__MAILTO__|__PAYLOAD__",
        lambda match: replacements[match.group()],
        template,
    )
