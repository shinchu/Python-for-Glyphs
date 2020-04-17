#! /usr/bin/env python
# coding: utf-8
# convert_to_neosnip.py
# 2020-04-15
#
import os, textwrap, re, unicodedata
from os import path
from glob import glob
from lxml import etree


def extract(file):
    doc = etree.parse(file)

    try:
        content = doc.xpath('//key[text()="content"]')[0].getnext().text
    except Exception as e:
        print(e)
        content = ''

    try:
        snippet = doc.xpath('//key[text()="tabTrigger"]')[0].getnext().text
    except Exception as e:
        print(e)
        snippet = ''

    try:
        abbr = doc.xpath('//key[text()="name"]')[0].getnext().text
    except Exception as e:
        print(e)
        abbr = ''

    return snippet, abbr, content


def format_content(snippet, content):

    # handle gsgui
    if snippet == "gsgui":
        content = re.sub(r'(.*\${[\d]+:)\${[\d]+\/.*\/.*\/g}(.*)', r'\1`substitute(Filename(), " ", "", "g")`\2', content)

    # handle clipboard
    if snippet == "clipboard":
        content = re.sub(r'\${2:', '', content)
        content = re.sub(r'(\( \$3 \))}(\))', r'\1\2', content)

    # handle plugindef
    if snippet == "plugindef":
        content = re.sub(r'(^.*)\(.*\$TM_CURRENT_LINE.*\):$', r'\1(`indent(".") ? "self" : ""`):', content, flags=(re.MULTILINE | re.DOTALL))
        content = re.sub(r'(.*)\${[\d]+\/.*\/\\t\\t\/}try:$', r'\1\n\ttry:', content, flags=(re.MULTILINE | re.DOTALL))
        content = re.sub(r'\\n', r'', content)

    # handle multiline placeholder
    if re.match(r'^.*\${[\d]+:[^}]*$\n', content, flags=(re.MULTILINE | re.DOTALL)):
        formatted_content = ""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'^.*\${[\d]+:[^}]*$', line):
                try:
                    next_line = lines[i+1]
                except:
                    next_line = ''
                try:
                    next_next_line = lines[i+2]
                except:
                    next_next_line = ''

                if re.match(r'^[^{]*}.*$', next_line):
                    line = re.sub(r'(^.*\${[\d]+:[^}]*$)', r'\1', line)
                    capture_next_line = re.match(r'(^[^{]*}).*$', next_line).groups()[0]
                    line += capture_next_line
                    next_line = re.sub(r'^[^{]*}(.*$)', r'\1', next_line)
                    lines[i+1] = next_line
                elif re.match(r'^\s*$', next_line) and re.match(r'^[^{]*}.*$', next_next_line):
                    line = re.sub(r'(^.*\${[\d]+:[^}]*$)', r'\1', line)
                    capture_next_next_line = re.match(r'(^[^{]*}).*$', next_next_line).groups()[0]
                    line += capture_next_next_line
                    next_next_line = re.sub(r'^[^{]*}(.*$)', r'\1', next_next_line)
                    lines[i+2] = next_next_line
                else:
                    line = re.sub(r'(^.*\${[\d]+:[^}]*$)', r'\1}', line)

            line = re.sub(r'^[^{]*}(.*$)', r'\1', line)
            line += '\n'
            formatted_content += line

        content = formatted_content

    formatted_content = ""
    for line in content.split('\n'):
        # handle $0
        line = line.replace('$0', '${0}')
        # handle $TM_FILENAME
        line = re.sub(r'\$TM_FILENAME', r'`Filename()`', line)
        # handle choice (choice is not implemented in either neosnippet or snipmate)
        line = re.sub(r'(.*\${[\d]+)(\|.*\|}.*)', r'\1:\2', line)
        # handle substitution (dynamic substitution is not implemented in either neosnippet or snipmate)
        line = re.sub(r'\${[\d]+\/.*\/(.*)\/}(\${.*})\${[\d]+\/.*\/(.*)\/}', r'\1\2\3', line)
        # handle indent
        line = re.sub(r'(^[\s]*)(\${\d+:)(\t+)(.*)', r'\1\3\2\4', line)
        if len(line) > 0:
            line = '\t' + line
        # handle empty line
        line = re.sub(r'^\s*$', r'', line)

        line = line + '\n'
        formatted_content += line

    return formatted_content


def main():
    mate_dir = path.join(path.dirname(os.getcwd()), 'TextMate/Python for Glyphs.tmbundle/Snippets')
    vim_dir = path.join(path.dirname(os.getcwd()), 'Vim/snippets')

    template = textwrap.dedent("""
        snippet\t{}
        abbr\t{}
        options\tindent
        {}
    """)

    neosnip = path.join(vim_dir, 'python.snip')
    try:
        open(neosnip, 'w').close()
    except Exception as e:
        import traceback
        print(e)
        print(traceback.format_exc())

    tmsnips = glob(path.join(mate_dir, '*.tmSnippet'))

    snippets = []
    for f in tmsnips:
        snippet, abbr, content = extract(f)

        # for duplicated snippet name
        if snippet  in snippets:
            abbr_formatted = '_'.join([re.sub(r'(\W)', lambda w: unicodedata.name(w.group()), word).lower() for word in abbr.split()[1:]])
            snippet += '_' + abbr_formatted

        snippets.append(snippet)

        content = format_content(snippet, content)

        with open(neosnip, 'a') as f:
            f.write(template.format(snippet, abbr, content))


if __name__ == "__main__":
    main()