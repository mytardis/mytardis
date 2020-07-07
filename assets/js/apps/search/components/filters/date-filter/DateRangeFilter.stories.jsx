import React from 'react'
import DateRangeFilter from './DateRangeFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: DateRangeFilter,
  title: 'Filters/Date range filter',
  decorators: [story => <div style={{ padding: '3rem', width:"300px"  }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const dateRangeFilterData = {
    value: {
        start: "2020-01-05",
        end: "2020-05-28"
    },
    onValueChange: action("Value changed"),
    options: {
        name: "CID Energy",
        hintStart: "Start date",
        hintEnd: "End date"
    },
}

export const emptyDateRangeFilterData = Object.assign({},dateRangeFilterData, {
    value: null
});

export const Default = () => (
    <DateRangeFilter {...dateRangeFilterData} />
)

export const Empty = () => (
    <DateRangeFilter {...emptyDateRangeFilterData} />
)
