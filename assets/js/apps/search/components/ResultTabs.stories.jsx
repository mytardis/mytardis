import React from 'react'
import  { ResultTabs } from './ResultSection'
import { action } from '@storybook/addon-actions';

export default {
    component: ResultTabs,
    title: 'Result tabs',
    decorators: [story => <div style={{ padding: '3rem'}}>{story()}</div>],
    excludeStories: /.*Data$/
};

export const countsData = {
    selectedLevel: "experiment",
    counts: {
        experiment: 14,
        dataset: 5,
        datafile: 80
    },
    onChange: action("level change")
}

export const emptyCountsData = Object.assign({},countsData,
    {
        counts: null
    }
);

export const Default = () => (<ResultTabs {...countsData} />)

export const EmptyCounts = () => (<ResultTabs {...emptyCountsData}></ResultTabs>)