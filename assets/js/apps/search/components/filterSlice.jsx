import { createSlice } from '@reduxjs/toolkit';

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

const fetchFilterList = async () => {
    const response = await fetch(`/api/v1/search_get-schemas/`, {
        method: "get",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken')
        }
    });
    if (!response.ok) {
        throw new Error("An error on the server occurred.")
    }
    return await response.json();
};

export const {
    getFiltersStart,
    getFiltersSuccess,
    getFiltersFailure
} = filters.actions;

export const initialiseFilters = async (dispatch) => {
    dispatch(getFiltersStart());
    try {
        const filters = await fetchFilterList();
        dispatch(getFiltersSuccess(filters));
    } catch (e) {
        dispatch(getFiltersFailure(e))
    }
}
