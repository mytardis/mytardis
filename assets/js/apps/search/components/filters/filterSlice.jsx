import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";
import TYPE_ATTRIBUTES from "./typeAttributes.json";

const initialState = {
    types: TYPE_ATTRIBUTES,
    typeSchemas: null,
    schemas: {
        byId: null,
        allIds: []
    },
    activeFilters: [],
    isLoading: true,
    error: null
}

const mapSchemasById = (schemasByType) => {
    // Generate a hashmap of schemas by their id, so we can look up
    // schemas by id.
    const schemasById = {},
        allIds = [];
    for (let type in schemasByType) {
        for (let schemaId in schemasByType[type]) {
            schemasById[schemaId] = schemasByType[type][schemaId];
            allIds.push(schemaId);
        }
    }
    return { byId: schemasById, allIds: allIds };
}

const mapSchemaIdToType = (schemasByType) => {
    const typeSchemas = {};
    for (let type in schemasByType) {
        typeSchemas[type] = [];
        for (let schemaId in schemasByType[type]) {
            typeSchemas[type].push(schemaId);
        }
    }
    return typeSchemas;
}

const findFilter = (filterList, fieldToFind) => {
    // Check if the filter is in the list by seeing 
    // if they are the same kind and the target is the same
    return filterList.findIndex(field => (
        typeof fieldToFind.kind == "string" &&
        fieldToFind.kind == field.kind &&
        Array.isArray(fieldToFind.target) &&
        field.target.every((part, idx) => (
            part == fieldToFind.target[idx]
        ))
    ));
}

const addToActiveFilters = (state,fieldInfo) => {
    const activeIndex = findFilter(
        state.activeFilters, fieldInfo
    );
    if (activeIndex === -1) {
        state.activeFilters.push(fieldInfo);
    }
}

const removeFromActiveFilters = (state, fieldInfo) => {
    const activeIndex = findFilter(
        state.activeFilters, fieldInfo
    );
    if (activeIndex === -1) {
        return;
    }
    // Remove from active filters list
    state.activeFilters.splice(activeIndex, 1);
}

// Selectors for different kinds of fields 
export const typeAttrSelector = (filterSlice, typeId, attributeId) => {
    return filterSlice.types
        .byId[typeId]
        .attributes
        .byId[attributeId];
}

export const allTypeAttrIdsSelector = (filterSlice, typeId) => {
    return filterSlice.types
        .byId[typeId]
        .attributes
        .allIds;
}

export const schemaParamSelector = (filterSlice, schemaId, paramId) => {
    return filterSlice.schemas
        .byId[schemaId]
        .parameters[paramId];
};

const updateTypeAttributeReducer = (state, {payload}) => {
    const { typeId, attributeId, value } = payload;
    const attribute = typeAttrSelector(state, typeId, attributeId);
    let target = [typeId, attributeId];
    if (attribute.nested_target) {
        // If there is a nested target field on the attribute, we add that to the end.
        // This is useful if we need to query a nested field.
        target = target.concat(attribute.nested_target);
    }
    const fieldInfo = {
        kind: "typeAttribute",
        target: target
    };
    attribute.value = value;
    if (value === null) {
        // If the new value is null, remove it from activeFilter list.
        removeFromActiveFilters(state,fieldInfo);
    } else {
        addToActiveFilters(state,fieldInfo);
    }
};

const updateSchemaParameterReducer = (state, {payload}) => {
    const { schemaId, parameterId, value } = payload;
    const parameter = schemaParamSelector(state, schemaId, parameterId);
    const fieldInfo = {
        kind: "schemaParameter",
        target: [schemaId, parameterId]
    };
    parameter.value = value;
    if (value === null) {
        removeFromActiveFilters(state, fieldInfo);
    } else {
        addToActiveFilters(state, fieldInfo);
    }
}

const updateActiveSchemasReducer = (state, {payload}) => {
    const { typeId, value } = payload;
    const activeSchemas = typeAttrSelector(state, typeId, "schema");
    const fieldInfo = {
        kind: "typeAttribute",
        target: [typeId,"schema"]
    };
    // Get the current active schema value. If null, then all schemas apply.
    const currActiveSchemas = activeSchemas.value ? activeSchemas.value.content : state.typeSchemas[typeId];
    // Same for new active schema value.
    const newActiveSchemas = value ? value.content : state.typeSchemas[typeId];
    // Find the schemas that will no longer be active.
    const diffSchemas = currActiveSchemas.filter(schema => (!newActiveSchemas.includes(schema)));
    // Then, find the filters on parameters that belong to the schema if any.
    // They need to be removed too.
    const parametersToRemove = state.activeFilters.filter(
        filter => (
            filter.kind === "schemaParameter" && 
            diffSchemas.includes(filter.target[0])
        )
    );
    
    // Now, update the active schemas field
    activeSchemas.value = value;
    if (value === null) {
        // If the new value is null, remove it from activeFilter list.
        removeFromActiveFilters(state,fieldInfo);
    } else {
        addToActiveFilters(state,fieldInfo);
    }

    // Finally, remove all the schema parameters which belong to schemas that are no longer active.
    parametersToRemove.forEach((paramToRemove) => {
        updateSchemaParameterReducer(state,{payload: {
            schemaId: paramToRemove.target[0],
            parameterId: paramToRemove.target[1],
            value: null
        }});
    });
}

