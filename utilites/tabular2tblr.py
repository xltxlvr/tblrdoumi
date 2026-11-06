import sys
import re
import json
import argparse
import os

def remove_comments(text):
    cleaned_lines = []
    for line in text.split('\n'):
        out_line = ""
        i = 0
        while i < len(line):
            if line[i] == '%':
                backslashes = 0
                j = i - 1
                while j >= 0 and line[j] == '\\':
                    backslashes += 1
                    j -= 1
                if backslashes % 2 == 0:
                    break
                else:
                    out_line += line[i]
            else:
                out_line += line[i]
            i += 1
        cleaned_lines.append(out_line)
    return '\n'.join(cleaned_lines)

def get_brace_content(text):
    text = text.strip()
    if not text.startswith('{'): 
        return "", text
    depth = 0
    for i, char in enumerate(text):
        if char == '{': depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[1:i].strip(), text[i+1:].strip()
    return "", text

def parse_multicolumn(cell_str):
    idx = cell_str.find(r"\multicolumn")
    if idx == -1: return cell_str, 1
    prefix = cell_str[:idx]
    remains = cell_str[idx + len(r"\multicolumn"):].strip()
    span_str, remains = get_brace_content(remains)
    col_span = int(span_str) if span_str.isdigit() else 1
    _, remains = get_brace_content(remains)
    content_str, remains = get_brace_content(remains)
    return (prefix + content_str + remains).strip(), col_span

def parse_multirow(cell_str):
    idx = cell_str.find(r"\multirow")
    if idx == -1: return cell_str, 1
    prefix = cell_str[:idx]
    remains = cell_str[idx + len(r"\multirow"):].strip()
    row_span_str, remains = get_brace_content(remains)
    row_span = int(row_span_str) if row_span_str.isdigit() else 1
    if remains.startswith('*'):
        remains = remains[1:].strip()
    else:
        _, remains = get_brace_content(remains)
    content_str, remains = get_brace_content(remains)
    return (prefix + content_str + remains).strip(), row_span

def convert_alignment_commands(text):
    text = re.sub(r'\\arraybackslash(?:\{\})?\s*', '', text)
    text = re.sub(r'\\centering\s*', r'\\SetCell{c}{} ', text)
    text = re.sub(r'\\raggedright\s*', r'\\SetCell{l}{} ', text)
    text = re.sub(r'\\raggedleft\s*', r'\\SetCell{r}{} ', text)

    text = re.sub(
        r'\\cellcolor(?:\[(.*?)\])?\{([^}]+)\}',
        lambda m: f"\\SetCell{{bg={m.group(2)}}}{{}}",
        text
    )
    return text.strip()

def convert_array_syntax_to_tblr(colspec):
    font_cmds = [
        r'\\tiny', r'\\scriptsize', r'\\footnotesize', r'\\small', r'\\normalsize',
        r'\\large', r'\\Large', r'\\LARGE', r'\\huge', r'\\Huge',
        r'\\rmfamily', r'\\sffamily', r'\\ttfamily',
        r'\\bfseries', r'\\mdseries',
        r'\\itshape', r'\\slshape', r'\\scshape', r'\\upshape'
    ]
    font_pattern = r'(' + '|'.join(font_cmds) + r')(?![a-zA-Z])'

    def extract_fonts(prefix_cmds):
        fonts_found = re.findall(font_pattern, prefix_cmds)
        if fonts_found:
            return f"font={''.join(fonts_found)}"
        return None

    pattern_pmb = r'(?:>\{([^}]*)\}\s*)?([pmb])\{([^}]+)\}'
    
    def replacer_pmb(match):
        prefix_cmds = match.group(1) or ""
        col_type = match.group(2)
        width = match.group(3)
        q_options = [width.strip()]
        if r'\centering' in prefix_cmds: q_options.append('c')
        elif r'\raggedright' in prefix_cmds: q_options.append('l')
        elif r'\raggedleft' in prefix_cmds: q_options.append('r')
        if col_type == 'm': q_options.append('m')
        elif col_type == 'b': q_options.append('b')
        color_match = re.search(r'\\columncolor(?:\[.*?\])?\{([^}]+)\}', prefix_cmds)
        if color_match: q_options.append(f"bg={color_match.group(1)}")
        font_opt = extract_fonts(prefix_cmds)
        if font_opt: q_options.append(font_opt)
        return f"Q[{','.join(q_options)}]"

    colspec = re.sub(pattern_pmb, replacer_pmb, colspec)
    pattern_clr = r'>\{([^}]*)\}\s*([clr])'
    
    def replacer_clr(match):
        prefix_cmds = match.group(1)
        col_type = match.group(2)
        q_options = []
        if r'\centering' in prefix_cmds: q_options.append('c')
        elif r'\raggedright' in prefix_cmds: q_options.append('l')
        elif r'\raggedleft' in prefix_cmds: q_options.append('r')
        else: q_options.append(col_type)
        color_match = re.search(r'\\columncolor(?:\[.*?\])?\{([^}]+)\}', prefix_cmds)
        if color_match: q_options.append(f"bg={color_match.group(1)}")
        font_opt = extract_fonts(prefix_cmds)
        if font_opt: q_options.append(font_opt)
        if len(q_options) > 0 and q_options != [col_type]:
            return f"Q[{','.join(q_options)}]"
        return col_type
        
    colspec = re.sub(pattern_clr, replacer_clr, colspec)
    colspec = re.sub(r'[@!<]\{[^}]*\}', '', colspec)
    colspec = colspec.replace('|', '')
    colspec = re.sub(r'\s+', ' ', colspec).strip()
    return colspec

