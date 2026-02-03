#!/usr/bin/env python3
"""
TXT to MD Batch Processor using Anthropic Claude API

This script processes all .txt files in a specified input folder,
sends each to Claude with a prompt from a text file, and saves
the response as a .md file in the output folder.

Each file is processed independently with no memory retention between files.
"""

# ==============================================================================
# CONFIGURATION - Edit these values to customize the script
# ==============================================================================

# Input folder containing .txt files to process
INPUT_FOLDER = r"G:\UF_MSCM\Maters Thesis\experiments\claude_extracts\batches"

# Output folder for generated .md files
OUTPUT_FOLDER = r"G:\UF_MSCM\Maters Thesis\experiments\output"

# Path to the prompt text file
PROMPT_FILE = r"G:\UF_MSCM\Maters Thesis\experiments\Prompt.txt"

# Claude API Key (get from https://console.anthropic.com/)
API_KEY = "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"

# Model to use:
# claude-sonnet-4-20250514      - Latest Sonnet, 200K context, balanced speed/quality
# claude-opus-4-20250514        - Latest Opus, 200K context, highest quality
# claude-3-5-sonnet-20241022    - Claude 3.5 Sonnet, 200K context
# claude-3-5-haiku-20241022     - Claude 3.5 Haiku, 200K context, fastest
# All models support 200K tokens (~150K characters input + output)
MODEL = "claude-sonnet-4-20250514"

# Maximum tokens for the response (output)
# For large input files, you may want substantial output
MAX_OUTPUT_TOKENS = 10000

# Delay between API calls in seconds
# Claude API has rate limits based on tokens per minute
# For large 150K character files, use 2-5 seconds
DELAY_BETWEEN_CALLS = 2.0

# Retry delay when rate limited (seconds)
RATE_LIMIT_RETRY_DELAY = 60

# Maximum retries per file when rate limited
MAX_RETRIES = 5

# ==============================================================================
# END OF CONFIGURATION - No need to edit below this line
# ==============================================================================

import os
import sys
import time
from pathlib import Path
import anthropic


def load_prompt_file(prompt_file: str) -> str:
    """Load the prompt from a text file."""
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    content = prompt_path.read_text(encoding='utf-8').strip()
    if not content:
        raise ValueError(f"Prompt file is empty: {prompt_file}")
    
    return content


def get_txt_files(input_dir: Path) -> list[Path]:
    """Get all .txt files in the input directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    txt_files = sorted(input_dir.glob("*.txt"))
    return txt_files


def process_file_with_claude(
    client: anthropic.Anthropic,
    model_name: str,
    file_content: str,
    prompt: str,
    max_tokens: int
) -> str:
    """
    Process a single file's content with Claude API.
    
    Each call creates a fresh conversation with no memory from previous calls.
    """
    # Combine prompt with file content
    full_message = f"{prompt}\n\n---\n\n{file_content}"
    
    # Make API call - each call is independent (no memory retention)
    message = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": full_message
            }
        ]
    )
    
    # Extract text response
    response_text = ""
    for block in message.content:
        if block.type == "text":
            response_text += block.text
    
    return response_text


def process_all_files(
    input_dir: Path,
    output_dir: Path,
    prompt: str,
    api_key: str,
    model_name: str,
    max_tokens: int,
    delay: float,
    rate_limit_delay: float,
    max_retries: int
) -> dict:
    """
    Process all .txt files in the input directory.
    
    Returns a summary dict with counts of processed, failed, and skipped files.
    """
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all txt files
    txt_files = get_txt_files(input_dir)
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return {"processed": 0, "failed": 0, "skipped": 0, "total": 0}
    
    print(f"Found {len(txt_files)} .txt file(s) to process")
    print(f"Model: {model_name}")
    print(f"Max output tokens: {max_tokens}")
    print(f"Delay between calls: {delay}s")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    results = {"processed": 0, "failed": 0, "skipped": 0, "total": len(txt_files)}
    
    for i, txt_file in enumerate(txt_files, 1):
        # Generate output filename
        output_filename = txt_file.stem + ".md"
        output_path = output_dir / output_filename
        
        print(f"\n[{i}/{len(txt_files)}] Processing: {txt_file.name}")
        
        try:
            # Read input file
            file_content = txt_file.read_text(encoding='utf-8')
            
            if not file_content.strip():
                print(f"  ⚠ Skipping empty file")
                results["skipped"] += 1
                continue
            
            print(f"  → Input size: {len(file_content):,} characters")
            
            # Process with Claude (fresh context, no memory) with retries
            response = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = process_file_with_claude(
                        client=client,
                        model_name=model_name,
                        file_content=file_content,
                        prompt=prompt,
                        max_tokens=max_tokens
                    )
                    break  # Success, exit retry loop
                    
                except anthropic.RateLimitError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = rate_limit_delay * (attempt + 1)  # Exponential backoff
                        print(f"  ⚠ Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise
                        
                except anthropic.APIStatusError as e:
                    last_error = e
                    # Check if it's an overload error (529)
                    if e.status_code == 529:
                        if attempt < max_retries - 1:
                            wait_time = rate_limit_delay * (attempt + 1)
                            print(f"  ⚠ API overloaded. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            time.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise  # Other API errors, don't retry
                        
                except anthropic.APIConnectionError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = 10 * (attempt + 1)
                        print(f"  ⚠ Connection error. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            if response is None:
                raise last_error
            
            # Save output
            output_path.write_text(response, encoding='utf-8')
            print(f"  ✓ Saved: {output_path.name} ({len(response):,} characters)")
            results["processed"] += 1
            
            # Small delay to avoid rate limiting
            if i < len(txt_files):
                time.sleep(delay)
                
        except anthropic.RateLimitError as e:
            print(f"  ✗ Rate limit error: {e}")
            results["failed"] += 1
        except anthropic.APIStatusError as e:
            print(f"  ✗ API error ({e.status_code}): {e.message}")
            results["failed"] += 1
        except anthropic.APIConnectionError as e:
            print(f"  ✗ Connection error: {e}")
            results["failed"] += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results["failed"] += 1
    
    return results


def main():
    # Use configuration from top of file, with environment variable fallback for API key
    api_key = API_KEY if API_KEY != "your-anthropic-api-key-here" else None
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: No API key provided.")
        print("Set API_KEY in the configuration section or ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    # Load prompt from file
    try:
        prompt = load_prompt_file(PROMPT_FILE)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print("=" * 50)
    print("TXT to MD Batch Processor (Claude)")
    print("=" * 50)
    print(f"Input folder:  {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Prompt file:   {PROMPT_FILE}")
    print(f"Model:         {MODEL}")
    print(f"Prompt preview: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    
    # Process files
    input_dir = Path(INPUT_FOLDER)
    output_dir = Path(OUTPUT_FOLDER)
    
    try:
        results = process_all_files(
            input_dir=input_dir,
            output_dir=output_dir,
            prompt=prompt,
            api_key=api_key,
            model_name=MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            delay=DELAY_BETWEEN_CALLS,
            rate_limit_delay=RATE_LIMIT_RETRY_DELAY,
            max_retries=MAX_RETRIES
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total files:     {results['total']}")
    print(f"Processed:       {results['processed']}")
    print(f"Failed:          {results['failed']}")
    print(f"Skipped (empty): {results['skipped']}")
    
    if results['failed'] > 0:
        sys.exit(1)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
