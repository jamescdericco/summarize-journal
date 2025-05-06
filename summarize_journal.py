#!/usr/bin/env python3

# TODO Retest journal.org functionality with the new skipping logic

# Summarize journal entries using Ollama

import os
import re
import requests
import argparse
import json
from typing import TypedDict

# --- Configuration ---
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2" # Default model, can be overridden by args
DEFAULT_INPUT_FILE = "journal.org"
DEFAULT_OUTPUT_FILE = "journal-summary.md"
# Basic prompt for summarization
DEFAULT_PROMPT_TEMPLATE = "Write a concise, one to three sentence summary of the following journal entry I wrote /no_think:\n\n{entry_text}"

class JournalEntry(TypedDict):
    heading: str | None # Optional heading, used when filename is not available, such as for Org Mode journals
    filename: str | None # Optional filename for markdown entries
    content: str

# --- Helper Functions ---

def parse_org_journal(file_path: str) -> list[JournalEntry]:
    """
    Parses an Emacs Org Mode file to extract journal entries.

    Args:
        file_path (str): Path to the journal.org file.

    Returns:
        list: A list of JournalEntry dictionaries
              Returns an empty list if the file cannot be read or
              no entries are found.
    """
    entries: list[JournalEntry] = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    # Regex to find journal entry headings and capture the date string
    # It looks for "** Journal Entry <DATE_STRING>" followed by content
    # until the next "** " heading or end of file.
    # Using re.DOTALL so '.' matches newline characters.
    # Using re.MULTILINE to ensure '^' matches start of lines for '** ' check.
    pattern = re.compile(r'^\*\* Journal Entry <(.*?)>\n(.*?)(?=\n^\*\* |\Z)', re.DOTALL | re.MULTILINE)

    for match in pattern.finditer(content):
        date_str = match.group(1).strip()
        entry_content = match.group(2).strip()

        if entry_content: # Only add if there's content
            entries.append({
                'heading': date_str,
                'filename': None, # Org Mode entries don't have a filename
                'content': entry_content
            })

    # For simplicity, we process in the order found in the file.
    # If chronological order is critical, add sorting logic here, potentially
    # filtering out entries where date parsing failed.

    return entries

def parse_journal_summary_file(file_path: str) -> list[JournalEntry]:
    """
    Parses a Markdown file to extract journal summaries.

    Args:
        file_path (str): Path to the journal summary markdown file.

    Returns:
        list: A list of JournalEntry dictionaries
              Returns an empty list if the file cannot be read or
              no entries are found.
    """
    entries: list[JournalEntry] = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    # Regex to find journal entry headings and capture the date string
    # It looks for "## <heading>" followed by content
    # until the next "## " heading or end of file.
    pattern = re.compile(r'^# (.*?)\n(.*?)(?=\n^# |\Z)', re.DOTALL | re.MULTILINE)

    for match in pattern.finditer(content):
        heading = match.group(1).strip()
        entry_content = match.group(2).strip()

        # Parse [[filename]] from the heading
        filename = None
        filename_match = re.search(r'\[\[(.*?)\]\]', heading)
        if filename_match:
            filename = filename_match.group(1).strip()

        if entry_content: # Only add if there's content
            entries.append({
                'heading': heading,
                'filename': filename,
                'content': entry_content
            })

    return entries


def summarize_with_ollama(text: str, model: str, ollama_url: str, prompt_template: str) -> str | None:
    """
    Sends text to the Ollama API for summarization.

    Args:
        text (str): The text content of the journal entry.
        model (str): The Ollama model name to use.
        ollama_url (str): The URL of the Ollama API endpoint.
        prompt_template (str): The template for the prompt, with {entry_text} placeholder.

    Returns:
        str: The summarized text, or None if an error occurs.
    """
    full_prompt = prompt_template.format(entry_text=text)
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False # Get the full response at once
    }
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"  Sending entry to Ollama (model: {model})...")
        url_endpoint = ollama_url + "/api/generate"
        response = requests.post(url_endpoint, json=payload, headers=headers, timeout=120) # Increased timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_data = response.json()
        summary = response_data.get('response', '').strip()

        # Filter out <think>...</think> tags or similar artifacts if needed
        summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
        # Add any other filtering rules here if necessary

        print("  Summary received.")
        return summary

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Ollama server at {ollama_url}.")
        print("Please ensure the Ollama server is running.")
        return None
    except requests.exceptions.Timeout:
        print("Error: Request to Ollama timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error during Ollama API request: {e}")
        # Optionally print more details for debugging
        # try:
        #     print(f"Ollama Response Status Code: {response.status_code}")
        #     print(f"Ollama Response Body: {response.text}")
        # except NameError: # response might not be defined if connection failed early
        #     pass
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from Ollama.")
        print(f"Ollama Response Text: {response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during summarization: {e}")
        return None