def process_and_save_tblr(latex_text, output_filename, keep_lines=False):

    latex_text = remove_comments(latex_text)

    blocks = []
    search_idx = 0
    while True:
        match = re.search(r"\\begin\{tabular\}", latex_text[search_idx:])
        if not match:
            break
        
        start_idx = search_idx + match.end()
        end_match = re.search(r"\\end\{tabular\}", latex_text[start_idx:])
        
        if not end_match:
            print("Error: \\end{tabular} 가 누락된 \\begin{tabular}가 있습니다.", file=sys.stderr)
            break
            
        end_idx = start_idx + end_match.end()
        
        blocks.append(latex_text[start_idx:end_idx])
        search_idx = end_idx

    if not blocks:
        print("Error: 유효한 \\begin{tabular} 코드가 없습니다.", file=sys.stderr)
        return

    is_multiple = len(blocks) > 1
    base_name, ext = os.path.splitext(output_filename)

    for i, block_text in enumerate(blocks):
        current_output = f"{base_name}-{i+1}{ext}" if is_multiple else output_filename
        _process_single_tabular(block_text, current_output, keep_lines=keep_lines)

def _process_single_tabular(text_after_begin, output_filename, keep_lines=False):
    if text_after_begin.startswith('['):
        pos_end = text_after_begin.find(']')
        if pos_end != -1:
            text_after_begin = text_after_begin[pos_end+1:].strip()

    raw_colspec, text_after_begin = get_brace_content(text_after_begin)
    colspec_extracted = convert_array_syntax_to_tblr(raw_colspec)

    idx_end = text_after_begin.find(r"\end{tabular}")
    if idx_end == -1:
        print("Error: \\end{tabular} 를 찾을 수 없습니다.", file=sys.stderr)
        return
    body_str = text_after_begin[:idx_end].strip()

    # 괘선 정보 문자열을 모을 리스트
    lines_opts = []

    if not keep_lines:
        body_str = re.sub(r'\\hline\s*', '', body_str)
        body_str = re.sub(r'\\cline\{[^}]+\}\s*', '', body_str)
    else:
        # [수정 1] 정규식을 사용하여 hline 뒤의 공백과 줄바꿈까지 함께 치환
        # 이중 hline 먼저 치환
        body_str = re.sub(r'\\hline\s*\\hline\s*', '[[HHLINE]]', body_str)
        # 단일 hline 치환
        body_str = re.sub(r'\\hline\s*', '[[HLINE]]', body_str)
        # cline 치환
        body_str = re.sub(r'\\cline\{([^}]+)\}\s*', r'[[CLINE:\1]]', body_str)

    body_str = re.sub(r'\\(?:top|mid|bottom)rule\s*', '', body_str)
    body_str = re.sub(
        r'\\rowcolor(?:\[(.*?)\])?\{([^}]+)\}',
        lambda m: f"\\SetRow{{bg={m.group(2)}}}{{}}",
        body_str
    )

    table_data = []
    current_row, current_cell = [], []
    brace_depth, i = 0, 0
    row_index = 0

    def append_cell_to_row(cell_chars):
        raw_text = "".join(cell_chars).strip()
        if not raw_text:
            current_row.append({"text": "", "col_span": 1, "row_span": 1})
            return
        clean_text, col_span = parse_multicolumn(raw_text)
        clean_text, row_span = parse_multirow(clean_text)
        clean_text = convert_alignment_commands(clean_text)
        current_row.append({"text": clean_text, "col_span": col_span, "row_span": row_span})
        for _ in range(col_span - 1):
            current_row.append({"text": "__DUMMY__", "col_span": 0, "row_span": 0})

    while i < len(body_str):
        if body_str[i:i+2] == '\\\\':
            if brace_depth == 0:
                append_cell_to_row(current_cell)
                table_data.append(current_row)
                current_row, current_cell = [], []
                row_index += 1
                i += 2
                continue
            else:
                current_cell.append('\\\\')
                i += 2
                continue
        if body_str[i] == '&' and brace_depth == 0:
            if i > 0 and body_str[i-1] == '\\':
                current_cell.append('&')
                i += 1
                continue
            append_cell_to_row(current_cell)
            current_cell = []
            i += 1
            continue
        if body_str[i] == '{':
            brace_depth += 1
        elif body_str[i] == '}':
            brace_depth -= 1

        # 괘선 토큰 처리
        if keep_lines and body_str.startswith('[[HHLINE]]', i):
            lines_opts.append(f"hline{{{row_index+1}}} = {{1}}{{-}}{{}}, % double")
            lines_opts.append(f"hline{{{row_index+1}}} = {{2}}{{-}}{{}}, % double")
            i += len('[[HHLINE]]')
            continue
        if keep_lines and body_str.startswith('[[HLINE]]', i):
            lines_opts.append(f"hline{{{row_index+1}}} = {{solid}}")
            i += len('[[HLINE]]')
            continue
        if keep_lines and body_str.startswith('[[CLINE:', i):
            j = body_str.find(']]', i)
            rng = body_str[i+8:j]  # "m-n"
            lines_opts.append(f"hline{{{row_index+1}}} = {{{rng}}}{{solid}}")
            i = j+2
            continue

        current_cell.append(body_str[i])
        i += 1

    if current_cell or current_row:
        append_cell_to_row(current_cell)
        if current_row:
            table_data.append(current_row)

    if table_data:
        last_row = table_data[-1]
        if all(cell["text"] == "__DUMMY__" or cell["text"].strip() == "" for cell in last_row):
            table_data.pop()

    rows = len(table_data)
    cols = max([len(r) for r in table_data]) if table_data else 0
    cells_json = []
    for r in range(rows):
        row_data = []
        for c in range(cols):
            if c < len(table_data[r]):
                cell = table_data[r][c]
                text = cell["text"] if cell["text"] != "__DUMMY__" else ""
                row_span, col_span = cell["row_span"], cell["col_span"]
            else:
                text, row_span, col_span = "", 1, 1
            row_data.append({"text": text, "row_span": row_span, "col_span": col_span})
        cells_json.append(row_data)

    # [수정 2] vline 처리: 중괄호 깊이를 추적하여 p{3cm} 등의 내부 텍스트 무시
    if keep_lines:
        raw_colspec_str = raw_colspec
        col_index = 0
        i = 0
        colspec_brace_depth = 0
        
        while i < len(raw_colspec_str):
            ch = raw_colspec_str[i]
            if ch == '{':
                colspec_brace_depth += 1
            elif ch == '}':
                colspec_brace_depth -= 1
            elif colspec_brace_depth == 0:  # 중괄호 바깥일 때만 열 지정자 및 파이프 확인
                if ch in "clrmQXp":
                    col_index += 1
                elif ch == '|':
                    if i+1 < len(raw_colspec_str) and raw_colspec_str[i+1] == '|':
                        lines_opts.append(f"vline{{{col_index+1}}} = {{1}}{{-}}{{}}, % double")
                        lines_opts.append(f"vline{{{col_index+1}}} = {{2}}{{-}}{{}}, % double")
                        i += 1  # 이중 파이프 건너뛰기
                    else:
                        lines_opts.append(f"vline{{{col_index+1}}} = {{solid}}")
            i += 1

    # 생성 시 lines_opts를 extra_lines로 안전하게 주입
    latex_code = generate_latex_with_colspec(
        cells_json, rows, cols,
        colspec_str=colspec_extracted,
        mode="natural",
        lines_mode="manual" if keep_lines else "default",
        extra_lines="\n".join(lines_opts) if keep_lines else None
    ) 

    # [수정 3] 치명적인 오류를 발생시키던 latex_code.replace("}", ...) 블록 완전 삭제
    # extra_lines로 이미 전달했으므로 문자열 변조가 불필요함

    data = {
        "tblr_format_version": "3.7",
        "env_type": "tabular",
        "rows": rows,
        "cols": cols,
        "colspec": colspec_extracted,
        "cells": cells_json,
        "column_widths": [100] * cols,
        "radio_state": "natural",
        "outer_options": "",
        "inner_extra": "",
        "lines": "\n".join(lines_opts) if keep_lines else "",
        "row_format": "",
        "cell_format": "",
        "generic_option": "",
        "latex_code": latex_code
    }

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Success: '{output_filename}' 생성 완료.", file=sys.stderr)

