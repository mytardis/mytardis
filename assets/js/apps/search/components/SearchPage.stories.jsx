import React from 'react'
import { SearchPage } from './SearchPage'
import { experimentListData } from './ResultList.stories'
import { Provider } from 'react-redux';
import { filtersData } from "./filters/filters-section/FiltersSection.stories";
import makeMockStore from "../util/makeMockStore";

export default {
    component: SearchPage,
    title: 'Search page',
    excludeStories: /.*Data$/
};

// Mock redux store for this story.
const makeSearchStore = (searchState, filtersState) => (
    makeMockStore({search: searchState, filters: filtersState})
)

export const dsResultsData = [
    {
        id: "1",
        type:"dataset",
        description: "ABC1",
        url: "",
        size: "11GB",
        userDownloadRights: "full"
    }
]

export const dfResultsData = [
    {
        id: "1",
        url: "",
        type:"datafile",
        filename:"DF1",
        size: "6MB",
        userDownloadRights:"partial"
    }
]

export const projectResultsData = [
    {
        id: "1",
        url: "",
        type:"project",
        name:"Understanding genetic drivers in acute megakaryoblastic leukaemia",
        size: "79GB",
        userDownloadRights:"partial"
    }
]

export const searchResultsData = {
    project: projectResultsData,
    experiment: experimentListData,
    dataset: dsResultsData,
    datafile: dfResultsData
}

export const searchInfoData = {
    searchTerm: null,
    isLoading: false,
    error:null,
    results: searchResultsData,
    selectedType: "experiment"
}

export const errorData = Object.assign({},searchInfoData,{
    error: "An error occurred",
    results: null
});

export const loadingData = Object.assign({},searchInfoData,{
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