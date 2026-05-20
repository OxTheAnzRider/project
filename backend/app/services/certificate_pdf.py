from datetime import datetime, timezone
import secrets
import string


def generate_verification_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "SC-" + datetime.now(timezone.utc).strftime("%Y") + "-" + "".join(
        secrets.choice(alphabet) for _ in range(9)
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_certificate_pdf_bytes(
    *,
    learner_wallet: str,
    institution_name: str,
    course_name: str,
    score_percentage: float,
    assessment_title: str,
    token_id: int | None,
    verification_code: str,
    verification_url: str,
) -> bytes:
    """
    Build a compact single-page PDF using raw PDF primitives.

    This keeps the preview self-contained. A production deployment can replace
    this with ReportLab/fpdf2 plus a real QR image while keeping the same call.
    """
    lines = [
        "SKILLCERT - CERTIFICATE OF MERIT",
        "",
        f"This certifies wallet {learner_wallet}",
        "has successfully completed",
        f"Course: {course_name}",
        f"Institution: {institution_name}",
        f"Assessment: {assessment_title}",
        f"Score: {score_percentage:.1f}%",
        f"Date: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        f"Verification Code: {verification_code}",
        f"NFT Token ID: {token_id if token_id is not None else 'pending'}",
        "Blockchain: Arbitrum Sepolia",
        "",
        "QR verification URL:",
        verification_url,
    ]

    y = 780
    text_ops = ["BT", "/F1 14 Tf"]
    for line in lines:
        text_ops.append(f"72 {y} Td ({_pdf_escape(line)}) Tj")
        text_ops.append("0 -24 Td")
        y -= 24
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode()

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b"\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)
