import { Button, Table } from 'react-bootstrap';
import React from 'react';
import './EntryPreviewCard.css'

export default function EntryPreviewCard(props) {


    
    let data = props.data;

    /**
     * Simply cuts of the time portion of the date
     * @param {*} date 
     */
    const formatDate = (date) => {
        return data.start_date.split('T')[0];
    }

    /**
     * Simply rewords raw json field name
     * @param {*} access 
     */
    const determineAccess = (access) => {
        return access === "partial" ? "Unavailable" : "Available";

    }

    /**
     * Returns an html table of parameters.
     * @param {Object} parameters The parameter section of the response data.
     */
    const previewParameterTable = (parameters) => {
        return parameters.map((param) => {
            if (param.sensitive !== "False") {
                return;
            }
            return (
                <tr className="parameter-table__row">
                    <td className="">{param.pn_id}</td>
                    <td>{param.value}</td>
                </tr>
            );
        });
    }

    //todo:
    // add lock icon based on accessibility
    // add tabsticker based on preview type (project/df/ds)
    // get actual parameter field name rather than parameter id.start_date
    // make variant for datafile preview.start_date
    // make variant for dataset preview.
    return (
        <div className="preview-card__body">
            <h1>{data.name}</h1>
            <div className="preview-card__access-status">
                {determineAccess(data.userDownloadRights)}
            </div>
            <div className="preview-card__count-detail">
                {`${data.counts.datafiles} datafiles, ${data.size}.`}
            </div>
            <div className="preview-card__count-detail">
                {`Contains ${data.counts.datafiles} datafiles from ${data.counts.datasets} datasets.`}
            </div>
            <div className="preview-card__date-added">
                Added on: {formatDate(data.date)}
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
                    <Button className="preview-card__button--right" href={`view/project/${data.id}`} variant="link">View details</Button>
                </div>
            </div>
        </div>
    );
}

// EXAMPLE JSONS FOR REFe

    // PROJECT ========
    // const data = {
    // counts": {
    //     "datafiles": 2,
    //     "datasets": 1,
    //     "experiments": 1
    //   },
    //   "description": "If you can see this and are not called Mike(or Noel) then the permissions have gone wrong",
    //   "end_date": null,
    //   "id": 1,
    //   "institution": [
    //     {
    //       "name": "Mikes ACL Institution"
    //     }
    //   ],
    //   "lead_researcher": {
    //     "username": "mlav736"
    //   },
    //   "name": "Mikes_ACL_Project",
    //   "parameters": [
    //     {
    //       "data_type": "STRING",
    //       "pn_id": "18",
    //       "sensitive": "False",
    //       "value": ""
    //     },
    //     {
    //       "data_type": "NUMERIC",
    //       "pn_id": "19",
    //       "sensitive": "False",
    //       "value": "7.0"
    //     },
    //     {
    //       "data_type": "STRING",
    //       "pn_id": "15",
    //       "sensitive": "False",
    //       "value": "Kiwi"
    //     },
    //     {
    //       "data_type": "STRING",
    //       "pn_id": "16",
    //       "sensitive": "False",
    //       "value": "Orange"
    //     }
    //   ],
    //   "size": "460.3 KB",
    //   "start_date": "2020-05-07T21:34:44+00:00",
    //   "userDownloadRights": "partial"
    // }


    // experiment ====
    // {
    //     "counts":{
    //        "datafiles":2,
    //        "datasets":1
    //     },
    //     "created_by":{
    //        "username":"mlav736"
    //     },
    //     "created_time":"2020-05-07T22:56:36.596706+00:00",
    //     "description":"here we go again",
    //     "end_time":null,
    //     "id":4,
    //     "parameters":[
    //        {
    //           "data_type":"STRING",
    //           "pn_id":"1",
    //           "sensitive":"False",
    //           "value":"kiwi"
    //        },
    //        {
    //           "data_type":"STRING",
    //           "pn_id":"3",
    //           "sensitive":"True",
    //           "value":"forbidden fruit"
    //        }
    //     ],
    //     "project":{
    //        "id":1
    //     },
    //     "size":"460.3 KB",
    //     "start_time":null,
    //     "title":"Test_ACLs",
    //     "update_time":"2020-06-09T02:09:56.872730+00:00",
    //     "userDownloadRights":"partial"
    //  }


    // dataset ===
    // {
    //     "counts":{
    //        "datafiles":2
    //     },
    //     "created_time":"2020-05-07T23:00:05+00:00",
    //     "description":"Some ACL-testing dataset",
    //     "experiments":[
    //        {
    //           "id":4,
    //           "project":{
    //              "id":1
    //           }
    //        }
    //     ],
    //     "id":1,
    //     "instrument":{
    //        "id":1,
    //        "name":"Mikes_ACL_Machine"
    //     },
    //     "modified_time":"2020-06-09T02:10:18.426980+00:00",
    //     "parameters":[
    //        {
    //           "data_type":"STRING",
    //           "pn_id":"4",
    //           "sensitive":"False",
    //           "value":"My Name"
    //        },
    //        {
    //           "data_type":"STRING",
    //           "pn_id":"5",
    //           "sensitive":"False",
    //           "value":"is"
    //        }
    //     ],
    //     "size":"460.3 KB",
    //     "tags":"bricks safe as",
    //     "userDownloadRights":"partial"
    //  }

    // datafile =======
    // {
    //     "created_time":null,
    //     "dataset":{
    //        "experiments":[
    //           {
    //              "id":4,
    //              "project":{
    //                 "id":1
    //              }
    //           }
    //        ],
    //        "id":1
    //     },
    //     "filename":"Mikes_test_datafile_1",
    //     "id":1,
    //     "modification_time":null,
    //     "parameters":[
    //        {
    //           "data_type":"STRING",
    //           "pn_id":"12",
    //           "sensitive":"False",
    //           "value":"My name is"
    //        }
    //     ],
    //     "size":"460.3 KB",
    //     "userDownloadRights":"full"
    //  }