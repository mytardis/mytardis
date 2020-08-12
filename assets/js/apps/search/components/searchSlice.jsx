import { createSlice } from '@reduxjs/toolkit';
import Cookies from 'js-cookie';
import { typeAttrSelector, schemaParamSelector, initialiseFilters } from "./filters/filterSlice";

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
        updateSearchTerm: (state, {payload}) => {
            state.searchTerm = payload;
        },
        getResultsStart: (state, {payload}) => {
            state.isLoading = true;
            state.error = null;
        },
        getResultsFailure: (state, action) => {
            state.isLoading = false;
            state.error = action.payload.toString();
            state.results = null;
        }
    }
})

const fetchSearchResults = (searchTerm,filters) => {
    const bodyJson = {};
    if (searchTerm !== null) {
        bodyJson.query = searchTerm;
    }
    if (filters !== null) {
        bodyJson.filters = filters;
    }
    return fetch(`/api/v1/search_simple-search/`,{
        method: 'post',
        headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: JSON.stringify(bodyJson)
    }).then(response => {
        if (!response.ok) {
            throw new Error("An error on the server occurred.")
        }
        return response.json()
    })
};

const buildFilterQuery = (filters) => {
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

export const runSearch = () => {
    return (dispatch, getState) => {
        const state = getState();
        const term = state.search.searchTerm,
            filters = buildFilterQuery(state.filters);
        console.log(filters);
        dispatch(getResultsStart(state.searchTerm));
        fetchSearchResults(term,filters)
            .then((results) => {
                dispatch(getResultsSuccess(results));
            }).catch((e) => {
                dispatch(getResultsFailure(e));
            });

    }
}

const parseQuery = (searchString) => {
    if (searchString[0] === "?") {
        searchString = searchString.substring(1);
    }
    const parts = searchString.split('&');
    let queryPart = null;
    for (const partIdx in parts) {
        if (parts[partIdx].indexOf('q=') === 0) {
            queryPart = parts[partIdx].substring(2);
            break;
        }
    }
    return queryPart;
}

export const initialiseSearch = () => {
    return (dispatch, getState) => {
        const query = parseQuery(window.location.search);
        if (!!query) {
            dispatch(updateSearchTerm(query));
        }
        dispatch(initialiseFilters());
        dispatch(runSearch());
    }
}


export const {
    getResultsStart,
    getResultsSuccess,
    getResultsFailure,
    updateSearchTerm
} = search.actions;

export default search.reducer;
