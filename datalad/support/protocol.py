# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" Protocolling  command calls.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
from os import linesep
import logging
import time

lgr = logging.getLogger('datalad.protocol')


class ProtocolInterface:
    """Interface class for protocols used by the Runner.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self._sections = [{}]
        self._title = ''

    def __iter__(self):
        return self._sections.__iter__()

    def __getitem__(self, item):
        return self._sections.__getitem__(item)

    def __str__(self):
        protocol_str = self._title
        for section in self._sections:
            protocol_str += linesep
            for key in section.keys():
                protocol_str += "%s: %s" % (key, section[key]) + linesep

        return protocol_str

    @abstractmethod
    def start_section(self, cmd):
        """Starts a new section of the protocol.

        To be used with a corresponding call of end_section().

        Parameters:
        -----------
        cmd: list
         The actual command and its options/arguments as a list

        Returns:
        --------
        int
          An id of the started section to be used as argument of the
          corresponding call of end_section().
        """
        raise NotImplementedError

    @abstractmethod
    def end_section(self, id_, exception):
        """Ends the section `id`.

        This ends the section defined by `id` as returned by start_section().

        Parameters:
        -----------
        id: int
        exception: Exception
          The exception raised by the command if any or None otherwise.

        Raises:
        -------
        IndexError
          in case `id` is invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def add_section(self, cmd, exception):
        """Adds a section to the protocol.

        This is an alternative to the use of start_section() and end_section().

        Parameters:
        -----------
        cmd: list
          The actual command and its options/arguments as a list
        exception: Exception
          The exception raised by the command if any or None otherwise.
        """
        raise NotImplementedError

    @abstractproperty
    def records_ext_commands(self):
        """Indicates whether or not the protocol is supposed to include
        external command calls.

        Returns:
        --------
        bool
        """
        raise NotImplementedError

    @abstractproperty
    def records_callables(self):
        """Indicates whether or not the protocol is supposed to include
        calls of python callables.

        Returns:
        --------
        bool
        """
        raise NotImplementedError

    @abstractproperty
    def do_execute_ext_commands(self):
        """Indicates whether or not the called commands are
        supposed to actually be executed.

        Returns:
        --------
        bool
        """
        raise NotImplementedError

    @abstractproperty
    def do_execute_callables(self):
        """Indicates whether or not the callables are supposed to actually
        be executed.

        Returns:
        --------
        bool
        """
        raise NotImplementedError

    def write_to_file(self, file_):
        """Writes the protocol to file.

        Parameters:
        -----------
        file_: str
          path of the file, the protocol is written to.
        """

        with open(file_, 'w') as f:
            f.write(self.__str__())


class NullProtocol(ProtocolInterface):
    """No protocolling is done at all.

    Records nothing and all calls are executed.
    This provides the default value for the Runner.
    """

    def __init__(self):
        super(NullProtocol, self).__init__()
        self._title = "No protocol available." + linesep
        self._sections[0] = {'NullProtocol': None}

    def start_section(self, cmd):
        return 0

    def end_section(self, id_, exception):
        pass

    def add_section(self, cmd, exception):
        pass

    @property
    def records_ext_commands(self):
        return False

    @property
    def records_callables(self):
        return False

    @property
    def do_execute_ext_commands(self):
        return True

    @property
    def do_execute_callables(self):
        return True


class DryRunProtocol(ProtocolInterface):
    """Protocol for dry runs.
    """
    def __init__(self):
        super(DryRunProtocol, self).__init__()
        self._title = "Dry run protocol:" + linesep

    def start_section(self, cmd):
        id_ = len(self._sections)
        self._sections.append({'command': cmd})
        return id_

    def end_section(self, id_, exception):
        pass

    def add_section(self, cmd, exception):
        self.start_section(cmd)

    @property
    def records_callables(self):
        return True

    @property
    def records_ext_commands(self):
        return True

    @property
    def do_execute_callables(self):
        return False

    @property
    def do_execute_ext_commands(self):
        return False


class DryRunExternalsProtocol(DryRunProtocol):
    """Protocol for dry runs of external commands only.
    """
    def __init__(self):
        super(DryRunExternalsProtocol, self).__init__()

    @property
    def records_callables(self):
        return False

    @property
    def do_execute_callables(self):
        return True


class ExecutionTimeProtocol(ProtocolInterface):
    """Protocol to record execution times of callables as well as of external
    commands.
    """

    def __init__(self):
        super(ExecutionTimeProtocol, self).__init__()
        self._title = "Execution time protocol:" + linesep

    def start_section(self, cmd):
        t_start = time.time()
        id_ = len(self._sections)
        self._sections.append({'command': cmd, 'start': t_start})
        return id_

    def end_section(self, id_, exception):
        t_end = time.time()
        self._sections[id_]['end'] = t_end
        self._sections[id_]['duration'] = t_end - self._sections[id_]['start']
        self._sections[id_]['exception'] = exception

    def add_section(self, cmd, exception):
        self._sections.append({'command': cmd, 'start': None, 'end': None,
                               'duration': None, 'exception': exception})

    @property
    def records_ext_commands(self):
        return True

    @property
    def records_callables(self):
        return True

    @property
    def do_execute_ext_commands(self):
        return True

    @property
    def do_execute_callables(self):
        return True


class ExecutionTimeExternalsProtocol(ExecutionTimeProtocol):
    """Protocol to record execution time of external commands only.
    """

    @property
    def records_callables(self):
        return False