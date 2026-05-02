#!/usr/bin/env python3
"""
generate.py — Jinja2 resume renderer with optional LaTeX build pipeline.

Usage examples
--------------
  ./generate.py                          # render all templates, data=resume.yaml, outdir=out/
  ./generate.py -v                       # same, with verbose output
  ./generate.py -d cv.yaml              # use a different data file
  ./generate.py -t resume.tex.j2        # render one specific template
  ./generate.py -o build/               # write outputs to build/
  ./generate.py -b                       # render + copy .cls + compile every .tex → PDF
  ./generate.py -b --cls myclass.cls    # use a custom .cls file when building
  ./generate.py -b -t resume.tex.j2 -v  # build one template, verbose
"""

import argparse
import os
import re
import shutil
import string
import subprocess
import sys
import textwrap

import jinja2
import yaml


# ---------------------------------------------------------------------------
# Jinja2 filters
# ---------------------------------------------------------------------------

def md_trailing_punc(value):
    """Strip trailing punctuation (used for Markdown rendering)."""
    pattern = r'[{}]*$'.format(re.escape(string.punctuation))
    return re.sub(pattern, '', value).strip()


def escape_latex(value):
    latex_special_chars = {
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
        '/':  r'{\slash}',
    }
    for char, escape in latex_special_chars.items():
        value = value.replace(char, escape)
    return value


def escape_md(value):
    md_special = ['*', '_', '`', '[', ']', '#', '+', '-', '|']
    for char in md_special:
        value = value.replace(char, f'\\{char}')
    return value


def escape_html(value):
    html_special = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}
    for char, esc in html_special.items():
        value = value.replace(char, esc)
    return value


def wrap_text(value, width=80, prefix=''):
    """Wrap text to *width* columns, preserving blank-line paragraph breaks.

    Parameters
    ----------
    value  : text to wrap
    width  : maximum line width (default 80)
    prefix : optional indent for the first line of each paragraph, e.g. '- '.
             Continuation lines are indented to the same column as *prefix*.
    """
    if value is None:
        return ''
    try:
        w = int(width)
    except Exception:
        w = 80

    text = str(value).strip()
    if not text:
        return ''

    paras = text.split('\n\n')
    wrapped_paras = []
    for p in paras:
        p = p.replace('\n', ' ').strip()
        if not p:
            wrapped_paras.append('')
            continue
        if prefix:
            subsequent = ' ' * len(prefix)
            wrapped = textwrap.fill(p, width=w, initial_indent=prefix,
                                    subsequent_indent=subsequent)
        else:
            wrapped = textwrap.fill(p, width=w)
        wrapped_paras.append(wrapped)

    return '\n\n'.join(wrapped_paras)


# ---------------------------------------------------------------------------
# Jinja2 environment factory
# ---------------------------------------------------------------------------

def make_env(template_dir: str) -> jinja2.Environment:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    env.trim_blocks   = True
    env.lstrip_blocks = True
    env.filters['escape_latex']    = escape_latex
    env.filters['escape_md']       = escape_md
    env.filters['escape_html']     = escape_html
    env.filters['md_trailing_punc'] = md_trailing_punc
    env.filters['wrap']            = wrap_text
    return env


# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

def name_slug(data: dict) -> str:
    """Return a filesystem-safe slug derived from the person's name."""
    name  = (data.get('name') or 'output').strip()
    parts = re.split(r'\s+', name)
    if len(parts) >= 2:
        return (parts[0] + parts[-1]).lower()
    return re.sub(r'[^A-Za-z0-9]+', '', name).lower() or 'output'


# ---------------------------------------------------------------------------
# Unique output-name helper
# ---------------------------------------------------------------------------

def make_unique(name: str, tpl_base: str, used: set) -> str:
    if name not in used:
        return name
    suffix_token = tpl_base.replace('.', '_')
    if '.' in name:
        head, tail = name.rsplit('.', 1)
        candidate = f"{head}.{suffix_token}.{tail}"
    else:
        candidate = f"{name}.{suffix_token}"
    i = 1
    while candidate in used:
        if '.' in name:
            head, tail = name.rsplit('.', 1)
            candidate = f"{head}.{suffix_token}.{i}.{tail}"
        else:
            candidate = f"{name}.{suffix_token}.{i}"
        i += 1
    return candidate


# ---------------------------------------------------------------------------
# Core render function
# ---------------------------------------------------------------------------

def render(template_file: str, data_file: str, output_file: str,
           template_dir: str = 'templates', verbose: bool = False) -> None:
    """Render *template_file* with *data_file* and write to *output_file*."""

    if verbose:
        print(f"  📄 Loading data   : {data_file}")
    with open(data_file) as f:
        data = yaml.safe_load(f)

    if verbose:
        print(f"  📐 Loading template: {template_file}")
    env      = make_env(template_dir)
    template = env.get_template(template_file)

    if verbose:
        print(f"  🖊️  Rendering       : {template_file} → {output_file}")
    result = template.render(**data)

    # Place output in outdir unless caller already supplied a directory path
    if not os.path.dirname(output_file):
        out_path = os.path.join("out", output_file)
    else:
        out_path = output_file

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(result)

    print(f"✅ Generated {out_path}")


# ---------------------------------------------------------------------------
# Build pipeline (mirrors the old `build` shell script)
# ---------------------------------------------------------------------------

