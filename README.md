# resumes-for-all

Generate resumes in multiple formats — **LaTeX**, **Markdown**, and **HTML** — from a single YAML source using **Jinja2 templates**.

This project automates resume generation locally and through **GitLab CI/CD** but it can be adapted for GitHub, too.
Your personal data lives in one file (`resume.yaml`), and `generate.py` renders every template in the `templates/` directory into a clean, named output file.

---

## 🧰 Features

- **Single source of truth:** All resume content in `resume.yaml`.
- **Multi-format output:** `.pdf`, `.tex`, `.md`, `.txt`, and `.html` from Jinja2 templates.
- **Auto naming & deduplication:** Generates consistent file names automatically.
- **Integrated build pipeline:** Copies the LaTeX class file and compiles all `.tex` → `.pdf` in one command.
- **Automation-ready:** Works locally and through GitLab CI/CD.
- **Extensible templates:** Add more formats (DOCX, JSON, etc.) easily.
- **Optional Rendering:** Some fields can be excluded or included with variables.

---

## 📦 Requirements

### Local Development

Make sure you have:

- Python 3.12 or later
- LaTeX packages:

```bash
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

- Python libraries:

```bash
pip install jinja2 pyyaml
```

---

## 🚀 Usage

### 1. Edit your data

Modify `resume.yaml` with your name, contact details, and experience.
Use `resume.sample.yaml` as a starting point.

---

### 2. Generate output files

Run the generator locally:

```bash
python generate.py
```

This scans the `templates/` directory for any files ending in `.j2`
and renders each one using your `resume.yaml` data.

All generated files are written to the `out/` directory by default.

Example output:

```text
out/
├── davidcrumpton.res8.tex
├── davidcrumpton.res8.pdf
├── davidcrumpton.tex
├── davidcrumpton.pdf
├── davidcrumpton.md
├── davidcrumpton.html
```

To render templates **and** compile all `.tex` files to PDF in one step:

```bash
python generate.py --build
```

This replaces the old `build` shell script. It copies `res.cls` into the output
directory and runs `pdflatex` on every `.tex` file found there.

---

### 3. CLI Options

`generate.py` supports a full set of command-line options:

```text
usage: generate.py [-h] [-d FILE] [-t FILE] [--template-dir DIR]
                   [-o DIR] [-b] [--cls FILE] [-v]
```

| Flag | Default | Description |
|---|---|---|
| `-d, --data FILE` | `resume.yaml` | YAML data file to render from |
| `-t, --template FILE` | *(all `.j2`)* | Render a single template instead of all |
| `--template-dir DIR` | `templates/` | Directory containing Jinja2 templates |
| `-o, --outdir DIR` | `out/` | Directory to write output files into |
| `-b, --build` | off | Run the full build pipeline (copy `.cls` + compile `.tex` → PDF) |
| `--cls FILE` | `res.cls` | LaTeX class file to copy into outdir during `--build` |
| `-v, --verbose` | off | Print detailed progress for every step |

**Examples:**

```bash
# Render all templates with verbose output
python generate.py -v

# Use a different data file
python generate.py -d cv.yaml

# Render a single template only
python generate.py -t res8_template.tex.j2

# Write outputs to a custom directory
python generate.py -o build/

# Full build: render + compile PDFs (replaces the old `build` script)
python generate.py --build

# Full build with a custom .cls file and verbose output
python generate.py --build --cls myclass.cls -v

