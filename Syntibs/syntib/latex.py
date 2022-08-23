import os
import subprocess
from subprocess import CalledProcessError

from data import Data as d
from data.decorators import data
from tempdir import TempDir


# Adapted and simplified from latex package


class LatexMkBuilder(object):
    """A latexmk based builder for LaTeX files.

    Uses the `latexmk
    <http://users.phys.psu.edu/~collins/software/latexmk-jcc/>`_ script to
    build latex files, which is part of some popular LaTeX distributions like
    `texlive <https://www.tug.org/texlive/>`_.

    The build process consists of copying the source file to a temporary
    directory and running latexmk on it, which will take care of reruns.
    """

    def __init__(self):
        # The path to the ``xelatex`` binary (will be looked up on ``$PATH``).
        self.xelatex = "xelatex"

    @data("source")
    def build_pdf(self, source, texinputs=[]):
        texinputs.append(
            bytes.decode(subprocess.check_output(["which", "xelatex"])).strip()
        )
        with TempDir() as tmpdir, source.temp_saved(suffix=".latex", dir=tmpdir) as tmp:

            # close temp file, so other processes can access it also on Windows
            tmp.close()

            base_fn = os.path.splitext(tmp.name)[0]
            output_fn = base_fn + ".pdf"

            args = [self.xelatex, tmp.name]

            # create environment
            newenv = os.environ.copy()
            newenv["TEXINPUTS"] = os.pathsep.join(texinputs) + os.pathsep

            try:
                subprocess.check_call(
                    args,
                    cwd=tmpdir,
                    env=newenv,
                    stdin=open(os.devnull, "r"),
                    stdout=open(os.devnull, "w"),
                    stderr=open(os.devnull, "w"),
                )
            except CalledProcessError as e:
                print(e)
                exit(1)

            return d(open(output_fn, "rb").read(), encoding=None)
