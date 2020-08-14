import React, { useState, useContext } from 'react'
import Table from 'react-bootstrap/Table';
import PropTypes from 'prop-types';
import { FiPieChart, FiLock } from 'react-icons/fi';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Nav from 'react-bootstrap/Nav';
import Badge from 'react-bootstrap/Badge';
import { useSelector } from "react-redux";
import './ResultSection.css';

export function ResultTabs({counts, selectedType, onChange}) {

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
        resultName = result[NameColumn[type]];
    return (
        <tr className="result-section--row" onClick={onSelect} onKeyUp={onSelect} tabIndex="0" role="button">
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
                        <p>Searching...</p>
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
        <Table responsive hover>
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
    selectedItem: PropTypes.string,
    onItemSelect: PropTypes.func
}

export function ResultList(props) {
    const [selected, onSelect] = useState(null)
    return (
        <PureResultList
            selectedItem={selected}
            onItemSelect={onSelect}
            {...props}
        />
    )
}

export function PureResultSection({ resultSets, selected,
    onSelect, isLoading, error }) {
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

    const currentResultSet = resultSets[selected],
        currentCount = counts[selected];
    return (
        <>
            <ResultTabs counts={counts} selectedType={selected} onChange={onSelect} />
            <div role="tabpanel" className="result-section--tabpanel">
                {(!isLoading && !error) &&
                    <p className="result-section--count-summary">
                        <span>Showing {currentCount} {currentCount > 1 ? "results" : "result"}.</span>
                    </p>
                }
                <ResultList results={currentResultSet} isLoading={isLoading} error={error} />
            </div>
        </>
    )
}

export default function ResultSection() {
    const [selectedType, onSelect ] = useState('experiment'),
        searchInfo = useSelector(
            (state) => state.search
        );
    return (
        <PureResultSection
            resultSets={searchInfo.results}
            error={searchInfo.error}
            isLoading={searchInfo.isLoading}
            selected={selectedType}
            onSelect={onSelect}
        />
    )
}