# Build a single template into a custom output directory
python generate.py -b -t resume.tex.j2 -o build/ -v
```

---

### 4. GitLab CI/CD Automation

The `.gitlab-ci.yml` pipeline handles automated builds.
It will:

1. Install Python and LaTeX dependencies
2. Run `generate.py --build`
3. Store `.pdf`, `.tex`, `.md`, and `.html` artifacts

All results appear under the **Artifacts** tab after a successful pipeline run.

---

## ⚙️ Template System

Templates live under the `templates/` directory:

| Template                  | Output Type | Description                     |
| ------------------------- | ----------- | ------------------------------- |
| `res8_template.tex.j2`    | LaTeX / PDF | Primary resume format           |
| `alt_template.tex.j2`     | LaTeX / PDF | Alternate layout                |
| `markdown_template.md.j2` | Markdown    | Simplified version for websites |
| `html_template.html.j2`   | HTML        | Clean, readable web resume      |

You can modify these Jinja2 templates or add new ones — any file ending in `.j2` will be automatically processed.

---

## 🧩 Naming Logic and Deduplication

The script automatically generates file names based on your name and template filename.

### 🔠 Slug Generation

- The generator extracts your name from `resume.yaml`:

  ```yaml
  name: David M. Crumpton
  ```

  → creates a slug: `davidcrumpton`

- That slug becomes the base name for all output files.

### 🧾 Example Naming Rules

| Template                  | Output Name              |
| ------------------------- | ------------------------ |
| `res8_template.tex.j2`    | `davidcrumpton.res8.tex` |
| `resume_template.tex.j2`  | `davidcrumpton.tex`      |
| `markdown_template.md.j2` | `davidcrumpton.md`       |
| `html_template.html.j2`   | `davidcrumpton.html`     |

If two templates would create the same file name (e.g. multiple `.tex` templates),
the generator automatically adds a disambiguating suffix:

```text
davidcrumpton.res8.tex
davidcrumpton.res8_template.tex
davidcrumpton.res8_template.1.tex
```

This ensures builds never overwrite outputs from different templates.

---

## Plain-text output

A plain-text template is included: `templates/resume.txt.j2`.

- The template centers the `name` (and an optional `title`) and left-justifies the rest.
- It supports a configurable page width via the top-level `page_width` value in `resume.yaml` (default: 80).
- Long paragraphs and bullet items are automatically wrapped to the page width using a registered `wrap` Jinja2 filter.

Example `resume.yaml` snippet to set width:

```yaml
options:
  txt:
    page_width: 72
```

The generator will produce `out/<slug>.txt` (e.g. `out/davidcrumpton.txt`). For best viewing, open the `.txt` file in a monospaced font or a terminal.

Notes:

- The `wrap` filter accepts an optional prefix used for bullets so wrapped lines align correctly (the template passes `"- "` for list items).
- If you want different headline behavior (for example a `headline` field instead of using `title`), update `resume.yaml` and the template accordingly.

---

## 🧠 How It Works Internally

1. Loads the YAML data file (default: `resume.yaml`) into memory using PyYAML.
2. Creates a `jinja2.Environment` configured for the templates directory.
3. Registers format-specific filters:
   - `escape_latex` — handles `&`, `%`, `$`, `#`, etc.
   - `escape_md` — escapes Markdown control characters.
   - `escape_html` — replaces `<`, `>`, and `&`.
   - `md_trailing_punc` — strips trailing punctuation from values.
   - `wrap` — wraps long text to a configurable column width.
4. Iterates over each template ending in `.j2` (or the single template specified with `-t`).
5. Builds a name slug and writes the rendered result into the output directory.
6. If `--build` is passed, copies the `.cls` file into the output directory and compiles every `.tex` file to PDF using `pdflatex`.

---

## 📜 License

This project is licensed under the **Apache License 2.0**.
See the [LICENSE](LICENSE) file for full details.

---

## 👤 Author

**David M. Crumpton**
LinkedIn: [linkedin.com/in/davidcrumpton](https://linkedin.com/in/davidcrumpton)

---

## 🧩 Example Extendability

To add a new format (for example, JSON or plain text):

1. Create a new file in `templates/` named `json_template.json.j2`
2. Use Jinja2 variables like `{{ name }}` and loops for `experience`
3. Run `python generate.py` — it will automatically detect and render it

---

**resumes-for-all** keeps your resume data and presentation in sync —
build once, export everywhere.