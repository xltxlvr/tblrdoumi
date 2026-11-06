#!/usr/bin/env python3
# version 2026-04-01, GUI
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox

import sys
import argparse
import argparse
import json
# import re
from openpyxl import load_workbook

def save_tex(filename, latex_code):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(latex_code)

def import_excel_with_merge(file_path):
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active

    rows, cols = ws.max_row, ws.max_column
    table = [[{} for _ in range(cols)] for _ in range(rows)]

    for r_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=rows, min_col=1, max_col=cols)):
        for c_idx, cell in enumerate(row):
            value = cell.value
            
            if value is not None:
                # 1. 값이 숫자(int, float)인 경우
                if isinstance(value, (int, float)):
                    # float이면서 소수점 아래 값이 0인 경우 (예: 3.0 -> 3) 정수로 변환
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    # 숫자는 중괄호 없이 문자열로만 변환
                    formatted_text = str(value)
                
                # 2. 값이 문자열 등 그 외의 타입인 경우
                else:
                    text_content = str(value).replace('\n', r' \\ ')
                    formatted_text = f"{{{text_content}}}"
            else:
                formatted_text = "{}"
            
            table[r_idx][c_idx] = {
                "text": formatted_text,
                "row_span": 1,
                "col_span": 1,
                "is_merged_child": False
            }

    # 병합된 셀 정보 업데이트
    for merged_range in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = merged_range.bounds
        row_span = max_row - min_row + 1
        col_span = max_col - min_col + 1
        
        start_r, start_c = min_row - 1, min_col - 1
        
        table[start_r][start_c]["row_span"] = row_span
        table[start_r][start_c]["col_span"] = col_span
        
        for dr in range(row_span):
            for dc in range(col_span):
                if dr == 0 and dc == 0:
                    continue
                
                target_r = start_r + dr
                target_c = start_c + dc
                
                table[target_r][target_c]["text"] = ""
                table[target_r][target_c]["is_merged_child"] = True

    wb.close()
    
    return table, rows, cols

def generate_latex_with_colspec(
    table, rows, cols,
    colspec_str=None,
    mode="natural",
    lines_mode="default",
    long_mode=False,
    rowhead=None,
    caption=None,
    label=None
):
    lines = []
    env_name = "longtblr" if long_mode else "tblr"

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

    if lines_mode == "default":
        lines.append("  hlines,")
        lines.append("  vlines,")
    elif lines_mode == "book":
        lines.append("  hline{1,Z}={1pt, solid},")
        lines.append("  hline{2}={solid},")

    if long_mode:
        if rowhead is None:
            rowhead = 1
        lines.append(f"  rowhead = {{{rowhead}}},")

    lines.append("}")

    for r in range(rows):
        row_content = []
        for c in range(cols):
            row_content.append(table[r][c]["text"])
        lines.append("  " + " & ".join(row_content) + " \\\\")

    lines.append(f"\\end{{{env_name}}}")
    return "\n".join(lines)

