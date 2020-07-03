import React from 'react'
import NumberRangeFilter from './NumberRangeFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: NumberRangeFilter,
  title: 'Filters/Number range filter',
  decorators: [story => <div style={{ padding: '3rem', width:"300px" }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const numRangeFilterData = {
    value: [{
        op: ">=",
        content: 2
    }, {
        op: "<=",
        content: 10
    }],
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
