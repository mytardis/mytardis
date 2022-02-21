/* eslint-disable camelcase */
/*eslint-env jest*/

import reducer, { 
    updateTypeAttribute,
    updateSchemaParameter,
    schemaSelector,
    updateActiveSchemas,
    updateFiltersByQuery,
    buildFilterQuery
} from "./filterSlice";
import { createNextState } from "@reduxjs/toolkit";

const mockStoreState = {
    types: {
        byId: {
            project: {
                attributes: {
                    byId: {
                        schema: {
                            "data_type": "STRING",
                            "id": "schema",
                            "full_name": "Schema"
                        },
                    },
                    allIds: ["schema"]
                }
            },
            experiment: {
                attributes: {
                    byId: {
                        schema: {
                            value: {
                                op: "is",
                                content: ["1"]
                            },
                            "data_type": "STRING",
                            "id": "schema",
                            "full_name": "Schema"
                        },
                        createdDate: {
                            data_type: "DATETIME",
                            id: "createdDate",
                            full_name: "Created Date",
                            value: null
                        }
                    },
                    allIds: ["schema", "createdDate"]
                }
            },
            dataset: {
                attributes: {
                    byId: {
                        schema: {
                            "data_type": "STRING",
                            "id": "schema",
                            "full_name": "Schema"

                        },
                        createdDate: {
                            data_type: "DATETIME",
                            id: "createdDate",
                            full_name: "Created Date",
                            value: { op: ">=", content: "2020-01-01" }
                        }
                    },
                    allIds: ["schema", "createdDate"]
                }
            },
            datafile: {
                attributes: {
                    byId: {
                        schema: {
                            "data_type": "STRING",
                            "id": "schema",
                            "full_name": "Schema"
                        }
                    },
                    allIds: ["schema"]
                }
            }
        },
        allIds: [
            "project",
            "experiment",
            "dataset",
            "datafile"
        ]
    },
    typeSchemas: {

        dataset: [
            "2",
            "14"
        ],
        experiment: [
            "1",
            "4"
        ],
    },
    schemas: {
        byId: {
            "1": {
                id: "1",
                parameters: {
                    "1": {
                        data_type: "STRING",
                        full_name: "Parameter 1",
                        id: "1"
                    },
                    "2": {
                        data_type: "STRING",
                        full_name: "Parameter 2",
                        id: "2"
                    },
                    "3": {
                        data_type: "STRING",
                        full_name: "Sensitive Parameter",
                        id: "3"
                    },
                    "10": {
                        data_type: "DATETIME",
                        full_name: "Datetime Parameter",
                        id: "10"
                    },
                    "11": {
                        data_type: "NUMERIC",
                        full_name: "Numeric Parameter",
                        id: "11"
                    }
                },
                schema_name: "Schema_ACL_experiment",
                type: "experiment"
            },
            "2": {
                id: "2",
                parameters: {
                    "4": {
                        data_type: "STRING",
                        full_name: "Parameter 1",
                        id: "4",
                        value: {
                            op: "contains",
                            content: "RNSeq"
                        }
                    },
                    "5": {
                        data_type: "STRING",
                        full_name: "Parameter 2",
                        id: "5"
                    },
                    "6": {
                        data_type: "STRING",
                        full_name: "Sensitive Parameter",
                        id: "6"
                    }
                },
                schema_name: "Schema_ACL_dataset",
                type: "dataset"
            },
            "4": {
                id: "4",
                parameters: {
                    "12": {
                        data_type: "STRING",
                        full_name: "Parameter 1",
                        id: "12"
                    },
                    "13": {
                        data_type: "NUMERIC",
                        full_name: "Numerical Parameter",
                        id: "13"
                    }
                },
                schema_name: "Schema_ACL_datafile2",
                type: "datafile"
            },
            "14": {
                id: "14",
                parameters: {
                    "20": {
                        data_type: "STRING",
                        full_name: "project_purpose",
                        id: "20"
                    },
                    "37": {
                        data_type: "STRING",
                        full_name: "project_purpose",
                        id: "37"
                    }
                },
                schema_name: "Default Project",
                type: "project"
            }
        },
        allIds: [
            "2",
            "1",
            "4",
            "14"
        ]
    },
    activeFilters: {
        project: [], 
        experiment: [{
            kind: "typeAttribute",
            target: ["experiment", "schema"],
        }],
        dataset: [
            {
                kind: "typeAttribute",
                target: ["dataset", "createdDate"],
            }, 
            {
                kind: "schemaParameter",
                target: ["2", "4"]
            }
        ],
        datafile: []
    },
    isLoading: false,
    error: null
};

