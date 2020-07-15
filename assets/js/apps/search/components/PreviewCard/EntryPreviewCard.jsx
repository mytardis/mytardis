import { Button } from 'react-bootstrap';
import React from 'react';
import './EntryPreviewCard.css'

export default function EntryPreviewCard(props) {
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

    let data = props.data;

    /**
     * Simply cuts of the time portion of the date
     * @param {*} date 
     */
    const formatDate = (date) => {
        return data.start_date.split('T')[0];
    }

    const determineAccess = (access) => {
        return access === "partial" ? "Unavailable" : "Available";
    }

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
            <div className="preview-card__button-wrapper--right">
                <div className="preview-card__inline-block-wrapper">
                    <Button className="preview-card__button--right" href={`view/project/${data.id}`} variant="link">View details</Button>
                </div>
            </div>
        </div>
    );
}