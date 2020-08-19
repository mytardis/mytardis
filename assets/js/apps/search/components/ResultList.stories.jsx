import React from 'react'
import { PureResultList } from './ResultSection'
import { action } from '@storybook/addon-actions';

export default {
    component: PureResultList,
    title: 'Result list',
    decorators: [story => <div style={{ padding: '3rem'}}>{story()}</div>],
    excludeStories: /.*Data$/
};

export const allAccessResultData = {
    id: "1",
    type: "experiment",
    title: "siNET",
    url: "",
    size:"35MB",
    userDownloadRights:"full"
};

export const someAccessResultData = {
    id: "2",
    type:"experiment",
    title: "Gastroblastoma",
    url: "",
    size:"4GB",
    userDownloadRights:"partial"
};

export const viewOnlyResultData = {
    id: "3",
    type:"experiment",
    title: "Lung",
    url:"",
    size:"0kB",
    userDownloadRights:"none"
};

const getResultsProps = (results) => (
    {
        results: results,
        onItemSelect: action("itemSelected"),
        selectedItem: null,
        error: null,
        isLoading: false
    }
)

const errorProps = {
    results: null,
    onItemSelect: action("itemSelected"),
    selectedItem: null,
    error: "Test error",
    isLoading: false
}

const loadingProps = Object.assign({},errorProps,{
    error: null,
    isLoading: true
});


export const experimentListData = [allAccessResultData, someAccessResultData, viewOnlyResultData];

export const Default = () => (
    <PureResultList {...getResultsProps(experimentListData)} />
)

export const Empty = () => (
    <PureResultList {...getResultsProps([])} />
)


export const AllAccess = () => (
    <PureResultList {...getResultsProps([allAccessResultData])} />
)

export const SomeAccess = () => (
    <PureResultList {...getResultsProps([someAccessResultData])} />
)

export const ViewOnlyAccess = () => (
    <PureResultList {...getResultsProps([viewOnlyResultData])} />
)

export const Error = () => (
    <PureResultList {...errorProps} />
)

export const Loading = () => (
    <PureResultList {...loadingProps} />
)