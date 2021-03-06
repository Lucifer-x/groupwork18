#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
get the commit count per sublevel pointwise or cumulative (c)
arguments is the tag as displayed by git tag and the number
of sublevels to be counted. If count is out of range for a
specific sublevel it will terminate the loop
"""

__author__ = "Group No.18 in DSP of Lanzhou University"
__copyright__ = "Copyright 2020, Study Project in Lanzhou University , China"
__license__ = "GPL V3"
__version__ = "0.1"
__maintainer__ = "Yuming Chen"
__email__ = "Chenym18@lzu.edu.cn"
__status__ = "Experimental"

import os, re, sys, subprocess, argparse
from datetime import datetime as dt
import pandas as pd


class InvalidRevError(Exception):
    pass


class InvalidPathError(EnvironmentError):
    pass


def getArg():
    """
    Using 'argparse' to handle the argument.
    :return: args
    """
    parser = argparse.ArgumentParser(description="Count the commit")
    parser.add_argument('-p', '--path', metavar='DIR', default='../linux/', help='path to Git Repository')
    parser.add_argument('-r', '--rev', type=str, default='v4', help='First Reversion')
    parser.add_argument('-g', '--rev-range', type=int, default=10, help='The range of the Reversion')
    parser.add_argument('-c', '--cumulative', action='store_true', default=False, help='Enable cumulative arguments')
    return parser.parse_args()


def get_commit_cnt(outs):
    """
    Changes
    :param outs:
    :return:
    """
    # if we request something that does not exist -> 0
    cnt = re.findall('[0-9]*-[0-9]*-[0-9]*', str(outs))
    return len(cnt)


def get_tag_days(outs, base):
    return ((int(outs) - base)) // 3600


class Rep:
    def __init__(self, args):
        self.path = args.path
        self.rev = args.rev
        self.rev_range = args.rev_range
        self.cumulative = args.cumulative
        self.result = {}
        # Verify the repository
        try:
            assert os.path.exists(os.path.join(self.path, '.git')), True
        except AssertionError:
            print('Invalid Git Repository')
            raise InvalidPathError from None

    def run_cmd(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True,
                             cwd=self.path)
        try:
            outs, errs = p.communicate(timeout=15)
            if p.returncode:
                print('Invalid Reversion')
                raise subprocess.CalledProcessError(p.returncode, cmd) from None
        except subprocess.TimeoutExpired:
            p.kill()
            raise RuntimeError("Timeout during get git commits") from None
        return outs

    def count(self):
        # Init the 'result' dict
        self.result['lv'] = []
        self.result['hour'] = []
        self.result['bugs'] = []
        rev1 = self.rev + "." + str(0)
        # Extract the time of the base commit from git
        base = self.run_cmd("git log -1 --pretty=format:\"%ct\" " + rev1)
        # Fill the 'result'
        for sl in range(1, self.rev_range + 1):
            rev2 = self.rev + "." + str(sl)
            gitcnt = "git rev-list --pretty=format:\"%ai\" " + rev1 + "..." + rev2
            gittag = "git log -1 --pretty=format:\"%ct\" " + rev2
            git_rev_list = self.run_cmd(gitcnt)
            commit_cnt = get_commit_cnt(git_rev_list)
            if not self.cumulative:
                rev1 = rev2
            if commit_cnt:
                git_tag_date = self.run_cmd(gittag)
                days = get_tag_days(git_tag_date, int(base))
                self.result['lv'].append(sl)
                self.result['hour'].append(days)
                self.result['bugs'].append(commit_cnt)
            else:
                break
        # Create a data frame to store the count result which is better than printing directly.
        df = pd.DataFrame(data=self.result)
        # Reformat the Table
        df.set_index('lv')  # Change index
        title = "#sublevel commits %s stable fixes" % self.rev  # Add title
        return title, df


if __name__ == "__main__":
    args = getArg()
    r = Rep(args)
    title, result = r.count()
    print(title)
    print(result)
