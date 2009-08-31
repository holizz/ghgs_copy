#!/usr/bin/env python

# Backs-up all your GitHub repositories to a project on Gitorious

# The user you're running this as must have push access to the Gitorious
# account, but GitHub repos are cloned over git://

# Ensure that the Gitorious project specified in conf.json exists, it won't
# be created for you

# Shorthand: gh=GitHub, gs=Gitorious

import getpass
import json
import lxml.html
import os
import re
import shutil
import subprocess
import tempfile
import urllib
import urllib2

class Copier:

    gh_repos = 'http://github.com/api/v2/json/repos/show/%(user)s'
    gh_clone = 'git://github.com/%(user)s/%(repo)s'
    gs_login = 'https://secure.gitorious.org/sessions'
    gs_project = 'http://gitorious.org/%(project)s'
    gs_create = 'http://gitorious.org/%(project)s/repositories'
    gs_regexp = '^git://gitorious.org/%(project)s/(.+)\.git$'
    gs_push = 'git@gitorious.org:%(project)s/%(repo)s.git'

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

        gh_repos = self.gh_list_repos()
        gs_repos = self.gs_list_repos()

        for repo in gh_repos:
            # Clone GitHub repo
            d = self.conf['github']
            d.update({'repo': repo})
            rurl = self.gh_clone % d
            rpath = os.path.join(self.conf['tmp_dir'],repo)
            cmd = ['git','clone','--mirror',rurl,rpath]
            print ' '.join(cmd)
            subprocess.call(cmd)

            # Normalise repo name for the benefit of Gitorious
            normrepo = re.sub('\.', '_', repo)

            # Create repo if not present in Gitorious
            if normrepo not in gs_repos:
                self.gs_create_repo(normrepo, gh_repos[repo])

            # Push GitHub repo to Gitorious
            d = self.conf['gitorious']
            d.update({'repo': normrepo})
            gs_rurl = self.gs_push % d
            # git remote add
            cmd = ['git','--git-dir='+rpath,'remote','add','gitorious',gs_rurl]
            print ' '.join(cmd)
            subprocess.call(cmd)
            # git push
            cmd = ['git','--git-dir='+rpath,'push','--mirror','gitorious']
            print ' '.join(cmd)
            subprocess.call(cmd)

        if not self.temp:
            shutil.rmtree(self.conf['tmp_dir'])

    def gh_list_repos(self):
        url = self.gh_repos % self.conf['github']
        j = json.load(urllib2.urlopen(url))
        repos = {}
        for repo in j['repositories']:
            repos[repo['name']] = repo['description']
        return repos

    def gs_list_repos(self):
        pu = self.gs_project % self.conf['gitorious']
        p = urllib2.urlopen(pu)
        l = lxml.html.parse(p)
        repos = []
        for a in l.xpath('//a[starts-with(@href,"git://")]'):
            href = a.attrib['href'].strip()
            exp = self.gs_regexp % self.conf['gitorious']
            m = re.match(exp, href)
            if m:
                repos.append(m.group(1))
        return repos

    def gs_create_repo(self, repo, desc=''):
        if self.conf['gitorious']['password'] == None:
            print "One or more repositories on GitHub aren't present on Gitorious, please enter your password"
            self.conf['gitorious']['password'] = getpass.getpass()

        od = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        urllib2.install_opener(od)

        d = {}
        for key in ['email','password']:
            d[key] = self.conf['gitorious'][key]
        data = urllib.urlencode(d)
        # Login
        #TODO: test what's returned
        od.open(self.gs_login, data)

        # Create repo
        data = urllib.urlencode({'repository[name]': repo,
            'repository[description]': desc})
        od.open(self.gs_create % self.conf['gitorious'], data)

if __name__ == '__main__':
    Copier().copy()
