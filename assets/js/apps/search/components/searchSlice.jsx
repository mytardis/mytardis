import { createSlice } from '@reduxjs/toolkit';
import Cookies from 'js-cookie';

const getResultFromHit = (hit,hitType,urlPrefix) => {
    const source = hit._source;
    source.type = hitType;
    source.url = `${urlPrefix}/${source.id}`;
    return source;
}

const getResultsFromResponse = (response) => {
// Grab the "_source" object out of each hit and also
// add a type attribute to them.
const hits = response.objects[0].hits,
    projectResults = hits["projects"].map((hit) => {
        return getResultFromHit(hit,"project","/project/view")
    }),
    expResults = hits["experiments"].map((hit) => {
        return getResultFromHit(hit,"experiment","/experiment/view")
    }),
    dsResults = hits["datasets"].map((hit) => {
        return getResultFromHit(hit,"dataset","/dataset")
    }),
    dfResults = hits["datafiles"].map((hit) => {
        return getResultFromHit(hit,"datafile","/datafile/view")
    });
return {
    project: projectResults,
    experiment: expResults,
    dataset: dsResults,
    datafile: dfResults
}
}

const initialState = {
    searchTerm: null,
    isLoading: false,
    error:null,
    results:null,
    activeFilters: []
};

const search = createSlice({
    name: 'search',
    initialState,
    reducers: {
        getResultsSuccess: {
            reducer: function (state, { payload }){
                state.results = payload;
                state.error = null;
                state.isLoading = false;
            },
            prepare: (rawResult) => {
                // Process the results first to extract hits and fill in URLs.
                return {
                    payload: getResultsFromResponse(rawResult)
                }
            }
        },
        getResultsStart: (state, {payload}) => {
            state.isLoading = true;
            state.error = null;
            state.searchTerm = payload;
        },
        getResultsFailure: (state, action) => {
            state.isLoading = false;
            state.error = action.payload.toString();
            state.results = null;
        }
    }
})

const fetchResults = (searchTerm) => (
    fetch(`/api/v1/search_simple-search/?query=${searchTerm}`,{
        method: 'get',
        headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
        },      
    }).then(response => {
        if (!response.ok) {
            throw new Error("An error on the server occurred.")
        }
        return response.json()
    })
);

export const updateTextSearch = (searchTerm) => {
    return (dispatch, getState) => {
        dispatch(getResultsStart(searchTerm));
        fetchResults(searchTerm).then((results) => {
            dispatch(getResultsSuccess(results));
        }).catch((e) => {
                dispatch(getResultsFailure(e));
        });
    }
}



export const {
    getResultsStart,
    getResultsSuccess,
    getResultsFailure
} = search.actions;

export default search.reducer;
