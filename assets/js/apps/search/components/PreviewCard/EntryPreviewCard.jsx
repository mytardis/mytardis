import { Button, Table } from "react-bootstrap";
import React from "react";
import { toggleShowSensitiveData } from "../searchSlice";
import "./EntryPreviewCard.css";
import moment from "moment";
import { FiUnlock, FiLock, FiPieChart } from "react-icons/fi";
import Switch from "react-switch";
import {
    OBJECT_TYPE_STICKERS
} from "../TabStickers/TabSticker";
import { useSelector, useDispatch } from "react-redux";
import PropTypes from "prop-types";

/**
     * Simply cuts of the time portion of the date
     * @param {*} date
     */
const formatDate = (date) => {
    date = date.split("T")[0];
    let readableDate = moment(date).format("Do MMMM YYYY");
    return `${readableDate}.`;
};

/**
     *
     * @param {*} data the json reponse data.
     * @param {*} type project/exp/df/ds
     */
const getDateAdded = (data, type) => {
    const DATE_ADDED_FIELD_BY_TYPE = {
        "project": "start_time",
        "experiment": "created_time",
        "dataset": "created_time",
        "datafile": "created_time"
    };
    const dateField = DATE_ADDED_FIELD_BY_TYPE[type];
    const date = data[dateField];
    return (date ? formatDate(date) : null);
};

/**
     * Gets the 'name' for the result type. fields differ depending on type.
     * @param {*} data
     * @param {*} type project, dataset or datafile
     */
const getName = (data, type) => {
    const NAME_FIELD_BY_TYPE = {
        "project": "name",
        "experiment": "title",
        "dataset": "description",
        "datafile": "filename"
    };
    const nameField = NAME_FIELD_BY_TYPE[type];
    return data[nameField];
};

/**
     * returns the datafile count and size informational text.
     * @param {*} data the json response
     * @param {*} type type of expected json response
     */
const getDataSize = (data) => {
    return `${data.size}.`;
};

const DataTypeAccess = ({downloadRights}) => {

    const formatAccessText = (s) => {
        if (s === "none") {
            s = "No";
        }
        return s.charAt(0).toUpperCase() + s.slice(1);
    };

    let accessText = `${formatAccessText(downloadRights)} access`;
    switch (downloadRights) {
        case "full":
            return (
                <div className="preview-card__access-status">
                    <span aria-label="This item can be downloaded."><FiUnlock /></span>
                    {accessText}
                </div>
            );
        case "partial":
            return (
                <div className="preview-card__access-status">
                    <span aria-label="This item can be downloaded."><FiPieChart /></span>
                    {accessText}
                </div>
            );
        default:
            return (
                <div className="preview-card__access-status">
                    <span aria-label="This item can be downloaded."><FiLock /></span>
                    {accessText}
                </div>
            );
    }
};

DataTypeAccess.propTypes = {
    downloadRights: PropTypes.string.isRequired
};

/**
     * Component showing a summary of the file counts under a MyTardis object.
     * @param {Object} counts An object of the number of file counts for object types under this object.
     * @param {String} type MyTardis type ID
     */
const FileCountSummary = ({ counts, type }) => {
    let datafilePlural;
    let datasetPlural;
    let experimentPlural;
    const pluralise = (count, noun) => (
        count !== 1 ? noun + "s" : noun
    );
    const getSummaryText = () => {
        if (counts) {
            datafilePlural = pluralise(counts.datafiles, "datafile");
            datasetPlural = pluralise(counts.datasets, "dataset");
            experimentPlural = pluralise(counts.experiments, "experiment");
        }    
        switch (type) {
            case "project":
                return `Contains ${counts.datafiles} ${datafilePlural} from ${counts.datasets} ${datasetPlural}, across ${counts.experiments} ${experimentPlural}.`;
            case "experiment":
                return `Contains ${counts.datafiles} ${datafilePlural} from ${counts.datasets} ${datasetPlural}.`;
            case "dataset":
                return `Contains ${counts.datafiles} ${datafilePlural}.`;
            default:
                return null;
        }    
    };
    const summary = getSummaryText();
    if (summary) {
        return (
            <div className="preview-card__count-detail">
                {summary}
            </div>
        );
    }
    return null;
};

FileCountSummary.propTypes = {
    counts: PropTypes.object,
    type: PropTypes.string.isRequired
};


