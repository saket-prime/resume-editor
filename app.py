import hashlib

import streamlit as st
import streamlit.components.v1 as components

from bulk_parser import parse_rows
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
        color-scheme: light;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4,
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"] {
        color: #162c28 !important;
    }

    h1 {
        font-size: clamp(2.2rem, 6vw, 3.8rem) !important;
        letter-spacing: -.055em;
        line-height: 1.1 !important;
    }

    .eyebrow {
        font-size: .75rem;
        font-weight: 700;
        letter-spacing: .17em;
        color: #317a66;
        margin-bottom: 1.4rem;
    }

    .intro {
        color: #526b61;
        font-size: 1.05rem;
        margin: 1rem 0 1.5rem;
    }

    /* Override dark-theme input backgrounds and text. */
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="textarea"],
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background-color: #ffffff !important;
        color: #162c28 !important;
        -webkit-text-fill-color: #162c28 !important;
        caret-color: #19755d !important;
    }

    [data-baseweb="input"],
    [data-baseweb="textarea"] {
        border-color: #b8cec3 !important;
        border-radius: 12px !important;
    }

    textarea::placeholder,
    input::placeholder {
        color: #71867c !important;
        -webkit-text-fill-color: #71867c !important;
        opacity: 1 !important;
    }

    textarea::selection,
    input::selection {
        background: #c9e9db;
        color: #162c28;
    }

    .stButton button,
    .stDownloadButton button,
    .stFormSubmitButton button {
        background: #ffffff !important;
        color: #195b46 !important;
        border: 1px solid #b8cec3 !important;
        border-radius: 12px !important;
        min-height: 3rem;
        font-weight: 600 !important;
    }

    .stButton button p,
    .stDownloadButton button p,
    .stFormSubmitButton button p {
        color: #195b46 !important;
    }

    button[kind="primary"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: #19755d !important;
        color: #ffffff !important;
        border-color: #19755d !important;
    }

    button[kind="primary"] p,
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primaryFormSubmit"] p {
        color: #ffffff !important;
    }

    button:disabled {
        opacity: .55 !important;
    }

    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #d6e3dc;
        border-radius: 16px;
        padding: 1.2rem;
    }

    [data-testid="stExpander"] {
        background: #ffffff;
        color: #162c28;
        border-color: #d6e3dc;
    }

    [data-testid="stAlert"] {
        background: #eef5f1 !important;
        color: #162c28 !important;
        border: 1px solid #cadfd3;
    }

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] li {
        color: #162c28 !important;
    }

    [data-testid="stText"] {
        color: #162c28 !important;
        white-space: pre-wrap;
    }

    .footer {
        color: #63796e;
        font-size: .8rem;
        margin-top: 2rem;
        line-height: 1.6;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-top: 1.5rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    /* Reduce spacing between candidate details and controls. */
[data-testid="stVerticalBlock"] {
    gap: .55rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
}

[data-testid="stCaptionContainer"] p {
    margin-bottom: 0;
    font-size: .8rem;
    line-height: 1.4;
}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_email_controls(name, email, pdf):
    components.html(
        share_html(
            recipient=email,
            subject=EMAIL_SUBJECT,
            body=default_body(name),
            pdf=pdf,
            filename=filename(name),
        ),
        height=95,
        scrolling=False,
    )


def render_candidate_card(result, number=None):
    """Compact candidate details and a single row of action buttons."""
    prefix = f"{number}. " if number is not None else ""

    with st.container(border=True):
        st.markdown(f"**{prefix}{result['name']}**")

        st.caption(
            f"{result['email']} · "
            f"₹{format_salary(result['package'])} per project · "
            f"{format_date(result['date'])}"
        )

        if result.get("error"):
            st.error(result["error"])
        else:
            render_email_controls(
                result["name"],
                result["email"],
                result["pdf"],
            )


def single_mode():
    st.subheader("Create one offer")

    with st.form("single_form", clear_on_submit=False):
        name = st.text_input(
            "Candidate’s full name",
            placeholder="e.g. Kotha Himaja",
            max_chars=120,
        )

        email = st.text_input(
            "Candidate’s email address",
            placeholder="candidate@example.com",
            max_chars=254,
        )

        package = st.number_input(
            "CTC in thousands (₹)",
            min_value=0.0,
            max_value=1000000.0,
            value=16.0,
            step=1.0,
        )

        st.caption(
            "16 means ₹16,000. Per-project pay will be ₹4,000."
        )

        submitted = st.form_submit_button(
            "Generate offer PDF",
            type="primary",
            use_container_width=True,
        )

    day = today_india()

    if submitted:
        # Remove an older offer before processing new details.
        st.session_state.pop("single_result", None)

        try:
            address = validate_email(email)

            with st.spinner("Preparing the offer PDF…"):
                document = build_docx(name, package, day=day)
                pdf = to_pdf(document)

            st.session_state["single_result"] = {
                "name": name.strip(),
                "email": address,
                "package": package,
                "date": day,
                "pdf": pdf,
            }

        except (ValueError, RuntimeError, OSError) as exc:
            st.error(str(exc))

    result = st.session_state.get("single_result")

    if not result:
        return

    if result["date"] != day:
        st.info(
            "The previous offer was generated on another date. "
            "Click Generate offer PDF to create today's version."
        )
        return

    render_candidate_card(result)

    st.caption(
        "After editing candidate details, click Generate offer PDF "
        "again to update this offer."
    )


def bulk_mode():
    st.subheader("Create offers in bulk")

    st.write(
        "Paste rows copied from your spreadsheet. "
        "**Name, package, and email can be in any column order. "
        "Blank cells are ignored.**"
    )

    st.caption(
        "Example: two blank cells, candidate name, 22, email. "
        "Package 22 produces ₹5,500 per project. "
        "Maximum 50 candidates per batch."
    )

    # A form submits the text area through the button.
    # Ctrl+Enter is optional, not required.
    with st.form("bulk_form", clear_on_submit=False):
        raw_text = st.text_area(
            "Paste your candidate rows",
            height=240,
            placeholder=(
                "Jane Doe\t22\tjane@example.com\n"
                "\t\tjohn@example.com\t20\tJohn Smith"
            ),
            help=(
                "Copy cells directly from Excel or Google Sheets. "
                "Blank columns are allowed. Include one name, "
                "one numeric package, and one email per row."
            ),
        )

        submitted = st.form_submit_button(
            "Generate offers",
            type="primary",
            use_container_width=True,
        )

    day = today_india()

    if submitted:
        st.session_state.pop("bulk_results", None)

        candidates, errors = parse_rows(
            raw_text,
            validate_email=validate_email,
            salary_amount=salary_amount,
            limit=50,
        )

        if errors:
            st.error(
                "Please correct the following rows and "
                "click Generate offers again:"
            )

            for error in errors:
                st.write(f"• {error}")

        else:
            results = []

            progress = st.progress(
                0,
                text="Starting PDF generation…",
            )

            for index, candidate in enumerate(candidates):
                progress.progress(
                    index / len(candidates),
                    text=(
                        f"Generating {index + 1} "
                        f"of {len(candidates)}: "
                        f"{candidate['name']}"
                    ),
                )

                result = {
                    **candidate,
                    "date": day,
                    "pdf": None,
                    "error": None,
                }

                try:
                    document = build_docx(
                        candidate["name"],
                        candidate["package"],
                        day=day,
                    )

                    result["pdf"] = to_pdf(document)

                except (ValueError, RuntimeError, OSError) as exc:
                    result["error"] = str(exc)

                results.append(result)

            progress.empty()

            st.session_state["bulk_results"] = results
            st.session_state["bulk_date"] = day

            st.session_state["bulk_batch_id"] = hashlib.sha256(
                raw_text.encode("utf-8")
            ).hexdigest()[:16]

    results = st.session_state.get("bulk_results")

    if not results:
        return

    if st.session_state.get("bulk_date") != day:
        st.info(
            "These offers were generated on another date. "
            "Click Generate offers to create today's versions."
        )
        return

    successful = sum(
        result["pdf"] is not None
        for result in results
    )

    st.success(
        f"{successful} of {len(results)} offer PDFs generated."
    )

    st.caption(
        "The list below reflects your last submitted batch. "
        "After editing the pasted rows, click Generate offers again."
    )
    for index, result in enumerate(results, start=1):
        render_candidate_card(result, number=index)


st.markdown(
    '<div class="eyebrow">'
    '✦ &nbsp; TECHNO INKAI / OFFER STUDIO'
    "</div>",
    unsafe_allow_html=True,
)

st.title("A new beginning.\nOne simple letter.")

st.session_state.setdefault("offer_mode", "single")

left, right = st.columns(2)

with left:
    if st.button(
        "Single candidate",
        type=(
            "primary"
            if st.session_state["offer_mode"] == "single"
            else "secondary"
        ),
        use_container_width=True,
    ):
        st.session_state["offer_mode"] = "single"
        st.rerun()

with right:
    if st.button(
        "Bulk mode",
        type=(
            "primary"
            if st.session_state["offer_mode"] == "bulk"
            else "secondary"
        ),
        use_container_width=True,
    ):
        st.session_state["offer_mode"] = "bulk"
        st.rerun()

st.markdown(
    '<p class="intro">'
    "Create one personalized offer or prepare an entire batch."
    "</p>",
    unsafe_allow_html=True,
)

if st.session_state["offer_mode"] == "single":
    single_mode()
else:
    bulk_mode()

st.markdown(
    """
    <div class="footer">
        Copy the formatted message, open the email draft,
        and paste into its blank message body.
        Attach the downloaded PDF manually.<br>
        No emails are sent automatically.
    </div>
    """,
    unsafe_allow_html=True,
)
