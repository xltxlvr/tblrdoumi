import json
import argparse
import sys
import re

def wrap_standalone(latex_code, doc_class="standalone"):
    return f"""\\documentclass{{{doc_class}}}

\\usepackage{{tabularray}}
\\usepackage{{xcolor,ninecolors}}
\\IfFileExists{{mytblrpreamble.tex}}{{\\input{{mytblrpreamble.tex}}}}{{}}
\\begin{{document}}

{latex_code}

\\end{{document}}
"""

def main():
    parser = argparse.ArgumentParser(
        description="Extract LaTeX code from JSON. Reads from stdin by default."
    )
    parser.add_argument("-i", "--input", help="Path to the .tblr file (optional)")
    parser.add_argument("-o", "--output", help="Save the output to a specific .tex file")
    parser.add_argument("-s", "--standalone", action="store_true",
                        help="Wrap output in standalone LaTeX document")
    parser.add_argument("-class", "--documentclass", default="standalone",
                        help="Document class to use (default: standalone)")
    parser.add_argument("--colspec", action="store_true",
                        help="Override colspec in latex_code using JSON 'colspec' value")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            json_content = f.read()
    else:
        json_content = sys.stdin.read()

    data = json.loads(json_content)
    latex_content = data.get("latex_code", "")

    # colspec 교체
    if args.colspec:
        colspec_value = data.get("colspec", "")
        if colspec_value and colspec_value.strip():
            latex_content = re.sub(
                r"colspec\s*=\s*\{[^}]*\}",
                f"colspec={{{colspec_value}}}",
                latex_content
            )
        else:
            print("Warning: JSON에 'colspec' 값이 없거나 비어 있음", file=sys.stderr)

    if args.standalone:
        latex_content = wrap_standalone(latex_content, args.documentclass)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(latex_content)
    else:
        print(latex_content)

if __name__ == "__main__":
    main()