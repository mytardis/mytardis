import React from 'react'
import NumberRangeFilter from './NumberRangeFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: NumberRangeFilter,
  title: 'Number range filter',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const numRangeFilterData = {
    value: {
        min: 2,
        max: 10
    },
    onValueChange: action("Value changed"),
    options: {
        name: "CID Energy",
        hintMin: "Minimum",
        hintMax: "Maximum"
    },
}

export const emptyNumRangeFilterData = Object.assign({},numRangeFilterData, {
    value: null
});

export const Default = () => (
    <NumberRangeFilter {...numRangeFilterData} />
)

export const Empty = () => (
    <NumberRangeFilter {...emptyNumRangeFilterData} />
)
