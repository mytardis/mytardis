import React, {  useCallback } from 'react'
import PropTypes from 'prop-types';
import { FiPieChart, FiLock, FiRefreshCcw } from 'react-icons/fi';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Nav from 'react-bootstrap/Nav';
import { useSelector, useDispatch } from "react-redux";
import { updateSelectedResult, updateSelectedType, totalHitsSelector, pageSizeSelector, pageFirstItemIndexSelector } from "./searchSlice";
import './ResultSection.css';
import EntryPreviewCard from './PreviewCard/EntryPreviewCard';
import Pager from "./sort-paginate/Pager";
import SortOptionsList from './sort-paginate/SortOptionsList';
import { typeSelector } from './filters/filterSlice';
import Button from "react-bootstrap/Button";

export function PureResultTabs({ counts, selectedType, onChange }) {
    const handleNavClicked = (key) => {
        if (key !== selectedType) {
            onChange(key);
        }
    };

    return (
        <Nav variant="tabs" activeKey={selectedType}>
            {counts.map(({ id, name, hitTotal }) => (
                <Nav.Item role="tab" key={id}>
                    <Nav.Link onSelect={handleNavClicked.bind(this, id)} eventKey={id}>
                        <span className="text-capitalize">{name}</span> {hitTotal !== null &&
                            <span>
                                (
                                {hitTotal}
                                <span className="sr-only">
                                    {hitTotal > 1 ? " results" : " result"}
                                </span>
                                )
                            </span>
                        }
                    </Nav.Link>
                </Nav.Item>
            ))}
        </Nav>
    );
}

PureResultTabs.propTypes = {
    counts: PropTypes.arrayOf(PropTypes.shape({
        name: PropTypes.string.isRequired,
        id: PropTypes.string.isRequired,
        hitTotal: PropTypes.number
    })).isRequired,
    selectedType: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired
};

export const ResultTabs = () => {
    const selectedType = useSelector(state => state.search.selectedType);
    const dispatch = useDispatch();
    const onSelectType = useCallback(
        (type) => {
            dispatch(updateSelectedType(type));
        },
        [dispatch]);
    const hitTotalsByType = useSelector(state => {
        // Returns a list of object types, along with the number of hits they have.
        // If there aren't any results, then we return a null (which is different from a search being done with zero results)
        const hitTotals = state.search.results ? state.search.results.totalHits : null;
        return state.filters.types.allIds.map(
            typeId => {
                const typeCollectionName = typeSelector(state.filters, typeId).collection_name;
                return {
                    name: typeCollectionName,
                    id: typeId,
                    hitTotal: hitTotals ? hitTotals[typeId] : null
                };
            }
        );
    });
    return (<PureResultTabs counts={hitTotalsByType} selectedType={selectedType} onChange={onSelectType} />);
};




const NameColumn = {
    "project": "name",
    "experiment": "title",
    "dataset": "description",
    "datafile": "filename"
};

export function ResultRow({ result, onSelect, isSelected }) {
    const type = result.type,
        resultName = result[NameColumn[type]],
        onKeyboardSelect = (e) => {
            // Only respond to Enter key selects.
            if (e.key !== "Enter") {
                return;
            }
            onSelect(e);
        };
    return (
        <tr className={isSelected ? "result-section--row row-active-primary" : "result-section--row row-primary"} onClick={onSelect} onKeyUp={onKeyboardSelect} tabIndex="0" role="button">
            <td className="result-row--download-col">
                {result.userDownloadRights == "none" &&
                    <OverlayTrigger overlay={
                        <Tooltip id="tooltip-no-download">
                            You can't download this item.
                            </Tooltip>
                    }>
                        <span><FiLock title="This item cannot be downloaded." /></span>
                    </OverlayTrigger>
                }
                {result.userDownloadRights == "partial" &&
                    <OverlayTrigger overlay={
                        <Tooltip id="tooltip-partial-download">
                            You can't download some files in this item.
                            </Tooltip>
                    }>
                        <span><FiPieChart title="Some files cannot be downloaded." /></span>
                    </OverlayTrigger>
                }
            </td>
            <td><a target="_blank" href={result.url}>{resultName}</a></td>
            <td>
                {result.userDownloadRights != "none" &&
                    <span>{result.size}</span>
                }
                {result.userDownloadRights == "none" &&
                    <span aria-label="Not applicable">&mdash;</span>
                }
            </td>
        </tr>
    )
}

ResultRow.propTypes = {
    result: PropTypes.object.isRequired,
    onSelect: PropTypes.func.isRequired,
    isSelected: PropTypes.bool.isRequired
}

