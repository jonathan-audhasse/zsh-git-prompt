#!/usr/bin/env python
from __future__ import print_function

# change this symbol to whatever you prefer
prehash = ':'

from subprocess import Popen, PIPE
import sys
import re

# `git status --porcelain --branch` can collect all information
# branch, remote_branch, untracked, staged, changed, conflicts, ahead, behind
po = Popen(['git', 'status', '--porcelain', '--branch'], env={'LC_ALL': 'C'}, stdout=PIPE, stderr=PIPE)
stdout, stderr = po.communicate()
if po.returncode != 0:
    sys.exit(0)  # Not a git repository

def get_tag_or_hash():
    cmd = Popen(['git', 'describe', '--exact-match'], stdout=PIPE, stderr=PIPE)
    so, se = cmd.communicate()
    tag = '%s' % so.decode('utf-8').strip()

    if tag:
        return tag
    else:
        cmd = Popen(['git', 'rev-parse', '--short', 'HEAD'], stdout=PIPE, stderr=PIPE)
        so, se = cmd.communicate()
        hash_name = '%s' % so.decode('utf-8').strip()
        return ''.join([prehash, hash_name])


# collect git status information
untracked, staged, changed, conflicts = [], [], [], []
num_ahead, num_behind = 0, 0
branch = ''
remote_branch = 'L'
status = [(line[0], line[1], line[2:]) for line in stdout.decode('utf-8').splitlines()]
for st in status:
    if st[0] == '#' and st[1] == '#':
        if re.search('Initial commit on', st[2]):
            branch = st[2].split(' ')[-1]
        elif re.search('No commits yet on', st[2]):
            branch = st[2].split(' ')[-1]
        elif re.search('no branch', st[2]):  # detached status
            branch = get_tag_or_hash()
        elif len(st[2].strip().split('...')) == 1:
            branch = st[2].strip()
        else:
            # current and remote branch info
            branch, rest = st[2].strip().split('...')
            remote_branch = rest.split(' ')[0]
            if len(rest.split(' ')) == 1:
                pass
            else:
                # ahead or behind
                divergence = ' '.join(rest.split(' ')[1:])
                divergence = divergence.lstrip('[').rstrip(']')
                for div in divergence.split(', '):
                    if 'ahead' in div:
                        num_ahead = int(div[len('ahead '):].strip())
                    elif 'behind' in div:
                        num_behind = int(div[len('behind '):].strip())
    elif st[0] == '?' and st[1] == '?':
        untracked.append(st)
    else:
        if st[1] == 'M':
            changed.append(st)
        if st[0] == 'U':
            conflicts.append(st)
        elif st[0] != ' ':
            staged.append(st)

def get_stash():
    cmd = Popen(['git', 'rev-parse', '--git-dir'], stdout=PIPE, stderr=PIPE)
    so, se = cmd.communicate()
    stash_file = '%s%s' % (so.decode('utf-8').rstrip(), '/logs/refs/stash')

    try:
        with open(stash_file) as f:
            return sum(1 for _ in f)
    except IOError:
        return 0

out = ' '.join([
	branch,
    remote_branch,
	str(num_ahead),
	str(num_behind),
    str(len(staged)),
    str(len(conflicts)),
    str(len(changed)),
    str(len(untracked)),
	str(get_stash()),
	])
print(out, end='')

