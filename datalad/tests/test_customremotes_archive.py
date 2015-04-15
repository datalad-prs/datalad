# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Tests for customremotes archives providing dl+archive URLs handling"""

import shlex
from os.path import realpath, pardir, join as opj, dirname, pathsep
from ..customremotes.base import AnnexExchangeProtocol
from ..customremotes.archive import AnnexArchiveCustomRemote
from ..cmd import Runner
from ..support.handle import Handle

from .utils import *


def get_bindir_PATH():
    # we will need to adjust PATH
    bindir = realpath(opj(dirname(__file__), pardir, pardir, 'bin'))
    PATH = os.environ['PATH']
    if bindir not in PATH:
        PATH = '%s%s%s' % (bindir, pathsep, PATH)
        #lgr.debug("Adjusted PATH to become {}".format(os.environ['PATH']))
    return PATH

# both files will have the same content
#fn_inarchive = 'test.dat'
#fn_extracted = 'test2.dat'
fn_inarchive = get_most_obscure_supported_name()
fn_extracted = fn_inarchive.replace('a', 'z')
# TODO -- obscure one for the tarball itself

# TODO: with_tree ATM for archives creates this nested top directory
# matching archive name, so it will be a/d/test.dat ... we don't want that probably
@with_tree(
    tree=(('a.tar.gz', (('d', ((fn_inarchive, '123'),)),)),
          (fn_extracted, '123')
         ))
@with_tempfile()
def test_basic_scenario(d, d2):
    # We could just propagate current environ I guess to versatile our testing
    env = os.environ.copy()
    env.update({'PATH': get_bindir_PATH(),
                'DATALAD_LOGTARGET': 'stderr'})
    if os.environ.get('DATALAD_LOGLEVEL'):
        env['DATALAD_LOGLEVEL'] = os.environ.get('DATALAD_LOGLEVEL')


    if os.environ.get('DATALAD_PROTOCOL_REMOTE'):
        protocol = AnnexExchangeProtocol(d, 'dl+archive:')
    else:
        protocol = None

    r = Runner(cwd=d, env=env, protocol=protocol)

    handle = Handle(d, runner=r)
    handle.annex_initremote('annexed-archives',
                            ['encryption=none', 'type=external', 'externaltype=dl+archive'])
    # We want two maximally obscure names, which are also different
    assert(fn_extracted != fn_inarchive)
    handle.add_to_annex('a.tar.gz', "Added tarball")
    handle.add_to_annex(fn_extracted, "Added the load file")

    # Operations with archive remote URL
    file_url = AnnexArchiveCustomRemote(path=d).get_file_url(
        archive_file='a.tar.gz', file='a/d/'+fn_inarchive)

    handle.annex_addurl_to_file(fn_extracted, file_url, ['--relaxed'])
    handle.annex_drop(fn_extracted)

    list_of_remotes = handle.annex_whereis(fn_extracted)
    in_('[annexed-archives]', list_of_remotes[fn_extracted])

    ok_broken_symlink(opj(d, fn_extracted))
    handle.get(fn_extracted)
    in_((fn_extracted, True), handle.file_has_content(fn_extracted))
    #ok_(exists(readlink(opj(d, fn_extracted))))

    handle.annex_rmurl(fn_extracted, file_url)
    with swallow_logs() as cm:
        assert_raises(RuntimeError, handle.annex_drop, fn_extracted) # no copies
        in_("git-annex: drop: 1 failed", cm.out)

    handle.annex_addurl_to_file(fn_extracted, file_url)
    handle.annex_drop(fn_extracted)
    handle.get(fn_extracted)
    handle.annex_drop(fn_extracted) # so we don't get from this one in next part

    # Let's create a clone and verify chain of getting file by getting the tarball
    cloned_handle = Handle(d2, d, runner=Runner(cwd=d2, env=env, protocol=protocol))
    # TODO: provide clone-method in GitRepo: cloned_handle = handle.getClone(d2) or sth.
    # we would still need to enable manually atm that special remote for archives
    cloned_handle.annex_enableremote('annexed-archives')


    ok_broken_symlink(opj(d2, 'a.tar.gz'))
    ok_broken_symlink(opj(d2, fn_extracted))
    cloned_handle.get(fn_extracted)
    ok_good_symlink(opj(d2, fn_extracted))
    # as a result it would also fetch tarball
    ok_good_symlink(opj(d2, 'a.tar.gz'))

    # TODO: dropurl, addurl without --relaxed, addurl to non-existing file