# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py
This file only covers tests for the main sheet. Tests for multiple sheets are in test_input_SpreadsheetInput_unflatten_multiplesheets.py

"""
from __future__ import unicode_literals
from .test_input_SpreadsheetInput import ListInput
from flattentool.schema import SchemaParser
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
import copy
from six import text_type

ROOT_ID_TITLES = {
    'ocid': 'Open Contracting ID',
    'custom': 'Custom'
}

def inject_root_id(root_id, d):
    """
    Insert the appropriate root id, with the given value, into the dictionary d and return.
    """
    d = copy.copy(d)
    if 'ROOT_ID' in d:
        if root_id != '':
            d.update({root_id: d['ROOT_ID']})
        del d['ROOT_ID']
    if 'ROOT_ID_TITLE' in d:
        if root_id != '':
            d.update({ROOT_ID_TITLES[root_id]: d['ROOT_ID_TITLE']})
        del d['ROOT_ID_TITLE']
    return d


UNICODE_TEST_STRING = 'éαГ😼𝒞人'
# ROOT_ID will be replace by the appropirate root_id name in the test (e.g. ocid)

testdata = [
    (
        'Basic flat',
        [{
            'ROOT_ID': '1',
            'id': 2,
            'testA': 3
        }],
        [{
                'ROOT_ID': '1',
                'id': 2,
                'testA': 3
        }],
        []
    ),
    (
        'Basic with zero',
        [{
            'ROOT_ID': '1',
            'id': 2,
            'testA': 0
        }],
        [{
                'ROOT_ID': '1',
                'id': 2,
                'testA': 0
        }],
        []
    ),
    (
        'Nested',
        [{
            'ROOT_ID': '1',
            'id': 2,
            'testO/testB': 3,
            'testO/testC': 4,
        }],
        [{
            'ROOT_ID': '1',
            'id': 2,
            'testO': {'testB': 3, 'testC': 4}
        }],
        []
    ),
    (
        'Unicode',
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'testU': UNICODE_TEST_STRING
        }],
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'testU': UNICODE_TEST_STRING
        }],
        []
    ),
    (
        'Single item array',
        [{
            'ROOT_ID': '1',
            'id': 2,
            'testL/0/id': 3,
            'testL/0/testB': 4
        }],
        [{
            'ROOT_ID': '1', 'id': 2, 'testL': [{
                'id': 3, 'testB': 4
            }],
        }],
        []
    ),
    (
        'Single item array without parent ID',
        [{
            'ROOT_ID': '1',
            'testL/0/id': '2',
            'testL/0/testB': '3',
        }],
        [{
            'ROOT_ID': '1',
            'testL': [{
                'id': '2',
                'testB': '3'
            }],
        }],
        []
    ),
    (
        'Empty',
        [{
            'ROOT_ID': '',
            'id': '',
            'testA': '',
            'testB': '',
            'testC': '',
            'testD': '',
            'testE': '',
        }],
        [],
        []
    ),
    (
        'Empty except for root id',
        [{
            'ROOT_ID': 1,
            'id': '',
            'testA': '',
            'testB': '',
            'testC': '',
            'testD': '',
            'testE': '',
        }],
        [{
            'ROOT_ID': 1
        }],
        []
    ),
# Previously this caused the error: TypeError: unorderable types: str() < int()
# Now one of the columns is ignored
    (
        'Mismatch of object/array for field not in schema',
        [OrderedDict([
            ('ROOT_ID', 1),
            ('id', 2),
            ('newtest/a', 3),
            ('newtest/0/a', 4),
        ])],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'newtest': {
                'a': 3,
            }
        }],
        ['Column newtest/0/a has been ignored, because it treats newtest as an array, but another column does not.']
    ),
# Previously this caused the error: TypeError: unorderable types: str() < int()
# Now one of the columns is ignored
    (
        'Mismatch of array/object for field not in schema',
        [OrderedDict([
            ('ROOT_ID', 1),
            ('id', 2),
            ('newtest/0/a', 4),
            ('newtest/a', 3),
        ])],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'newtest': [
                {'a': 4}
            ]
        }],
        ['Column newtest/a has been ignored, because it treats newtest as an object, but another column does not.']
    ),
# Previously this caused the error: 'Cell' object has no attribute 'get'
# Now one of the columns is ignored
    (
        'str / array mixing',
        [OrderedDict([
            ('ROOT_ID', 1),
            ('id', 2),
            ('newtest', 3),
            ('newtest/0/a', 4),
        ])],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'newtest': 3
        }],
        ['Column newtest/0/a has been ignored, because it treats newtest as an array, but another column does not.']
    ),
    (
        'str / object mixing',
        [OrderedDict([
            ('ROOT_ID', 1),
            ('id', 2),
            ('newtest', 3),
            ('newtest/a', 4),
        ])],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'newtest': 3
        }],
        ['Column newtest/a has been ignored, because it treats newtest as an object, but another column does not.']
    ),
# Previously this caused the error: KeyError('ocid',)
# Now it works, but probably not as intended
# The missing Root ID should be picked up in schema validation
# (Cove will do this automatically).
    (
        'Root ID is missing',
        [OrderedDict([
            ('id', 2),
            ('testA', 3),
        ])],
        [{
            'id': 2,
            'testA': 3
        }],
        []
    ),
]

# Test cases that require our schema aware JSON pointer logic, so must be run
# with the relevant schema
testdata_pointer = [
    (
        'Single item array without json numbering',
        [{
            'ROOT_ID': '1',
            'testR/id': '2',
            'testR/testB': '3',
            'testR/testX': '3',
        }],
        [{
            'ROOT_ID': '1',
            'testR': [{
                'id': '2',
                'testB': '3',
                'testX': '3'
            }],
        }],
        []
    ),
    (
        'Multi item array one with varied numbering ',
        [{
            'ROOT_ID': '1',
            'testR/id': '-1',
            'testR/testB': '-1',
            'testR/testX': '-2',
            'testR/0/id': '0',
            'testR/0/testB': '1',
            'testR/0/testX': '1',
            'testR/5/id': '5',
            'testR/5/testB': '5',
            'testR/5/testX': '6',
        }],
        [{
            'ROOT_ID': '1',
            'testR': [{
                'id': '-1',
                'testB': '-1',
                'testX': '-2'
            },
            {
                'id': '0',
                'testB': '1',
                'testX': '1'
            },
            {
                'id': '5',
                'testB': '5',
                'testX': '6'
            }
            ]
        }],
        []
    ),
]

def create_schema(root_id):
    schema = {
        'properties': {
            'id': {
                'title': 'Identifier',
                'type': 'integer',
            },
            'testA': {
                'title': 'A title',
                'type': 'integer',
            },
            'testB': {
                'title': 'B title',
                'type': 'object',
                'properties': {
                    'testC': {
                        'title': 'C title',
                        'type': 'integer',
                    },
                    'testD': {
                        'title': 'D title',
                        'type': 'integer',
                    }
                }
            },
            'testR': {
                'title': 'R title',
                'type': 'array',
                'rollUp': ['id', 'testB'],
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {
                            'title': 'Identifier',
                            'type': 'string',
                            # 'type': 'integer',
                            # integer does not work, as testB:integer is not
                            # in the rollUp
                        },
                        'testB': {
                            'title': 'B title',
                            'type': 'string',
                        },
                        'testC': {
                            'title': 'C title',
                            'type': 'string',
                        },
                        'testSA': {
                            'title': 'SA title',
                            'type': 'array',
                            'items': {
                                'type': 'string'
                            }
                        }
                    }
                }
            },
            'testU': {
                'title': UNICODE_TEST_STRING,
                'type': 'string',
            },
            'testSA': {
                'title': 'SA title',
                'type': 'array',
                'items': {
                    'type': 'string'
                }
            }
        }
    }
    if root_id:
        schema.update({
            root_id: {
                'title': ROOT_ID_TITLES[root_id],
                'type': 'string'
            }
        })
    return schema

testdata_titles = [
    (
        'Basic flat',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'A title': 3
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testA': 3
        }],
        []
    ),
    (
        'Nested',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'B title:C title': 3,
            'B title:D title': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testB': {'testC': 3, 'testD': 4}
        }],
        []
    ),
    (
        'Nested titles should be converted individually',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'B title:C title': 3,
            'B title:Not in schema': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testB': {'testC': 3, 'Not in schema': 4}
        }],
        []
    ),
    (
        'Should be space and case invariant',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'B  title : c  title': 3,
            'btitle : Not in schema': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testB': {'testC': 3, 'Not in schema': 4}
        }],
        []
    ),
    (
        'Unicode',
        [{
            'ROOT_ID_TITLE': UNICODE_TEST_STRING,
            UNICODE_TEST_STRING: UNICODE_TEST_STRING
        }],
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'testU': UNICODE_TEST_STRING
        }],
        []
    ),
   (
        'Single item array',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:Identifier': 3,
            'R title:B title': 4
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'id': '3', 'testB': '4'
            }],
        }],
        []
    ),
    (
        'Single item array without parent ID',
        [{
            'ROOT_ID_TITLE': '1',
            'R title:Identifier': '2',
            'R title:B title': '3'
        }],
        [{
            'ROOT_ID': '1',
            'testR': [{
                'id': '2',
                'testB': '3'
            }],
        }],
        []
    ),
    (
        '''
        Properties of a single item array shouldn't need to be in rollUp list
        for their titles to be converted
        ''',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:Identifier': 3,
            'R title:C title': 4
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'id': '3',
                'testC': '4'
            }],
        }],
        []
    ),
    (
        'Single item array, titles should be converted individually',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:C title': 3,
            'R title:Not in schema': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'testC': '3',
                'Not in schema': 4
            }],
        }],
        []
    ),
    (
        'Multi item array, allow numbering',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:C title': 3,
            'R title:Not in schema': 4,
            'R title:0:C title': 5,
            'R title:0:Not in schema': 6,
            'R title:5:C title': 7,
            'R title:5:Not in schema': 8,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'testC': '3',
                'Not in schema': 4
            },
            {
                'testC': '5',
                'Not in schema': 6
            },
            {
                'testC': '7',
                'Not in schema': 8
            }
            ]
        }],
        []
    ),
    (
        'Empty',
        [{
            'ROOT_ID_TITLE': '',
            'Identifier': '',
            'A title': '',
            'B title': '',
            'C title': '',
            'D title': '',
            'E title': '',
        }],
        [],
        []
    ),
    (
        'Empty except for root id',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': '',
            'A title': '',
            'B title': '',
            'C title': '',
            'D title': '',
            'E title': '',
        }],
        [{
            'ROOT_ID': 1
        }],
        []
    ),
    (
        'Test arrays of strings (1 item)',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'SA title': 'a',
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testSA': [ 'a' ],
        }],
        []
    ),
    (
        'Test arrays of strings (2 items)',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'SA title': 'a;b',
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testSA': [ 'a', 'b' ],
        }],
        []
    ),
    (
        'Test arrays of strings within an object array (1 item)',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:SA title': 'a',
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'testSA': [ 'a' ],
            }]
        }],
        []
    ),
    (
        'Test arrays of strings within an object array (2 items)',
        [{
            'ROOT_ID_TITLE': 1,
            'Identifier': 2,
            'R title:SA title': 'a;b',
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testR': [{
                'testSA': [ 'a', 'b' ],
            }]
        }],
        []
    ),
]

ROOT_ID_PARAMS =     [
        ('ocid', {}), # If not root_id kwarg is passed, then a root_id of ocid is assumed
        ('ocid', {'root_id': 'ocid'}),
        ('custom', {'root_id': 'custom'}),
        ('', {'root_id': ''})
    ]

# Since we're not using titles, and titles mode should fall back to assuming
# we've supplied a fieldname, we should be able to run this test with
# convert_titles and use_schema as True or False
@pytest.mark.parametrize('convert_titles', [True, False])
@pytest.mark.parametrize('use_schema', [True, False])
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
@pytest.mark.parametrize('comment,input_list,expected_output_list,warning_messages', testdata)
def test_unflatten(convert_titles, use_schema, root_id, root_id_kwargs, input_list, expected_output_list, recwarn, comment, warning_messages):
    # Not sure why, but this seems to be necessary to have warnings picked up
    # on Python 2.7 and 3.3, but 3.4 and 3.5 are fine without it
    import warnings
    warnings.simplefilter('always')

    extra_kwargs = {'convert_titles': convert_titles}
    extra_kwargs.update(root_id_kwargs)
    spreadsheet_input = ListInput(
        sheets={
            'custom_main': [
                inject_root_id(root_id, input_row) for input_row in input_list
            ]
        },
        **extra_kwargs)
    spreadsheet_input.read_sheets()

    parser = SchemaParser(
        root_schema_dict=create_schema(root_id) if use_schema else {"properties": {}},
        root_id=root_id,
        rollup=True
    )
    parser.parse()
    spreadsheet_input.parser = parser

    expected_output_list = [
        inject_root_id(root_id, expected_output_dict) for expected_output_dict in expected_output_list
    ]
    if expected_output_list == [{}]:
        # We don't expect an empty dictionary
        expected_output_list = []
    assert list(spreadsheet_input.unflatten()) == expected_output_list
    # We expect no warning_messages
    if not convert_titles: # TODO what are the warning_messages here
        assert [str(x.message) for x in recwarn.list] == warning_messages


@pytest.mark.parametrize('convert_titles', [True, False])
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
@pytest.mark.parametrize('comment,input_list,expected_output_list,warning_messages', testdata_pointer)
def test_unflatten_pointer(convert_titles, root_id, root_id_kwargs, input_list, expected_output_list, recwarn, comment, warning_messages):
    return test_unflatten(convert_titles=convert_titles, use_schema=True, root_id=root_id, root_id_kwargs=root_id_kwargs, input_list=input_list, expected_output_list=expected_output_list, recwarn=recwarn, comment=comment, warning_messages=warning_messages)


@pytest.mark.parametrize('comment,input_list,expected_output_list,warning_messages', testdata_titles)
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
def test_unflatten_titles(root_id, root_id_kwargs, input_list, expected_output_list, recwarn, comment, warning_messages):
    """
    Essentially the same as test unflatten, except that convert_titles and
    use_schema are always true, as both of these are needed to convert titles
    properly. (and runs with different test data).
    """
    if root_id != '':
        # Skip all tests with a root ID for now, as this is broken
        # https://github.com/OpenDataServices/flatten-tool/issues/84
        pytest.skip()
    return test_unflatten(convert_titles=True, use_schema=True, root_id=root_id, root_id_kwargs=root_id_kwargs, input_list=input_list, expected_output_list=expected_output_list, recwarn=recwarn, comment=comment, warning_messages=warning_messages)


