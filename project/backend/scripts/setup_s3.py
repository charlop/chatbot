"""
S3 Setup Script for LocalStack.

Creates S3 bucket and uploads test PDF files to match seeded contracts.

Usage:
    uv run python scripts/setup_s3.py --create-bucket
    uv run python scripts/setup_s3.py --upload-pdfs
    uv run python scripts/setup_s3.py --reset  # Delete and recreate everything
    uv run python scripts/setup_s3.py --all    # Create bucket and upload PDFs
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import date, timedelta
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.exceptions import ClientError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Configuration
S3_ENDPOINT = "http://localhost:4566"
S3_BUCKET = "test-contract-documents"
AWS_REGION = "us-east-1"

# Sample data matching seed_db.py
MAKES_MODELS = [
    ("Toyota", "Camry"),
    ("Honda", "Accord"),
    ("Ford", "F-150"),
    ("Chevrolet", "Silverado"),
    ("Tesla", "Model 3"),
    ("BMW", "3 Series"),
    ("Mercedes-Benz", "C-Class"),
    ("Audi", "A4"),
    ("Nissan", "Altima"),
    ("Hyundai", "Elantra"),
    ("Mazda", "CX-5"),
    ("Subaru", "Outback"),
    ("Volkswagen", "Jetta"),
    ("Kia", "Sportage"),
    ("Jeep", "Wrangler"),
]

PREMIUMS = [
    500.00,
    750.00,
    625.00,
    550.00,
    800.00,
    675.00,
    700.00,
    525.00,
    775.00,
    600.00,
    650.00,
    725.00,
    575.00,
    825.00,
    625.00,
]

METHODS = [
    "Pro-rata",
    "Flat-rate",
    "Short-rate",
    "Pro-rata",
    "Flat-rate",
    "Short-rate",
    "Pro-rata",
    "Flat-rate",
    "Short-rate",
    "Pro-rata",
    "Flat-rate",
    "Short-rate",
    "Pro-rata",
    "Flat-rate",
    "Short-rate",
]

FEES = [
    50.00,
    75.00,
    60.00,
    55.00,
    80.00,
    65.00,
    70.00,
    52.50,
    77.50,
    60.00,
    65.00,
    72.50,
    57.50,
    82.50,
    62.50,
]


def get_s3_client():
    """Get S3 client configured for LocalStack."""
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name=AWS_REGION,
    )


def create_bucket():
    """Create S3 bucket in LocalStack."""
    s3_client = get_s3_client()

    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ Bucket '{S3_BUCKET}' already exists")
        return True
    except ClientError:
        # Bucket doesn't exist, create it
        try:
            s3_client.create_bucket(Bucket=S3_BUCKET)
            print(f"✅ Created bucket '{S3_BUCKET}'")
            return True
        except ClientError as e:
            print(f"❌ Failed to create bucket: {e}")
            return False


def delete_bucket():
    """Delete S3 bucket and all its contents."""
    s3_client = get_s3_client()

    try:
        # Delete all objects first
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        if "Contents" in response:
            objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
            s3_client.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objects})
            print(f"✅ Deleted {len(objects)} objects from bucket")

        # Delete bucket
        s3_client.delete_bucket(Bucket=S3_BUCKET)
        print(f"✅ Deleted bucket '{S3_BUCKET}'")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"ℹ️  Bucket '{S3_BUCKET}' doesn't exist")
            return True
        else:
            print(f"❌ Failed to delete bucket: {e}")
            return False


def generate_gap_contract_pdf(
    contract_id: str,
    account_number: str,
    customer_name: str,
    make: str,
    model: str,
    year: int,
    vin: str,
    premium: float,
    method: str,
    fee: float,
    contract_date: date,
) -> bytes:
    """
    Generate a realistic GAP Insurance Contract PDF.

    Returns:
        PDF content as bytes
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#954293"),
        spaceAfter=12,
        alignment=1,  # Center
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#954293"),
        spaceAfter=10,
    )
    normal_style = styles["Normal"]

    # Build content
    story = []

    # Title
    story.append(Paragraph("GUARANTEED ASSET PROTECTION (GAP) INSURANCE AGREEMENT", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Contract Information
    story.append(Paragraph("CONTRACT INFORMATION", heading_style))
    contract_info = [
        ["Contract ID:", contract_id],
        ["Account Number:", account_number],
        ["Customer Name:", customer_name],
        ["Contract Date:", contract_date.strftime("%B %d, %Y")],
    ]
    t = Table(contract_info, colWidths=[2 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * inch))

    # Vehicle Information
    story.append(Paragraph("VEHICLE INFORMATION", heading_style))
    vehicle_info = [
        ["Year:", str(year)],
        ["Make:", make],
        ["Model:", model],
        ["VIN:", vin],
    ]
    t = Table(vehicle_info, colWidths=[2 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * inch))

    # Coverage Details
    story.append(Paragraph("COVERAGE DETAILS", heading_style))
    story.append(
        Paragraph(
            "This Guaranteed Asset Protection (GAP) Insurance Agreement provides coverage for the difference "
            "between the actual cash value of your vehicle at the time of a total loss and the amount you owe "
            "on your auto loan or lease.",
            normal_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    coverage_info = [
        ["GAP Insurance Premium:", f"${premium:.2f}"],
        ["Refund Calculation Method:", method],
        ["Cancellation Fee:", f"${fee:.2f}"],
    ]
    t = Table(coverage_info, colWidths=[2.5 * inch, 3.5 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * inch))

    # Terms and Conditions
    story.append(Paragraph("REFUND POLICY", heading_style))
    story.append(
        Paragraph(
            f"If you cancel this GAP Agreement, you may be entitled to a refund. The refund will be calculated "
            f"using the <b>{method}</b> method. A cancellation fee of <b>${fee:.2f}</b> will be deducted from any "
            f"refund amount.",
            normal_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Refund method details
    if method == "Pro-rata":
        refund_text = (
            "Under the Pro-rata method, the refund is calculated based on the number of days remaining "
            "in the contract term divided by the total number of days in the contract term, multiplied "
            "by the premium paid."
        )
    elif method == "Flat-rate":
        refund_text = (
            "Under the Flat-rate method, a fixed percentage of the premium is refunded based on when "
            "the cancellation occurs during the contract term."
        )
    else:  # Short-rate
        refund_text = (
            "Under the Short-rate method, the refund is calculated as the unearned premium minus a "
            "penalty for early cancellation. This method typically results in a lower refund than Pro-rata."
        )

    story.append(Paragraph(refund_text, normal_style))
    story.append(Spacer(1, 0.3 * inch))

    # What's Covered
    story.append(Paragraph("WHAT'S COVERED", heading_style))
    story.append(Paragraph("GAP Insurance covers:", normal_style))
    story.append(Spacer(1, 0.1 * inch))

    covered_items = [
        "• The difference between your vehicle's actual cash value and your loan balance",
        "• Outstanding loan balance up to 150% of the vehicle's actual cash value",
        "• Your primary insurance deductible up to $1,000",
        "• Sales tax, title, and registration fees included in the loan",
    ]
    for item in covered_items:
        story.append(Paragraph(item, normal_style))
    story.append(Spacer(1, 0.3 * inch))

    # Signature Block
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("AGREEMENT SIGNATURES", heading_style))
    signature_table = [
        ["Customer Signature:", "_" * 40, "Date:", "_" * 20],
        ["", "", "", ""],
        ["Dealer Representative:", "_" * 40, "Date:", "_" * 20],
    ]
    t = Table(signature_table, colWidths=[1.5 * inch, 2.5 * inch, 0.8 * inch, 1.2 * inch])
    t.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(t)

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle(
        "Footer", parent=normal_style, fontSize=8, textColor=colors.grey, alignment=1  # Center
    )
    story.append(
        Paragraph(
            "This is a legally binding contract. Please read carefully and keep for your records.",
            footer_style,
        )
    )

    # Build PDF
    doc.build(story)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def upload_test_pdfs():
    """Generate and upload test PDFs for all 15 contracts."""
    s3_client = get_s3_client()

    print("\n📄 Generating and uploading test PDFs...")
    print("=" * 60)

    uploaded_count = 0

    for i in range(15):
        make, model = MAKES_MODELS[i]
        year = 2020 + (i % 5)
        account_number = f"{i+1:012d}"
        contract_id = f"GAP-2024-{i+1:04d}"
        customer_name = f"Test Customer {i+1}"
        vin = f"1HGCM82633A{i+1:06d}"
        premium = PREMIUMS[i]
        method = METHODS[i]
        fee = FEES[i]
        contract_date = date.today() - timedelta(days=i * 30)

        # Generate PDF
        pdf_bytes = generate_gap_contract_pdf(
            contract_id=contract_id,
            account_number=account_number,
            customer_name=customer_name,
            make=make,
            model=model,
            year=year,
            vin=vin,
            premium=premium,
            method=method,
            fee=fee,
            contract_date=contract_date,
        )

        # Upload to S3
        s3_key = f"contracts/2024/{contract_id}.pdf"

        try:
            s3_client.put_object(
                Bucket=S3_BUCKET, Key=s3_key, Body=pdf_bytes, ContentType="application/pdf"
            )
            uploaded_count += 1
            print(f"  ✅ {contract_id}.pdf ({len(pdf_bytes)} bytes)")
        except ClientError as e:
            print(f"  ❌ Failed to upload {contract_id}.pdf: {e}")

    print("=" * 60)
    print(f"✅ Uploaded {uploaded_count}/15 PDFs to s3://{S3_BUCKET}")
    return uploaded_count == 15


def list_uploaded_pdfs():
    """List all uploaded PDFs in the bucket."""
    s3_client = get_s3_client()

    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)

        if "Contents" in response:
            print("\n📂 Uploaded PDFs:")
            print("=" * 60)
            for obj in response["Contents"]:
                size_kb = obj["Size"] / 1024
                print(f"  • {obj['Key']} ({size_kb:.1f} KB)")
            print("=" * 60)
            print(f"Total: {len(response['Contents'])} files")
        else:
            print("\nℹ️  No PDFs found in bucket")

        return True
    except ClientError as e:
        print(f"❌ Failed to list objects: {e}")
        return False


def verify_localstack():
    """Verify LocalStack is running and accessible."""
    s3_client = get_s3_client()

    try:
        # Try to list buckets
        s3_client.list_buckets()
        print("✅ LocalStack S3 is accessible")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to LocalStack S3 at {S3_ENDPOINT}")
        print(f"   Error: {e}")
        print("\n💡 Make sure LocalStack is running:")
        print("   cd backend && docker-compose up -d localstack")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup S3 for LocalStack")
    parser.add_argument("--create-bucket", action="store_true", help="Create S3 bucket")
    parser.add_argument("--upload-pdfs", action="store_true", help="Generate and upload test PDFs")
    parser.add_argument("--list", action="store_true", help="List uploaded PDFs")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate everything")
    parser.add_argument("--all", action="store_true", help="Create bucket and upload PDFs")

    args = parser.parse_args()

    # If no args, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    print("\n" + "=" * 60)
    print("S3 Setup for LocalStack")
    print("=" * 60)

    # Verify LocalStack is running
    if not verify_localstack():
        sys.exit(1)

    # Reset (delete and recreate)
    if args.reset or args.all:
        print("\n🗑️  Resetting S3 bucket...")
        delete_bucket()
        create_bucket()
        if not args.all:
            upload_test_pdfs()
            list_uploaded_pdfs()

    # Create bucket
    if args.create_bucket or args.all:
        print("\n📦 Creating S3 bucket...")
        create_bucket()

    # Upload PDFs
    if args.upload_pdfs or args.all:
        print("\n📤 Uploading test PDFs...")
        upload_test_pdfs()
        list_uploaded_pdfs()

    # List PDFs
    if args.list:
        list_uploaded_pdfs()

    print("\n" + "=" * 60)
    print("✅ S3 setup complete!")
    print("=" * 60)
    print("\n💡 Verify setup:")
    print(f"   aws --endpoint-url={S3_ENDPOINT} s3 ls s3://{S3_BUCKET}/contracts/2024/ --recursive")
    print("\n💡 Download a PDF:")
    print(
        f"   aws --endpoint-url={S3_ENDPOINT} s3 cp s3://{S3_BUCKET}/contracts/2024/000000000001/GAP-2024-0001.pdf /tmp/test.pdf"
    )
    print("   open /tmp/test.pdf")
    print()


if __name__ == "__main__":
    main()
