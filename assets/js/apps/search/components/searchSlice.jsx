import { createSlice } from '@reduxjs/toolkit';
import Cookies from 'js-cookie';
import { initialiseFilters, buildFilterQuery, updateFiltersByQuery } from "./filters/filterSlice";

const getResultFromHit = (hit,hitType,urlPrefix) => {
    const source = hit._source;
    source.type = hitType;
    source.url = `${urlPrefix}/${source.id}`;
    return source;
}

const getResultsFromResponse = (response) => {
// Grab the "_source" object out of each hit and also
// add a type attribute to them.
const hits = response.hits,
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
    activeFilters: [],
    selectedType: "experiment",
    selectedResult: null
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
        updateSearchTerm: (state, {payload}) => {
            state.searchTerm = payload;
        },
        getResultsStart: (state) => {
            state.isLoading = true;
            state.error = null;
            state.selectedResult = null;
        },
        getResultsFailure: (state, {payload:error}) => {
            state.isLoading = false;
            state.error = error.toString();
            state.results = null;
        },
        updateSelectedType: (state,{payload: selectedType}) => {
            state.selectedType = selectedType;
            state.selectedResult = null;
        },
        updateSelectedResult: (state, {payload: selectedResult}) => {
            state.selectedResult = selectedResult;
        }
    }
})

const fetchSearchResults = (queryBody) => {
    return fetch(`/api/v1/search_simple-search/`,{
        method: 'post',
        headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: JSON.stringify(queryBody)
    }).then(response => {
        if (!response.ok) {
            throw new Error("An error on the server occurred.")
        }
        return response.json()
    })
};

const buildQueryBody = (state) => {
    const term = state.search.searchTerm,
        filters = buildFilterQuery(state.filters),
        queryBody = {};
    if (term !== null && term !== "") {
        queryBody.query = term;
    }
    if (filters !== null) {
        queryBody.filters = filters;
    }
    return queryBody;
}

const runSearchWithQuery = (queryBody) => {
    return (dispatch) => {
        dispatch(getResultsStart());
        return fetchSearchResults(queryBody)
            .then((results) => {
                dispatch(getResultsSuccess(results));
            }).catch((e) => {
                dispatch(getResultsFailure(e));
            });
    }
}

const getDisplayQueryString = (queryBody) => {
    // Determine how to show the query in the URL, depending on what's in the query body.
    const queryPrefix = "?q=";
    if (queryBody.filters) {
        // If the query contains filters, then use the stringified JSON format.
        return queryPrefix + JSON.stringify(queryBody);
    } else if (queryBody.query) {
        // If the query only has a search term, then just use the search term.
        return queryPrefix + queryBody.query;
    } else {
        // when there aren't any filters or search terms don't show a query at all.
        return location.pathname;
    }
}

const parseQuery = (searchString) => {
    // Find and return the query string or JSON body.
    if (searchString[0] === "?") {
        searchString = searchString.substring(1);
    }
    searchString = decodeURI(searchString);
    const parts = searchString.split('&');
    let queryPart = null;
    for (const partIdx in parts) {
        if (parts[partIdx].indexOf('q=') === 0) {
            queryPart = parts[partIdx].substring(2);
            break;
        }
    }
    if (!queryPart) { return {}; }
    try {
        return JSON.parse(queryPart);
    } catch (e) {
        // When we fail to parse, we assume it's a search term string.
        return { query: queryPart };
    }
}


const updateWithQuery = (queryBody) => {
    return (dispatch) => {
        dispatch(updateSearchTerm(queryBody.query));
        dispatch(updateFiltersByQuery(queryBody.filters));
    }
}

export const runSearch = () => {
    return (dispatch, getState) => {
        const state = getState();
        const queryBody = buildQueryBody(state);
        dispatch(runSearchWithQuery(queryBody));
        window.history.pushState(queryBody,"",getDisplayQueryString(queryBody));
    }
}


export const restoreSearchFromHistory = (restoredState) => {
    return (dispatch) => {
        dispatch(runSearchWithQuery(restoredState));
        dispatch(updateWithQuery(restoredState));
    }
}


export const initialiseSearch = () => {
    return (dispatch, getState) => {
        const queryBody = parseQuery(window.location.search);
        window.history.replaceState(queryBody,"",getDisplayQueryString(queryBody));
        dispatch(runSearchWithQuery(queryBody));
        dispatch(initialiseFilters()).then(() => {
            if (!!queryBody) {
                dispatch(updateWithQuery(queryBody));
            }
        });
    }
}


export const {
    getResultsStart,
    getResultsSuccess,
    getResultsFailure,
    updateSearchTerm,
    updateSelectedType,
    updateSelectedResult
} = search.actions;

export default search.reducer;