def save_table(filename, table, rows, cols, latex_code, colspec, mode, long_mode, caption=None, label=None, rowhead=None):
    data = {
        "rows": rows,
        "cols": cols,
        "colspec": colspec,
        "latex_code": latex_code,
        "cells": table,
        "radio_state": mode
    }
    if long_mode:
        data["env_type"] = "longtblr"
        outer_parts = []
        if caption:
            outer_parts.append(f"caption={{{caption}}}")
        if label:
            outer_parts.append(f"label={{{label}}}")
        if outer_parts:
            data["outer_options"] = "\n".join(outer_parts)
        if rowhead is not None:
            data["inner_extra"] = f"rowhead = {rowhead}"

    if not filename.endswith(".tblr"):
        filename = filename.rsplit(".", 1)[0] + ".tblr"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_gui():
    root = tk.Tk()
    root.title("Excel2tblr Converter")
    root.geometry("410x390")

    # --- UI Layout Helpers ---
    padding = {'padx': 5, 'pady': 5}

    # Input file
    tk.Label(root, text="Input Excel file").grid(row=0, column=0, sticky="w", **padding)
    input_var = tk.StringVar()
    tk.Entry(root, textvariable=input_var, width=30).grid(row=0, column=1, **padding)
    tk.Button(root, text="Browse", command=lambda: input_var.set(
        filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    )).grid(row=0, column=2, **padding)

    # Output file
    tk.Label(root, text="Output JSON (.tblr)").grid(row=1, column=0, sticky="w", **padding)
    output_var = tk.StringVar()
    tk.Entry(root, textvariable=output_var, width=30).grid(row=1, column=1, **padding)
    tk.Button(root, text="Save As", command=lambda: output_var.set(
        filedialog.asksaveasfilename(defaultextension=".tblr", 
                                     filetypes=[("tblr files", "*.tblr"), ("All Files", "*.*")])
    )).grid(row=1, column=2, **padding)

    # Tex option
    tex_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Generate TeX", variable=tex_var).grid(row=2, column=0, sticky="w", **padding)
    tex_file_var = tk.StringVar()
    tk.Entry(root, textvariable=tex_file_var, width=30).grid(row=2, column=1, **padding)
    tk.Button(root, text="Browse", command=lambda: tex_file_var.set(
        filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("TeX files", "*.tex")])
    )).grid(row=2, column=2, **padding)

    # colspec, mode, lines
    tk.Label(root, text="Colspec").grid(row=3, column=0, sticky="w", **padding)
    colspec_var = tk.StringVar()
    tk.Entry(root, textvariable=colspec_var, width=30).grid(row=3, column=1, **padding)

    tk.Label(root, text="Mode").grid(row=4, column=0, sticky="w", **padding)
    mode_var = tk.StringVar(value="natural")
    mode_frame = tk.Frame(root)
    mode_frame.grid(row=4, column=1, columnspan=2, sticky="w")
    for m in ["natural", "linewidth", "manual"]:
        tk.Radiobutton(mode_frame, text=m, variable=mode_var, value=m).pack(side="left")

    tk.Label(root, text="Lines").grid(row=5, column=0, sticky="w", **padding)
    lines_var = tk.StringVar(value="default")
    lines_frame = tk.Frame(root)
    lines_frame.grid(row=5, column=1, columnspan=2, sticky="w")
    for l in ["default", "book"]:
        tk.Radiobutton(lines_frame, text=l, variable=lines_var, value=l).pack(side="left")

    # Long option
    long_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Use longtblr", variable=long_var).grid(row=6, column=0, sticky="w", **padding)

    tk.Label(root, text="Rowhead").grid(row=7, column=0, sticky="w", **padding)
    rowhead_var = tk.StringVar()
    tk.Entry(root, textvariable=rowhead_var, width=30).grid(row=7, column=1, **padding)
    
    tk.Label(root, text="Caption").grid(row=8, column=0, sticky="w", **padding)
    caption_var = tk.StringVar()
    tk.Entry(root, textvariable=caption_var, width=30).grid(row=8, column=1, **padding)
    
    tk.Label(root, text="Label").grid(row=9, column=0, sticky="w", **padding)
    label_var = tk.StringVar()
    tk.Entry(root, textvariable=label_var, width=30).grid(row=9, column=1, **padding)

    def run_conversion():
        # 1. 입력값 검증
        if not input_var.get():
            messagebox.showwarning("Warning", "Please select an input Excel file.")
            return

        # 2. 출력 파일명 기본값 설정 (요청 사항)
        target_output = output_var.get() if output_var.get().strip() else "output.tblr"
        
        # 3. 데이터 변환 로직
        try:
            # Rowhead 정수 변환 예외 처리
            try:
                rowhead_val = int(rowhead_var.get()) if rowhead_var.get().strip() else None
            except ValueError:
                messagebox.showerror("Error", "Rowhead must be a number.")
                return

            table, rows, cols = import_excel_with_merge(input_var.get())
            
            latex_code = generate_latex_with_colspec(
                table, rows, cols,
                colspec_str=colspec_var.get(),
                mode=mode_var.get(),
                lines_mode=lines_var.get(),
                long_mode=long_var.get(),
                rowhead=rowhead_val,
                caption=caption_var.get() if long_var.get() else None,
                label=label_var.get() if long_var.get() else None
            )

            # 파일 저장 (설정된 target_output 사용)
            save_table(target_output, table, rows, cols, latex_code,
                       colspec_var.get(), mode_var.get(), long_var.get(),
                       caption=caption_var.get(), label=label_var.get(),
                       rowhead=rowhead_val)

            # TeX 파일 저장 로직 (TeX 생성 체크 시 경로가 없으면 기본값 설정)
            if tex_var.get():
                target_tex = tex_file_var.get() if tex_file_var.get().strip() else "output.tex"
                save_tex(target_tex, latex_code)

            messagebox.showinfo("Success", f"Conversion completed!\nSaved to: {target_output}")
            # root.quit() # 바로 종료하고 싶지 않다면 주석 처리 혹은 유지
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # 실행 버튼 디자인 강조
    tk.Button(root, text="Convert Now", command=run_conversion, 
              bg="#4CAF50", fg="white", width=20).grid(row=10, column=0, columnspan=3, pady=20)

    root.mainloop()

def main():
    # 1. 인자가 아무것도 없는 경우 바로 GUI 실행
    if len(sys.argv) == 1:
        run_gui()
        return

    # 2. 인자가 있는 경우 CLI 파서 설정
    parser = argparse.ArgumentParser(description="Convert Excel to LaTeX tblr/longtblr")
    
    # 필수 인자 및 옵션들
    parser.add_argument("excel", help="Input Excel file (.xlsx)")
    parser.add_argument("-o", "--output", help="Output JSON(.tblr) file", default="output.json")
    parser.add_argument("--tex", help="Output TeX file")
    parser.add_argument("--colspec", help="Manual colspec string")
    parser.add_argument("--mode", choices=["natural", "linewidth", "manual"], default="natural")
    parser.add_argument("--lines", choices=["default", "book"], default="default")

    # longtblr 관련 옵션
    parser.add_argument("--long", action="store_true", help="Use longtblr environment")
    parser.add_argument("--rowhead", type=int, help="Number of header rows (only with --long)")
    parser.add_argument("--caption", help="Caption text (only with --long)")
    parser.add_argument("--label", help="Label text (only with --long)")

    # 3. 파싱 실행
    args = parser.parse_args()

    # 4. 로직 수행
    table, rows, cols = import_excel_with_merge(args.excel)

    latex_code = generate_latex_with_colspec(
        table, rows, cols,
        colspec_str=args.colspec,
        mode=args.mode,
        lines_mode=args.lines,
        long_mode=args.long,
        rowhead=args.rowhead if args.long else None,
        caption=args.caption if args.long else None,
        label=args.label if args.long else None
    )

    save_table(
        args.output, table, rows, cols, latex_code, args.colspec, args.mode,
        args.long, 
        caption=args.caption if args.long else None,
        label=args.label if args.long else None,
        rowhead=args.rowhead if args.long else None
    )

    if args.tex:
        save_tex(args.tex, latex_code)

if __name__ == "__main__":
    main()
