import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";
import TYPE_ATTRIBUTES from "./typeAttributes.json";

const initialState = {
    types: TYPE_ATTRIBUTES,
    typeSchemas: null,
    schemas: {
        byId: {},
        allIds: []
    },
    activeFilters: { project: [], experiment: [], dataset: [], datafile: [] },
    isLoading: true,
    error: null
};

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

const addToActiveFilters = (state,fieldInfo, typeId) => {
    const activeIndex = findFilter(
        state.activeFilters[typeId], fieldInfo
    );
    if (activeIndex === -1) {
        state.activeFilters[typeId].push(fieldInfo);
    }
}

const removeFromActiveFilters = (state, fieldInfo, typeId) => {
    const activeIndex = findFilter(
        state.activeFilters[typeId], fieldInfo
    );
    if (activeIndex === -1) {
        return;
    }
    // Remove from active filters list
    state.activeFilters[typeId].splice(activeIndex, 1);
}

export const typeSelector = (filtersSlice, typeId) => filtersSlice.types.byId[typeId];

export const typeAttrFilterValueSelector = (filtersSlice, typeId, attributeId) => {
    const value = typeSelector(filtersSlice, typeId).attributes.byId[attributeId].value;
    return value;
};

export const schemaSelector = (filterSlice, schemaId) => {
    return filterSlice.schemas
        .byId[schemaId];
};

/**
 *  Selector for the filter value for a schema parameter.
 * @param {*} filtersSlice Redux filters slice
 * @param {string} schemaId schema ID
 * @param {string} paramId parameter ID
 */
export const schemaParamFilterValueSelector = (filtersSlice, schemaId, paramId) => {
    const value = schemaSelector(filtersSlice, schemaId).parameters[paramId].value;
    return value;
};

const updateTypeAttributeReducer = (state, {payload}) => {
    const { typeId, attributeId, value } = payload;
    const attribute = typeSelector(state, typeId).attributes.byId[attributeId];
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
        removeFromActiveFilters(state,fieldInfo, typeId);
    } else {
        addToActiveFilters(state,fieldInfo,typeId);
    }
};

const updateSchemaParameterReducer = (state, {payload}) => {
    const { schemaId, parameterId, value } = payload;
    const schema = schemaSelector(state, schemaId);
    const typeId = schema.type;
    const parameter = schema.parameters[parameterId];
    const fieldInfo = {
        kind: "schemaParameter",
        target: [schemaId, parameterId]
    };
    parameter.value = value;
    if (value === null) {
        removeFromActiveFilters(state, fieldInfo, typeId);
    } else {
        addToActiveFilters(state, fieldInfo, typeId);
    }
}