def generate_latex_with_colspec(
    table, rows, cols,
    colspec_str=None,
    mode="natural",
    lines_mode="default",
    long_mode=False,
    rowhead=None,
    caption=None,
    label=None,
    extra_lines=None
):
    lines = []
    env_name = "longtblr" if long_mode else "tblr"

    # 환경 시작
    if long_mode:
        bracket_opts = []
        if caption:
            bracket_opts.append(f"caption = {{{caption}}},")
        if label:
            bracket_opts.append(f"label = {{{label}}},")
        if bracket_opts:
            lines.append(f"\\begin{{{env_name}}}[")
            for opt in bracket_opts:
                lines.append(f"  {opt}")
            lines.append("]{")
        else:
            lines.append(f"\\begin{{{env_name}}}{{")
    else:
        lines.append(f"\\begin{{{env_name}}}{{")

    # colspec 처리 (원래 의도대로 복구)
    if mode == "linewidth":
        final_colspec = " ".join(["X[c,m]"] * cols)
        lines.append("  width = \\linewidth,")
        lines.append(f"  colspec = {{{final_colspec}}},")
    elif mode == "natural":
        final_colspec = " ".join(["l"] * cols)
        lines.append(f"  colspec = {{{final_colspec}}},")
    elif mode == "manual":
        final_colspec = colspec_str.strip() if colspec_str else " ".join(["l"] * cols)
        lines.append(f"  colspec = {{{final_colspec}}},")

    # lines 옵션 처리 (콤마 누락 방지 및 빈 줄 정리)
    if lines_mode == "default":
        lines.append("  hlines,")
        lines.append("  vlines,")
    elif lines_mode == "book":
        lines.append("  hline{1,Z}={1pt, solid},")
        lines.append("  hline{2}={solid},")
    elif lines_mode == "manual" and extra_lines:
        for opt in extra_lines.strip().split("\n"):
            clean_opt = opt.strip()
            if clean_opt:
                # 끝에 콤마가 없다면 추가해 줌
                if not clean_opt.endswith(','):
                    clean_opt += ','
                lines.append("  " + clean_opt)

    # longtblr 옵션
    if long_mode:
        if rowhead is None:
            rowhead = 1
        lines.append(f"  rowhead = {{{rowhead}}},")

    # 여기서 딱 한 번 닫기
    lines.append("}")

    # 테이블 본문
    for r in range(rows):
        row_content = []
        for c in range(cols):
            row_content.append(table[r][c]["text"])
        lines.append("  " + " & ".join(row_content) + " \\\\")

    # 환경 종료
    lines.append(f"\\end{{{env_name}}}")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Convert LaTeX 'tabular' to '.tblr' JSON format. Reads from stdin by default."
    )
    parser.add_argument("-i", "--input", help="Input .tex file path (optional)")
    parser.add_argument("-o", "--output", help="Output .tblr file path (default: input_name.tblr or output.tblr)")
    parser.add_argument("--lines", action="store_true", help="Keep and convert hline/cline/vline information (experimental)")

    args = parser.parse_args()
    input_text = ""

    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        except FileNotFoundError:
            print(f"Error: '{args.input}' 파일이 없습니다.", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("LaTeX tabular 코드 붙여넣기 (완료 후 Enter + Ctrl+D(Mac/Linux) 또는 Ctrl+Z(Windows)): ", file=sys.stderr)
        input_text = sys.stdin.read()

    if not input_text.strip():
        print("Error: 입력 데이터가 없습니다.", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if not output_path:
        if args.input:
            output_path = os.path.splitext(args.input)[0] + ".tblr"
        else:
            output_path = "output.tblr"
    else:
        if not os.path.splitext(output_path)[1]:
            output_path += ".tblr"

    # keep_lines 옵션 전달
    process_and_save_tblr(input_text, output_path, keep_lines=args.lines)

if __name__ == "__main__":
    main()
