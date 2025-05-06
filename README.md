# Journal Summarizer (`summarize_journal.py`)

A Python command-line tool to summarize journal entries using a locally running Ollama language model. It processes multiple Markdown journal entry files or a ingle Emacs Org Mode file with multiple entries and generates a single consolidated Markdown file containing the summaries. For Markdown inputs, it automatically includes Obsidian-style internal links (`[[filename]]`) in the summary headings, linking back to the original journal entry files.

The most common use case is summarizing a batch of Obsidian daily notes into a single overview file.

## Features

* **AI Summarization:** Leverages Ollama models running locally to generate concise summaries of journal entries.
* **Multiple Input Formats:**
    * Processes multiple individual Markdown files (`.md`), treating each file as a single entry.
    * Parses a single Emacs Org Mode file (`.org`), extracting entries based on `** Journal Entry <DATE_STRING>` headings.
* **Consolidated Output:** Creates a single Markdown file (`.md`) containing all generated summaries.
* **Obsidian Integration:** Automatically generates Obsidian-style `[[filename]]` links in headings for summaries derived from Markdown files.
* **Incremental Summaries:** Checks the output file before processing and skips entries that have already been summarized, preventing duplicates and allowing you to update the summary file easily.
* **Configurable:** Allows specifying the Ollama model, API URL, and the summarization prompt via command-line arguments.
* **User-Friendly:** Provides progress feedback, tests Ollama connection, and asks for confirmation before potentially lengthy processing.

## Prerequisites

1.  **Python 3:** Ensure you have Python 3 installed.
2.  **Python `requests` library:** Install it using pip:
    ```bash
    pip install requests
    # or
    pip3 install requests
    ```
3.  **Ollama:** You need a running Ollama instance.
    * Download and install Ollama from [https://ollama.com/](https://ollama.com/).
    * Ensure the Ollama server is running (it usually runs in the background after installation). By default, the script assumes it's available at `http://localhost:11434`.
4.  **Ollama Model:** Download the language model you want to use. The script defaults to `llama3.2`. You can download it via:
    ```bash
    ollama pull llama3.2
    ```
    Replace `llama3.2` with any other model supported by Ollama if you prefer.

## Installation

1.  Clone this repository or download the `summarize_journal.py` script.
2.  Make the script executable (optional but convenient):
    ```bash
    chmod +x summarize_journal.py
    ```
3.  Install the required Python library (see Prerequisites).

## Usage

Run the script from your terminal using `python3` or `./summarize_journal.py` if you made it executable.

```bash
python3 summarize_journal.py --output-md <output_summary_file.md> [input options] [configuration options]
```
### Input Options (Choose One)
`--input-entry-md <file1.md> [<file2.md> ...]`: Specify one or more Markdown files. Each file is treated as a separate journal entry. You can use wildcards (like `*`) if your shell supports them to select multiple files (e.g., all daily notes from a specific year).
The filename (without the .md extension) will be used to create an Obsidian-style link in the summary heading (e.g., `[[2025-05-06]]`).

`--input-journal-org <journal.org>`: Specify a single Emacs Org Mode file. The script will look for level 2 headings matching the pattern `** Journal Entry <DATE_STRING>`.
The `<DATE_STRING>` part of the heading will be used as the heading in the summary file (e.g., `2025-05-06 Tue`).

### Output Option (Required)
`-o, --output-md <path/to/output_summary.md>`: Specifies the path where the consolidated Markdown summary file will be created or appended to.
Configuration Options (Optional)
`-m, --model <model_name>`: Specify the Ollama model to use for summarization. (Default: llama3.2)
`-u, --url <ollama_api_url>`: Specify the URL of your running Ollama instance. (Default: `http://localhost:11434`)
`--prompt <prompt_template>`: Define a custom prompt template. Use {entry_text} as a placeholder for the journal entry content. (Default: "Write a concise, one to three sentence summary of the following journal entry I wrote /no_think:\n\n{entry_text}")
### Examples
1. Summarize Obsidian Daily Notes from 2025:
(Assumes daily notes are named like `YYYY-MM-DD.md` or `YYYYMMDD*.md` and your shell expands the wildcard `*`)

```bash
python3 summarize_journal.py \
    --input-entry-md ~/Documents/Obsidian/MyVault/Daily/2025*.md \
    --output-md ~/Documents/Obsidian/MyVault/Summaries/Journal-2025-Summary.md
```

2. Summarize specific Markdown entry files:

```bash
python3 summarize_journal.py \
    --input-entry-md entry1.md path/to/another_entry.md \
    --output-md summary.md
```

3. Summarize an Emacs Org Mode journal:
```bash
python3 summarize_journal.py \
    --input-journal-org ~/Documents/Org/my_journal.org \
    --output-md ~/Documents/Org/my_journal_summary.md
```

4. Use a different Ollama model and specify the URL:

```bash
python3 summarize_journal.py \
    --input-entry-md notes/*.md \
    --output-md notes_summary.md \
    --model qwen3 \
    --url [http://192.168.1.100:11434](http://192.168.1.100:11434)
```

## Input Formats
Markdown (`--input-entry-md`): Each .md file provided is treated as a single, complete journal entry. The content of the file is sent to Ollama.

Org Mode (`--input-journal-org`): The script parses the specified .org file looking for headings like `** Journal Entry <some date or identifier>`. The text between one such heading and the next `**` heading (or the end of the file) is considered the content of that entry.

## Output Format
The output is a single Markdown file containing the summaries. Each summary is preceded by a level 1 heading (#).

For summaries from Markdown files, the heading will be # [[filename]] (e.g., # [[2025-05-06]]).

For summaries from Org Mode files, the heading will be # DATE_STRING (e.g., `# 2025-05-06 Tue`), based on what was captured from the `** Journal Entry <DATE_STRING>` heading.

Each summary follows its heading, separated by a blank line.

## Skipping Processed Entries
Before summarizing an entry, the script checks if a summary with the corresponding heading already exists in the `--output-md` file.

For Markdown inputs, it checks for headings like `# [[filename]]`.
For Org Mode inputs, it checks for headings like `# DATE_STRING`.

If a matching heading is found, that entry is skipped. This allows you to run the script repeatedly on the same set of files without generating duplicate summaries, only adding summaries for new entries.

## Troubleshooting
Connection Error: "Could not connect to Ollama server..." Ensure the Ollama application is running and accessible at the specified URL (default http://localhost:11434). Check firewall settings if accessing Ollama remotely.

Timeout: "Request to Ollama timed out." The model might be taking too long to respond. This can happen with large entries or slow hardware. The script has a default timeout of 120 seconds. Complex models might require more time.

Model Not Found: Ensure the model name specified with --model (or the default llama3.2) has been downloaded via `ollama pull <model_name>`.

File Not Found: Double-check the paths provided for input and output files. Ensure wildcard patterns are expanding correctly in your shell.

JSON Decode Error: Indicates an unexpected response from the Ollama server. Check the Ollama server logs for more details.
