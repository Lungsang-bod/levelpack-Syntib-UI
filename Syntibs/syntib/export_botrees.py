from pathlib import Path
import re


def export_tree(tree, derived_trees, rules, out_dir, filename, format, from_roof, draw_square, font, write_all):
    """
    Exports trees to PNG, PDF, SVG, LATEX and MSHANG formats
    :param tree:
    :param derived_trees:
    :param rules:
    :param out_dir:
    :param filename:
    :param format: either of png, pdf, svg, latex and mshang
    :param from_roof:
    :param draw_square:
    :param font:
    :param write_all:
    :return:
    """
    # write rules
    Path(out_dir / f"{filename.stem}_rules.txt").write_text(rules, encoding="utf-8-sig")

    # write to chosen export format
    # PNG
    if format == "png":
        tree.build_png(
            Path(out_dir / f"{filename.stem}.png"),
            from_roof=from_roof,
            draw_square=draw_square,
            font=font,
        )
        if write_all:
            for num, v in enumerate(derived_trees):
                v.build_png(
                    Path(out_dir / f"{filename.stem}_version{num + 1}.png"),
                    from_roof=from_roof,
                    draw_square=draw_square,
                    font=font,
                )

    # PDF
    elif format == "pdf":
        tree.build_pdf(
            Path(out_dir / f"{filename.stem}.pdf"),
            from_roof=from_roof,
            draw_square=draw_square,
            font=font,
        )
        if write_all:
            for num, v in enumerate(derived_trees):
                v.build_pdf(
                    Path(out_dir / f"{filename.stem}_version{num + 1}.pdf"),
                    from_roof=from_roof,
                    draw_square=draw_square,
                    font=font,
                )

    # SVG
    elif format == "svg":
        Path(out_dir / f"{filename.stem}.svg").write_text(
            tree.build_svg(font=font), encoding="utf-8-sig"
        )
        if write_all:
            for num, v in enumerate(derived_trees):
                Path(out_dir / f"{filename.stem}_version{num + 1}.svg").write_text(
                    v.build_svg(font=font), encoding="utf-8-sig"
                )

    # LATEX
    elif format == "latex":
        Path(out_dir / f"{filename.stem}.tex").write_text(
            tree.gen_latex(from_roof=from_roof, draw_square=draw_square, font=font)
        )
        if write_all:
            for num, v in enumerate(derived_trees):
                Path(out_dir / f"{filename.stem}_version{num + 1}.tex").write_text(
                    v.gen_latex(
                        from_roof=from_roof, draw_square=draw_square, font=font
                    ),
                    encoding="utf-8-sig",
                )

    # MSHANG
    elif format == "mshang":
        def generate_mshang_link(tree):
            str_tree = re.sub(r"\s+", " ", str(tree).replace("\n", ""))
            str_tree = str_tree.replace("(", "[").replace(")", "]")
            return "http://mshang.ca/syntree/?i=" + str_tree.replace("_", " ").replace(
                " ", "%20"
            )

        mshang = generate_mshang_link(tree)
        if write_all:
            mshang += "\n\nextra trees:\n"
            mshang += "\n\n".join([generate_mshang_link(t) for t in derived_trees])
        Path(out_dir / f"{filename.stem}_mshang.txt").write_text(
            mshang, encoding="utf-8-sig"
        )

    else:
        raise SyntaxError(
            'allowed formats are: "png" "pdf" "svg", "latex" and "mshang"'
        )