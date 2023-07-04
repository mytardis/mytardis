/* eslint-disable camelcase */
import React, { useCallback, useMemo } from "react";
import { DropdownButton, Dropdown, Form } from "react-bootstrap";
import { SORT_ORDER, updateResultSort, removeResultSort, activeSortSelector, runSingleTypeSearch, sortableAttributesSelector, sortOrderSelector } from "../searchSlice";
import { useSelector, useDispatch } from "react-redux";
import PropTypes from "prop-types";
import { AiOutlineSortAscending, AiOutlineSortDescending } from "react-icons/ai";
import "./SortOptionsList.css";

const getSortSummaryText = (activeAttributes) => {
    if (activeAttributes.length === 0) {
        return "Sort";
    } else if (activeAttributes.length === 1) {
        return `Sort: ${activeAttributes[0].full_name}`;
    } else {
        return `Sort: ${activeAttributes[0].full_name} and ${activeAttributes.length - 1} more`;
    }
};
export function PureSortOptionsList({attributesToSort = [], activeSort, onSortUpdate, onSortRemove}) {
    if (!activeSort) {
        activeSort = [];
    }
    // Generate a hashmap of attributes and their sort options by ID for easier lookup.
    const attributeMap = useMemo(() => {
        const attrMap = {};
        attributesToSort.forEach(attribute => {
            const attributeSortIndex = activeSort.findIndex(sortId => sortId === attribute.id);
            const hasActiveSort = attributeSortIndex !== -1;
            const priority = hasActiveSort ? attributeSortIndex + 1 : undefined;
            attrMap[attribute.id] = { attribute, hasActiveSort, priority };
        });
        return attrMap;
    }, [attributesToSort, activeSort]);

    const activeAttributes = useMemo(() => (
        activeSort.map(sort => (attributeMap[sort].attribute))
    ), [activeSort, attributeMap]);

    const handleActiveClicked = useCallback((attribute, e) => {
        e.stopPropagation();
        e.preventDefault();
        // Toggle active sort state depending on current state.
        if (attributeMap[attribute.id].hasActiveSort) {
            onSortRemove(attribute.id);
        } else {
            onSortUpdate(attribute.id, attribute.order);
        }
    }, [attributeMap, onSortUpdate, onSortRemove]);
    const handleOrderClicked = useCallback((attribute, order, e) => {
        e.stopPropagation();
        e.preventDefault();
        if (attribute.order !== order) {
            onSortUpdate(attribute.id, order);
        }
    }, [onSortUpdate]);
    const hasActiveSort = activeSort.length > 0;
    const shouldDisplayPriority = activeSort.length > 1;
    return (      
        <DropdownButton 
            title={<>
                <AiOutlineSortAscending />
                <span>
                    { getSortSummaryText(activeAttributes) }
                </span>
            </>} 
            variant={hasActiveSort ? "primary" : "outline-primary"}
            className="sortoptions"
            menuRole="menu"
        >
            {
                attributesToSort.map(attribute => {
                    const { id, full_name, order } = attribute;
                    const isActive = attributeMap[id].hasActiveSort;
                    const priority = attributeMap[id].priority;
                    return (
                        <Dropdown.ItemText
                            as="div" 
                            key={id} 
                            className="sortoptions--item row-primary" 
                            role="menuitem"
                            onClick={handleActiveClicked.bind(this, attribute)}
                        >
                            <span className="sortoptions-item--check">
                                <Form.Check
                                    checked={isActive}
                                    onClick={handleActiveClicked.bind(this, attribute)}
                                    type="checkbox"
                                    id={id + "-sort-active"}
                                />
                            </span>
                            <span className="sortoptions-item--label">
                                <label htmlFor={id + "-sort-active"}>
                                    {full_name}
                                </label>
                            </span>
                            <span 
                                className="sortoptions-item--sortorder-asc"
                                role="menuitemradio" 
                                onClick={handleOrderClicked.bind(this, attribute, SORT_ORDER.ascending)}    
                            >
                                <Form.Check
                                    checked={order === SORT_ORDER.ascending}
                                    onClick={handleOrderClicked.bind(this, attribute, SORT_ORDER.ascending)}
                                    type="radio"
                                    name={id + "-sort-order"}
                                    id={id + "-sort-asc"}
                                />
                                <label htmlFor={id + "-sort-asc"}>
                                    <AiOutlineSortAscending /><span className="sr-only">Sort ascending</span>
                                </label>
                            </span>
                            <span 
                                className="sortoptions-item--sortorder-desc"
                                role="menuitemradio"
                                onClick={handleOrderClicked.bind(this, attribute, SORT_ORDER.descending)}
                            >
                                <Form.Check
                                    checked={order === SORT_ORDER.descending}
                                    onClick={handleOrderClicked.bind(this, attribute, SORT_ORDER.descending)}
                                    type="radio"
                                    name={id + "-sort-order"}
                                    id={id + "-sort-desc"}
                                />
                                <label htmlFor={id + "-sort-desc"}>
                                    <AiOutlineSortDescending /><span className="sr-only">Sort descending</span>
                                </label>
                            </span>
                            <span className="sortoptions-item--priority">
                                {shouldDisplayPriority ? priority : null}
                            </span>
                        </Dropdown.ItemText>
                    ); 
                })
            }
        </DropdownButton>
    );
}

PureSortOptionsList.propTypes = {
    attributesToSort: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        full_name: PropTypes.string.isRequired,
        order: PropTypes.string
    })).isRequired,
    activeSort: PropTypes.arrayOf(PropTypes.string),
    onSortUpdate: PropTypes.func.isRequired,
    onSortRemove: PropTypes.func.isRequired
};

export default function SortOptionsList({typeId}) {

    const dispatch = useDispatch();
    const allSortOptions = useSelector(state => {
        const sortableAttributes = sortableAttributesSelector(state.filters, typeId);
        return sortableAttributes.map(({id, full_name}) => {
            const order = sortOrderSelector(state.search, typeId, id);
            return {
                id,
                full_name,
                order
            };
        });
    });
    const activeSort = useSelector(state => activeSortSelector(state.search, typeId));

    const handleSortUpdate = useCallback((attributeId, order) => {
        dispatch(updateResultSort({
            typeId,
            attributeId,
            order
        }));
        dispatch(runSingleTypeSearch(typeId));
    }, [dispatch, typeId]);

    const handleSortRemove = useCallback(attributeId => {
        dispatch(removeResultSort({
            typeId,
            attributeId
        }));
        dispatch(runSingleTypeSearch(typeId));
    }, [dispatch, typeId]);

    return (
        <PureSortOptionsList 
            activeSort={activeSort}
            attributesToSort={allSortOptions}
            onSortRemove={handleSortRemove}
            onSortUpdate={handleSortUpdate}
        />
    );
}

SortOptionsList.propTypes = {
    typeId: PropTypes.string.isRequired
};