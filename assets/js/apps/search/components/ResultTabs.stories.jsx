import React from 'react'
import { PureResultTabs } from './ResultSection'
import { action } from '@storybook/addon-actions';

export default {
    component: PureResultTabs,
    title: "Result tabs",
    decorators: [story => <div style={{ padding: "3rem"}}>{story()}</div>],
    excludeStories: /.*Data$/
};

export const countsData = {
    selectedType: "project",
    counts: [
        {
            id: "project",
            name: "projects",
            hitTotal: 4
        },
        {
            id: "experiment",
            name: "experiments",
            hitTotal: 14
        },
        {
            id: "dataset",
            name: "datasets",
            hitTotal: 5
        },
        {
            id: "datafile",
            name: "datafiles",
            hitTotal: 80
        }
    ],
    onChange: action("level change")
};

export const emptyCountsData = Object.assign({}, countsData,
    {
        counts: [
            {
                id: "project",
                name: "projects"
            },
            {
                id: "experiment",
                name: "experiments"
            },
            {
                id: "dataset",
                name: "datasets"
            },
            {
                id: "datafile",
                name: "datafiles"
            }
        ]
    }
);

export const Default = () => (<PureResultTabs {...countsData} />);

export const EmptyCounts = () => (<PureResultTabs {...emptyCountsData} />);