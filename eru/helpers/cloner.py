# coding: utf-8

from pygit2 import clone_repository, RemoteCallbacks
from pygit2.credentials import Keypair, UserPass

from eru.config import GIT_KEY_PUB, GIT_KEY_PRI, GIT_KEY_USER, GIT_KEY_ENCRYPT
from eru.config import GIT_USERNAME, GIT_PASSWORD


def _get_credit(url):
    if (GIT_KEY_PUB and GIT_KEY_PRI and GIT_KEY_USER and url.startswith('git')):
        return Keypair(GIT_KEY_USER, GIT_KEY_PUB, GIT_KEY_PRI, GIT_KEY_ENCRYPT)
    if (GIT_USERNAME and GIT_PASSWORD and url.startswith('http')):
        return UserPass(GIT_USERNAME, GIT_PASSWORD)
    return None


def clone_code(repo_url, clone_path, revision, branch=None):
    """branch 为 None, 默认用远端的 default branch"""
    cred = _get_credit(repo_url)
    cbs = RemoteCallbacks(cred, None)
    repo = clone_repository(repo_url, clone_path,
            bare=False, checkout_branch=branch, callbacks=cbs)
    repo.checkout('HEAD')
    obj = repo.revparse_single(revision)
    repo.checkout_tree(obj.tree)
