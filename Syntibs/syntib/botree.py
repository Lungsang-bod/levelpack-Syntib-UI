import textwrap
import re
from collections import defaultdict
from html import escape
from pathlib import Path

from nltk import Tree
from nltk.treeprettyprinter import TreePrettyPrinter
from pdf2image import convert_from_bytes

from .latex import LatexMkBuilder


class BoTree(Tree):
    def build_svg(self, sentence=None, highlight=(), font=None):
        """
        Pretty-print this tree as .svg
        For explanation of the arguments, see the documentation for
        `nltk.treeprettyprinter.TreePrettyPrinter`.
        """
        return BoTreePrettyPrinter(self, sentence, highlight).svg(font=font)

    def gen_latex(self, from_roof=None, draw_square=False, font=None):
        qtree = self.pformat_latex_qtree()
        qtree = re.sub(r"([^a-zA-Z\[\].\s\\_]+)", r"\\bo{\1}", qtree)
        header1 = textwrap.dedent("""
                                    \\documentclass{article}
                                    \\usepackage{polyglossia}
                                    \\usepackage{fontspec} 
                                    \\usepackage{tikz-qtree}
                                    
                                    \\newfontfamily\\monlam[Path = """)

        if font:
            header2 = "/resources/]{" + font
        else:
            header2 = "/resources/]{monlam_uni_ouchan2.ttf"
        header2 += textwrap.dedent("""
                                    }
                                    \\newcommand{\\bo}[1]{\\monlam{#1}}
                                    
                                    \\begin{document}
                                    
                                    \\hoffset=-1in
                                    \\voffset=-1in
                                    \\setbox0\hbox{
                                    \\begin{tikzpicture}
                                    \\tikzset{every tree node/.style={align=center,anchor=north, text height=7}}""")
        footer = textwrap.dedent("""
                                    \\end{tikzpicture}
                                            }
                                    \\pdfpageheight=\\dimexpr\\ht0+\\dp0\\relax
                                    \\pdfpagewidth=\\wd0
                                    \\shipout\\box0
                                    
                                    
                                    \\stop""")
        square = textwrap.dedent("""
                                    \\tikzset{edge from parent/.style=
                                    {draw,
                                    edge from parent path={(\\tikzparentnode.south)
                                    -- +(0,-8pt)
                                    -| (\\tikzchildnode)}}}""")

        if from_roof:
            header2 += (
                "\\tikzset{frontier/.style={distance from root="
                + str(from_roof)
                + "pt}}\n"
            )
        if draw_square:
            header2 += square
        document = header1 + str(Path(__file__).parent) + header2 + qtree + footer
        document = document.replace("\\", "\\")
        return document

    def build_pdf(
        self, filename, texinputs=[], from_roof=None, draw_square=False, font=None
    ):
        source = self.gen_latex(from_roof=from_roof, draw_square=draw_square, font=font)
        bld_cls = lambda: LatexMkBuilder()
        builder = bld_cls()
        pdf = builder.build_pdf(source, texinputs)
        pdf.save_to(filename)

    def build_png(self, filename, from_roof=None, draw_square=False, font=None):
        source = self.gen_latex(from_roof=from_roof, draw_square=draw_square, font=font)
        bld_cls = lambda: LatexMkBuilder()
        builder = bld_cls()
        pdf = builder.build_pdf(source, [])
        png = convert_from_bytes(bytes(pdf), fmt="png")[0]
        png.save(filename)


class BoTreePrettyPrinter(TreePrettyPrinter):
    def svg(self, nodecolor="blue", leafcolor="red", funccolor="green", font=None):
        """
        :return: SVG representation of a tree.
        """
        if not font:
            font = "Noto Sans Tibetan"
        fontsize = 12
        hscale = 40
        vscale = 25
        hstart = vstart = 20
        width = max(col for _, col in self.coords.values())
        height = max(row for row, _ in self.coords.values())
        result = [
            '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
            'width="%dem" height="%dem" viewBox="%d %d %d %d">'
            % (
                width * 3,
                height * 2.5,
                -hstart,
                -vstart,
                width * hscale + 3 * hstart,
                height * vscale + 3 * vstart,
            )
        ]

        children = defaultdict(set)
        for n in self.nodes:
            if n:
                children[self.edges[n]].add(n)

        # horizontal branches from nodes to children
        for node in self.nodes:
            if not children[node]:
                continue
            y, x = self.coords[node]
            x *= hscale
            y *= vscale
            x += hstart
            y += vstart + fontsize // 2
            childx = [self.coords[c][1] for c in children[node]]
            xmin = hstart + hscale * min(childx)
            xmax = hstart + hscale * max(childx)
            result.append(
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;" '
                'points="%g,%g %g,%g" />' % (xmin, y, xmax, y)
            )
            result.append(
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;" '
                'points="%g,%g %g,%g" />' % (x, y, x, y - fontsize // 3)
            )

        # vertical branches from children to parents
        for child, parent in self.edges.items():
            y, _ = self.coords[parent]
            y *= vscale
            y += vstart + fontsize // 2
            childy, childx = self.coords[child]
            childx *= hscale
            childy *= vscale
            childx += hstart
            childy += vstart - fontsize
            result += [
                '\t<polyline style="stroke:white; stroke-width:10; fill:none;"'
                ' points="%g,%g %g,%g" />' % (childx, childy, childx, y + 5),
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;"'
                ' points="%g,%g %g,%g" />' % (childx, childy, childx, y),
            ]

        # write nodes with coordinates
        for n, (row, column) in self.coords.items():
            node = self.nodes[n]
            x = column * hscale + hstart
            y = row * vscale + vstart
            if n in self.highlight:
                color = nodecolor if isinstance(node, Tree) else leafcolor
                if isinstance(node, Tree) and node.label().startswith("-"):
                    color = funccolor
            else:
                color = "black"
            result += [
                '\t<text style="text-anchor: middle; fill: %s; '
                'font-size: %dpx; font-family: %s" x="%g" y="%g">%s</text>'
                % (
                    color,
                    fontsize,
                    font,
                    x,
                    y,
                    escape(node.label() if isinstance(node, Tree) else node),
                )
            ]

        result += ["</svg>"]
        return "\n".join(result)
