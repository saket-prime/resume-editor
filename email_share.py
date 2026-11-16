"""Open email drafts or share a PDF through the device's email apps.

No SMTP connection, mailbox password, or backend email sending is used.
"""

import base64
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
    """Predefined email message personalized with the candidate's name."""
    return (
        f"Dear Candidate,\n\n"
        f"Greetings from Techno Inkai.\n\n"
        f"Please carefully review the following instructions to ensure smooth onboarding.\n\n"
        f"Employment Process\n\n"
        f"To commence work, kindly print the offer letter, sign it manually, "
        f"and email the scanned copy to the official email ID provided "
        f"(hr@technoinkai.com). Digital signatures are not permitted.\n\n"
        f"Along with the signed offer letter, please submit:\n\n"
        f"- Aadhaar Card copy\n"
        f"- PAN Card copy\n"
        f"- Higher Qualification Certificate\n"
        f"- Passport-size Photograph\n"
        f"- Bank Details\n\n"
        f"All documents must also be shared on WhatsApp at 70130 88594.\n\n"
        f"Working Guidelines\n\n"
        f"- Working hours are flexible (Monday–Friday).\n"
        f"- Technical support hours: 11:00 AM – 03:00 PM "
        f"(Lunch: 1:00 PM – 2:00 PM).\n"
        f"- Contact support at 70130 88594 for technical assistance "
        f"(Calls only for technical issues; otherwise, WhatsApp text).\n"
        f"- Copy-paste and use of auto-correction/auto-spacing software "
        f"is strictly prohibited.\n"
        f"- No refund policy upon resignation.\n"
        f"- Registration validity: 1 months "
        f"(no break exceeding 3 months allowed).\n\n"
        f"We look forward to your cooperation.\n\n"
        f"Regards,\n"
        f"Technical Support Team\n"
        f"Techno Inkai\n"
        f"Contact: 70130 88594"
    )


def share_html(recipient, subject, body, pdf, filename):
    """Build the device-sharing interface and email-draft fallback."""
    recipient = validate_email(recipient)

    payload = json.dumps(
        {
            "recipient": recipient,
            "title": subject,
            "text": body,
            "filename": filename,
            "pdf": base64.b64encode(pdf).decode("ascii"),
        },
        ensure_ascii=True,
    ).replace("<", "\\u003c")

    mailto = (
        "mailto:"
        + quote(recipient, safe="@")
        + "?"
        + urlencode(
            {"subject": subject, "body": body},
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
            font: 600 15px system-ui, sans-serif;
            border-radius: 12px;
            padding: 13px 17px;
            cursor: pointer;
            display: inline-block;
            margin: 0 8px 10px 0;
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

        .secondary {
            background: #e4eee8;
            color: #162c28;
        }

        #status {
            line-height: 1.5;
            overflow-wrap: anywhere;
        }

        button:disabled {
            opacity: .6;
            cursor: wait;
        }

        @media (max-width: 480px) {
            button,
            a {
                width: 100%;
                text-align: center;
                margin-right: 0;
            }
        }
    </style>
</head>

<body>

    <a
        href="__MAILTO__"
        target="_blank"
        rel="noopener noreferrer"
    >
        Open email draft
    </a>

    <button id="copy" class="secondary" type="button">
        Copy recipient
    </button>

    <p id="status" role="status" aria-live="polite">
        Send mail opens your device's sharing menu with the PDF
        and message. Choose an email app.
    </p>

    <script>
        const data = __PAYLOAD__;
        const status = document.getElementById("status");
        const shareButton = document.getElementById("share");
        const copyButton = document.getElementById("copy");

        const bytes = Uint8Array.from(
            atob(data.pdf),
            character => character.charCodeAt(0)
        );

        const file = new File(
            [bytes],
            data.filename,
            {type: "application/pdf"}
        );

        copyButton.onclick = async () => {
            try {
                await navigator.clipboard.writeText(data.recipient);

                status.textContent =
                    "Recipient copied. Paste it into your email app.";
            } catch (error) {
                status.textContent =
                    "Copy this recipient: " + data.recipient;
            }
        };

        shareButton.onclick = async () => {
            shareButton.disabled = true;

            try {
                if (
                    !navigator.share ||
                    !navigator.canShare ||
                    !navigator.canShare({files: [file]})
                ) {
                    status.textContent =
                        "PDF sharing is unavailable in this browser or " +
                        "embedded app. Download the PDF above, select " +
                        "Open email draft, and attach the downloaded file.";

                    return;
                }

                await navigator.share({
                    files: [file],
                    title: data.title,
                    text: data.text
                });

                status.textContent =
                    "Sharing closed. Check the recipient, subject, " +
                    "message, PDF attachment, and sending account in " +
                    "your email app. Nothing is sent automatically.";

            } catch (error) {
                if (error.name === "AbortError") {
                    status.textContent =
                        "Sharing cancelled. You can try again.";
                } else {
                    status.textContent =
                        "Sharing could not open. Download the PDF above, " +
                        "then use Open email draft and attach it manually.";
                }
            } finally {
                shareButton.disabled = false;
            }
        };
    </script>
</body>
</html>
"""

    # Insert the payload last so message content cannot affect placeholders.
    return template.replace(
        "__MAILTO__",
        html.escape(mailto, quote=True),
    ).replace(
        "__PAYLOAD__",
        payload,
    )
