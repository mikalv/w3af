"""
test_vulns.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import os
import re
import unittest

from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.data.constants.vulns import VULNS
from w3af.core.controllers.ci.constants import ARTIFACTS_DIR

       
class TestVulnsConstants(unittest.TestCase):
    
    LOCATION = os.path.join(ROOT_PATH, 'core', 'data', 'constants', 'vulns.py')
    
    def test_no_duplicated_ids(self):
        # Just skip the entire license header
        vulns_file = file(self.LOCATION) 
        for _ in xrange(21):
            vulns_file.readline()
            
        vuln_id_list = re.findall('(\d+):', vulns_file.read())
        filtered = set()
        dups = set()
        
        for vuln_id in vuln_id_list:
            if vuln_id in filtered:
                dups.add(vuln_id)
            
            filtered.add(vuln_id)

        self.assertEquals(set([]), dups)
    
    def test_no_empty(self):
        items = VULNS.items()
        empty_values = set([(key, val) for (key, val) in items if not val])
        self.assertEqual(set([]), empty_values)

    def get_all_vulnerability_names(self):
        # Just skip the entire license header
        vulns_file = file(self.LOCATION)
        for _ in xrange(21):
            vulns_file.readline()

        return re.findall('\d+: ?[\'"](.*?)[\'"]', vulns_file.read())

    def test_vulnerability_names_unique(self):
        dups = []
        vuln_names = self.get_all_vulnerability_names()
        dup_ignore = {'Vacant',
                      'Unhandled error in web application'}

        for name in vuln_names:
            if vuln_names.count(name) > 1 and name not in dups\
            and name not in dup_ignore:
                dups.append(name)

        self.assertEqual(dups, [])

    def test_all_vulnerability_names_used(self):
        vuln_names = self.get_all_vulnerability_names()
        plugins_path = os.path.join(ROOT_PATH, 'plugins')
        vuln_template_path = os.path.join(ROOT_PATH, 'core', 'data', 'kb',
                                          'vuln_templates')

        all_plugin_sources = ''
        for dir_name, subdir_list, file_list in os.walk(plugins_path):

            for fname in file_list:
                if not fname.endswith('.py'):
                    continue

                if fname.startswith('test_'):
                    continue

                if fname == '__init__.py':
                    continue

                full_path = os.path.join(plugins_path, dir_name, fname)

                ignores = {'/attack/db/sqlmap/',
                           '/attack/payloads/',
                           '/plugins/tests/'}

                should_continue = False
                for ignore in ignores:
                    if ignore in full_path:
                        should_continue = True
                        break

                if should_continue:
                    continue

                all_plugin_sources += file(full_path).read()

        for dir_name, subdir_list, file_list in os.walk(vuln_template_path):

            for fname in file_list:
                if not fname.endswith('.py'):
                    continue

                if fname.startswith('test_'):
                    continue

                if fname == '__init__.py':
                    continue

                full_path = os.path.join(vuln_template_path, dir_name, fname)
                all_plugin_sources += file(full_path).read()

        missing_ignore = {'TestCase',
                          'Vacant',
                          'Blind SQL injection vulnerability'}

        for vuln_name in vuln_names:
            if vuln_name in missing_ignore:
                continue

            msg = '"%s" not in plugin sources' % vuln_name
            self.assertIn(vuln_name, all_plugin_sources, msg)

    @attr('ci_ignore')
    def test_vuln_updated(self):
        """
        Each time we call Info.set_name during a test (and only during tests,
        not run when the user is running w3af) we check if the name of the
        vulnerability being set is actually in the vuln.py database or not,
        if it's not we append it to a file called /tmp/missing-vulndb.txt

        This test asserts that the file:
            * Doesn't exist
            * Is empty
            * Fail if not

        Since we want to run this test at the end, we tag it as ci_fails for the
        main running to ignore it, but then we run it manually from circle.yml
        """
        missing = os.path.join(ARTIFACTS_DIR, 'missing-vulndb.txt')

        if not os.path.exists(missing):
            # Perfect!
            return

        missing_list = []
        for line in file(missing):
            line = line.strip()

            if not line:
                continue

            missing_list.append(line)

        missing_list = list(set(missing_list))
        missing_list.sort()

        self.maxDiff = None
        self.assertEqual(missing_list, [])