def run_build(outdir: str, cls_file: str, verbose: bool = False) -> None:
    """Copy the .cls file and compile every .tex in *outdir* with pdflatex."""

    # 1. Copy the LaTeX class file
    if os.path.isfile(cls_file):
        dest = os.path.join(outdir, os.path.basename(cls_file))
        if verbose:
            print(f"  📋 Copying {cls_file} → {dest}")
        shutil.copy2(cls_file, dest)
        print(f"✅ Copied {cls_file} → {dest}")
    else:
        print(f"⚠️  Warning: cls file '{cls_file}' not found — skipping copy.",
              file=sys.stderr)

    # 2. Compile every .tex file found in outdir
    tex_files = sorted(
        os.path.join(outdir, f)
        for f in os.listdir(outdir)
        if f.endswith('.tex') and os.path.isfile(os.path.join(outdir, f))
    )

    if not tex_files:
        print(f"⚠️  No .tex files found in '{outdir}' — nothing to compile.",
              file=sys.stderr)
        return

    for tex in tex_files:
        if verbose:
            print(f"  🔨 Running pdflatex on {tex}")
        try:
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', outdir, tex],
                capture_output=not verbose,   # show output only in verbose mode
                text=True,
            )
            if result.returncode == 0:
                pdf = os.path.splitext(tex)[0] + '.pdf'
                print(f"✅ Compiled {tex} → {pdf}")
            else:
                print(f"❌ pdflatex failed for {tex} (exit {result.returncode})",
                      file=sys.stderr)
                if not verbose and result.stdout:
                    # Surface the tail of pdflatex output to help diagnose errors
                    tail = '\n'.join(result.stdout.splitlines()[-20:])
                    print(tail, file=sys.stderr)
        except FileNotFoundError:
            print("❌ pdflatex not found — is TeX Live / MacTeX installed?",
                  file=sys.stderr)
            sys.exit(1)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='generate.py',
        description='Render Jinja2 resume templates and (optionally) compile to PDF.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    p.add_argument(
        '-d', '--data',
        default='resume.yaml',
        metavar='FILE',
        help='YAML data file (default: resume.yaml)',
    )
    p.add_argument(
        '-t', '--template',
        default=None,
        metavar='FILE',
        help='Single template file to render (default: all *.j2 in templates/)',
    )
    p.add_argument(
        '--template-dir',
        default='templates',
        metavar='DIR',
        help='Directory containing Jinja2 templates (default: templates/)',
    )
    p.add_argument(
        '-o', '--outdir',
        default='out',
        metavar='DIR',
        help='Output directory (default: out/)',
    )
    p.add_argument(
        '-b', '--build',
        action='store_true',
        help='Run the full build pipeline: copy .cls file and compile .tex → PDF',
    )
    p.add_argument(
        '--cls',
        default='res.cls',
        metavar='FILE',
        help='LaTeX class file to copy into outdir during --build (default: res.cls)',
    )
    p.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed progress for every step',
    )

    return p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    verbose  = args.verbose
    outdir   = args.outdir
    data_file = args.data
    tpl_dir  = args.template_dir

    # ── Validate inputs ────────────────────────────────────────────────────
    if not os.path.isfile(data_file):
        print(f"❌ Data file not found: {data_file}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(tpl_dir):
        print(f"❌ Template directory not found: {tpl_dir}", file=sys.stderr)
        sys.exit(1)

    # ── Load data once to derive slug ──────────────────────────────────────
    if verbose:
        print(f"📂 Data file      : {data_file}")
        print(f"📂 Template dir   : {tpl_dir}")
        print(f"📂 Output dir     : {outdir}")

    with open(data_file) as f:
        data = yaml.safe_load(f)

    slug = name_slug(data)
    if verbose:
        print(f"🔖 Output slug    : {slug}")

    # ── Collect templates to render ────────────────────────────────────────
    if args.template:
        templates = [args.template]
        if verbose:
            print(f"🎯 Single template: {args.template}")
    else:
        templates = sorted(f for f in os.listdir(tpl_dir) if f.endswith('.j2'))
        if verbose:
            print(f"🗂️  Templates found : {templates}")

    if not templates:
        print("⚠️  No templates found — nothing to render.", file=sys.stderr)
        sys.exit(0)

    # ── Render ─────────────────────────────────────────────────────────────
    used: set[str] = set()

    for tpl in templates:
        base   = os.path.splitext(tpl)[0]          # e.g. 'res8_template.tex'
        suffix = base.replace('_template', '')      # e.g. 'res8.tex'

        if suffix.startswith('resume.'):
            ext      = suffix.split('.', 1)[1]
            out_name = f"{slug}.{ext}"
        else:
            out_name = f"{slug}.{suffix}"

        out_name = make_unique(out_name, base, used)
        used.add(out_name)

        out_path = os.path.join(outdir, out_name)

        if verbose:
            print(f"\n🔧 Template: {tpl}")

        render(tpl, data_file, out_path,
               template_dir=tpl_dir, verbose=verbose)

    # ── Optional build pipeline ────────────────────────────────────────────
    if args.build:
        if verbose:
            print(f"\n🏗️  Starting build pipeline (cls={args.cls}, outdir={outdir})")
        run_build(outdir, cls_file=args.cls, verbose=verbose)

    if verbose:
        print("\n🎉 Done.")


if __name__ == '__main__':
    main()