export function PureResultList({ results, selectedItem, onItemSelect, error, isLoading }) {
    results = results || [];
    let body, listClassName = "result-section__container";
    const handleItemSelected = (id) => {
        if (isLoading) {
            // During loading, we disable selecting for preview card.
            return;
        }
        onItemSelect(id);
    };

    if (isLoading) {
        // Add the loading class to show effect.
        listClassName += " loading";
    }

    if (error) {
        return (
            // If there was an error during the search
            <div className="result-section--msg result-section--error-msg">
                <p>An error occurred. Please try another query, or reload the page and try searching again.</p>
                <p><Button onClick={() => location.assign("/search")}><FiRefreshCcw /> Reload</Button></p>
            </div>
        );
    }

    else if (!isLoading && results.length == 0) {
        // If the results are empty...
        body = (
            <tr>
                <td colSpan="3">
                    <div className="result-section--msg">
                        <p>No results. Please adjust your search and try again.</p>
                    </div>
                </td>
            </tr>
        )
    }

    else {
        // Render the results in table.
        body = results.map((result) => (
            <ResultRow key={result.id}
                onSelect={handleItemSelected.bind(this, result.id)}
                result={result}
                isSelected={result.id === selectedItem}
            />
        ));
    }

    return (
        <div className={listClassName}>
            <table className="table">
                <thead>
                    <tr>
                        <th></th>
                        <th>Name</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tbody>
                    {body}
                </tbody>
            </table>
        </div>
    )
}

PureResultList.propTypes = {
    results: PropTypes.arrayOf(Object),
    error: PropTypes.string,
    isLoading: PropTypes.bool,
    selectedItem: PropTypes.number,
    onItemSelect: PropTypes.func
}

const ResultSummary = ({typeId}) => {
    const currentCount = useSelector(state => totalHitsSelector(state.search, typeId));
    const currentPageSize = useSelector(state => pageSizeSelector(state.search, typeId));
    const currentFirstItem = useSelector(state => pageFirstItemIndexSelector(state.search, typeId));
    const currentLastItem = Math.min(currentCount, currentFirstItem + currentPageSize - 1);
    return (
        <p className="result-section--count-summary">
            <span>Showing {currentFirstItem} - {currentLastItem} of {currentCount} {currentCount > 1 ? "results" : "result"}.</span>
        </p>
    );
};

export function PureResultSection({ resultSets, selectedType,
    selectedResult, onSelectResult, isLoading, error }) {
    let selectedEntry = getSelectedEntry(resultSets, selectedResult, selectedType);
    const currentResultSet = resultSets ? resultSets[selectedType] : null;
    return (
        <section className="d-flex flex-column flex-grow-1 overflow-hidden">
            <ResultTabs />
            <div role="tabpanel" className="result-section--tabpanel">
                {!error &&
                    <>
                    <ResultSummary typeId={selectedType} />
                    <SortOptionsList typeId={selectedType} />
                    </>
                }
                <div className="tabpanel__container--horizontal">
                    <PureResultList results={currentResultSet} selectedItem={selectedResult} onItemSelect={onSelectResult} isLoading={isLoading} error={error} />
                    {!error &&
                        <EntryPreviewCard
                            data={selectedEntry}
                        />
                    }
                </div>
                {!error &&
                    <Pager objectType={selectedType} />
                }
            </div>
        </section>
    )
}


/**
 * Returns the data of the selected row. Returns null if it cannot get find the selected result.
 * @param {*} resultSets
 * @param {*} selectedResult
 * @param {*} selectedType
 */
function getSelectedEntry(resultSets, selectedResult, selectedType) {
    let selectedEntry = null;
    if (resultSets && selectedResult) {
        selectedEntry = resultSets[selectedType].filter(result => result.id === selectedResult)[0];
    }
    return selectedEntry;
}

export default function ResultSection() {
    const selectedType = useSelector(state => state.search.selectedType),
        selectedResult = useSelector(state => state.search.selectedResult),
        dispatch = useDispatch(),
        onSelectResult = (selectedResult) => {
            dispatch(updateSelectedResult(selectedResult));
        },
        resultSets = useSelector(
            (state) => state.search.results ? state.search.results.hits : null
        ),
        error = useSelector(
            (state) => state.search.error
        ),
        isLoading = useSelector(
            (state) => state.search.isLoading
        );

    return (
        <PureResultSection
            resultSets={resultSets}
            error={error}
            isLoading={isLoading}
            selectedType={selectedType}
            selectedResult={selectedResult}
            onSelectResult={onSelectResult}
        />
    )
}