const updateActiveSchemasReducer = (state, {payload}) => {
    const { typeId, value } = payload;
    
    const activeSchemasVal = typeAttrFilterValueSelector(state, typeId, "schema");
    const fieldInfo = {
        kind: "typeAttribute",
        target: [typeId, "schema"],
    };
    // Get the current active schema value. If null, then all schemas apply.
    const currActiveSchemas = activeSchemasVal ? activeSchemasVal.content : state.typeSchemas[typeId];
    // Same for new active schema value.
    const newActiveSchemas = value ? value.content : state.typeSchemas[typeId];
    // Find the schemas that will no longer be active.
    const diffSchemas = currActiveSchemas.filter(schema => (!newActiveSchemas.includes(schema)));
    // Then, find the filters on parameters that belong to the schema if any.
    // They need to be removed too.
    const parametersToRemove = state.activeFilters[typeId].filter(
        filter => (
            filter.kind === "schemaParameter" && 
            diffSchemas.includes(filter.target[0])
        )
    );
    
    // Now, update the active schemas field
    typeSelector(state, typeId).attributes.byId.schema.value = value;
    if (value === null) {
        // If the new value is null, remove it from activeFilter list.
        removeFromActiveFilters(state,fieldInfo, typeId);
    } else {
        addToActiveFilters(state,fieldInfo, typeId);
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
    // Because active filters are grouped by type,
    // we iterate through each of the type lists
    // and reset them.
    const allTypes = state.types.allIds;
    allTypes.forEach(typeId => {
        const filtersForType = state.activeFilters[typeId];
        const activeFilters = Array.from(filtersForType);
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
    })
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
                let currValue, newValue;
                switch (kind) {
                    // TODO Refactor this function so that logic for 
                    // adding filter values to existing can be reused
                    // by both typeAttribute and schemaParameter.
                    case "typeAttribute":
                        // We may have added value for this field earlier in the iteration.
                        currValue = typeAttrFilterValueSelector(state,target[0],target[1]);
                        if (!currValue) {
                            newValue = value;
                        } else {
                            if (Array.isArray(currValue)){
                                currValue.push(value);
                                newValue = currValue;
                            } else {
                                newValue = [currValue, value];
                            }
                        }
                        if (target[1] === "schema") {
                            updateActiveSchemasReducer(state, { payload: { typeId: target[0], newValue } });
                        } else {
                            updateTypeAttributeReducer(state, { payload: { typeId: target[0], attributeId: target[1], value: newValue } })
                        }
                        break;
                    case "schemaParameter":
                        currValue = schemaParamFilterValueSelector(state,target[0],target[1]);
                        if (!currValue) {
                            newValue = value;
                        } else {
                            if (Array.isArray(currValue)){
                                currValue.push(value);
                                newValue = currValue;
                            } else {
                                newValue = [currValue, value];
                            }
                        }
                        updateSchemaParameterReducer(state, { payload: { schemaId: target[0], parameterId: target[1], value: newValue } });
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

/**
 * Given a MyTardis object type, return the type itself and object types
 * which affect the search results for that type.
 * In MyTardis search, cross filtering is applied, such that results
 * for an object type depends on filters on that type and types above
 * it in the hierachy.
 * @param {string} type - one of the MyTardis object types.
 */
const getCrossFilteredTypes = (type) => {
    switch (type) {
        case "project":
            return ["project"];
        case "experiment":
            return ["project", "experiment"];
        case "dataset":
            return ["project", "experiment", "dataset"];
        case "datafile":
            return ["project", "experiment", "dataset", "datafile"];
        default:
            return [];
    }
};

export const fieldSelector = (filtersSlice, fieldInfo) => {
    const { kind, target } = fieldInfo;
    switch (kind) {
    case "typeAttribute":
        return typeSelector(filtersSlice, target[0]).attributes.byId[target[1]];
    case "schemaParameter":
        return schemaSelector(filtersSlice, target[0]).parameters[target[1]];
    default:
        throw new Error("Field type not supported.");
    }

};

export const filterValueSelector = (filtersSlice, filterFieldInfo) => {
    const filter = fieldSelector(filtersSlice, filterFieldInfo);
    if (!filter || !(filter instanceof Object)) {
        throw new Error("Could not find field.");
    }
    return Array.isArray(filter.value) ? filter.value : [filter.value];
};

export const activeFiltersSelector = (filtersSlice) => {

};

/**
 * Resolves the filter and returns filter value serialised in
 * the form expected by the search API.
 * @param filtersSlice
 * @param filterFieldInfo
 */
const getFilterQueryValue = (filtersSlice, filterFieldInfo) => {
    const field = fieldSelector(filtersSlice, filterFieldInfo);
    const filterValue = filterValueSelector(filtersSlice, filterFieldInfo);
    const filterType = { type: field.data_type };
    return filterValue.map(value => (
        Object.assign({}, filterFieldInfo, filterType, value)
    ));
};

/**
 * Selector for whether there are any active filters in the search.
 * @param {*} filterSlice Redux filter slice
 */
export function hasActiveFiltersSelector(filterSlice) {
    // First, look through whether any filters are active.
    const activeFilters = filterSlice.activeFilters;
    for (const typeId in activeFilters) {
        if (activeFilters[typeId] && activeFilters[typeId].length > 0) {
            return true;
        }
    }
    return false;
}


/**
 * Returns active filter values in search API query form.
 * @param filtersSlice - Filters state slice.  
 * @param {string} matchesType - If null, returns query with all filters. 
 * If a MyTardis object type is specified, then only filters of that type
 * and filters of types that will be cross-filtered will be returned.
 */
export const buildFilterQuery = (filtersSlice, matchesType) => {
    let typesToInclude = [];
    if (matchesType) {
        typesToInclude = getCrossFilteredTypes(matchesType);
    } else {
        typesToInclude = filtersSlice.types.allIds;
    }
    let filtersInQuery = [];
    typesToInclude.forEach(typeId => {
        // Grab filters from that type.
        filtersInQuery = filtersInQuery.concat(filtersSlice.activeFilters[typeId]);
    });
    const allFilters = filtersInQuery.map(getFilterQueryValue.bind(this, filtersSlice))
    // "Flatten" the array so filters with multiple values are in same array.
        .reduce((acc, val) => acc.concat(val), []);
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
        dispatch(getFiltersFailure(e));
    });
};

export default filters.reducer;