import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";

const initialTypeAttributes = {
    projects: {
        attributes: {
            schema: {
                
            }
        }
    },
    experiments: {
        attributes: {
            schema: {}
        }
    },
    datasets: {
        attributes: {
            schema: {}
        }
    },
    datafiles: {
        attributes: {
            schema: {}
        }
    }
};



const initialState = {
    types: {
        byId: initialTypeAttributes,
        allIds: ['projects', 'experiments', 'datasets', 'datafiles']
    },
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
        .attributes[attributeId];
}

export const schemaParamSelector = (filterSlice, schemaId, paramId) => {
    return filterSlice.schemas
        .byId[schemaId]
        .parameters[paramId];
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
        getFiltersFailure: (state, { payload }) => {
            console.log("Error", payload);
            state.isLoading = false;
            state.error = payload;
        },
        updateTypeAttribute: (state, {payload}) => {
            const { typeId, attributeId, value } = payload;
            const attribute = typeAttrSelector(state, typeId, attributeId);
            const fieldInfo = {
                kind: "typeAttribute",
                target: [typeId,attributeId],
                type: attribute.data_type
            };
            attribute.value = value;
            if (value === null) {
                // If the new value is null, remove it from activeFilter list.
                removeFromActiveFilters(state,fieldInfo);
            } else {
                addToActiveFilters(state,fieldInfo);
            }
        },
        updateSchemaParameter: (state, {payload}) => {
            const { schemaId, parameterId, value } = payload;
            const parameter = schemaParamSelector(state, schemaId, parameterId);
            const fieldInfo = {
                kind: "schemaParameter",
                target: [schemaId, parameterId],
                type: parameter.data_type
            };
            parameter.value = value;
            if (value === null) {
                removeFromActiveFilters(state, fieldInfo);
            } else {
                addToActiveFilters(state, fieldInfo);
            }
        },

        updateActiveSchemas: (state, {payload}) => {
            const { typeId, value } = payload;
            const activeSchemas = typeAttrSelector(state, typeId, "schema");
            const fieldInfo = {
                kind: "typeAttribute",
                target: [typeId,"schema"],
                type: "STRING"
            };
            // Get the current active schema value. If null, then all schemas apply.
            const currActiveSchemas = attribute.value ? attribute.value.content : state.typeSchemas[typeId];
            // Same for new active schema value.
            const newActiveSchemas = value ? attribute.value.content : state.typeSchemas[typeId];
            // Find the schemas that will no longer be active.
            const diffSchemas = currActiveSchemas.filter(schema => (newActiveSchemas.includes(schema)));
            // Then, find the filters on parameters that belong to the schema if any.
            // They need to be removed too.
            const parameters = state.activeFilters.filter(
                filter => (
                    filter.kind === "schemaParameter" && 
                    diffSchemas.includes(filter.target[0])
                )
            );
            
        },

        updateFilter: (state, { payload }) => {
            console.log(payload);
            const { field, value } = payload;
            let selector;
            switch (field.kind) {
                case "typeAttribute":
                    const attribute = typeAttrSelector(state, field.target[0], field.target[1]);
                    attribute.value = value;
                    break;
                default:
                    break;
            }
            const activeIndex = findFilter(
                state.activeFilters, field
            );
            if (activeIndex === -1) {
                state.activeFilters.push(field);
            }
        },
        removeFilter: (state, { payload }) => {
            console.log(payload);
            const { field, value } = payload;
            let selector;
            switch (field.kind) {
                case "typeAttribute":
                    const attribute = typeAttrSelector(state, field.target[0], field.target[1]);
                    attribute.value = null;
                    break;
                default:
                    break;
            }
            const activeIndex = findFilter(
                state.activeFilters, field
            );
            if (activeIndex === -1) {
                return;
            } else {
                // Remove from active filters list
                state.activeFilters.splice(activeIndex, 1);
            }
        }
    }
})

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
    updateFilter,
    removeFilter,
    updateTypeAttribute,
    updateSchemaParameter
} = filters.actions;

export const initialiseFilters = () => (dispatch) => {
    dispatch(getFiltersStart());
    fetchFilterList().then(filters => {
        dispatch(getFiltersSuccess(filters));
    }).catch((e) => {
        dispatch(getFiltersFailure(e))
    });
}

export default filters.reducer;