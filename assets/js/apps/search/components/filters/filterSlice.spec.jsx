import reducer, { updateTypeAttribute } from "./filterSlice";
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
                        data_type: "STRING",
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
                        data_type: "STRING",
                        id: "createdDate",
                        full_name: "Created Date",
                        value: "2020-01-01"
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
    activeFilters: [{
        kind: 'typeAttribute',
        target: ['datasets','createdDate'],
        type: 'STRING'
    }],
    isLoading: false,
    error: null
};

it('can add filter for type attributes', () => {
    const type = "experiments",
        attribute = "createdDate",
        newValue = "2020-01-23",
        expectedNewState = createNextState(mockStoreState, draft => {
            draft.activeFilters.push({
                kind: 'typeAttribute',
                target: [type, attribute]
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
            draft.activeFilters = [];
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
        newValue = "2020-03-03",
        expectedNewState = createNextState(mockStoreState, draft => {
            draft.types.byId[type].attributes.createdDate.value = newValue;
        });
    expect(reducer(mockStoreState, updateTypeAttribute({
        typeId: type,
        attributeId: attribute,
        value: newValue
    }))).toEqual(expectedNewState);
});