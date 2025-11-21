# Test PDFs Directory

This directory can be used to store custom test PDF files that you want to upload to LocalStack S3.

## Automatic PDF Generation

By default, the `setup_s3.py` script **automatically generates** realistic GAP insurance contract PDFs that match the seeded database contracts. You don't need to manually create or place PDFs here.

```bash
# Generate and upload all 15 test PDFs automatically
cd backend
uv run python scripts/setup_s3.py --all
```

## Custom PDF Files (Optional)

If you want to use your own PDF files instead of generated ones, you can place them here with the following naming convention:

```
GAP-2024-0001.pdf
GAP-2024-0002.pdf
...
GAP-2024-0015.pdf
```

Then modify the `setup_s3.py` script's `upload_test_pdfs()` function to upload from this directory instead of generating PDFs.

## Example: Using Custom PDFs

1. Place your PDF files in this directory:
   ```
   backend/test_pdfs/
   ├── GAP-2024-0001.pdf
   ├── GAP-2024-0002.pdf
   └── ...
   ```

2. Upload them to LocalStack:
   ```bash
   # Manual upload with AWS CLI
   for i in {1..15}; do
     contract_id=$(printf "GAP-2024-%04d" $i)
     account_num=$(printf "%012d" $i)
     aws --endpoint-url=http://localhost:4566 s3 cp \
       test_pdfs/${contract_id}.pdf \
       s3://test-contract-documents/contracts/2024/${account_num}/${contract_id}.pdf
   done
   ```

## Testing PDF Upload

After uploading, verify the PDFs are accessible:

```bash
# List all PDFs in bucket
aws --endpoint-url=http://localhost:4566 s3 ls \
  s3://test-contract-documents/contracts/2024/ --recursive

# Download a test PDF
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://test-contract-documents/contracts/2024/000000000001/GAP-2024-0001.pdf \
  /tmp/test.pdf

# View the PDF
open /tmp/test.pdf  # macOS
# or
xdg-open /tmp/test.pdf  # Linux
```

## Generated PDF Contents

The automatically generated PDFs include:

- **Contract Information:** Contract ID, account number, customer name, contract date
- **Vehicle Information:** Year, make, model, VIN
- **Coverage Details:** GAP insurance premium, refund calculation method, cancellation fee
- **Terms & Conditions:** Refund policy with detailed method explanations
- **What's Covered:** Comprehensive coverage list
- **Signature Block:** For customer and dealer representative

All values match the seeded database records exactly, making it easy to test the extraction and chat features.

## Notes

- This directory is **optional** and only needed if you want to use custom PDFs
- The `.gitkeep` file keeps this directory in version control
- PDF files (*.pdf) are ignored by git (see `.gitignore`)
- LocalStack stores PDFs in `backend/localstack/` directory
