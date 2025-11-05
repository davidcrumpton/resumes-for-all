#!/usr/bin/env python3
import yaml, jinja2, os, re, string
import textwrap


def render(template_file, data_file, output_file):
    # print (f"📝 Rendering {template_file} with {data_file} -> {output_file}")
    with open(data_file) as f:
        data = yaml.safe_load(f)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.filters['escape_latex'] = escape_latex
    env.filters['escape_md'] = escape_md
    env.filters['escape_html'] = escape_html
    env.filters['md_trailing_punc'] = md_trailing_punc
    env.filters['wrap'] = wrap_text

    template = env.get_template(template_file)
    result = template.render(**data)

    # Write outputs into the `out/` directory unless a path is provided
    if not os.path.dirname(output_file):
        out_path = os.path.join("out", output_file)
    else:
        out_path = output_file

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(result)

    print(f"✅ Generated {out_path}")


def md_trailing_punc(value):

  # The pattern r'[{}]*$'.format(re.escape(string.punctuation))
  # matches one or more punctuation characters at the end of the string.
  # re.escape is used because string.punctuation contains characters that 
  # have special meaning in regex, like '.' and '*'.
  
  # string.punctuation includes: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
  
  pattern = r'[{}]*$'.format(re.escape(string.punctuation))
  cleaned_value = re.sub(pattern, '', value).strip()
  
  return cleaned_value

def escape_latex(value):
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
        '/' : r'{\slash}',
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
    """Wrap text to a given width preserving paragraphs.

    - value: text to wrap
    - width: desired maximum line width (int)
    - prefix: optional string to use as initial indent for each paragraph
      (useful for bullets like '- '). Subsequent lines are indented to
      the same length as the prefix.
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

    # Split into paragraphs separated by blank lines
    paras = text.split('\n\n')
    wrapped_paras = []
    for p in paras:
        p = p.replace('\n', ' ').strip()
        if not p:
            wrapped_paras.append('')
            continue
        if prefix:
            subsequent = ' ' * len(prefix)
            wrapped = textwrap.fill(p, width=w, initial_indent=prefix, subsequent_indent=subsequent)
        else:
            wrapped = textwrap.fill(p, width=w)
        wrapped_paras.append(wrapped)

    return '\n\n'.join(wrapped_paras)

if __name__ == "__main__":
    # Render every template in the templates/ directory that ends with .j2
    data_file = "resume.yaml"
    tpl_dir = "templates"

    # Load data once to build an output-name slug from the person's name
    with open(data_file) as f:
        data = yaml.safe_load(f)
    name = (data.get('name') or 'output').strip()
    parts = re.split(r"\s+", name)
    if len(parts) >= 2:
        slug = (parts[0] + parts[-1]).lower()
    else:
        slug = re.sub(r'[^A-Za-z0-9]+', '', name).lower() or 'output'

    for tpl in sorted(os.listdir(tpl_dir)):
        if not tpl.endswith('.j2'):
            continue
        base = os.path.splitext(tpl)[0]  # e.g. 'res8_template.tex'
        # remove the '_template' marker if present: 'res8_template.tex' -> 'res8.tex'
        suffix = base.replace('_template', '')

        # If the template is the general 'resume' template, use just the extension
        if suffix.startswith('resume.'):
            ext = suffix.split('.', 1)[1] if '.' in suffix else suffix
            out_name = f"{slug}.{ext}"
        else:
            out_name = f"{slug}.{suffix}"

        # Ensure we don't produce duplicate output filenames
        used = globals().get('_generated_outputs')
        if used is None:
            used = set()
            globals()['_generated_outputs'] = used

        def make_unique(name, tpl_base):
            if name not in used:
                return name
            # split final extension
            if '.' in name:
                head, tail = name.rsplit('.', 1)
                suffix_token = tpl_base.replace('.', '_')
                candidate = f"{head}.{suffix_token}.{tail}"
            else:
                suffix_token = tpl_base.replace('.', '_')
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

        out_name = make_unique(out_name, base)
        used.add(out_name)

        render(tpl, data_file, out_name)
