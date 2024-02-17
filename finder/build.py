
import os
#  pip install css-html-js-minify
from  css_html_js_minify.html_minifier import remove_html_comments, condense_style, condense_script, clean_unneeded_html_tags, condense_html_whitespace, unquote_html_attributes

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
HTML_FILE=os.path.join(SCRIPT_DIR, 'finder.html')
HTML_COMP_FILE=os.path.join(SCRIPT_DIR, 'finder_compresesd.html')
DATA_FILE=os.path.join(SCRIPT_DIR, 'webs', 'cock','data.h')
INGRS_FILE=os.path.join(SCRIPT_DIR, 'data.js')

ingrs = "const data = [[false, 'Vodka', 'Водка', '1'],[true, 'Pivo', 'Пиво', '9'],[false, 'Martini', 'Мартини', '9'],]; /*AAA*/"
coctails = "const coctails = [[40, 'Ерш', [0, 1]],[7, 'Водка Мартини', [0, 2]],]; /*BBB*/"

with open(INGRS_FILE, 'r', encoding='utf-8') as f:
    for r in f.readlines():
        r = r[:-1] if r.endswith('\n') else r
        if r.startswith('const data = '):
            ingrs = r
        if r.startswith('const coctails = '):
            coctails = r

# read finder.html., replace data and coctails.
html_fle_fixed = ''
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    for r in f.readlines():
        r = r.replace(
            "const data = [[false, 'Vodka', 'Водка', '1'],[true, 'Pivo', 'Пиво', '9'],[false, 'Martini', 'Мартини', '9'],];",
            ingrs
        ).replace(
            "const coctails = [[40, 'Ерш', [0, 1]],[7, 'Водка Мартини', [0, 2]],];",
            coctails
        )
        html_fle_fixed += r

# process_single_html_file(HTML_COMP_FILE, overwrite=True, comments=True) 

html_fle_compressed = remove_html_comments(html_fle_fixed) 
html_fle_compressed = condense_style(html_fle_compressed)
html_fle_compressed = condense_script(html_fle_compressed)
# html_fle_compressed = clean_unneeded_html_tags(html_fle_compressed)
html_fle_compressed = condense_html_whitespace(html_fle_compressed)
html_fle_compressed = unquote_html_attributes(html_fle_compressed)

with open(HTML_COMP_FILE, 'w', encoding='utf-8') as f:
    f.write(html_fle_compressed)

# html_fle_compressed = ''
# with open(HTML_COMP_FILE, 'r', encoding='utf-8') as f:
#     for r in f.readlines():
#         html_fle_compressed += r

# write this into data.h
LINE_LEN = 4000
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    f.write('const char* cockFinderHtml = ')
    for r in html_fle_compressed.split('\n'):
        for rs in [r[i:i+LINE_LEN] for i in range(0, len(r), LINE_LEN)]:
            rs = rs.replace(
                '"',
                '\\"'
            ).replace(
                '`',
                '\\`'
            ).replace(
                '\\\\"',
                '\\"'
            )
            rs = '"' + rs[:] + '"\n'
            f.write(rs)
        f.write('"\\n"\n')
    f.write(';')










