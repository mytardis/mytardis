import React from "react";
import DateRangeFilter from "./DateRangeFilter";

export default {
    component: DateRangeFilter,
    title: "Filters/Date range filter",
    decorators: [story => <div style={{ padding: "3rem", width: "300px" }}>{story()}</div>],
    excludeStories: /.*Data$/,
    parameters: { actions: { argTypesRegex: "^on.*" } }
};

export const dateRangeFilterData = {
    value: [
        {
            op: ">=",
            content: "2020-01-05"
        },
        {
            op: "<=",
            content: "2020-05-28"
        }
    ],
    id: "cidEnergy",
    options: {
        hintStart: "Start date",
        hintEnd: "End date"
    },
};

export const emptyDateRangeFilterData = Object.assign({}, dateRangeFilterData, {
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

const Template = (args) => <DateRangeFilter {...args} />;

export const Default = Template.bind({});
Default.args = dateRangeFilterData;

export const Empty = Template.bind({});
Empty.args = emptyDateRangeFilterData;

export const OnlyShowStart = Template.bind({});
OnlyShowStart.args = onlyShowStartFilterData;

export const OnlyShowEnd = Template.bind({});
OnlyShowEnd.args = onlyShowEndFilterData;

export const NoLabels = Template.bind({});
NoLabels.args = noLabelsFilterData;