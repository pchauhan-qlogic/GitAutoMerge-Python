import os, time, requests
from synthtool import shell

OWNER = "paraschauhance"
GITHUB = "https://github.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
is_cloned = os.path.isdir(os.path.join(BASE_DIR, ".git"))

class GitAutoMergeFork(object):
    def __init__(self, user_name):
        self.username = user_name
        self.repo = "google-cloud-java"
        self.private_repo = self.repo + "-private"

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
        repo_list = (
            (self.repo1_remote_name, self.repo1),
            (self.repo2_remote_name, self.repo2),
            (self.fork1_remote_name, self.fork1),
            (self.fork2_remote_name, self.fork2)
        )
        for repo_name, url in repo_list:
            if self.is_repo_exist_on_git(url):
                self.add_remote_url(repo_name, url)
            else:
                print("{} url have not repo exist".format(url))
                sys.exit()


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

    def has_diff(self, from_repo, to_repo):
        has_more_changes = False
        output = shell.run(["git", "diff",  "{}/master".format(from_repo), "{}/master".format(to_repo), "--shortstat"])
        if output.stdout:
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
    shell.run(["git", "fetch", "--all"])
    is_diff = git_merge.has_diff(git_merge.repo1_remote_name, git_merge.repo2_remote_name)
    if is_diff:
        is_conflict = False
        branch_name = "comparing_branch_{}".format(int(time.time()))
        shell.run(["git", "checkout", "{}/master".format(git_merge.repo1_remote_name), "-B", branch_name])
        try:
            merge_code = shell.run(["git", "merge", "{}/master".format(git_merge.repo2_remote_name), "--no-commit"])
        except Exception as e:
            is_conflict = True
            shell.run(["git", "reset", "--hard"])


        if is_conflict:
            branch_name = "comparing_branch_{}".format(int(time.time()))
            shell.run(["git", "checkout", "{}/master".format(git_merge.repo1_remote_name), "-B", branch_name])
            shell.run(["git", "push", git_merge.fork2_remote_name, branch_name, "-f"])
            print("{} branch has been pushed successfully.".format(branch_name))
            out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.private_repo),
                             "-h", "{}/{}:{}".format(git_merge.username, git_merge.private_repo, branch_name), "-m",
                             "msg for sync branch {} to master".format(branch_name)])
            print(out.stdout)

            branch_name = "comparing_branch_{}".format(int(time.time()))
            shell.run(["git", "checkout", "{}/master".format(git_merge.repo2_remote_name), "-B", branch_name])
            shell.run(["git", "push", git_merge.fork1_remote_name, branch_name, "-f"])
            print("{} branch has been pushed successfully.".format(branch_name))
            out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.repo),
                             "-h", "{}/{}:{}".format(git_merge.username, git_merge.repo, branch_name), "-m",
                             "msg for sync branch {} to master".format(branch_name)])
            print(out.stdout)
        else:
            merge_br_repo1_diff = shell.run(["git", "diff", "{}/master".format(git_merge.repo1_remote_name),
                                             branch_name, "--shortstat"])
            merge_br_repo2_diff = shell.run(["git", "diff", "{}/master".format(git_merge.repo2_remote_name),
                                             branch_name, "--shortstat"])

            if merge_br_repo1_diff.stdout is "":
                branch_name = "comparing_branch_{}".format(int(time.time()))
                shell.run(["git", "checkout", "{}/master".format(git_merge.repo1_remote_name), "-B", branch_name])
                shell.run(["git", "push", git_merge.fork2_remote_name, branch_name, "-f"])
                print("{} branch has been pushed successfully.".format(branch_name))
                out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.private_repo),
                                 "-h", "{}/{}:{}".format(git_merge.username, git_merge.private_repo, branch_name), "-m",
                                 "msg for sync branch {} to master".format(branch_name)])
                print(out.stdout)

            if merge_br_repo2_diff.stdout is "":
                branch_name = "comparing_branch_{}".format(int(time.time()))
                shell.run(["git", "checkout", "{}/master".format(git_merge.repo2_remote_name), "-B", branch_name])
                shell.run(["git", "push", git_merge.fork1_remote_name, branch_name, "-f"])
                print("{} branch has been pushed successfully.".format(branch_name))
                out = shell.run(["hub", "pull-request", "-b", "{}/{}:master".format(OWNER, git_merge.repo),
                                 "-h", "{}/{}:{}".format(git_merge.username, git_merge.repo, branch_name), "-m",
                                 "msg for sync branch {} to master".format(branch_name)])
                print(out.stdout)