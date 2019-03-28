import os
import re, time

import requests
from synthtool import shell

OWNER = "pmakani"
GITHUB = "https://github.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
is_cloned = os.path.isdir(os.path.join(BASE_DIR, ".git"))


class GitAutoMergeFork(object):
    def __init__(self, user_name):
        self.username = user_name
        self.repo = "google-cloud-java"
        self.private_repo = self.repo + "-private"
        # self.private_repo = "google-cloud-java" + "-private"

        self.repo1 = "{}/{}/{}".format(GITHUB, OWNER, self.repo)
        self.fork1 = "{}/{}/{}".format(GITHUB, self.username, self.repo)
        self.repo1_remote_name = "repo1"
        self.fork1_remote_name = "fork1"

        self.repo2 = "{}/{}/{}".format(GITHUB, OWNER, self.private_repo)
        self.fork2 = "{}/{}/{}".format(GITHUB, self.username, self.private_repo)
        self.repo2_remote_name = "repo2"
        self.fork2_remote_name = "fork2"

    def add_n_fetch_remote_repo(self):
        if is_cloned is False:
            shell.run(["git", "init"])
            # shell.run(["git", "clone", self.fork1])
        # if not self.check_repo_exist("origin"):
        #     shell.run(["git", "clone", self.fork1])
        repo_list = (
            (self.repo1_remote_name, self.repo1),
            (self.repo2_remote_name, self.repo2),
            (self.fork1_remote_name, self.fork1),
            (self.fork2_remote_name, self.fork2)
        )
        for repo_name, url in repo_list:
            if self.is_repo_exist_on_git(url):
                self.add_remote_url(repo_name, url)
                shell.run(["git", "fetch", repo_name])
            else:
                print("{} url have not repo exist".format(url))
                sys.exit()

        # self.add_remote_url(self.repo1_remote_name, self.repo1)
        # self.add_remote_url(self.repo2_remote_name, self.repo2)
        # self.add_remote_url(self.fork1_remote_name, self.fork1)
        # self.add_remote_url(self.fork2_remote_name, self.fork2)
        # shell.run(["git", "fetch", self.repo1_remote_name])
        # shell.run(["git", "fetch", self.repo2_remote_name])
        # shell.run(["git", "fetch", self.fork1_remote_name])
        # shell.run(["git", "fetch", self.fork2_remote_name])
        # shell.run(["git", "fetch", "origin"])

    def is_repo_exist_on_git(self, url):
        is_exist = False
        try:
            return requests.get(url).status_code == 200
        except requests.exceptions.RequestException as e:
            print(e)
        return is_exist

    def add_remote_url(self,remote_name , url):
        if not self.check_repo_exist(remote_name):
            shell.run(["git", "remote", "add", remote_name, url])
        else:
            self.add_sync_repo_in_remote(remote_name, url)

    def add_sync_repo_in_remote(self,remote_name, url):
        shell.run(["git", "remote", "set-url", remote_name, url])

    def check_repo_exist(self,  remote_name):
        output = shell.run(["git", "remote","-v"])
        if output.stdout:
            return remote_name in output.stdout
        return False

    def sync_master_with_upstream(self, fork, repo):
        print("started syncing with upstream :")
        shell.run(["git", "checkout", "{}/master".format(fork), "-f"])
        if shell.run(["git", "diff", "{}/master".format(fork), "{}/master".format(repo)]).stdout:
            print("different found beetween  {} master and {} master".format(fork, repo))
            shell.run(["git", "rebase", "{}/master".format(repo)])
            shell.run(["git", "push", fork, "{}/master".format(fork)])
            print("succesfully rebased {} master with {} master".format(fork, repo))


    def has_more_diff(self, from_repo, to_repo):
        has_more_changes = False
        # ["git",  "diff", "master", "against_fork/master" ,"--shortstat"]
        # output = shell.run(["git", "diff",  "fork1/master", "fork2/master", "--shortstat"])
        # output =  208 files changed, 39625 insertions(+), 9481 deletions(-)
        output = shell.run(["git", "diff",  "{}/master".format(from_repo), "{}/master".format(to_repo), "--shortstat"])
        if output.stdout:
            print(output.stdout)
            insertion_str = re.findall("\d+ insertion", output.stdout)
            if insertion_str:
                count_list = re.findall("\d+", insertion_str[0])
                if count_list:
                    count = int(count_list[0])
                    if count > 0:
                        has_more_changes = True
        return has_more_changes

if __name__ == '__main__':
    import  sys
    if len(sys.argv) is 1:
        print("please pass username in argument")
        exit()
    username = sys.argv[1]
    print(username)
    git_merge = GitAutoMergeFork(username)
    git_merge.add_n_fetch_remote_repo()
    git_merge.sync_master_with_upstream(git_merge.fork1_remote_name,
                                        git_merge.repo1_remote_name)
    git_merge.sync_master_with_upstream(git_merge.fork2_remote_name,
                                        git_merge.repo1_remote_name)

    if git_merge.has_more_diff(git_merge.fork1_remote_name, git_merge.fork2_remote_name):
        print("more difference beetween {} master from {} master".format(git_merge.fork1_remote_name,
                                                                         git_merge.fork2_remote_name))
        branch_name = "sync_branch_{}".format(int(time.time()))
        shell.run(["git", "checkout", "{}/master".format(git_merge.fork2_remote_name), "-f"])
        shell.run(["git", "checkout", "-b", branch_name])
        shell.run(["git", "push", git_merge.fork1_remote_name, branch_name, "-f"])

        print("{} branch has been pushed successfully.".format(branch_name))
        out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.repo),
                         "-h", "{}/{}:{}".format(git_merge.username, git_merge.repo, branch_name), "-m",
                         "msg for sync branch {} to master".format(branch_name)])
        print(out.stdout)

    if git_merge.has_more_diff(git_merge.fork2_remote_name, git_merge.fork1_remote_name):
        print("more difference beetween {} master from {} master".format(git_merge.fork2_remote_name,
                                                                         git_merge.fork1_remote_name))
        branch_name = "sync_branch_{}".format(int(time.time()))
        shell.run(["git", "checkout", "{}/master".format(git_merge.fork1_remote_name), "-f"])
        shell.run(["git", "checkout", "-b", branch_name])
        shell.run(["git", "push", git_merge.fork2_remote_name, branch_name, "-f"])

        print("{} branch has been pushed successfully.".format(branch_name))
        out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.repo + "-private"),
                   "-h",  "{}/{}:{}".format(git_merge.username, git_merge.repo + "-private", branch_name), "-m",
                   "msg for sync branch {} to master".format(branch_name)])
        print(out.stdout)
