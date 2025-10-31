# resumes-for-all

Generate resumes in multiple formats — **LaTeX**, **Markdown**, and **HTML** — from a single YAML source using **Jinja2 templates**.

This project automates resume generation locally and through **GitLab CI/CD** but it can be adapted for GitHub, too.
Your personal data lives in one file (`resume.yaml`), and `generate.py` renders every template in the `templates/` directory into a clean, named output file.

---

## 🧰 Features

- **Single source of truth:** All resume content in `resume.yaml`.
- **Multi-format output:** `.pdf`, `.tex`, `.md`, and `.html` from Jinja2 templates.
- **Auto naming & deduplication:** Generates consistent file names automatically.
- **Automation-ready:** Works locally and through GitLab CI/CD.
- **Extensible templates:** Add more formats (DOCX, JSON, etc.) easily.

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

All generated files are written to an `out/` directory for convenience.

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

To produce PDFs:

```bash
# replace my name with yours
cp res.cls out/
pdflatex out/davidcrumpton.res8.tex
pdflatex out/davidcrumpton.tex
# OR to build all including PDFs in out/ folder
./build
```

---

### 3. GitLab CI/CD Automation

The `.gitlab-ci.yml` pipeline handles automated builds.
It will:

1. Install Python and LaTeX dependencies
2. Run `generate.py`
3. Compile all `.tex` files into PDFs
4. Store `.pdf`, `.tex`, `.md`, and `.html` artifacts

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

  → creates a slug:
  `davidcrumpton`

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

## 🧠 How It Works Internally

1. Loads `resume.yaml` into memory using PyYAML.
2. Creates a `jinja2.Environment` configured for `templates/`.
3. Registers format-specific filters:

   - `escape_latex` — handles `&`, `%`, `$`, `#`, etc.
   - `escape_md` — escapes Markdown control characters.
   - `escape_html` — replaces `<`, `>`, and `&`.
4. Iterates over each template ending in `.j2`.
5. Builds a name slug and writes the rendered result into `out/`.

---

## 📜 License

This project is licensed under the **Apache License 2.0**.
See the [LICENSE](LICENSE) file for full details.

---

## 👤 Author

**David M. Crumpton**
LinkedIn: [linkedin.com/in/davidcrumpton](https://linkedin.com/in/davidcrumpton)

---

### 🧩 Example Extendability

To add a new format (for example, JSON or plain text):

1. Create a new file in `templates/` named `json_template.json.j2`
2. Use Jinja2 variables like `{{ name }}` and loops for `experience`
3. Run `python generate.py` — it will automatically detect and render it

---

**resumes-for-all** keeps your resume data and presentation in sync —
build once, export everywhere.
