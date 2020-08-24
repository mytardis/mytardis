import reducer, { 
    updateTypeAttribute,
    updateSchemaParameter,
    schemaParamSelector,
    updateActiveSchemas,
    updateFiltersByQuery
} from "./filterSlice";
import { createNextState } from "@reduxjs/toolkit";

const mockStoreState = {
    types: {
        byId: {
            projects: {
                attributes: {
                    byId: {
                        schema: {},
                    },
                    allIds: ["schema"]
                }
            },
            experiments: {
                attributes: {
                    byId: {
                        schema: {
                            value: {
                                op: "is",
                                content: ["1"]
                            }
                        },
                        createdDate: {
                            data_type: "DATETIME",
                            id: "createdDate",
                            full_name: "Created Date",
                            value: null
                        }
                    },
                    allIds: ["schema","createdDate"]
                }
            },
            datasets: {
                attributes: {
                    byId: {
                        schema: {},
                        createdDate: {
                            data_type: "DATETIME",
                            id: "createdDate",
                            full_name: "Created Date",
                            value: { op: ">=", content: "2020-01-01" }
                        }
                    },
                    allIds: ["schema","createdDate"]
                }
            },
            datafiles: {
                attributes: {
                    byId: {
                        schema: {}
                    },
                    allIds: ["schema"]
                }
            }
        },
        allIds: [
            'projects',
            'experiments',
            'datasets',
            'datafiles'
        ]
    },
    typeSchemas: {

        datasets: [
            '2',
            '14'
        ],
        experiments: [
            '1',
            '4'
        ],
    },
    schemas: {
        byId: {
            '1': {
                id: '1',
                parameters: {
                    '1': {
                        data_type: 'STRING',
                        full_name: 'Parameter 1',
                        id: '1'
                    },
                    '2': {
                        data_type: 'STRING',
                        full_name: 'Parameter 2',
                        id: '2'
                    },
                    '3': {
                        data_type: 'STRING',
                        full_name: 'Sensitive Parameter',
                        id: '3'
                    },
                    '10': {
                        data_type: 'DATETIME',
                        full_name: 'Datetime Parameter',
                        id: '10'
                    },
                    '11': {
                        data_type: 'NUMERIC',
                        full_name: 'Numeric Parameter',
                        id: '11'
                    }
                },
                schema_name: 'Schema_ACL_experiment',
                type: 'experiments'
            },
            '2': {
                id: '2',
                parameters: {
                    '4': {
                        data_type: 'STRING',
                        full_name: 'Parameter 1',
                        id: '4',
                        value: {
                            op: "contains",
                            content: "RNSeq"
                        }
                    },
                    '5': {
                        data_type: 'STRING',
                        full_name: 'Parameter 2',
                        id: '5'
                    },
                    '6': {
                        data_type: 'STRING',
                        full_name: 'Sensitive Parameter',
                        id: '6'
                    }
                },
                schema_name: 'Schema_ACL_dataset',
                type: 'datasets'
            },
            '4': {
                id: '4',
                parameters: {
                    '12': {
                        data_type: 'STRING',
                        full_name: 'Parameter 1',
                        id: '12'
                    },
                    '13': {
                        data_type: 'NUMERIC',
                        full_name: 'Numerical Parameter',
                        id: '13'
                    }
                },
                schema_name: 'Schema_ACL_datafile2',
                type: 'datafiles'
            },
            '14': {
                id: '14',
                parameters: {
                    '20': {
                        data_type: 'STRING',
                        full_name: 'project_purpose',
                        id: '20'
                    },
                    '37': {
                        data_type: 'STRING',
                        full_name: 'project_purpose',
                        id: '37'
                    }
                },
                schema_name: 'Default Project',
                type: 'projects'
            }
        },
        allIds: [
            '2',
            '1',
            '4',
            '14'
        ]
    },
    activeFilters: [{
        kind: 'typeAttribute',
        target: ['datasets', 'createdDate'],
    }, {
        kind: 'schemaParameter',
        target: ['2', '4'],
    }, {
        kind: 'typeAttribute',
        target: ['experiments','schema'],
    }],
    isLoading: false,
    error: null
};

describe('Type attribute reducer', () => {

    it('can add filter for type attributes', () => {
        const type = "experiments",
            attribute = "createdDate",
            newValue = { op: ">=", content: "2020-01-23" },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters.push({
                    kind: 'typeAttribute',
                    target: [type, attribute]
                });
                draft.types.byId[type].attributes.byId.createdDate.value = newValue
            });
        expect(reducer(mockStoreState, updateTypeAttribute({
            typeId: type,
            attributeId: attribute,
            value: newValue
        }))).toEqual(expectedNewState);
    });

    it('can remove filter for type attributes', () => {
        const type = "datasets",
            attribute = "createdDate",
            newValue = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters = draft.activeFilters.filter(
                    f => (
                        f.target[0] != "datasets" && f.target[1] != "createdDate"
                    )
                );
                draft.types.byId[type].attributes.byId.createdDate.value = newValue;
            });
        expect(reducer(mockStoreState, updateTypeAttribute({
            typeId: type,
            attributeId: attribute,
            value: newValue
        }))).toEqual(expectedNewState);
    });

    it('can update filter value for type attributes', () => {
        const type = "datasets",
            attribute = "createdDate",
            newValue = { op: ">=", content: "2020-03-03" },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[type].attributes.byId.createdDate.value = newValue;
            });
        expect(reducer(mockStoreState, updateTypeAttribute({
            typeId: type,
            attributeId: attribute,
            value: newValue
        }))).toEqual(expectedNewState);
    });
});

