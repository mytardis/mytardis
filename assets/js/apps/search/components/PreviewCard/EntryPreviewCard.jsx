//todo:
// add reference to url field. - done
// moment js for date.
import { Button, Table } from 'react-bootstrap';
import React from 'react';
import './EntryPreviewCard.css'
import { FiUnlock, FiLock, FiX } from 'react-icons/fi';
import {
    ProjectTabSticker,
    ExperimentTabSticker,
    DatasetTabSticker,
    DatafileTabSticker
} from '../TabStickers/TabSticker';

export const EntryPreviewCard = (props) => {
    let { data, type } = props;

    /**
     * Simply cuts of the time portion of the date
     * @param {*} date 
     */
    const formatDate = (date) => {
        return date.split('T')[0];
    }

    /**
     * Simply rewords raw json field name
     * @param {*} access 
     */
    const determineAccess = (access) => {
        return access === "partial" ? "Unavailable" : "Available";
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
        return (!!date ? formatDate(date) : 'Unknown');
    }

    /**
     * Returns an html table of parameters.
     * @param {Object} parameters The parameter section of the response data.
     */
    const previewParameterTable = (parameters) => {
        return parameters.map((param, idx) => {
            if (param.sensitive !== "False") {
                return;
            }
            return (
                <tr key={`preview-card__param-entry-${idx}`} className="parameter-table__row">
                    <td>{param.pn_id}</td>
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
    const getDataSize = (data, type) => {
        switch (type) {
            case 'datafile':
                return `${data.size}.`
            default:
                return `${data.counts.datafiles} datafiles, ${data.size}.`
        }
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

    const DataTypeAccess = (props) => {
        let { data } = props;
        if (data.userDownloadRights === "Unavailable") {
            return (
                <div className="preview-card__access-status">
                    <span aria-label="This item cannot be downloaded."><FiLock /></span>
                    {`${determineAccess(data.userDownloadRights)}`}
                </div>
            )
        } else {
            return (
                <div className="preview-card__access-status">
                    <span aria-label="This item can be downloaded."><FiUnlock /></span>
                    {`${determineAccess(data.userDownloadRights)}`}
                </div>
            )
        }
    }

    /**
     * 
     * @param {*} data project/exp/datafile/dataset json response data
     * @param {*} type project/exp/datafile/dataset
     */
    const DeepCountSummary = (props) => {
        let { data, type } = props;
        let summary;
        switch (type) {
            case 'project':
                summary = `Contains ${data.counts.datafiles} datafiles from ${data.counts.datasets} datasets.`;
                break;
            case 'experiment':
                summary = `Contains ${data.counts.datafiles} datafiles from ${data.counts.datasets} datasets.`;
                break;
            case 'dataset':
                summary = `Contains ${data.counts.datafiles} datafiles.`;
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

    return (
        <div className="preview-card__body">
            <span className="preview-card__close" aria-label="Close preview panel">
                <button onClick={props.onClick}>
                    <FiX />
                </button>
            </span>
            <div className="preview-card__header">
                <div >
                    {getTabSticker(type)}
                </div>
                <h3>
                    {getName(data, type)}
                </h3>
            </div>
            <DataTypeAccess data={data}></DataTypeAccess>
            <div className="preview-card__count-detail">
                {getDataSize(data, type)}
            </div>
            <DeepCountSummary data={data} type={type}></DeepCountSummary>
            <div className="preview-card__date-added">
                Added on {getDateAdded(data, type)}
            </div>
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
            <div className="preview-card__button-wrapper--right">
                <div className="preview-card__inline-block-wrapper">
                    <Button variant="primary" className="preview-card__button--right" href={data.url}>View details</Button>
                </div>
            </div>
        </div>
    );
}