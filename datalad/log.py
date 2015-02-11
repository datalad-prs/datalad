# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
"""
 COPYRIGHT: Yaroslav Halchenko 2013

 LICENSE: MIT

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
"""

__copyright__ = 'Copyright (c) 2013 Yaroslav Halchenko'
__license__ = 'MIT'

import logging, os, sys

__all__ = ['is_interactive', 'ColorFormatter', 'log']

def is_interactive():
    """Return True if all in/outs are tty"""
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()

# Recipe from http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
# by Brandon Thomson
# Adjusted for automagic determination either coloring is needed and
# prefixing of multiline log lines
class ColorFormatter(logging.Formatter):

    FORMAT = ("$BOLD%(asctime)-15s$RESET [%(levelname)s] "
              "%(message)s "
              "($BOLD%(filename)s$RESET:%(lineno)d)")

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    COLORS = {
      'WARNING': YELLOW,
      'INFO': WHITE,
      'DEBUG': BLUE,
      'CRITICAL': YELLOW,
      'ERROR': RED
    }

    def __init__(self, use_color=None):
        if use_color is None:
            # if 'auto' - use color only if all streams are tty
            use_color = is_interactive()
        msg = self.formatter_msg(self.FORMAT, use_color)
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def formatter_msg(self, fmt, use_color=False):
        if use_color:
            fmt = fmt.replace("$RESET", self.RESET_SEQ).replace("$BOLD", self.BOLD_SEQ)
        else:
            fmt = fmt.replace("$RESET", "").replace("$BOLD", "")
        return fmt

    def format(self, record):
        if record.msg.startswith('| '):
            # If we already log smth which supposed to go without formatting, like
            # output for running a command, just return the message and be done
            return record.msg

        levelname = record.levelname
        if self.use_color and levelname in self.COLORS:
            fore_color = 30 + self.COLORS[levelname]
            levelname_color = self.COLOR_SEQ % fore_color + "%-7s" % levelname + self.RESET_SEQ
            record.levelname = levelname_color
        record.msg = record.msg.replace("\n", "\n| ")

        return logging.Formatter.format(self, record)


def set_level(level=None, default='WARNING', lgr=None, name='datalad'):
    """Helper to set loglevel for an arbitrary logger

    By default operates for 'datalad'.
    TODO: deduce name from upper module name so it could be reused without changes
    """
    if level is None:
        # see if nothing in the environment
        level = os.environ.get(name.upper() + '_LOGLEVEL', None)
    if level is None:
        level = default

    try:
        # it might be a string which still represents an int
        log_level = int(level)
    except ValueError:
        # or a string which corresponds to a constant;)
        log_level = getattr(logging, level.upper())

    if lgr is None:
        lgr = logging.getLogger(name)
    lgr.setLevel(log_level)


def _init_datalad_logger():
    # By default mimic previously talkative behavior
    lgr = logging.getLogger('datalad')
    log_handler = logging.StreamHandler(sys.stdout)

    # But now improve with colors and useful information such as time
    log_handler.setFormatter(ColorFormatter())
    #logging.Formatter('%(asctime)-15s %(levelname)-6s %(message)s'))
    lgr.addHandler(log_handler)
    return lgr

lgr = _init_datalad_logger()
set_level(lgr=lgr)                           # will set the default