describe('Schema parameter reducer', () => {
    it('can add filter value for schema parameters', () => {
        const schema = "1",
            parameter = "2",
            newValue = { op: 'contains', content: 'Blue' },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters.push({
                    kind: "schemaParameter",
                    target: [schema, parameter]
                });
                draft.schemas.byId[schema].parameters[parameter].value = newValue;
            });
        expect(reducer(mockStoreState, updateSchemaParameter({
            schemaId: schema,
            parameterId: parameter,
            value: newValue
        }))).toEqual(expectedNewState);
    });

    it('can remove filter value for schema parameters', () => {
        const schema = "2",
            parameter = "4",
            newValue = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters = draft.activeFilters.filter(
                    f => (
                        f.target[0] != "2" && f.target[1] != "4"
                    )
                );
                draft.schemas.byId[schema].parameters[parameter].value = newValue;
            });
        expect(reducer(mockStoreState, updateSchemaParameter({
            schemaId: schema,
            parameterId: parameter,
            value: newValue
        }))).toEqual(expectedNewState);
    });

    it('can update filter value for schema parameters', () => {
        const schema = "2",
            parameter = "4",
            newValue = { op: 'contains', content: 'RNSeq' },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.schemas.byId[schema].parameters[parameter].value = newValue;
            });
        expect(reducer(mockStoreState, updateSchemaParameter({
            schemaId: schema,
            parameterId: parameter,
            value: newValue
        }))).toEqual(expectedNewState);
    });

});

describe('Active schema reducer', () => {
    it('can add active schema', () => {
        const typeId = "datasets",
            value = {op: "is",content:["2"]},
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters.push({
                    kind: "typeAttribute",
                    target: [typeId, "schema"]
                });
        });
        expect(reducer(mockStoreState, updateActiveSchemas({
            typeId,
            value
        }))).toEqual(expectedNewState);
    });

    it('can remove active schema', () => {
        const typeId = "experiments",
            value = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters = draft.activeFilters.filter( filter => (
                    !(
                        filter.kind === "typeAttribute" &&
                        filter.target[0] === typeId &&
                        filter.target[1] === "schema"
                    )
                ));
            });
            expect(reducer(mockStoreState, updateActiveSchemas({
                typeId,
                value
            }))).toEqual(expectedNewState);    
    });

    it('can update active schema along with associated parameters', () => {
        const typeId = "datasets",
            value = {op: "is",content:["14"]},
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters.push({
                    kind: "typeAttribute",
                    target: [typeId, "schema"]
                });
                // The parameter associated with the schema ID "2" should now be removed
                // Because schema ID "2" is also a dataset schema.
                // By setting the active schema to only 14, this implicitly removes schema
                // ID "2". 
                draft.activeFilters = draft.activeFilters.filter( filter => 
                    (!(
                        filter.kind === "schemaParameter" &&
                        filter.target[0] === "2" &&
                        filter.target[1] === "4"
                    ))
                );
                draft.schemas.byId["2"].parameters["4"].value = null;
        });
        expect(reducer(mockStoreState, updateActiveSchemas({
            typeId,
            value
        }))).toEqual(expectedNewState);
    });

})

describe('Schema parameter selector', () => {
    it('can fetch a schema parameter', () => {
        const parameter = schemaParamSelector(mockStoreState, "1", "2");
        expect(parameter.full_name).toEqual('Parameter 2');
        expect(parameter.data_type).toEqual('STRING');
    })
})

describe('Reset and update filter state by query body', () => {
    const twoValueQuery = {
        content: [
            {
                kind: 'schemaParameter',
                target: [
                    '1',
                    '11'
                ],
                type: 'NUMERIC',
                op: '>=',
                content: '5'
            },
            {
                kind: 'schemaParameter',
                target: [
                    '1',
                    '11'
                ],
                type: 'NUMERIC',
                op: '<=',
                content: '15'
            }
        ],
        op: 'and'
    };
    it('can reset and update filters with two values', () => {
        const expectedNewState = createNextState(mockStoreState, draft => {
            // The current values should be now null.
            draft.types.byId['datasets'].attributes.byId['createdDate'].value = null;
            draft.types.byId['experiments'].attributes.byId['schema'].value = null;
            draft.schemas.byId['2'].parameters['4'].value = null;
            draft.schemas.byId['1'].parameters['11'].value = [
                {
                    op: '>=', content: '5'
                },{
                    op: '<=', content: '15'
                }
            ];
            draft.activeFilters = [{kind: 'schemaParameter', target: ['1','11']}];
        });
        expect(reducer(mockStoreState,updateFiltersByQuery(twoValueQuery))).toEqual(expectedNewState);
    })
})