const resetFiltersReducer = (state) => {
    const activeFilters = Array.from(state.activeFilters);
    activeFilters.forEach(({ kind, target }) => {
        switch (kind) {
            case "typeAttribute":
                if (target[1] === "schema") {
                    updateActiveSchemasReducer(state, {
                        payload: {
                            typeId: target[0],
                            value: null
                        }
                    })
                } else {
                    updateTypeAttributeReducer(state, {
                        payload: {
                            typeId: target[0],
                            attributeId: target[1],
                            value: null
                        }
                    })
                }
                break;
            case "schemaParameter":
                updateSchemaParameterReducer(state, {
                    payload: {
                        schemaId: target[0],
                        parameterId: target[1],
                        value: null
                    }
                })
                break;
        }
    });
};

const filters = createSlice({
    name: 'filters',
    initialState,
    reducers: {
        getFiltersStart: (state, { payload }) => {
            state.isLoading = true;
            state.error = null;
        },
        getFiltersSuccess: (state, { payload }) => {
            state.schemas = mapSchemasById(payload);
            state.typeSchemas = mapSchemaIdToType(payload);
            state.isLoading = false;
            state.error = null;
        },
        getFiltersFailure: (state, { payload:error }) => {
            console.error("Error", error);
            state.isLoading = false;
            state.error = error.toString();
        },
        updateTypeAttribute: updateTypeAttributeReducer,
        updateSchemaParameter: updateSchemaParameterReducer,
        updateActiveSchemas: updateActiveSchemasReducer,
        resetFilters: resetFiltersReducer,
        updateFiltersByQuery: (state, { payload:filterQuery }) => {
            // First, clear all previous filters to start off with a fresh slate.
            // TODO Optimise this if necessary when there are a lot of filters.
            resetFiltersReducer(state);
            if (!filterQuery || !filterQuery.content) {
                return;
            }
            // Take the filter list from the content of the root "and" query.
            const filterList = filterQuery.content;
            filterList.forEach(filter => {
                const {kind ,target, content, op} = filter,
                    value = {op, content};
                let currValue;
                switch (kind) {
                    case "typeAttribute":
                        // We may have added value for this field earlier in the iteration.
                        currValue = typeAttrSelector(state,target[0],target[1]).value;
                        if (currValue) {
                            if (!Array.isArray(currValue)) {
                                currValue = [currValue];
                            }
                            currValue.push(value);
                        } else {
                            if (target[1] === "schema") {
                                updateActiveSchemasReducer(state,{payload: {typeId: target[0], value}});
                            } else {
                                updateTypeAttributeReducer(state,{payload: {typeId: target[0], attributeId: target[1], value}})
                            }
                        }
                        break;
                    case "schemaParameter":
                        currValue = schemaParamSelector(state,target[0],target[1]).value;
                        if (currValue) {
                            if (!Array.isArray(currValue)) {
                                currValue = [currValue];
                            }
                            currValue.push(value);
                        } else {
                            updateSchemaParameterReducer(state, {payload: {schemaId: target[0], parameterId: target[1], value}});
                        }
                        break;
                    default:
                        console.error("Unhandled filter kind while updating filters by filter query.");
                }
            });
        }
    }
});

const fetchFilterList = () => {
    return fetch(`/api/v1/search_get-schemas/`, {
        method: "get",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken')
        }
    }).then(response => {
        if (!response.ok) {
            throw new Error("An error on the server occurred.")
        }
        return response.json();
    }).then(responseJSON => (responseJSON.objects[0].schemas));
};

export const {
    getFiltersStart,
    getFiltersSuccess,
    getFiltersFailure,
    updateTypeAttribute,
    updateSchemaParameter,
    updateActiveSchemas,
    resetFilters,
    updateFiltersByQuery
} = filters.actions;

export const buildFilterQuery = (filters) => {
    const allFilters = filters.activeFilters.map(filterFieldInfo => {
        const { kind, target } = filterFieldInfo;
        let filter;
        switch (kind) {
            case "typeAttribute":
                filter = typeAttrSelector(filters,target[0],target[1]);
                break;                
            case "schemaParameter":
                filter = schemaParamSelector(filters,target[0],target[1]);
                break;
            default:
                break;
        }
        const filterValue = Array.isArray(filter.value) ? filter.value : [filter.value],
            filterType = {type: filter.data_type};
        return filterValue.map(value => (
            Object.assign({},filterFieldInfo, filterType, value)
        ));
    // "Flatten" the array so filters with multiple values are in same array.
    }).reduce((acc, val) => acc.concat(val), []);
    if (allFilters.length === 0) {
        return null;
    }
    return {
        content: allFilters,
        op: "and"
    };
}

export const initialiseFilters = () => (dispatch) => {
    dispatch(getFiltersStart());
    return fetchFilterList().then(filters => {
        dispatch(getFiltersSuccess(filters));
    }).catch((e) => {
        dispatch(getFiltersFailure(e))
    });
}

export default filters.reducer;