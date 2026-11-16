"""Open email drafts and copy a formatted email message.

No SMTP connection, mailbox password, or backend sending is used.
"""

import html
import json
import re
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
        "at 70130 88594.\n\n"
        "Working Guidelines\n\n"
        "- Working hours are flexible (Monday–Friday).\n"
        "- Technical support hours: 11:00 AM – 03:00 PM "
        "(Lunch: 1:00 PM – 2:00 PM).\n"
        "- Contact support at 70130 88594 for technical assistance "
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
        "Contact: 70130 88594"
    )


def formatted_body(body):
    """Create an escaped HTML message with selected phrases bolded."""
    bold_phrases = [
        "Techno Inkai",
        "Employment Process",
        "70130 88594",
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
    """Build the draft link and formatted-message copy controls.

    pdf and filename are retained for compatibility with app.py.
    The PDF must be downloaded and attached manually.
    """
    recipient = validate_email(recipient)
    rich_body = formatted_body(body)

    payload = json.dumps(
        {
            "recipient": recipient,
            "text": body,
            "html": rich_body,
        },
        ensure_ascii=True,
    ).replace("<", "\\u003c")

    mailto = (
        "mailto:"
        + quote(recipient, safe="@")
        + "?"
        + urlencode(
            {
                "subject": subject,
                "body": body,
            },
            quote_via=quote,
        )
    )

    template = """
<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font: 14px system-ui, sans-serif;
            color: #162c28;
            margin: 0;
        }

        button,
        a {
            box-sizing: border-box;
            font: 600 14px system-ui, sans-serif;
            display: inline-block;
            border-radius: 10px;
            padding: 12px 14px;
            margin: 0 6px 8px 0;
            cursor: pointer;
        }

        button {
            background: #19755d;
            color: white;
            border: 0;
        }

        a {
            color: #19755d;
            border: 1px solid #bdd5cb;
            text-decoration: none;
        }

        #status {
            line-height: 1.4;
            overflow-wrap: anywhere;
        }

        #preview {
            max-height: 125px;
            overflow: auto;
            border: 1px solid #dbe5df;
            padding: 10px;
            border-radius: 8px;
            margin-top: 8px;
            user-select: text;
            -webkit-user-select: text;
        }

        summary {
            cursor: pointer;
        }
    </style>
</head>

<body>
    <button id="formatted" type="button">
        Copy formatted message
    </button>

    <a
        href="__MAILTO__"
        target="_blank"
        rel="noopener noreferrer"
    >
        Open email draft
    </a>

    <button id="recipient" type="button">
        Copy recipient
    </button>

    <p id="status" role="status" aria-live="polite">
        Copy the formatted message, open the draft, then replace
        its plain message by pasting. Attach the downloaded PDF
        manually. Titan may remove formatting.
    </p>

    <details>
        <summary>
            Formatted preview / select and copy manually
        </summary>

        <div id="preview">__PREVIEW__</div>
    </details>

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

                const item = new ClipboardItem({
                    "text/html": new Blob(
                        [data.html],
                        {type: "text/html"}
                    ),
                    "text/plain": new Blob(
                        [data.text],
                        {type: "text/plain"}
                    )
                });

                await navigator.clipboard.write([item]);

                status.textContent =
                    "Formatted message copied. Open the draft, " +
                    "select its existing message, and paste to replace it. " +
                    "Check the bold formatting before sending.";

            } catch (error) {
                status.textContent =
                    "Formatted clipboard access is unavailable. " +
                    "Expand the formatted preview, select its text, " +
                    "and copy manually. The email app may still " +
                    "remove formatting.";
            }
        };

        document.getElementById("recipient").onclick = async () => {
            try {
                await navigator.clipboard.writeText(data.recipient);

                status.textContent =
                    "Recipient copied. Copy formatted message again " +
                    "before pasting the email body.";

            } catch (error) {
                status.textContent =
                    "Copy this recipient: " + data.recipient;
            }
        };
    </script>
</body>
</html>
"""

    # Substitute user-controlled content in one pass so it cannot
    # accidentally be interpreted as another template placeholder.
    replacements = {
        "__MAILTO__": html.escape(mailto, quote=True),
        "__PREVIEW__": rich_body,
        "__PAYLOAD__": payload,
    }

    return re.sub(
        r"__MAILTO__|__PREVIEW__|__PAYLOAD__",
        lambda match: replacements[match.group()],
        template,
    )
