import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";

const initialTypeAttributes = {
    projects: {
        attributes: {
            schema: null
        }
    },
    experiments: {
        attributes: {
            schema: null
        }
    },
    datasets: {
        attributes: {
            schema: null
        }
    },
    datafiles: {
        attributes: {
            schema: null
        }
    }
};



const initialState = {
    types: {
        byId: initialTypeAttributes,
        allIds: ['projects','experiments','datasets','datafiles']
    },
    typeSchemas: null,
    schemas:{
        byId: null,
        allIds: []
    },
    isLoading: true,
    error: null
}

const mapSchemasById = (schemasByType) => {
    // Generate a hashmap of schemas by their id, so we can look up
    // schemas by id.
    const schemasById = {},
            allIds = [];
    for (let type in schemasByType) {
        for (let schemaId in schemasByType[type]){
            schemasById[schemaId] = schemasByType[type][schemaId];
            allIds.push(schemaId);
        }
    }
    return {byId: schemasById,allIds: allIds};
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

const filters = createSlice({
    name: 'filters',
    initialState,
    reducers: {
        getFiltersStart: (state, {payload}) => {
            state.isLoading = true;
            state.error = null;
        },
        getFiltersSuccess: (state, {payload}) => {
            state.schemas = mapSchemasById(payload);
            state.typeSchemas = mapSchemaIdToType(payload);
            state.isLoading = false;
            state.error = null;
        },
        getFiltersFailure: (state, {payload}) => {
            console.log("Error",payload);
            state.isLoading = false;
            state.error = payload;
        },
        updateFilter: (state, {payload}) => {
            console.log(payload);
            payload.forEach( filterValue => {
                switch (filterValue.kind) {
                    case "typeAttribute":
                        break;
                    case "schemaParameter":
                        const [schemaId, paramId] = filterValue.target;
                        state.schemasById[schemaId]
                            .parameters[paramId]
                            .value = filterValue;
                        break;
                    default:
                        break;
                }
            })
            return state;
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
    updateFilter
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