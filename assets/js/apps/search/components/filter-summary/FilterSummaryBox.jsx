import React, { Fragment, useCallback } from "react";
import PropTypes from "prop-types";
import { Badge, Button } from "react-bootstrap";
import "./FilterSummaryBox.css";
import { useDispatch, useSelector } from "react-redux";
import {
    resetFilters,
    schemaParamFilterValueSelector,
    schemaSelector,
    typeSelector,
    typeAttrFilterValueSelector,
    hasActiveFiltersSelector
} from "../filters/filterSlice";
import {
    runSearch,
    updateSearchTerm,
    hasActiveSearchTermSelector
} from "../searchSlice";

function InvalidFilterBadge() {
    return <Badge variant="secondary">(Invalid filter)</Badge>;
}

function AndOperatorBadge() {
    return <span className="filter-summarybox__badge filter-summarybox__badge--separator">and</span>;
}

function MultiValueContentBadge({ content }) {
    return content.map(filterValue =>
        <Badge
            key={filterValue}
            variant="secondary"
            className="filter-summary-box__badge"
        >
            {filterValue}
        </Badge>);
}

MultiValueContentBadge.propTypes = {
    content: PropTypes.arrayOf(PropTypes.string).isRequired
};

function SingleValueContentBadge({ content }) {
    return <Badge
        variant="secondary"
        className="filter-summary-box__badge"
    >
        {content}
    </Badge>;
}

SingleValueContentBadge.propTypes = {
    content: PropTypes.string.isRequired
};

function FilterBadge({ fieldName, value }) {
    
    return <div className="filter-summary-box__badge-group">
        <Badge variant="secondary" className="filter-summary-box__badge">{fieldName}</Badge>
        {value.map(({ op, content }) =>
            <Fragment key={Array.isArray(content) ? content.join(",") : content}>
                <Badge variant="secondary" className="filter-summary-box__badge filter-summarybox__badge--op">{op}</Badge>
                {op === "is" ?
                    <MultiValueContentBadge content={content} />
                    : <SingleValueContentBadge content={content} />}
            </Fragment>
        )}
    </div>;

}

FilterBadge.propTypes = {
    typeId: PropTypes.string.isRequired,
    fieldName: PropTypes.string.isRequired,
    value: PropTypes.arrayOf(PropTypes.shape({
        op: PropTypes.string.isRequired,
        content: PropTypes.any.isRequired
    })).isRequired
};

function SchemaParameterFilterBadge({ fieldInfo }) {
    const schemaId = fieldInfo.target[0], parameterId = fieldInfo.target[1];
    const typeId = useSelector(state => schemaSelector(state.filters, schemaId).type);
    const fullFieldName = useSelector(state => {
        const type = typeSelector(state.filters, typeId);
        const schema = schemaSelector(state.filters, schemaId);
        const schemaParam = schema.parameters[parameterId];
        if (!type || !schema || !schemaParam) {
            return "";
        } else {
            return `${type.full_name}.${schema.schema_name}.${schemaParam.full_name}`;
        }
    });
    if (fullFieldName === "") {
        return <InvalidFilterBadge />;
    } else {
        const filterValue = useSelector(
            state => {
                let value = schemaParamFilterValueSelector(state.filters, schemaId, parameterId);
                if (value && !Array.isArray(value)) {
                    value = [value];
                }
                return value;
            }
        );

        return <FilterBadge typeId={typeId} fieldName={fullFieldName} value={filterValue} />;
    }
}

function TypeAttributeFilterBadge({ fieldInfo }) {
    const typeId = fieldInfo.target[0], attributeId = fieldInfo.target[1];
    const fullFieldName = useSelector(state => {
        const type = typeSelector(state.filters, typeId);
        const attribute = type.attributes.byId[attributeId];
        if (!type || !attribute) {
            return "";
        } else {
            return `${type.full_name}.${attribute.full_name}`;
        }
    });
    if (fullFieldName === "") {
        return <InvalidFilterBadge />;
    } else {
        const filterValue = useSelector(
            state => {
                let value = typeAttrFilterValueSelector(state.filters, typeId, attributeId);
                if (value && !Array.isArray(value)) {
                    value = [value];
                }
                return value;
            }
        );
        return <FilterBadge typeId={typeId} fieldName={fullFieldName} value={filterValue} />;
    }
}

