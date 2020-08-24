import { Button, Table } from 'react-bootstrap';
import React from 'react';
import './EntryPreviewCard.css'
import moment from 'moment';
import { FiUnlock, FiLock, FiX, FiPieChart } from 'react-icons/fi';
import {
    ProjectTabSticker,
    ExperimentTabSticker,
    DatasetTabSticker,
    DatafileTabSticker
} from '../TabStickers/TabSticker';

export default function EntryPreviewCard(props) {
    let { data, onClick } = props;
    let type;
    if (data) {
        type = data.type;
    }

    /**
     * Simply cuts of the time portion of the date
     * @param {*} date
     */
    const formatDate = (date) => {
        date = date.split('T')[0];
        let readableDate = moment(date).format("Do MMMM YYYY");
        return `${readableDate}.`;
    }

    /**
     * Gets the 'name' for the result type. fields differ depending on type.
     * @param {*} data
     * @param {*} type project, dataset or datafile
     */
    const getName = (data, type) => {
        switch (type) {
            case 'project':
                return data.name;
            case 'experiment':
                return data.title;
            case 'dataset':
                return `${data.description} #${data.id}`
            case 'datafile':
                return data.filename;
        }
    }

    /**
     *
     * @param {*} data the json reponse data.
     * @param {*} type project/exp/df/ds
     */
    const getDateAdded = (data, type) => {
        let date;
        switch (type) {
            case 'project':
                date = data.start_date;
                break;
            case 'experiment':
                date = data.created_time;
                break;
            case 'dataset':
                date = data.created_time;
                break;
            case 'datafile':
                date = data.created_time;
                break;
        }
        return (!!date ? formatDate(date) : null);
    }

    /**
     * Returns an html table of parameters.
     * @param {Object} parameters The parameter section of the response data.
     */
    const previewParameterTable = (parameters) => {
        return parameters.map((param, idx) => {
            return (
                <tr key={`preview-card__param-entry-${idx}`} className="parameter-table__row">
                    <td>{param.pn_name}</td>
                    <td>{param.value}</td>
                </tr>
            );
        });
    }

    /**
     * returns the datafile count and size informational text.
     * @param {*} data the json response
     * @param {*} type type of expected json response
     */
    const getDataSize = (data) => {
        return `${data.size}.`;
    }

    const getTabSticker = (type) => {
        switch (type) {
            case 'project':
                return <ProjectTabSticker></ProjectTabSticker>;
            case 'experiment':
                return <ExperimentTabSticker></ExperimentTabSticker>;
            case 'dataset':
                return <DatasetTabSticker></DatasetTabSticker>;
            case 'datafile':
                return <DatafileTabSticker></DatafileTabSticker>;
        }
    }

    const formatAccessText = (s) => {
        if (s === 'none') {
            s = "No";
        }
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    const DataTypeAccess = (props) => {
        let { data } = props;
        let accessText = `${formatAccessText(data.userDownloadRights)} access`
        switch (data.userDownloadRights) {
            case "full":
                return (
                    <div className="preview-card__access-status">
                        <span aria-label="This item can be downloaded."><FiUnlock /></span>
                        {accessText}
                    </div>
                )
            case "partial":
                return (
                    <div className="preview-card__access-status">
                        <span aria-label="This item can be downloaded."><FiPieChart /></span>
                        {accessText}
                    </div>
                )
            default:
                return (
                    <div className="preview-card__access-status">
                        <span aria-label="This item can be downloaded."><FiLock /></span>
                        {accessText}
                    </div>
                )
        }
    }
    /**
         *
         * @param {*} data project/exp/datafile/dataset json response data
         * @param {*} type project/exp/datafile/dataset
         */
        const FileCountSummary = (props) => {
            let { data, type } = props;
            let summary;
            let datafilePlural;
            let datasetPlural;
            let experimentPlural;
            if (data.counts) {
                datafilePlural = data.counts.datafiles <= 1 ? 'datafile' : 'datafiles';
                datasetPlural = data.counts.datasets <= 1 ? 'dataset' : 'datasets';
                experimentPlural = data.counts.experiments <= 1 ? 'experiment' : 'experiments';
            }
            switch (type) {
                case 'project':
                    summary = `Contains ${data.counts.datafiles} ${datafilePlural} from ${data.counts.datasets} ${datasetPlural}, across ${data.counts.experiments} ${experimentPlural}.`;
                    break;
                case 'experiment':
                    summary = `Contains ${data.counts.datafiles} ${datafilePlural} from ${data.counts.datasets} ${datasetPlural}.`;
                    break;
                case 'dataset':
                    summary = `Contains ${data.counts.datafiles} ${datafilePlural}.`;
                    break;
                default:
                    summary = null;
                    break;
            }
            if (summary) {
                return (
                    <div className="preview-card__count-detail">
                        {summary}
                    </div>
                )
            }
            return null;
        }

    const ParameterTable = (props) => {
        let { parameters } = props;
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
            )
        } else {
            return null;
        }
    }

    if (data === null) {
        return (
            <div className="preview-card__body">
                Please select a row to view the details.
            </div>
        )
    }
    return (
        <div className="preview-card__body">
            <span className="preview-card__close" aria-label="Close preview panel">
                {/* <button onClick={onClick}>
                    <FiX />
                </button> */}
            </span>
            <div className="preview-card__header">
                <div >
                    {getTabSticker(type)}
                </div>
                <h5>
                    {getName(data, type)}
                </h5>
            </div>
            <DataTypeAccess data={data}></DataTypeAccess>
            <div className="preview-card__count-detail">
                {getDataSize(data, type)}
            </div>
            <FileCountSummary data={data} type={type}></FileCountSummary>
            { !getDateAdded(data,type) ? null :
                <div className="preview-card__date-added">
                    Added on the {getDateAdded(data, type)}
                </div>
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