def append_summary_to_markdown(output_file, heading, summary):
    """
    Appends a formatted summary to the output Markdown file.

    Args:
        output_file (str): Path to the output markdown file.
        heading (str): Heading for the entry's summary
        summary (str): The summary text generated by Ollama.
    """
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"# {heading}\n\n")
            f.write(f"{summary}\n\n") # Add summary and extra newline
            print(f"  Summary appended to {output_file}")
    except Exception as e:
        print(f"Error writing to output file {output_file}: {e}")

def test_ollama_connection(url: str) -> bool:
    """Test connection to Ollama server."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to Ollama server at {url}")
        print(f"Details: {str(e)}")
        return False

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Summarize Emacs Org Mode journal entries using Ollama.")
    parser.add_argument(
        "-j", "--input-journal-org",
        help=f"Path to the input journal containing multiple entries in Emacs Org Mode format"
    )
    parser.add_argument(
        "-e", "--input-entry-md",
        nargs='+',
        help="Path to one or more input journal entry file(s) in Markdown format"
    )
    parser.add_argument(
        "-o", "--output-md",
        required=True,
        help=f"Path to the output Markdown summary file (default: {DEFAULT_OUTPUT_FILE})"
    )
    parser.add_argument(
        "-m", "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model name to use for summarization (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "-u", "--url",
        default=DEFAULT_OLLAMA_URL,
        help=f"URL for the Ollama API endpoint (default: {DEFAULT_OLLAMA_URL})"
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT_TEMPLATE,
        help="Prompt template for Ollama (use {entry_text} as placeholder)"
    )

    args = parser.parse_args()

    print(f"Starting journal summarization...")
    print(f"Output file: {args.output_md}")
    print(f"Ollama model: {args.model}")
    print(f"Ollama URL: {args.url}")
    
    # Exit with an error if both --intput-org-journal and --input-md-file are provided
    if args.input_journal_org and args.input_entry_md:
        print("Error: Please provide either --input-org-journal or --input-md-file, not both.")
        return
    
    # If the output file exists, parse the existing summaries to determine what to skip
    existing_summaries = parse_journal_summary_file(args.output_md)
    files_already_summarized = {entry['filename'] + '.md' for entry in existing_summaries if entry['filename']}
    

    entries: list[JournalEntry] = []

    # Calculate the set of files not already summarized
    if args.input_entry_md:        
        files_to_summarize: list[str] = [md_file_path for md_file_path in args.input_entry_md if os.path.basename(md_file_path) not in files_already_summarized]

        # Read each markdown file and parse the entries
        for md_file_path in files_to_summarize:
            print(f"Reading file: {md_file_path}")
            # Read the content of the markdown file
            try:
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.splitext(os.path.basename(md_file_path))[0]
                    entries.append({
                        'heading': None,
                        'filename': filename,
                        'content': content
                    })
            except FileNotFoundError:
                print(f"Error: Input file not found at {md_file_path}")
                continue
            except Exception as e:
                print(f"Error reading file {md_file_path}: {e}")
                continue
            
    elif args.input_journal_org:
        entries = parse_org_journal(args.input_journal_org)

    if not entries:
        print("No new journal entries found or file could not be read. Exiting.")
        return

    print(f"Found {len(entries)} journal entries to process.")

    # Confirm with the user before proceeding
    print(f"\nThe following entries will be processed:")
    for entry in entries:
        if entry['filename']:
            print(f"  - {entry['filename']}.md")
        else:
            # If no filename, use the heading (date string)
            # This is for Org Mode entries
            if entry['heading']:
                print(f"  - {entry['heading']}")
            else:
                print("  - No filename or heading available.")
    
    confirm = input("Do you want to proceed with summarization? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Exiting without processing.")
        return

    # Test connection to Ollama server
    if not test_ollama_connection(args.url):
        return

    processed_count = 0
    for i, entry in enumerate(entries):
        heading = f'[[{entry["filename"]}]]' if entry['filename'] else entry['heading']
        print(f"\nProcessing entry {i+1}/{len(entries)} (heading: {heading})...")

        # Basic check for empty content, although parser should handle it
        if not entry['content']:
            print("  Skipping entry with empty content.")
            continue

        summary = summarize_with_ollama(entry['content'], args.model, args.url, args.prompt)

        if summary:
            append_summary_to_markdown(args.output_md, heading, summary)
            processed_count += 1
        else:
            print(f"  Failed to generate summary for entry (Date: {entry['heading']}). Exiting.")
            return

    print(f"\nSummarization complete. Processed {processed_count}/{len(entries)} entries.")
    print(f"Summaries appended to: {args.output_md}")

if __name__ == "__main__":
    main()
