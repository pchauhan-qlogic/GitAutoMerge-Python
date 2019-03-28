import synthtool
from synthtool import shell

BRANCH1 = "branch3"
MASTER = "master"


def check_status(branch=BRANCH1):
    pass

def get_branch_diff(currentBranch, compBranch):
    return shell.run(['git', 'diff', '--name-only', currentBranch + '..' + compBranch])

def checkout_branch(branch = MASTER):
    return shell.run(["git", "checkout", branch])

def pull_latest_changes(branch = MASTER):
    return shell.run(["git", "pull", "origin", branch])

def fetch_all_branches():
    return shell.run(["git", "fetch", "--all"])

def open_pr(from_branch=BRANCH1, to_branch=MASTER):
    fetch_all_branches()
    checkout_branch(to_branch)
    pull_latest_changes(to_branch)
    checkout_branch(from_branch)
    pull_latest_changes(from_branch)
    diff_in_branch = get_branch_diff(from_branch, to_branch)
    if diff_in_branch.stdout:
        return shell.run(["hub", "pull-request", "-b", to_branch, "-m" , "pull request msg"])
    return

