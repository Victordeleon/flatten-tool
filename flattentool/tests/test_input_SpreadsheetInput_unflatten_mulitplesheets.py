# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py

Tests that only apply for multiple sheets.
"""
from __future__ import unicode_literals
from .test_input_SpreadsheetInput import ListInput
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
from six import text_type

class TestUnflatten(object):
    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    },
                    {
                        'ocid': 1,
                        'id': 3,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'subField/0/testA': 3,
                    },
                    {
                        'ocid': 1,
                        'id': 2,
                        'subField/0/testA': 4,
                    }
                ]
            }
            )
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {
                'ocid': 1,
                'id': 2,
                'subField': [
                    {'testA': 3},
                    {'testA': 4},
                ]
            },
            {
                'ocid': 1,
                'id': 3
            }
        ]

    @pytest.mark.parametrize('nested_id_in_subsheet', [True, False])
    def test_nested_sub_sheet(self, nested_id_in_subsheet):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/id': 3,
                        'testA/testB': 4,
                    }
                ],
                'sub': [
                    # It used to be neccesary to supply testA/id in this
                    # situation, but now it's optional
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/id': 3,
                        'testA/subField/0/testC': 5,
                    } if nested_id_in_subsheet else {
                        'ocid': 1,
                        'id': 2,
                        'testA/subField/0/testC': 5,
                    }
                ]
            }
            )
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'testA': {
                'id': 3,
                'testB': 4,
                'subField': [{'testC': 5}]
            }}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets=OrderedDict([
                ('custom_main', [
                    OrderedDict([
                        ('ocid', 1),
                        ('id', 2),
                    ]),
                    OrderedDict([
                        ('ocid', 1),
                        ('id', 6),
                    ])
                ]),
                ('sub1', [
                    {
                        'ocid': 1,
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/testA': 4,
                    }
                ]),
                ('sub2', [
                    {
                        'ocid': 1,
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/sub2Field/0/testB': 5,
                    }
                ])
            ])
            )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 2
        assert list(unflattened[0]) == ['ocid', 'id', 'sub1Field']
        assert unflattened[0]['ocid'] == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]
        assert unflattened[1] == {'ocid':1 , 'id':6}

    def test_nested_id(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'subField/0/id': 3,
                        'subField/0/testA/id': 4,
                    }
                ]
            }
            )
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': {'id': 4}}]}
        ]

    def test_missing_columns(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'id': '',
                        'subField/0/id': 3,
                        'subField/0/testA': 4,
                    },
                    {
                        'ocid': 1,
                        'id': 2,
                        'subField/0/id': 3,
                        'subField/0/testA': 5,
                    }
                ]
            }
            )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        # Check that following lines are parsed correctly
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]},
            {'ocid': 1, 'subField': [{'id': 3, 'testA': 4}]},
        ]

    def test_unmatched_id(self, recwarn):
        spreadsheet_input = ListInput(
            sheets=OrderedDict([
                ('custom_main', [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ]),
                ('sub', [
                    {
                        'ocid': 1,
                        'id': 100,
                        'subField/0/id': 3,
                        'subField/0/testA': 4,
                    },
                    {
                        'ocid': 1,
                        'id': 2,
                        'subField/0/id': 3,
                        'subField/0/testA': 5,
                    }
                ])
            ])
            )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]},
            {'ocid': 1, 'id': 100, 'subField': [{'id': 3, 'testA': 4}]},
        ]


class TestUnflattenRollup(object):
    def test_same_rollup(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testC': 3,
                        'testA/0/id': 4,
                        'testA/0/testB': 5,
                    },
                    {
                        'ocid': 6,
                        'id': 7,
                        'testC': 8,
                        'testA/0/testB': 9,
                    }
                ],
                'testA': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/0/id': 4,
                        'testA/0/testB': 5,
                    },
                    {
                        'ocid': 6,
                        'id': 7,
                        'testA/0/testB': 9,
                    }
                ]
            },
        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'testC':3, 'testA': [{'id': 4, 'testB': 5}]},
            {'ocid': 6, 'id': 7, 'testC':8, 'testA': [
                {'testB': 9}, {'testB': 9}
                # We have duplicates here because there's no ID to merge these
                # on. This is different to the old behaviour. Issue filed at
                # https://github.com/OpenDataServices/flatten-tool/issues/99
            ]},
        ]
        # We expect no warnings
        assert recwarn.list == []

    def test_conflicting_rollup(self, recwarn):
        spreadsheet_input = ListInput(
            sheets=OrderedDict([
                ('main', [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/0/id': 3,
                        'testA/0/testB': 4
                    }
                ]),
                ('testA', [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/0/id': 3,
                        'testA/0/testB': 5,
                    }
                ])
            ])

        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert unflattened == [
            {
                'ocid': 1,
                'id': 2,
                'testA': [{
                    'id': 3,
                    'testB': 4
                    # (Since sheets are parsed in the order they appear, and the first value is used).
                }]
            }
        ]
        # We should have a warning about the conflict
        w = recwarn.pop(UserWarning)
        assert 'Conflict when merging field "testB" for ocid "1", id "2" in sheet testA: "4" != "5"' in text_type(w.message)


class TestUnflattenEmpty(object):
    def test_sub_sheet_empty(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [],
                'subsheet': [
                    {
                        'ocid': '',
                        'id': '',
                        'testA': '',
                        'testB': '',
                        'testC': '',
                        'testD': '',
                    }
                ]
            }
            )
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 0


class TestUnflattenCustomRootID(object):
    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom': 1,
                        'id': 2,
                        'subField/0/testA': 3,
                    }
                ]
            },
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'subField': [{'testA': 3}]}
        ]

    def test_nested_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom': 1,
                        'id': 2,
                        'testA/subField/0/testB': 3,
                    }
                ]
            },
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'testA': {'subField': [{'testB': 3}]}}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets=OrderedDict([
                ('custom_main', [
                    OrderedDict([
                        ('custom', 1),
                        ('id', 2),
                    ])
                ]),
                ('sub1', [
                    {
                        'custom': 1,
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/testA': 4,
                    }
                ]),
                ('sub2', [
                    {
                        'custom': 1,
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/sub2Field/0/testB': 5,
                    }
                ])
            ]),
            root_id='custom')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert list(unflattened[0]) == ['custom', 'id', 'sub1Field']
        assert unflattened[0]['custom'] == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]


class TestUnflattenNoRootID(object):
    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'id': 2,
                        'subField/0/testA': 3,
                    }
                ]
            },
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'subField': [{'testA': 3}]}
        ]

    def test_nested_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'id': 2,
                        'testA/subField/0/testB': 3,
                    }
                ]
            },
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'testA': {'subField': [{'testB': 3}]}}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets=OrderedDict([
                ('custom_main', [
                    OrderedDict([
                        ('id', 2),
                    ])
                ]),
                ('sub1', [
                    {
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/testA': 4,
                    }
                ]),
                ('sub2', [
                    {
                        'id': 2,
                        'sub1Field/0/id': 3,
                        'sub1Field/0/sub2Field/0/testB': 5,
                    }
                ])
            ]),
            root_id='')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]


from flattentool.schema import SchemaParser

def test_with_schema():
    spreadsheet_input = ListInput(
        sheets={
            'custom_main': [
                {
                    'ocid': 1,
                    'id': 2,
                    'testA': 3
                }
            ],
            'sub': [
                {
                    'ocid': 1,
                    'id': 2,
                    'testR/testB': 4 # test that we can infer this an array from schema
                }
            ]
        }
        )
    spreadsheet_input.read_sheets()

    parser = SchemaParser(
        root_schema_dict={
            'properties': {
                'id': {
                    'type': 'string',
                },
                'testR': {
                    'type': 'array',
                    'items': {
                        'type': 'object'
                    }
                },
            }
        },
        root_id='ocid',
        rollup=True
    )
    parser.parse()
    spreadsheet_input.parser = parser
    assert list(spreadsheet_input.unflatten()) == [{
        'ocid': 1,
        'id': '2', # check that we join correctly when this gets converted to a
                   # string because of the schema type
        'testA': 3,
        'testR': [{
            'testB': 4
        }]
    }]

