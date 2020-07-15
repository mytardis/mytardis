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
    value: [
        {
            op:">=",
            content: "2020-01-05"
        },
        {
            op: "<=",
            content: "2020-05-28"
        }
    ],
    onValueChange: action("Value changed"),
    options: {
        name: "cidEnergy",
        hintStart: "Start date",
        hintEnd: "End date"
    },
}

export const emptyDateRangeFilterData = Object.assign({},dateRangeFilterData, {
    value: null
});

export const Default = (storyMetadata,onValueChange) => {
    let props = dateRangeFilterData;
    if (onValueChange) {
        props = Object.assign({}, dateRangeFilterData, {
            onValueChange
        })
    }
    return <DateRangeFilter {...props} />
}

export const Empty = (storyMetadata,onValueChange) => {
    let props = emptyDateRangeFilterData;
    if (onValueChange) {
        props = Object.assign({},emptyDateRangeFilterData, {
            onValueChange
        })
    }
    return <DateRangeFilter {...props} />
}
