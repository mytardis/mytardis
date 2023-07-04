import React from "react";
import { SearchPage } from "./SearchPage";
import { experimentListData } from "./ResultList.stories";
import { Provider } from "react-redux";
import { filtersData } from "./filters/filters-section/FiltersSection.stories";
import makeMockStore from "../util/makeMockStore";
import { SORT_ORDER } from "./searchSlice";

export default {
    component: SearchPage,
    title: "Search page",
    excludeStories: /.*Data$/
};

// Mock redux store for this story.
const makeSearchStore = (searchState, filtersState) => (
    makeMockStore({search: searchState, filters: filtersState})
);

export const dsResultsData = [
    {
        id: "1",
        type: "dataset",
        description: "ABC1",
        url: "",
        size: "11GB",
        userDownloadRights: "full"
    }
];

export const dfResultsData = [
    {
        id: "1",
        url: "",
        type: "datafile",
        filename: "DF1",
        size: "6MB",
        userDownloadRights: "partial"
    }
];

export const projectResultsData = [
    {
        id: "1",
        url: "",
        type: "project",
        name: "Understanding genetic drivers in acute megakaryoblastic leukaemia",
        size: "79GB",
        userDownloadRights: "partial"
    }
];

export const searchResultsData = {
    project: projectResultsData,
    experiment: experimentListData,
    dataset: dsResultsData,
    datafile: dfResultsData
};

export const searchInfoData = {
    searchTerm: null,
    isLoading: false,
    error: null,
    results: {
        hits: searchResultsData,
        totalHits: {
            project: projectResultsData.length,
            experiment: experimentListData.length,
            dataset: dsResultsData.length,
            datafile: dfResultsData.length
        }
    },
    showSensitiveData: false,
    selectedType: "experiment",
    pageNumber: {
        project: 1,
        experiment: 1,
        dataset: 1,
        datafile: 1
    },
    pageSize: {
        project: 10,
        experiment: 10,
        dataset: 10,
        datafile: 10
    },
    sort: {
        project: {
            active: [ "institution"],
            order: {
                "institution": SORT_ORDER.descending
            }
        }, experiment: {
            active: [ "institution" ],
            order: {
                "institution": SORT_ORDER.descending
            }        
        }, dataset: {
            active: [ "institution" ],
            order: {
                "institution": SORT_ORDER.descending
            }
        }, datafile: {
            active: [ "institution" ],
            order: {
                "institution": SORT_ORDER.descending
            }
        }
    }
};

export const errorData = Object.assign({}, searchInfoData, {
    error: "An error occurred",
    results: null
});

export const loadingData = Object.assign({}, searchInfoData, {
    isLoading: true,
    results: null
});

export const Default = () => (
    <Provider store={makeSearchStore(searchInfoData, filtersData)}>
        <SearchPage />
    </Provider>
);

export const Error = () => (
    <Provider store={makeSearchStore(errorData, filtersData)}>
        <SearchPage />
    </Provider>
);

export const Loading = () => (
    <Provider store={makeSearchStore(loadingData, filtersData)}>
        <SearchPage />
    </Provider>
);