function QuickSearchBadge({ typeId, searchTerm }) {
    const type = useSelector(
        state => typeSelector(state.filters, typeId)
    );
    if (!type || !searchTerm) {
        return <InvalidFilterBadge />;
    } else {
        const searchTermAsBadgeValue = [{
            op: "contains",
            content: searchTerm
        }];
        return <FilterBadge
            fieldName={type.full_name}
            typeId={typeId}
            value={searchTermAsBadgeValue}
        />;
    }
}

function QuickSearchBadgeList() {
    const searchTermsById = useSelector(
        state => state.search.searchTerm || {}
    );
    const typesWithSearchTerms = Object.keys(searchTermsById);
    return <>{
        typesWithSearchTerms.map((typeId, index) => {
            const isLastFilter = index === typesWithSearchTerms.length - 1;
            return <Fragment key={typeId + "-search-term"}>
                <QuickSearchBadge
                    key={typeId}
                    typeId={typeId}
                    searchTerm={searchTermsById[typeId]}
                />
                {!isLastFilter ? <AndOperatorBadge /> : null}
            </Fragment>;
        })
    }</>;
}

function getFilterBadge(filterKind) {
    switch (filterKind) {
        case "typeAttribute":
            return TypeAttributeFilterBadge;
        case "schemaParameter":
            return SchemaParameterFilterBadge;
        default:
            break;
    }
}

function FilterSummaryFilterList() {
    // Fetch the dictionary of active filters and flatten it into an array.
    const activeFiltersByTypeId = useSelector(state => state.filters.activeFilters);
    const activeFilters = [];
    for (const typeId in activeFiltersByTypeId) {
        activeFiltersByTypeId[typeId].forEach(filter => {
            activeFilters.push(filter);
        });
    }

    return <>
        {activeFilters.map((filter, index) => {
            const isLastFilter = index === activeFilters.length - 1;
            const ApplicableFilterBadge = getFilterBadge(filter.kind);
            return <Fragment key={filter.kind + filter.target.join(",")}>
                <ApplicableFilterBadge fieldInfo={filter} />
                {!isLastFilter ? <AndOperatorBadge /> : null}
            </Fragment>;
        })
        }
    </>;
}

function ResetFiltersButton() {
    const dispatch = useDispatch();
    const onResetFilters = useCallback(
        () => {
            dispatch(resetFilters());
            dispatch(updateSearchTerm({
                searchTerm: {},
                replaceState: true
            }));
            dispatch(runSearch());
        },
        [dispatch]
    );
    const hasActiveFiltersOrSearchTerm = useSelector(state =>
        hasActiveFiltersSelector(state.filters) ||
        hasActiveSearchTermSelector(state.search)
    );
    if (!hasActiveFiltersOrSearchTerm) {
        return null;
    } else {
        return <Button variant="link" className="px-0" onClick={onResetFilters}>
            Reset
        </Button>;
    }
}

function BadgeList() {
    const hasSearchTerm = useSelector(
        state => hasActiveSearchTermSelector(state.search)
    );
    const hasFilters = useSelector(
        state => hasActiveFiltersSelector(state.filters)
    );
    if (hasSearchTerm || hasFilters) {
        return <div className=""><span>Showing results that match </span> 
            <QuickSearchBadgeList />
            {hasSearchTerm && hasFilters ? <AndOperatorBadge /> : null}
            <FilterSummaryFilterList />.
        </div>;
    } else {
        return <p className="mb-0">Showing all results. Use options on the left to refine your search.</p>;
    }
}
export default function FilterSummaryBox() {
    return (
        <div className="card">
            <div className="card-body">
                <BadgeList />
                <ResetFiltersButton />
            </div>
        </div>
    );
}
