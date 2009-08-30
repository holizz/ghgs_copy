#!/usr/bin/env python

# Backs-up all your GitHub repositories to a project on Gitorious

# The user you're running this as must have push access to the Gitorious
# account, but GitHub repos are cloned over git://

# Shorthand: gh=GitHub, gs=Gitorious

import json
import lxml.html
import os
import re
import tempfile
import urllib2

class Copier:

    gh_repos = 'http://github.com/api/v2/json/repos/show/%(user)s'
    gh_clone = 'git://github.com/%(user)s/%(repo)s'
    gs_project = 'http://gitorious.org/%(proj)s'
    gs_regexp = '^git://gitorious.org/%(proj)s/(.+)\.git$'

    def __init__(self):
        self.conf = json.load(open('conf.json'))

    def copy(self):
        if self.conf['tmp_dir'] == None:
            self.conf['tmp_dir'] = tempfile.mkdtemp()
            self.temp = True
        else:
            self.temp = False
            try:
                os.makedirs(self.conf['tmp_dir'])
            except OSError, e:
                if not e.errno == 17: # dir already exists
                    raise

        # Clone GitHub repos
        gh_repos = self.gh_list_repos()
        print gh_repos
        #TODO

        # List repos in Gitorious
        gs_repos = self.gs_list_repos()
        print gs_repos

        # Create repos if not existing
        #TODO

        # Push each gh repo to Gitorious
        #TODO

        if self.temp:
            pass#TODO: rm -rf self.conf['tmp_dir']

    def gh_list_repos(self):
        url = self.gh_repos % {'user': self.conf['github']['user']}
        j = json.load(urllib2.urlopen(url))
        repos = []
        for repo in j['repositories']:
            repos.append(repo['name'])
        return repos

    def gs_list_repos(self):
        pu = self.gs_project % {'proj':self.conf['gitorious']['project']}
        p = urllib2.urlopen(pu)
        l = lxml.html.parse(p)
        repos = []
        for a in l.xpath('//a[starts-with(@href,"git://")]'):
            href = a.attrib['href'].strip()
            exp = self.gs_regexp%{'proj':self.conf['gitorious']['project']}
            m = re.match(exp, href)
            if m:
                repos.append(m.group(1))
        return repos

    def gs_create_repo(self, repo):
        if self.conf['gitorious']['password'] == None:
            print "There is a new repository on GitHub named '%(repo)s', enter your password to create the repo on Gitorious" % {'repo':repo}
            pass#TODO: collect password
        pass#TODO: auth and create repo

if __name__ == '__main__':
    Copier().copy()