export default function EntryPreviewCard({ data }) {
    let type;
    if (data) {
        type = data.type;
    }

    // setting up redux logic
    let showSensitiveData = useSelector(state => state.search.showSensitiveData);
    const dispatch = useDispatch(),
        toggleSensitiveData = () => {
            dispatch(toggleShowSensitiveData());
        };

    /**
     * Returns an table of parameters.
     * @param {Object} parameters The parameter section of the response data.
     */
    const previewParameterTable = (parameters) => {
        return parameters.map((param, idx) => {
            if (param.hasOwnProperty("sensitive")) {
                if (showSensitiveData) {
                    return (
                        <tr key={`preview-card__param-entry-${idx}`} className="parameter-table__row">
                            <td style={{ backgroundColor: "#fcfba2" }}>{" " + param.pn_name}</td>
                            <td style={{ backgroundColor: "#fcfba2" }}><FiUnlock></FiUnlock>{" " + param.value}</td>
                        </tr>
                    );
                } else {
                    return (
                        <tr key={`preview-card__param-entry-${idx}`} className="parameter-table__row">
                            <td >{" " + param.pn_name}</td>
                            <td ><FiLock aria-label="Sensitive parameter value"></FiLock><em role="button" onClick={toggleSensitiveData}> Click to show.</em></td>
                        </tr>
                    );
                }
            } else {
                return (
                    <tr key={`preview-card__param-entry-${idx}`} className="parameter-table__row">
                        <td>{param.pn_name}</td>
                        <td>{param.value}</td>
                    </tr>
                );
            }
        });
    };

    /**
     * Given a MyTardis object's parameters, checks if the sensitive values switch
     * should be shown.
     * @param {Array} parameters The array of object parameters.
     */
    const shouldShowSensitiveValuesSwitch = (parameters) => (
        parameters.length > 0 &&
        parameters.filter(param => param.hasOwnProperty("sensitive")).length > 0
    );

    /**
     * The parameter table component
     * @param {*} props
     */
    const ParameterTable = ({ parameters }) => {
        if (parameters.length > 0) {
            return (
                <Table striped bordered hover size="sm" className="preview-card__parameter-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {previewParameterTable(data.parameters)}
                    </tbody>
                </Table>
            );
        } else {
            return null;
        }
    };

    if (data === null) {
        return (
            <div className="preview-card__body">
                Please select a row to view the details.
            </div>
        );
    }

    function renderTypeSticker() {
        const TypeSticker = OBJECT_TYPE_STICKERS[type];
        return <TypeSticker />;
    }

    return (
        <div className="preview-card__body">
            <span className="preview-card__close" aria-label="Close preview panel">
            </span>
            <div className="preview-card__header">
                <div >
                    {renderTypeSticker()}
                </div>
                <h5>
                    {getName(data, type)}
                </h5>
            </div>
            <DataTypeAccess downloadRights={data.userDownloadRights} />
            <div className="preview-card__count-detail">
                {getDataSize(data, type)}
            </div>
            <FileCountSummary counts={data.counts} type={type} />
            { !getDateAdded(data, type) ? null :
                <div className="preview-card__date-added">
                    Added on the {getDateAdded(data, type)}
                </div>
            }
            { shouldShowSensitiveValuesSwitch(data.parameters) &&
                <label htmlFor="showSensitiveDataSwitch" aria-label="Toggle sensitive data label" className="switch__label">
                    <span className="sensitive__label-text"><b>Show sensitive values</b></span>
                    <Switch
                        id="showSensitiveDataSwitch"
                        aria-label="Toggle sensitive data switch"
                        onChange={toggleSensitiveData}
                        checked={showSensitiveData}
                        checkedIcon={false}
                        uncheckedIcon={false}
                        height={20}
                        width={40}
                        handleDiameter={25}
                        onHandleColor={"#007bff"}
                        onColor={"#a3cfff"}
                        boxShadow={"0 0 1px 1px #8a8a8a"}
                    />
                </label>
            }
            <ParameterTable parameters={data.parameters} />
            <div className="preview-card__button-wrapper--right">
                <div className="preview-card__inline-block-wrapper">
                    <Button variant="primary" className="preview-card__button--right" target="_blank" href={data.url}>View details</Button>
                </div>
            </div>
        </div>
    );
}

EntryPreviewCard.propTypes = {
    data: PropTypes.object
};