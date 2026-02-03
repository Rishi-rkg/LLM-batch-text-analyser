# Batch Processing Toolkit for Document Analysis

A collection of Python scripts for batch processing documents using AI APIs. This toolkit includes scripts for extracting text from PDFs and processing text files with Google Gemini or Anthropic Claude APIs.

---

## Scripts Included

| Script | Purpose |
|--------|---------|
| `pdf_to_txt_batch.py` | Extract text from PDF files to TXT files |
| `txt_to_md_gemini.py` | Process TXT files with Google Gemini API → MD output |
| `txt_to_md_claude.py` | Process TXT files with Anthropic Claude API → MD output |

---

## Typical Workflow

```
PDF Files → [pdf_to_txt_batch.py] → TXT Files → [txt_to_md_gemini.py OR txt_to_md_claude.py] → MD Files
```

1. **Extract text** from PDFs using `pdf_to_txt_batch.py`
2. **Process text** with AI using either Gemini or Claude script
3. **Get markdown output** with AI-generated analysis/summaries

---

## Installation

### Requirements

- Python 3.8 or higher

### Install Dependencies

```bash
# For PDF extraction (choose one)
pip install PyMuPDF      # Recommended - fast and accurate
# OR
pip install pdfplumber   # Alternative

# For Gemini API
pip install google-genai

# For Claude API
pip install anthropic
```

---

## Script 1: PDF to TXT Batch Extractor

### `pdf_to_txt_batch.py`

Extracts text from all PDF files in a folder and saves as TXT files.

### Configuration

Edit the configuration section at the top of the script:

```python
# Input folder containing PDF files
INPUT_FOLDER = r"G:\path\to\pdf_files"

# Output folder for extracted TXT files
OUTPUT_FOLDER = r"G:\path\to\txt_output"
```

### Usage

```bash
python pdf_to_txt_batch.py
```

### Output

- Each `document.pdf` produces `document.txt`
- Preserves text structure and formatting where possible

---

## Script 2: TXT to MD with Google Gemini

### `txt_to_md_gemini.py`

Processes TXT files using Google Gemini API and outputs markdown files.

### Configuration

Edit the configuration section at the top of the script:

```python
# Input folder containing .txt files to process
INPUT_FOLDER = r"G:\path\to\txt_files"

# Output folder for generated .md files
OUTPUT_FOLDER = r"G:\path\to\md_output"

# Path to the prompt text file
PROMPT_FILE = r"G:\path\to\Prompt.txt"

# Gemini API Key
API_KEY = "your-gemini-api-key-here"

# Model to use
MODEL = "gemini-1.5-flash"

# Delay between API calls (seconds)
DELAY_BETWEEN_CALLS = 0.1

# Retry delay when rate limited (seconds)
RATE_LIMIT_RETRY_DELAY = 30

# Maximum retries per file
MAX_RETRIES = 3
```

### Available Models

| Model | Context Window | Best For |
|-------|---------------|----------|
| `gemini-2.0-flash` | 128K tokens (~96K chars) | Small files, fastest |
| `gemini-2.0-flash-lite` | 128K tokens | Lighter variant |
| `gemini-1.5-flash` | 1M tokens (~750K chars) | Large files ✓ |
| `gemini-1.5-pro` | 2M tokens (~1.5M chars) | Very large files, highest quality |

### For Large Files (150K+ characters)

```python
MODEL = "gemini-1.5-flash"          # Use 1M context model
DELAY_BETWEEN_CALLS = 1.0           # Increase delay
RATE_LIMIT_RETRY_DELAY = 60         # Longer retry wait
MAX_RETRIES = 5                     # More retries
```

### Get API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API key"
3. Create or copy your API key

### Usage

```bash
python txt_to_md_gemini.py
```

---

## Script 3: TXT to MD with Anthropic Claude

### `txt_to_md_claude.py`

Processes TXT files using Anthropic Claude API and outputs markdown files.

### Configuration

Edit the configuration section at the top of the script:

```python
# Input folder containing .txt files to process
INPUT_FOLDER = r"G:\path\to\txt_files"

# Output folder for generated .md files
OUTPUT_FOLDER = r"G:\path\to\md_output"

# Path to the prompt text file
PROMPT_FILE = r"G:\path\to\Prompt.txt"

# Claude API Key
API_KEY = "your-anthropic-api-key-here"

# Model to use
MODEL = "claude-sonnet-4-20250514"

# Maximum tokens for the response (output)
MAX_OUTPUT_TOKENS = 8192

# Delay between API calls (seconds)
DELAY_BETWEEN_CALLS = 2.0

# Retry delay when rate limited (seconds)
RATE_LIMIT_RETRY_DELAY = 60

# Maximum retries per file
MAX_RETRIES = 5
```

