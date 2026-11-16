import streamlit as st
import streamlit.components.v1 as components

from email_share import default_body, share_html, validate_email
from generator import (
    build_docx,
    filename,
    format_date,
    format_salary,
    today_india,
    to_pdf,
)

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
            radial-gradient(ellipse at top left, #e5f5ef 0, transparent 55%),
            #f7f8fa;
        color: #162c28;
    }

    .block-container {
        max-width: 860px;
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
        max-width: 530px;
        margin-bottom: 2rem;
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
        min-height: 3.1rem;
        border-radius: 12px;
        font-weight: 600;
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

st.markdown(
    '<div class="eyebrow">✦ &nbsp; TECHNO INKAI / OFFER STUDIO</div>',
    unsafe_allow_html=True,
)

st.title("A new beginning.\nOne simple letter.")

st.markdown(
    """
    <p class="intro">
        Create a personalized offer from your original Word template.
        Add the details, generate your PDF, and share it through your email app.
    </p>
    """,
    unsafe_allow_html=True,
)

name = st.text_input(
    "Candidate’s full name",
    placeholder="e.g. Kotha Himaja",
    max_chars=120,
)

recipient = st.text_input(
    "Candidate’s email address",
    placeholder="candidate@example.com",
    max_chars=254,
)

ctc = st.number_input(
    "CTC in thousands (₹)",
    min_value=0.0,
    max_value=1000000.0,
    value=16.0,
    step=1.0,
    help="Enter 16 for ₹16,000. Per-project pay = CTC × 1,000 ÷ 4.",
)

day = today_india()
pay = format_salary(ctc) if ctc > 0 else "—"

st.markdown(
    f"""
    <div class="preview">
        <span>PER PROJECT · CTC ÷ 4</span>
        <strong>₹{pay}</strong>
        <span>Issue date · {format_date(day)} · India time</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Only the issue date, candidate name, and per-project pay "
    "are filled into the document."
)

signature = (name.strip(), ctc, day.isoformat())

# Invalidate the generated PDF when its document inputs change.
if st.session_state.get("signature") != signature:
    st.session_state.pop("pdf", None)

if st.button(
    "Generate offer PDF →",
    type="primary",
    use_container_width=True,
):
    try:
        with st.spinner("Preparing your offer…"):
            document = build_docx(name, ctc)
            pdf = to_pdf(document)

        st.session_state.update(
            pdf=pdf,
            signature=signature,
        )

    except (ValueError, RuntimeError, OSError) as exc:
        st.error(str(exc))

if "pdf" in st.session_state:
    pdf = st.session_state["pdf"]
    attachment_name = filename(name)

    st.success("Your offer is ready.")

    st.download_button(
        "Download offer PDF ↓",
        data=pdf,
        file_name=attachment_name,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Send mail")

    subject = "Offer Letter"
    body = default_body(name)

    st.caption(
        "Choose Gmail or Titan from your device’s sharing menu. "
        "Select the sending account inside that app."
    )

    with st.expander("Preview email message", expanded=True):
        st.write(
            f"To: {recipient.strip() or 'Enter candidate email above'}"
        )
        st.write(f"Subject: {subject}")
        st.text(body)
        st.caption(f"Attachment: {attachment_name}")

    try:
        address = validate_email(recipient)

    except ValueError:
        st.info(
            "Enter a valid candidate email above to enable Send mail."
        )

    else:
        components.html(
            share_html(
                recipient=address,
                subject=subject,
                body=body,
                pdf=pdf,
                filename=attachment_name,
            ),
            height=310,
        )

    st.caption(
        "Sharing depends on your browser and installed email apps. "
        "Check the recipient, subject, message, and attachment before sending. "
        "If file sharing is unavailable, download the PDF above, "
        "open the email draft, and attach the file manually."
    )

st.markdown(
    """
    <div class="footer">
        Original template. Three personalized details.<br>
        Generated files are held in your session;
        no candidate database or document archive is created.
    </div>
    """,
    unsafe_allow_html=True,
)
