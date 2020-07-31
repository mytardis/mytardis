import reducer, { updateTypeAttribute, updateSchemaParameter, schemaParamSelector } from "./filterSlice";
import { createNextState } from "@reduxjs/toolkit";

const mockStoreState = {
    types: {
        byId: {
            projects: {
                attributes: {
                    schema: {},
                }
            },
            experiments: {
                attributes: {
                    schema: {},
                    createdDate: {
                        data_type: "DATETIME",
                        id: "createdDate",
                        full_name: "Created Date",
                        value: null
                    }
                }
            },
            datasets: {
                attributes: {
                    schema: {},
                    createdDate: {
                        data_type: "DATETIME",
                        id: "createdDate",
                        full_name: "Created Date",
                        value: { op: ">=", content: "2020-01-01" }
                    }
                }
            },
            datafiles: {
                attributes: {
                    schema: {}
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
            '1'
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
            '14'
        ]
    },
    activeFilters: [{
        kind: 'typeAttribute',
        target: ['datasets', 'createdDate'],
        type: 'STRING'
    },{
        kind: 'schemaParameter',
        target: ['2','4'],
        type: 'STRING'
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
                    target: [type, attribute],
                    type: "DATETIME"
                });
                draft.types.byId[type].attributes.createdDate.value = newValue
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
                draft.types.byId[type].attributes.createdDate.value = newValue;
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
                draft.types.byId[type].attributes.createdDate.value = newValue;
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
            newValue = {op:'contains', content: 'Blue'},
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters.push({
                    kind: "schemaParameter",
                    target: [schema,parameter],
                    type: "STRING"
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
            newValue = {op:'contains', content: 'RNSeq'},
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

describe('Schema parameter selector', () => {
    it('can fetch a schema parameter', () => {
        const parameter = schemaParamSelector(mockStoreState,"1","2");
        expect(parameter.full_name).toEqual('Parameter 2');
        expect(parameter.data_type).toEqual('STRING');
    })
})