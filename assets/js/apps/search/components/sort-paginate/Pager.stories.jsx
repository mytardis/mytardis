import React from "react";
import { PurePager } from "./Pager";
import { action } from "@storybook/addon-actions";

export default {
    component: PurePager,
    title: "Pager",
    decorators: [story => <div style={{ padding: "3rem" }}>{story()}</div>],
    excludeStories: /.*Data$/
};

export const paginationData = {
    typeId: "experiment",
    pageNum: 5,
    pageSize: 50,
    totalPages: 10,
    onPageNumChange: action("Page number change"),
    onPageSizeChange: action("Page size change")
};

export const lessThanFivePagesData = Object.assign({}, paginationData, {
    pageNum: 1,
    totalPages: 4
});

export const onePageData = Object.assign({}, paginationData, {
    pageNum: 1,
    totalPages: 1
});

export const noPagesData = Object.assign({}, paginationData, {
    pageNum: 0,
    totalPages: 0
});

export const lastPageData = Object.assign({}, paginationData, {
    pageNum: 10,
    totalPages: 10
});

export const Default = () => (
    <PurePager {...paginationData} />
);

export const LessThanFivePages = () => (
    <PurePager {...lessThanFivePagesData} />
);

export const OnePage = () => (
    <PurePager {...onePageData} />
);

export const NoPages = () => (
    <PurePager {...noPagesData} />
);

export const LastPage = () => (
    <PurePager {...lastPageData} />
);