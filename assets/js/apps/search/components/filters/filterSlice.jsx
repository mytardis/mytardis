import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";

const initialTypeAttributes = {
    projects: {
        attributes: {
            schema: {
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
        updateFilter: (state, { payload }) => {
            console.log(payload);
            const { field, value } = payload;
            let selector;
            switch (field.kind) {
                case "typeAttribute":
                    selector = typeAttributeSelector(field.target, true);
                    selector(state).value = value;
                    break;
                case "schemaParameter":
                    selector = schemaParameterSelector(field.target, true);
                    selector(state).value = value;
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
                    selector = typeAttributeSelector(field.target, true)
                    selector(state).value = null;
                    break;
                case "schemaParameter":
                    selector = schemaParameterSelector(field.target, true)
                    selector(state).value = null;
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


// Selectors for different kinds of filter targets.
export const typeAttributeSelector = (target,isFromFiltersSliceRoot) => {
    const [typeId, attributeId] = target;
    return (state) => {
        const root = isFromFiltersSliceRoot ? state : state.filters;
        return root.types
            .byId[typeId]
            .attributes[attributeId];
    }
};

export const schemaParameterSelector = (target,isFromFiltersSliceRoot) => {
    const [schemaId, paramId] = target;
    return (state) => {
        const root = isFromFiltersSliceRoot ? state : state.filters;
        return root.schemas
            .byId[schemaId]
            .parameters[paramId];
    }
};

export const SELECTORS_BY_KIND = {
    schemaParameter: schemaParameterSelector,
    typeAttribute: typeAttributeSelector
}

export const {
    getFiltersStart,
    getFiltersSuccess,
    getFiltersFailure,
    updateFilter,
    removeFilter
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