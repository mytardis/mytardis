import React from "react";
import { PureSortOptionsList } from "./SortOptionsList";
import { SORT_ORDER } from "../searchSlice";


export default {
    component: PureSortOptionsList,
    title: "Sort options list",
    decorators: [story => <div style={{ padding: "3rem" }}>{story()}</div>],
    parameters: { actions: { argTypesRegex: '^on.*' } },
    excludeStories: /.*Data$/
};

export const sortData = {
    attributesToSort: [
        {
            id: "name",
            full_name: "Name",
            order: SORT_ORDER.ascending
        },
        {
            id: "createdDate",
            full_name: "Ingestion date",
            order: SORT_ORDER.descending
        },
        {
            id: "institution",
            full_name: "Institution",
            order: SORT_ORDER.ascending
        }
    ],
    activeSort: null
};

export const activeSortData = {
    attributesToSort: [
        {
            id: "name",
            full_name: "Description",
            order: SORT_ORDER.ascending
        },
        {
            id: "createdDate",
            full_name: "Created date",
            order: SORT_ORDER.ascending
        }
    ],
    activeSort: ["name"]
};

export const multiSelectedData = Object.assign({}, sortData, {
    activeSort: ["name", "createdDate"]
});

const Template = (args) => <PureSortOptionsList {...args} />;

export const Default = Template.bind({});
Default.args = sortData;

export const SortActive = Template.bind({});
SortActive.args = activeSortData;

export const MultiSelected = Template.bind({});
MultiSelected.args = multiSelectedData;