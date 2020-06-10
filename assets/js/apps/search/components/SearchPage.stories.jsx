import React from 'react'
import { PureSearchPage } from './SearchPage'
import SearchInfoContext from './SearchInfoContext'
import { experimentListData } from './ResultList.stories'
import { action } from '@storybook/addon-actions'

export default {
    component: PureSearchPage,
    title: 'Search page',
    excludeStories: /.*Data$/
};

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
    updateSearch: action("update search requested")
}

export const errorData = Object.assign({},searchInfoData,{
    error: "An error occurred",
    results: null,
});

export const loadingData = Object.assign({},searchInfoData,{
    isLoading: true,
    results: null,
});

export const Default = () => (
    <SearchInfoContext.Provider value={searchInfoData}>
        <PureSearchPage />
    </SearchInfoContext.Provider>
);

export const Error = () => (
    <SearchInfoContext.Provider value={errorData}>
        <PureSearchPage />
    </SearchInfoContext.Provider>
);

export const Loading = () => (
    <SearchInfoContext.Provider value={loadingData}>
        <PureSearchPage />
    </SearchInfoContext.Provider>
);