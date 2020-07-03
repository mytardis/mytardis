import { createSlice } from '@reduxjs/toolkit';
import Cookies from "js-cookie";

const initialState = {
    filtersByKind: null,
    isLoading: false,
    error: null
}

const filters = createSlice({
    name: 'filters',
    initialState,
    reducers: {
        getFiltersStart: (state, {payload}) => {
            state.isLoading = true;
            state.filtersByKind = null;
            state.error = null;
        },
        getFiltersSuccess: (state, {payload}) => {
            state.filtersByKind = {
                typeAttributes: {},
                schemaParameters:payload
            };
            state.isLoading = false;
            state.error = null;
        },
        getFiltersFailure: (state, {payload}) => {
            state.isLoading = false;
            state.error = payload;
            state.filtersByKind = null;
        },
        updateFilter: (state, {payload}) => {
            console.log(payload);
            // const {schemaType, schemaId, parameterId, value } = payload;
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