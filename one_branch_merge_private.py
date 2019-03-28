import re, time
from synthtool import shell

OWNER = "pmakani"
USENAME = "pchauhan-qlogic"

REPO = "google-cloud-java-private"
AGAINST_REPO = "google-cloud-java1"

GITHUB = "https://github.com"


class GitAutoMergeFork(object):

    def __init__(self, user_name=USENAME):
        self.upstream = "{}/{}/{}".format(GITHUB, OWNER, REPO)
        self.fork2 = "{}/{}/{}".format(GITHUB, user_name, AGAINST_REPO)
        self.upstream2 = "{}/{}/{}".format(GITHUB, OWNER, AGAINST_REPO)
        self.fork2_name = "against_fork"
        self.upstream_name = "upstream"
        self.upstream2_name = "against_upstream"

    def add_fetch_remote_repo(self):
        self.add_remote_url(self.upstream_name, self.upstream)
        self.add_remote_url(self.fork2_name, self.fork2)
        self.add_remote_url(self.upstream2_name, self.upstream2)
        shell.run(["git", "fetch", self.upstream_name])
        shell.run(["git", "fetch", self.fork2_name])
        shell.run(["git", "fetch", self.upstream2_name])
        shell.run(["git", "fetch", "origin"])

    def sync_master_with_upstream(self):
        print("started syncing with upstream :")
        shell.run(["git", "checkout", "master"])
        if shell.run(["git", "diff", "master", "upstream/master"]).stdout:
            print("different found beetween master and upstream master")
            shell.run(["git", "rebase", "upstream/master"])
            shell.run(["git", "push", "origin", "master"])
            print("succesfully rebased master with upstream master")

    def add_remote_url(self,remote_name , url):
        if not self.check_second_repo_exist(remote_name):
            shell.run(["git", "remote", "add", remote_name, url])
        else:
            self.add_sync_repo_in_remote(remote_name, url)

    def add_sync_repo_in_remote(self,remote_name, url):
        shell.run(["git", "remote", "set-url", remote_name, url])

    def check_second_repo_exist(self,  remote_name):
        output = shell.run(["git", "remote","-v"])
        if output.stdout:
            return remote_name in output.stdout
        return False

    def git_push_origin_head(self):
        return shell.run(["git", "push", "origin",  "HEAD:master"])

    def has_more_diff(self):
        has_more_changes = False
        # ["git",  "diff", "master", "against_fork/master" ,"--shortstat"]
        output = shell.run(["git", "diff",  "master", "against_fork/master", "--shortstat"])
        # output =  208 files changed, 39625 insertions(+), 9481 deletions(-)
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
    git_merge = GitAutoMergeFork()
    git_merge.add_fetch_remote_repo()
    git_merge.sync_master_with_upstream()

    if git_merge.has_more_diff():
        print("more difference beetween master and fork master")
        branch_name = "sync_branch_{}".format(int(time.time()))
        shell.run(["git", "checkout", "{}/master".format(git_merge.fork2_name)])
        shell.run(["git", "checkout", "-b", branch_name])
        shell.run(["git", "push", "origin", branch_name])
        print("{} branch has been pushed successfully.".format(branch_name))
        out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, REPO),
                   "-h",  "{}/{}:{}".format(USENAME, REPO, branch_name), "-m",
                   "msg for sync branch {} to master".format(branch_name)])
        print(out.stdout)
