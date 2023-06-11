import React from "react";
import FilterSummaryBox from "./FilterSummaryBox";
import makeMockStore from "../../util/makeMockStore";
import { filtersData } from "../filters/filters-section/FiltersSection.stories";
import { Provider } from "react-redux";
import { searchInfoData } from "../SearchPage.stories";

const store = makeMockStore({
    search: searchInfoData,
    filters: filtersData
});

export default {
    component: FilterSummaryBox,
    title: "Filter summary box",
    parameters: { actions: { argTypesRegex: "^on.*" } },
    decorators: [story => <Provider store={store}><div style={{ padding: "3rem" }}>{story()}</div></Provider>]
};

const Template = (args) => <FilterSummaryBox {...args}/>;

export const Default = Template.bind({});