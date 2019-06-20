#!/usr/bin/env python3
from src.search import Search
import unittest
import os
import subprocess


class TestSearch(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = 'tmp_test'
        self.to_remove = []
        os.mkdir(self.tmp_dir)
        self.search = Search()

    def test_extract_vehicle_details(self):
        data = [{'name': 'nm1'}, {'name': 'nm2'}, {'name': 'nm3'}]
        expected = ['nm1', 'nm2', 'nm3']
        actual = self.search.extract_key_names(data)
        self.assertEqual(expected, actual)

    def test_set_api_key(self):
        expected = 'abc123'
        key_file = 'tmp_test/test.key'
        self.to_remove.append(key_file)
        self.search.config.store_api_key(key_file, expected)
        key = self.search.config.get_api_key(key_file)
        self.assertEqual(expected, key)

    def test_squeeze(self):
        data = [{'name': 'test1', 'value': 1},
                {'name': 'test2', 'value': 2}]
        expected = {'test1': 1, 'test2': 2}
        actual = self.search.squeeze(data)
        self.assertEqual(expected, actual)

    def test_sort_elements(self):
        data = {'b': 2, 'c': 3, 'a': 1}
        expected = [('a', 1), ('b', 2), ('c', 3)]
        actual = self.search.sort_elements(data.items())
        self.assertEqual(expected, actual)

    def test_get_all_makes(self):
        actual = subprocess.check_output(['python3', 'run.py', '-get', 'all-makes', '-v'])
        self.assertTrue(actual)

    def test_get_all_models(self):
        actual = subprocess.check_output(['python3', 'run.py', '-get', 'all-models', '-m', 'Ford', '-v'])
        self.assertTrue(actual)

    def test_get_all_bodies(self):
        actual = subprocess.check_output(['python3', 'run.py', '-get', 'all-bodies', '-v'])
        self.assertTrue(actual)

    def test_invalid_make(self):
        actual = subprocess.check_output(['python3', 'run.py', '-m', 'Abc', '-v'])
        self.assertTrue(actual)

    def test_invalid_model(self):
        actual = subprocess.check_output(['python3', 'run.py', '-m', 'Ford', '-M', 'Abc' '-v'])
        self.assertTrue(actual)

    def test_invalid_body(self):
        actual = subprocess.check_output(['python3', 'run.py', '-m', 'Ford', '--body', 'abc', '-v'])
        self.assertTrue(actual)

    def test_invalid_gearbox(self):
        actual = subprocess.check_output(['python3', 'run.py', '-m', 'Ford', '--gearbox', 'abc', '-v'])
        self.assertTrue(actual)

    def tearDown(self):
        for f in self.to_remove:
            os.remove(f)
        os.rmdir(self.tmp_dir)


if __name__ == '__main__':
    unittest.main()
