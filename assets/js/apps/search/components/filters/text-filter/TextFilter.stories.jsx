import React from 'react'
import TextFilter from './TextFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: TextFilter,
  title: 'Filters/Text filter',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const textFilterData = {
    value: {op: "contains", content:"text"},
    onValueChange: action("Value changed"),
    options: {
        name: "Name",
        hint: "Name of the dataset (e.g. NET-Plasma.)"
    },
}

export const emptyTextFilterData = Object.assign({},textFilterData, {
    value: null
});

export const Default = () => (
    <TextFilter {...textFilterData} />
)

export const Empty = () => (
    <TextFilter {...emptyTextFilterData} />
)
