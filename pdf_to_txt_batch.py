#!/usr/bin/env python3
"""
OCIS Literature Extractor for Claude
=====================================
Extracts text from PDFs and prepares them for efficient upload to Claude.

Usage:
    python extract_papers_for_claude.py /path/to/zotero/pdfs

Requirements:
    pip install pymupdf

Output:
    - Individual .txt files for each PDF
    - Batched files (10 papers each) ready for upload
    - A manifest listing all processed papers
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)


def clean_text(text):
    """Clean extracted text for better readability."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove page headers/footers patterns (common in academic papers)
    text = re.sub(r'\n\d+\s*\n', '\n', text)
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()


def extract_pdf_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"[Page {page_num}]\n{page_text}")
        
        doc.close()
        return clean_text('\n\n'.join(text_parts))
    
    except Exception as e:
        return f"ERROR extracting {pdf_path}: {str(e)}"


def get_paper_metadata(filename, text):
    """Try to extract basic metadata from filename and text."""
    # Clean filename for title guess
    name = Path(filename).stem
    # Remove common Zotero patterns like "Author - Year - Title"
    name = re.sub(r'^\d{4}\s*[-_]\s*', '', name)
    name = re.sub(r'[-_]', ' ', name)
    
    # Try to find DOI in text
    doi_match = re.search(r'10\.\d{4,}/[^\s]+', text[:5000])
    doi = doi_match.group(0).rstrip('.,;') if doi_match else "Not found"
    
    return {
        'filename': filename,
        'title_guess': name[:100],
        'doi': doi,
        'pages': text.count('[Page '),
        'chars': len(text)
    }


def process_folder(input_folder, output_folder=None, batch_size=5):
    """Process all PDFs in a folder."""
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"ERROR: Folder not found: {input_folder}")
        sys.exit(1)
    
    # Create output folder
    if output_folder:
        output_path = Path(output_folder)
    else:
        output_path = input_path / "claude_extracts"
    
    output_path.mkdir(exist_ok=True)
    individual_folder = output_path / "individual"
    individual_folder.mkdir(exist_ok=True)
    batches_folder = output_path / "batches"
    batches_folder.mkdir(exist_ok=True)
    
    # Find all PDFs (including in subfolders - Zotero's default export structure)
    pdfs = list(input_path.glob("*.pdf")) + list(input_path.glob("*.PDF"))
    pdfs += list(input_path.glob("**/*.pdf")) + list(input_path.glob("**/*.PDF"))
    # Remove duplicates while preserving order
    seen = set()
    unique_pdfs = []
    for p in pdfs:
        if p not in seen:
            seen.add(p)
            unique_pdfs.append(p)
    pdfs = sorted(unique_pdfs, key=lambda x: x.name.lower())
    
    if not pdfs:
        print(f"ERROR: No PDF files found in {input_folder}")
        sys.exit(1)
    
    print(f"Found {len(pdfs)} PDF files")
    print(f"Output folder: {output_path}")
    print("-" * 50)
    
    # Process each PDF
    results = []
    all_texts = []
    
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] Processing: {pdf_path.name[:50]}...")
        
        text = extract_pdf_text(pdf_path)
        metadata = get_paper_metadata(pdf_path.name, text)
        
        if text.startswith("ERROR"):
            print(f"  WARNING: {text}")
            metadata['status'] = 'error'
        else:
            metadata['status'] = 'success'
            
            # Save individual file
            safe_name = re.sub(r'[^\w\-]', '_', pdf_path.stem)[:50]
            txt_path = individual_folder / f"{i:03d}_{safe_name}.txt"
            
            # Add header to individual file
            header = f"""{'='*60}
PAPER {i}: {metadata['title_guess']}
{'='*60}
Source: {pdf_path.name}
DOI: {metadata['doi']}
Pages: {metadata['pages']}
{'='*60}

"""
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(header + text)
            
            all_texts.append((i, pdf_path.name, metadata, text))
        
        results.append(metadata)
    
    # Create batched files
    print("-" * 50)
    print("Creating batched files for upload...")
    
    batch_num = 1
    for batch_start in range(0, len(all_texts), batch_size):
        batch = all_texts[batch_start:batch_start + batch_size]
        batch_content = f"""{'#'*60}
# OCIS LITERATURE BATCH {batch_num}
# Papers {batch_start + 1} to {batch_start + len(batch)} of {len(all_texts)}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'#'*60}

INSTRUCTIONS FOR CLAUDE:
For each paper below, please extract:
1. Research Question/Objective
2. Key Findings (2-3 bullets)
3. OCIS Relevance (Cost/Schedule/Change Order/Contract domain)
4. Key Quotes (with page numbers)
5. Methodology
6. Gaps/Limitations

{'='*60}

"""
        for idx, filename, meta, text in batch:
            batch_content += f"""
{'='*60}
PAPER {idx}: {meta['title_guess']}
{'='*60}
Filename: {filename}
DOI: {meta['doi']}
Pages: {meta['pages']}
{'='*60}

{text}

{'~'*60}
END OF PAPER {idx}
{'~'*60}

"""
        
        batch_path = batches_folder / f"batch_{batch_num:02d}_papers_{batch_start+1}_to_{batch_start+len(batch)}.txt"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Get file size
        size_mb = batch_path.stat().st_size / (1024 * 1024)
        print(f"  Batch {batch_num}: {len(batch)} papers, {size_mb:.1f} MB")
        
        batch_num += 1
    
    # Create manifest
    manifest = f"""# OCIS Literature Extraction Manifest
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Total Papers: {len(pdfs)}
Successfully Extracted: {sum(1 for r in results if r['status'] == 'success')}
Errors: {sum(1 for r in results if r['status'] == 'error')}
Batches Created: {batch_num - 1}

## Upload Instructions

1. Go to your OCIS Claude Project
2. Upload batch files one at a time from: {batches_folder}
3. Say: "Please extract structured notes for these papers"
4. Wait for response, then upload next batch

## Papers Processed

| # | Status | Pages | Chars | Filename |
|---|--------|-------|-------|----------|
"""
    
    for i, r in enumerate(results, 1):
        manifest += f"| {i} | {r['status']} | {r['pages']} | {r['chars']:,} | {r['filename'][:40]}... |\n"
    
    manifest_path = output_path / "MANIFEST.md"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest)
    
    # Summary
    print("-" * 50)
    print("COMPLETE!")
    print(f"  Individual texts: {individual_folder}")
    print(f"  Batch files:      {batches_folder}")
    print(f"  Manifest:         {manifest_path}")
    print("-" * 50)
    print("\nNEXT STEPS:")
    print(f"1. Check the batch files in: {batches_folder}")
    print("2. Upload each batch to Claude (one at a time)")
    print("3. Request structured extraction for each batch")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample:")
        print("  python extract_papers_for_claude.py ~/Zotero/storage/my_collection")
        print("  python extract_papers_for_claude.py ./papers ./output")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_folder(input_folder, output_folder)
