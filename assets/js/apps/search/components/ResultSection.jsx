import React, { useState, useContext } from 'react'
import Table from 'react-bootstrap/Table';
import PropTypes from 'prop-types';
import { FiPieChart, FiLock } from 'react-icons/fi';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Nav from 'react-bootstrap/Nav';
import Badge from 'react-bootstrap/Badge';
import { useSelector, useDispatch } from "react-redux";
import { updateSelectedResult, updateSelectedType } from "./searchSlice";
import './ResultSection.css';
import EntryPreviewCard from './PreviewCard/EntryPreviewCard';

export function ResultTabs({ counts, selectedType, onChange }) {

    if (!counts) {
        counts = {
            experiment: null,
            dataset: null,
            datafile: null,
            project: null
        }
    }

    const handleNavClicked = (key) => {
        if (key !== selectedType) {
            onChange(key);
        }
    }

    const renderTab = (key, label) => {
        // const badgeVariant = selectedType === key ? "primary":"secondary";
        const badgeVariant = "secondary";
        return (
            <Nav.Item role="tab">
                <Nav.Link onSelect={handleNavClicked.bind(this, key)} eventKey={key}>
                    {label} {counts[key] !== null &&
                        <Badge variant={badgeVariant}>
                            {counts[key]} <span className="sr-only">{counts[key] > 1 ? "results" : "result"}</span>
                        </Badge>}</Nav.Link>
            </Nav.Item>
        );
    }

    return (
        <Nav variant="tabs" activeKey={selectedType}>
            {renderTab("project", "Projects", counts.datafile, selectedType)}
            {renderTab("experiment", "Experiments", counts.experiment, selectedType)}
            {renderTab("dataset", "Datasets", counts.dataset, selectedType)}
            {renderTab("datafile", "Datafiles", counts.datafile, selectedType)}
        </Nav>
    )
}

ResultTabs.propTypes = {
    counts: PropTypes.shape({
        project: PropTypes.number,
        experiment: PropTypes.number,
        dataset: PropTypes.number,
        datafile: PropTypes.number
    }),
    selectedType: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired
}


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
        <tr className={isSelected ? "result-section--row table-active" : "result-section--row" } onClick={onSelect} onKeyUp={onKeyboardSelect} tabIndex="0" role="button">
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
    let body;
    const handleItemSelected = (id) => {
        onItemSelect(id);
    }

    if (error) {
        return (
            // If there was an error during the search
            <div className="result-section--msg result-section--error-msg">
                <p>An error occurred. Please try another query, or refresh the page and try searching again.</p>
            </div>
        );
    }

    else if (isLoading) {
        body = (
            // If the search is in progress.
            <tr>
                <td colSpan="3">
                    <div className="result-section--msg">
                        <p>Loading...</p>
                    </div>
                </td>
            </tr>
        );
    }

    else if (!results ||
        (Array.isArray(results) && results.length == 0)) {
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
        <Table className="result-section__container" responsive hover>
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
        </Table>
    )
}

PureResultList.propTypes = {
    results: PropTypes.arrayOf(Object),
    error: PropTypes.string,
    isLoading: PropTypes.bool,
    selectedItem: PropTypes.number,
    onItemSelect: PropTypes.func
}

export function PureResultSection({ resultSets, selectedType,
    onSelectType, selectedResult, onSelectResult, isLoading, error }) {
    let counts;
    if (!resultSets) {
        resultSets = {};
        counts = {
            project: null,
            experiment: null,
            dataset: null,
            datafile: null
        }
    } else {
        counts = {};
        for (let key in resultSets) {
            counts[key] = resultSets[key].length;
        }
    }

        let selectedEntry = getSelectedEntry(resultSets, selectedResult, selectedType);

        const currentResultSet = resultSets[selectedType],
            currentCount = counts[selectedType];
        return (
            <>
                <ResultTabs counts={counts} selectedType={selectedType} onChange={onSelectType} />
                <div role="tabpanel" className="result-section--tabpanel">
                    {(!isLoading && !error) &&
                        <p className="result-section--count-summary">
                            <span>Showing {currentCount} {currentCount > 1 ? "results" : "result"}.</span>
                        </p>
                    }
                    <div className="tabpanel__container--horizontal">
                        <PureResultList results={currentResultSet} selectedItem={selectedResult} onItemSelect={onSelectResult} isLoading={isLoading} error={error} />
                        {(!isLoading && !error && currentCount > 0) &&
                            <EntryPreviewCard
                                data={selectedEntry}
                            />
                        }
                    </div>
                </div>
            </>
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
            onSelectType = (type) => {
                dispatch(updateSelectedType(type));
            },
            onSelectResult = (selectedResult) => {
                dispatch(updateSelectedResult(selectedResult));
            },
            searchInfo = useSelector(
                (state) => state.search
            );
        return (
            <PureResultSection
                resultSets={searchInfo.results}
                error={searchInfo.error}
                isLoading={searchInfo.isLoading}
                selectedType={selectedType}
                onSelectType={onSelectType}
                selectedResult={selectedResult}
                onSelectResult={onSelectResult}
            />
        )
    }
