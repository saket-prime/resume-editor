import csv
import hashlib
import io
from decimal import Decimal, InvalidOperation

import streamlit as st
import streamlit.components.v1 as components

from email_share import default_body, share_html, validate_email
from generator import (
    build_docx,
    filename,
    format_date,
    format_salary,
    salary_amount,
    today_india,
    to_pdf,
)


EMAIL_SUBJECT = "OFFER LETTER — Techno Inkai"
MAX_BULK_ROWS = 50


st.set_page_config(
    page_title="Techno Inkai · Offer Studio",
    page_icon="✦",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                ellipse at top left,
                #e5f5ef 0,
                transparent 55%
            ),
            #f7f8fa;
        color: #162c28;
    }

    .block-container {
        max-width: 900px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    h1 {
        font-size: clamp(2.2rem, 6vw, 3.8rem) !important;
        letter-spacing: -.055em;
        line-height: 1.08 !important;
    }

    .eyebrow {
        font-size: .75rem;
        font-weight: 700;
        letter-spacing: .17em;
        color: #317a66;
        margin-bottom: 1.6rem;
    }

    .intro {
        font-size: 1.08rem;
        color: #63766f;
        max-width: 600px;
        margin-bottom: 1.5rem;
    }

    .preview {
        padding: 1.3rem 0;
        border-top: 1px solid #e4ebe7;
        border-bottom: 1px solid #e4ebe7;
        margin: 1.2rem 0;
    }

    .preview span {
        font-size: .8rem;
        color: #63766f;
    }

    .preview strong {
        font-size: 1.55rem;
        display: block;
        margin-top: .3rem;
    }

    .stButton button,
    .stDownloadButton button {
        min-height: 3rem;
        border-radius: 12px;
        font-weight: 600;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
    }

    .footer {
        font-size: .8rem;
        color: #6d7f77;
        margin-top: 2rem;
        line-height: 1.6;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-top: 1.7rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_email_controls(candidate_name, recipient, pdf):
    """Use the existing formatted-copy and blank-draft controls."""
    components.html(
        share_html(
            recipient=recipient,
            subject=EMAIL_SUBJECT,
            body=default_body(candidate_name),
            pdf=pdf,
            filename=filename(candidate_name),
        ),
        height=320,
        scrolling=True,
    )


def parse_package(value):
    """Accept package values such as 22, 22.5, or 22,000.

    Values retain the app's existing units: thousands of rupees.
    Therefore 22 means ₹22,000, while 22,000 means 22,000 thousands.
    """
    cleaned = value.strip().replace(",", "")

    if not cleaned:
        raise ValueError("Salary/package is missing.")

    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(
            "Salary/package must be a number, such as 22."
        ) from exc

    # Reuse the generator's existing range and calculation validation.
    salary_amount(amount)

    return amount


def parse_bulk_rows(raw_text):
    """Parse rows copied directly from Excel or Google Sheets.

    Spreadsheet clipboard data normally uses tabs between columns.
    Comma-separated CSV is also supported.
    """
    if not raw_text.strip():
        return [], ["Paste at least one candidate row."]

    delimiter = "\t" if "\t" in raw_text else ","

    try:
        reader = csv.reader(
            io.StringIO(raw_text),
            delimiter=delimiter,
            strict=True,
        )

        rows = [
            (reader.line_num, [cell.strip() for cell in row])
            for row in reader
            if any(cell.strip() for cell in row)
        ]

    except csv.Error:
        return [], [
            "Could not read the pasted rows. Copy the three columns "
            "directly from your spreadsheet and paste again."
        ]

    # Optionally ignore a recognizable column-header row.
    if rows:
        first = rows[0][1]

        if len(first) == 3:
            name_header = first[0].lower()
            salary_header = first[1].lower()
            email_header = first[2].lower()

            if (
                name_header in {
                    "name",
                    "candidate",
                    "candidate name",
                    "full name",
                }
                and salary_header in {
                    "salary",
                    "package",
                    "ctc",
                    "salary/package",
                }
                and email_header in {
                    "email",
                    "email address",
                    "candidate email",
                }
            ):
                rows = rows[1:]

    if not rows:
        return [], ["No candidate rows were found."]

    if len(rows) > MAX_BULK_ROWS:
        return [], [
            f"Paste at most {MAX_BULK_ROWS} candidates at a time."
        ]

    candidates = []
    errors = []

    for row_number, cells in rows:
        if len(cells) != 3:
            errors.append(
                f"Row {row_number}: expected exactly three columns "
                "in this order: Name, Salary/Package, Email."
            )
            continue

        name, package_text, email_text = cells

        if (
            not name
            or len(name) > 120
            or any(ord(character) < 32 for character in name)
        ):
            errors.append(
                f"Row {row_number}: enter a name of 1–120 characters "
                "without line breaks."
            )
            continue

        try:
            package = parse_package(package_text)
            email = validate_email(email_text)

        except ValueError as exc:
            errors.append(f"Row {row_number}: {exc}")
            continue

        candidates.append(
            {
                "row_number": row_number,
                "name": name,
                "package": package,
                "email": email,
            }
        )

    return candidates, errors


def render_single_mode():
    st.subheader("Create one offer")

    name = st.text_input(
        "Candidate’s full name",
        placeholder="e.g. Kotha Himaja",
        max_chars=120,
        key="single_name",
    )

    recipient = st.text_input(
        "Candidate’s email address",
        placeholder="candidate@example.com",
        max_chars=254,
        key="single_email",
    )

    package = st.number_input(
        "CTC in thousands (₹)",
        min_value=0.0,
        max_value=1000000.0,
        value=16.0,
        step=1.0,
        help=(
            "Enter 16 for ₹16,000. "
            "Per-project pay = CTC × 1,000 ÷ 4."
        ),
        key="single_package",
    )

    day = today_india()
    pay = format_salary(package) if package > 0 else "—"

    st.markdown(
        f"""
        <div class="preview">
            <span>PER PROJECT · CTC ÷ 4</span>
            <strong>₹{pay}</strong>
            <span>
                Issue date · {format_date(day)} · India time
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    signature = (
        name.strip(),
        str(package),
        day.isoformat(),
    )

    if st.session_state.get("single_signature") != signature:
        st.session_state.pop("single_pdf", None)

    if st.button(
        "Generate offer PDF →",
        type="primary",
        use_container_width=True,
        key="generate_single",
    ):
        try:
            with st.spinner("Preparing your offer…"):
                document = build_docx(name, package, day=day)
                pdf = to_pdf(document)

            st.session_state["single_pdf"] = pdf
            st.session_state["single_signature"] = signature

        except (ValueError, RuntimeError, OSError) as exc:
            st.error(str(exc))

    if "single_pdf" not in st.session_state:
        return

    pdf = st.session_state["single_pdf"]

    st.success("Your offer is ready.")

    st.download_button(
        "Download offer PDF ↓",
        data=pdf,
        file_name=filename(name),
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        key="download_single",
    )

    st.divider()
    st.subheader("Prepare email")

    with st.expander("Preview email message"):
        st.write(f"Subject: {EMAIL_SUBJECT}")
        st.text(default_body(name))

    try:
        email = validate_email(recipient)

    except ValueError:
        st.info(
            "Enter a valid candidate email above "
            "to enable the email controls."
        )

    else:
        render_email_controls(name, email, pdf)


def render_bulk_mode():
    st.subheader("Create offers in bulk")

    st.write(
        "Copy the three columns from your sheet and paste them below: "
        "**Name → Salary/Package → Email**."
    )

    st.caption(
        "Use the same package units as single mode: "
        "22 means ₹22,000 and produces ₹5,500 per project. "
        f"Maximum {MAX_BULK_ROWS} candidates per batch."
    )

    raw_text = st.text_area(
        "Paste spreadsheet rows",
        height=230,
        placeholder=(
            "Candidate One\t22\tcandidate1@example.com\n"
            "Candidate Two\t20\tcandidate2@example.com"
        ),
        key="bulk_input",
        help=(
            "Copy cells directly from Excel or Google Sheets. "
            "Keep the order Name, Salary/Package, Email. "
            "A header row is optional."
        ),
    )

    day = today_india()

    fingerprint = hashlib.sha256(
        (raw_text + "\n" + day.isoformat()).encode("utf-8")
    ).hexdigest()

    # Do not display PDFs generated from different rows or another date.
    if st.session_state.get("bulk_fingerprint") != fingerprint:
        st.session_state.pop("bulk_results", None)

    if not raw_text.strip():
        st.info(
            "Paste your rows to see a preview and generate their offers."
        )
        return

    candidates, errors = parse_bulk_rows(raw_text)

    if errors:
        st.error(
            "Please correct these rows before generating the batch:\n\n"
            + "\n".join(f"- {error}" for error in errors)
        )

    if candidates:
        st.write(
            f"**{len(candidates)} valid candidate(s)** · "
            f"Issue date: **{format_date(day)}**"
        )

        st.dataframe(
            [
                {
                    "Name": candidate["name"],
                    "Package (₹ thousands)": str(candidate["package"]),
                    "Per-project pay (₹)": format_salary(
                        candidate["package"]
                    ),
                    "Email": candidate["email"],
                }
                for candidate in candidates
            ],
            use_container_width=True,
            hide_index=True,
        )

    generate = st.button(
        "Generate all offer PDFs →",
        type="primary",
        use_container_width=True,
        disabled=bool(errors) or not candidates,
        key="generate_bulk",
    )

    if generate:
        results = []
        total = len(candidates)

        progress = st.progress(
            0,
            text="Starting PDF generation…",
        )

        # The same captured date is used for every PDF in this batch.
        for index, candidate in enumerate(candidates):
            progress.progress(
                index / total,
                text=(
                    f"Generating {index + 1} of {total}: "
                    f"{candidate['name']}"
                ),
            )

            result = dict(candidate)

            try:
                document = build_docx(
                    candidate["name"],
                    candidate["package"],
                    day=day,
                )

                result["pdf"] = to_pdf(document)
                result["error"] = None

            except (ValueError, RuntimeError, OSError) as exc:
                result["pdf"] = None
                result["error"] = str(exc)

            results.append(result)

        progress.progress(
            1.0,
            text="Batch processing complete.",
        )

        st.session_state["bulk_results"] = results
        st.session_state["bulk_fingerprint"] = fingerprint

    results = st.session_state.get("bulk_results")

    if not results:
        return

    successful = sum(
        result["pdf"] is not None
        for result in results
    )
    failed = len(results) - successful

    if failed:
        st.warning(
            f"{successful} PDF(s) generated. "
            f"{failed} candidate(s) could not be processed."
        )
    else:
        st.success(
            f"All {successful} offer PDFs are ready."
        )

    st.subheader("Candidate offers")

    for index, result in enumerate(results):
        with st.container(border=True):
            st.subheader(
                f"{index + 1}. {result['name']}"
            )

            st.write(result["email"])

            st.caption(
                f"Per-project pay: ₹{format_salary(result['package'])}"
                f" · Issue date: {format_date(day)}"
            )

            if result["error"]:
                st.error(result["error"])
                continue

            st.download_button(
                "Download offer PDF ↓",
                data=result["pdf"],
                file_name=filename(result["name"]),
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key=f"bulk_download_{fingerprint}_{index}",
            )

            render_email_controls(
                candidate_name=result["name"],
                recipient=result["email"],
                pdf=result["pdf"],
            )


st.markdown(
    '<div class="eyebrow">'
    '✦ &nbsp; TECHNO INKAI / OFFER STUDIO'
    "</div>",
    unsafe_allow_html=True,
)

st.title("A new beginning.\nOne simple letter.")

st.session_state.setdefault("offer_mode", "single")

single_column, bulk_column = st.columns(2)

with single_column:
    if st.button(
        "Single candidate",
        type=(
            "primary"
            if st.session_state["offer_mode"] == "single"
            else "secondary"
        ),
        use_container_width=True,
        key="single_mode_button",
    ):
        st.session_state["offer_mode"] = "single"
        st.rerun()

with bulk_column:
    if st.button(
        "Bulk mode",
        type=(
            "primary"
            if st.session_state["offer_mode"] == "bulk"
            else "secondary"
        ),
        use_container_width=True,
        key="bulk_mode_button",
    ):
        st.session_state["offer_mode"] = "bulk"
        st.rerun()

st.markdown(
    """
    <p class="intro">
        Create personalized offer letters from your original template.
        Prepare one offer or an entire batch.
    </p>
    """,
    unsafe_allow_html=True,
)

if st.session_state["offer_mode"] == "single":
    render_single_mode()
else:
    render_bulk_mode()

st.caption(
    "Email drafts contain the recipient and subject only. "
    "Use Copy formatted message, open the draft, and paste into "
    "the blank message body. Attach the downloaded PDF manually. "
    "Bold formatting depends on the email app."
)

st.markdown(
    """
    <div class="footer">
        Original template. Three personalized details.<br>
        PDFs stay in your browser session.
        No emails are sent automatically.
    </div>
    """,
    unsafe_allow_html=True,
)
