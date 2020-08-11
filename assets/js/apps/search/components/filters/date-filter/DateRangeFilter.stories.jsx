import React from 'react'
import DateRangeFilter from './DateRangeFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: DateRangeFilter,
  title: 'Filters/Date range filter',
  decorators: [story => <div style={{ padding: '3rem', width:"300px"  }}>{story()}</div>],
  excludeStories: /.*Data$/,
  parameters: {
    // Disabled snapshot testing as the datetime picker has a special class
    // for which day is today - which changes daily and invalidates the test.
    storyshots: { disable: true },
  }
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

export const onlyShowStartFilterData = Object.assign({}, dateRangeFilterData, {
    options: Object.assign({}, dateRangeFilterData.options, {
        hideEnd: true
    })
});

export const onlyShowEndFilterData = Object.assign({}, dateRangeFilterData, {
    options: Object.assign({}, dateRangeFilterData.options, {
        hideStart: true
    })
});

export const noLabelsFilterData = Object.assign({}, dateRangeFilterData, {
    options: Object.assign({}, dateRangeFilterData.options, {
        hideLabels: true
    })
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

export const OnlyShowStart = () => (
    <DateRangeFilter {...onlyShowStartFilterData} />
)

export const OnlyShowEnd = () => (
    <DateRangeFilter {...onlyShowEndFilterData} />
)

export const NoLabels = () => (
    <DateRangeFilter {...noLabelsFilterData} />
)