describe("Type attribute reducer", () => {

    it("can add filter for type attributes", () => {
        const type = "experiment",
            attribute = "createdDate",
            newValue = { op: ">=", content: "2020-01-23" },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters[type].push({
                    kind: "typeAttribute",
                    target: [type, attribute]
                });
                draft.types.byId[type].attributes.byId.createdDate.value = newValue;
            });
        expect(reducer(mockStoreState, updateTypeAttribute({
            typeId: type,
            attributeId: attribute,
            value: newValue
        }))).toEqual(expectedNewState);
    });

    it("can remove filter for type attributes", () => {
        const type = "dataset",
            attribute = "createdDate",
            newValue = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters[type] = draft.activeFilters[type].filter(
                    f => (
                        f.target[0] !== "dataset" && f.target[1] !== "createdDate"
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

    it("can update filter value for type attributes", () => {
        const type = "dataset",
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

describe("Schema parameter reducer", () => {
    it("can add filter value for schema parameters", () => {
        const schema = "1",
            parameter = "2",
            newValue = { op: "contains", content: "Blue" },
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters.experiment.push({
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

    it("can remove filter value for schema parameters", () => {
        const schema = "2",
            parameter = "4",
            newValue = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.activeFilters.dataset = draft.activeFilters.dataset.filter(
                    f => (
                        f.target[0] !== "2" && f.target[1] !== "4"
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

    it("can update filter value for schema parameters", () => {
        const schema = "2",
            parameter = "4",
            newValue = { op: "contains", content: "RNSeq" },
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

describe("Active schema reducer", () => {
    it("can add active schema", () => {
        const typeId = "dataset",
            value = {op: "is", content: ["2"]},
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters[typeId].push({
                    kind: "typeAttribute",
                    target: [typeId, "schema"]
                });
            });
        expect(reducer(mockStoreState, updateActiveSchemas({
            typeId,
            value
        }))).toEqual(expectedNewState);
    });

    it("can remove active schema", () => {
        const typeId = "experiment",
            value = null,
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters[typeId] = draft.activeFilters[typeId].filter( filter => (
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

    it("can update active schema along with associated parameters", () => {
        const typeId = "dataset",
            value = {op: "is", content: ["14"]},
            expectedNewState = createNextState(mockStoreState, draft => {
                draft.types.byId[typeId].attributes.byId.schema.value = value;
                draft.activeFilters[typeId].push({
                    kind: "typeAttribute",
                    target: [typeId, "schema"]
                });
                // The parameter associated with the schema ID "2" should now be removed
                // Because schema ID "2" is also a dataset schema.
                // By setting the active schema to only 14, this implicitly removes schema
                // ID "2". 
                draft.activeFilters[typeId] = draft.activeFilters[typeId].filter( filter => 
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

});

describe("Schema parameter selector", () => {
    it("can fetch a schema parameter", () => {
        const parameter = schemaSelector(mockStoreState, "1").parameters["2"];
        expect(parameter.full_name).toEqual("Parameter 2");
        expect(parameter.data_type).toEqual("STRING");
    });
});

describe("Reset and update filter state by query body", () => {
    const twoValueQuery = {
        content: [
            {
                kind: "schemaParameter",
                target: [
                    "1",
                    "11"
                ],
                type: "NUMERIC",
                op: ">=",
                content: "5"
            },
            {
                kind: "schemaParameter",
                target: [
                    "1",
                    "11"
                ],
                type: "NUMERIC",
                op: "<=",
                content: "15"
            }
        ],
        op: "and"
    };
    it("can reset and update filters with two values", () => {
        const expectedNewState = createNextState(mockStoreState, draft => {
            // The current values should be now null.
            draft.types.byId.dataset.attributes.byId.createdDate.value = null;
            draft.types.byId.experiment.attributes.byId.schema.value = null;
            draft.schemas.byId["2"].parameters["4"].value = null;
            draft.schemas.byId["1"].parameters["11"].value = [
                {
                    op: ">=", content: "5"
                }, {
                    op: "<=", content: "15"
                }
            ];
            draft.activeFilters = {project: [], dataset: [], datafile: [], experiment: [{kind: "schemaParameter", target: ["1", "11"]}]};
        });
        expect(reducer(mockStoreState, updateFiltersByQuery(twoValueQuery))).toEqual(expectedNewState);
    });
});

describe("Filter query builder", ()=> {
    it("should only include relevant filters in single type queries", () => {
        const expectedValue = {
            op: "and",
            content: [
                {
                    kind: "typeAttribute",
                    target: ["experiment", "schema"],
                    type: "STRING",
                    op: "is",
                    content: ["1"]
                },
                
            ]
        };
        expect(buildFilterQuery(mockStoreState, "experiment")).toEqual(expectedValue);
    });
    it("should include all filters in queries that include all types", () => {
        const expectedValue = {
            op: "and",
            content: [
                {
                    kind: "typeAttribute",
                    target: ["experiment", "schema"],
                    type: "STRING",
                    op: "is",
                    content: ["1"]
                },
                {
                    kind: "typeAttribute",
                    target: ["dataset", "createdDate"],
                    type: "DATETIME",
                    op: ">=",
                    content: "2020-01-01"
                }, 
                {
                    kind: "schemaParameter",
                    target: ["2", "4"],
                    type: "STRING",
                    op: "contains",
                    content: "RNSeq"
                }
            ]
        };
        expect(buildFilterQuery(mockStoreState)).toEqual(expectedValue);
    });
});