### Available Models

| Model | Context Window | Speed | Quality |
|-------|---------------|-------|---------|
| `claude-sonnet-4-20250514` | 200K tokens | Fast | High ✓ |
| `claude-opus-4-20250514` | 200K tokens | Slower | Highest |
| `claude-3-5-sonnet-20241022` | 200K tokens | Fast | High |
| `claude-3-5-haiku-20241022` | 200K tokens | Fastest | Good |

All Claude models support 200K tokens (~150K characters), suitable for large files.

### Get API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key

### Usage

```bash
python txt_to_md_claude.py
```

---

## Creating a Prompt File

Both AI scripts require a prompt file (`Prompt.txt`) that tells the AI how to process each document.

### Example Prompts

**Summarization:**
```text
Please summarize the following document. Include:
- Main topic and purpose
- Key findings or arguments
- Important data or statistics
- Conclusions and recommendations

Format your response as clean markdown.
```

**Data Extraction:**
```text
Extract the following information from this document:

## Key Information
- Document type
- Date/time references
- People/organizations mentioned
- Monetary amounts
- Action items or deadlines

## Summary
Provide a brief 2-3 sentence summary.
```

**Analysis:**
```text
Analyze this document and provide:

1. **Overview**: What is this document about?
2. **Key Points**: List the main arguments or findings
3. **Methodology**: How was the research/analysis conducted?
4. **Results**: What were the outcomes?
5. **Limitations**: Any noted limitations or gaps?
6. **Relevance**: How does this relate to construction data standardization?

Format as structured markdown.
```

---

## Output

All scripts produce:

- Progress updates for each file processed
- Summary at the end showing:
  - Total files found
  - Successfully processed
  - Failed (with error messages)
  - Skipped (empty files)

### Example Output

```
==================================================
TXT to MD Batch Processor (Claude)
==================================================
Input folder:  G:\UF_MSCM\Maters Thesis\experiments\claude_extracts\batches
Output folder: G:\UF_MSCM\Maters Thesis\experiments\output
Prompt file:   G:\UF_MSCM\Maters Thesis\experiments\Prompt.txt
Model:         claude-sonnet-4-20250514
--------------------------------------------------

[1/10] Processing: document1.txt
  → Input size: 145,230 characters
  ✓ Saved: document1.md (3,421 characters)

[2/10] Processing: document2.txt
  → Input size: 152,108 characters
  ✓ Saved: document2.md (4,102 characters)

...

==================================================
SUMMARY
==================================================
Total files:     10
Processed:       10
Failed:          0
Skipped (empty): 0

Done!
```

---

## Error Handling

All scripts handle common errors:

| Error | Handling |
|-------|----------|
| Empty files | Skipped automatically |
| Rate limiting | Waits and retries (configurable) |
| API errors | Logged, continues with next file |
| Connection errors | Retries with backoff |
| File not found | Reports error and exits |

---

## Tips

### Performance

- **Gemini** is generally faster and has higher rate limits
- **Claude** may provide more nuanced analysis for complex documents
- Start with small batches to test your prompt before processing all files

### Cost Management

- Each file = 1 API call
- Larger files use more tokens = higher cost
- Check pricing:
  - [Gemini Pricing](https://ai.google.dev/pricing)
  - [Claude Pricing](https://www.anthropic.com/pricing)

### Prompt Tips

- Be specific about output format
- Include examples if needed
- Specify what to include/exclude
- Request markdown formatting for clean output

---

## Troubleshooting

### "No module named 'anthropic'"
```bash
pip install anthropic
```

### "No module named 'google.genai'"
```bash
pip install google-genai
```

### "No module named 'fitz'" (for PDF extraction)
```bash
pip install PyMuPDF
```

### Rate Limit Errors

Increase these values in the configuration:
```python
DELAY_BETWEEN_CALLS = 5.0      # More delay between files
RATE_LIMIT_RETRY_DELAY = 120   # Longer wait on rate limit
MAX_RETRIES = 10               # More retry attempts
```

### File Too Large

- For Gemini: Use `gemini-1.5-flash` or `gemini-1.5-pro`
- For Claude: All models support 200K tokens (should handle most files)
- Consider splitting very large files

---

## License

These scripts are provided as-is for research and educational purposes.

---

## Support

For API-specific issues:
- [Gemini Documentation](https://ai.google.dev/docs)
- [Claude Documentation](https://docs.anthropic.com/)
