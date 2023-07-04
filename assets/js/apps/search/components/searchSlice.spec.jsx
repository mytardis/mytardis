/*eslint-env jest*/

import reducer, {
    removeResultSort,
    SORT_ORDER,
    updateResultSort,
    parseQuery
} from "./searchSlice";
import { createNextState } from "@reduxjs/toolkit";
import { searchInfoData } from "./SearchPage.stories";

describe("Query parser", () => {
    it("can parse text search terms", () => {
        expect(parseQuery("?q={\"query\":{\"project\":\"abc\"}}")).toEqual({query: {project: "abc"}});
    });

    it("can parse numerical search terms", () => {
        expect(parseQuery("?q={\"query\": {\"project\": 2}}")).toEqual({query: {project: 2}});
    });

    it("can parse complex search query", () => {
        expect(parseQuery("?q={\"filters\":\"1\"}")).toEqual({filters: "1"});
    });

    it("can parse special characters", () => {
        expect(parseQuery("?q=%3A")).toEqual({query: {
            project: ":",
            experiment: ":",
            dataset: ":",
            datafile: ":"
        }});
    });

    it("can parse legacy search URLs that have search term strings", () => {
        expect(parseQuery("?q=test")).toEqual({query: {
            project: "test",
            experiment: "test",
            dataset: "test",
            datafile: "test"
        }});
    });

    it("can parse square brackets as a search term", () => {
        expect(parseQuery("?q=%5B2%5D")).toEqual({query: {
            project: "[2]",
            experiment: "[2]",
            dataset: "[2]",
            datafile: "[2]"
        }});
    });
});

describe("Sort reducers", () => {

    it("can add sort in the order they are added", () => {
        const expectedSearchState = createNextState(searchInfoData, draft => {
            draft.sort.project.active.push("createdDate");
            draft.sort.project.order.createdDate = SORT_ORDER.ascending;
        });
        expect(reducer(searchInfoData, updateResultSort({
            typeId: "project",
            attributeId: "createdDate",
            order: SORT_ORDER.ascending
        }))).toEqual(expectedSearchState);
    });

    it("can remove the correct sort option", () => {
        const expectedSearchState = createNextState(searchInfoData, draft => {
            draft.sort.project.active = [];
        });
        expect(reducer(searchInfoData, removeResultSort({
            typeId: "project",
            attributeId: "institution",
        }))).toEqual(expectedSearchState);
    });
});
