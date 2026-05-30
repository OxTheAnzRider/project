from datetime import datetime, timezone
from io import BytesIO
import secrets
import string

from fpdf import FPDF
import qrcode


def generate_verification_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "SC-" + datetime.now(timezone.utc).strftime("%Y") + "-" + "".join(
        secrets.choice(alphabet) for _ in range(9)
    )


def _safe_text(value: object) -> str:
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


def _short_wallet(wallet: str) -> str:
    wallet = _safe_text(wallet)
    if len(wallet) <= 18:
        return wallet
    return f"{wallet[:10]}...{wallet[-8:]}"


def _make_qr_png(data: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _centered_text(pdf: FPDF, y: float, text: str, size: int, style: str = "", color=(35, 39, 47)):
    pdf.set_xy(30, y)
    pdf.set_font("Times", style, size)
    pdf.set_text_color(*color)
    pdf.cell(237, 10, _safe_text(text), align="C")


def build_certificate_pdf_bytes(
    *,
    learner_wallet: str,
    issuer_name: str,
    course_name: str,
    score_percentage: float,
    assessment_title: str,
    token_id: int | None,
    verification_code: str,
    verification_url: str,
) -> bytes:
    """Build a polished single-page landscape certificate PDF."""
    issued_date = datetime.now(timezone.utc).date().strftime("%B %d, %Y")
    token_label = str(token_id) if token_id is not None else "Pending"

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.add_page()

    page_w = pdf.w
    page_h = pdf.h

    # Background and formal border.
    pdf.set_fill_color(250, 249, 246)
    pdf.rect(0, 0, page_w, page_h, "F")
    pdf.set_draw_color(29, 78, 111)
    pdf.set_line_width(1.2)
    pdf.rect(10, 10, page_w - 20, page_h - 20)
    pdf.set_draw_color(212, 175, 55)
    pdf.set_line_width(0.5)
    pdf.rect(15, 15, page_w - 30, page_h - 30)

    # Corner accents.
    pdf.set_draw_color(29, 78, 111)
    pdf.set_line_width(0.7)
    for x, y, sx, sy in ((20, 20, 1, 1), (page_w - 20, 20, -1, 1), (20, page_h - 20, 1, -1), (page_w - 20, page_h - 20, -1, -1)):
        pdf.line(x, y, x + (22 * sx), y)
        pdf.line(x, y, x, y + (22 * sy))

    # Header.
    _centered_text(pdf, 24, "SKILLCERT", 20, "B", (29, 78, 111))
    pdf.set_draw_color(212, 175, 55)
    pdf.set_line_width(0.4)
    pdf.line(112, 38, 185, 38)
    _centered_text(pdf, 44, "Certificate of Achievement", 32, "B", (35, 39, 47))
    _centered_text(pdf, 61, "This certificate is proudly presented to", 13, "", (84, 92, 102))

    # Recipient.
    _centered_text(pdf, 77, _short_wallet(learner_wallet), 22, "B", (17, 24, 39))
    pdf.set_draw_color(197, 205, 214)
    pdf.set_line_width(0.3)
    pdf.line(78, 92, 219, 92)

    # Body copy.
    _centered_text(pdf, 101, "for successfully completing", 13, "", (84, 92, 102))
    _centered_text(pdf, 116, course_name, 24, "B", (29, 78, 111))
    _centered_text(pdf, 132, f"Assessment: {assessment_title}", 12, "", (65, 72, 82))
    _centered_text(pdf, 143, f"Issued by {issuer_name} on {issued_date}", 12, "", (65, 72, 82))

    # Score badge.
    pdf.set_fill_color(29, 78, 111)
    pdf.set_draw_color(29, 78, 111)
    pdf.ellipse(128, 154, 41, 25, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_xy(128, 160)
    pdf.cell(41, 7, f"{score_percentage:.1f}%", align="C")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(128, 168)
    pdf.cell(41, 5, "FINAL SCORE", align="C")

    # Verification panel.
    panel_x, panel_y, panel_w, panel_h = 194, 143, 68, 43
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(218, 223, 230)
    pdf.rect(panel_x, panel_y, panel_w, panel_h, "DF")
    qr_png = _make_qr_png(verification_url)
    pdf.image(qr_png, x=panel_x + 4, y=panel_y + 5, w=30, h=30)
    pdf.set_text_color(35, 39, 47)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(panel_x + 37, panel_y + 6)
    pdf.multi_cell(27, 4, "VERIFY CERTIFICATE", align="L")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(panel_x + 37, panel_y + 18)
    pdf.multi_cell(27, 4, f"Code:\n{_safe_text(verification_code)}", align="L")
    pdf.set_xy(panel_x + 37, panel_y + 31)
    pdf.multi_cell(27, 4, f"Token:\n{_safe_text(token_label)}", align="L")

    # Signature block.
    pdf.set_draw_color(60, 68, 78)
    pdf.line(35, 178, 102, 178)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(35, 39, 47)
    pdf.set_xy(35, 181)
    pdf.cell(67, 5, _safe_text(issuer_name), align="C")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(84, 92, 102)
    pdf.set_xy(35, 187)
    pdf.cell(67, 4, "Authorized Issuer", align="C")

    # Footer proof line.
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(84, 92, 102)
    pdf.set_xy(25, 198)
    pdf.cell(247, 4, _safe_text(f"Blockchain: Arbitrum Sepolia  |  Verification: {verification_url}"), align="C")

    output = pdf.output(dest="S")
    if isinstance(output, bytearray):
        return bytes(output)
    if isinstance(output, str):
        return output.encode("latin-1")
    return output
