import React, { Fragment, useEffect, useState } from 'react';
import PublicationCard from './PublicationCard';
import {deletePub, fetchPubs} from "./utils/FetchData";


const PublicationsList = () => {
  const [releasedPubsList, setReleasePubsList] = useState([]);
  const [draftPubsList, setDraftPubsList] = useState([]);
  const [retractedPubsList, setRetractedPubsList] = useState([]);
  const [scheduledPubsList, setScheduledPubsList] = useState([]);
  const handleDelete = (e, id) => {
    deletePub(id);
    console.log(id);
  };

  useEffect(() => {
    fetchPubs('draft').then((data) => {
      setDraftPubsList(data);
    });
    fetchPubs('released').then((data) => {
      setReleasePubsList(data);
    });
    fetchPubs('retracted').then((data) => {
      setRetractedPubsList(data);
    });
    fetchPubs('scheduled').then((data) => {
      setScheduledPubsList(data);
    });
  }, []);
  return (
    <Fragment>
      <div className="row">
        <div className="row row-cols-1 row-cols-md-3 row-cols-lg-4 row-cols-xl-5">
          {draftPubsList.length > 0 ? draftPubsList.map(item => <PublicationCard key={item.id} publicationType="draft" data={item} handleDelete={handleDelete} />) : <></>}
          {scheduledPubsList.length > 0 ? scheduledPubsList.map(item => <PublicationCard key={item.id} publicationType="scheduled" data={item} />) : <></>}
          {retractedPubsList.length > 0 ? retractedPubsList.map(item => <PublicationCard key={item.id} publicationType="retracted" data={item} />) : <></>}
          {releasedPubsList.length > 0 ? releasedPubsList.map(item => <PublicationCard key={item.id} publicationType="released" data={item} />) : <></>}
        </div>
      </div>

    </Fragment>
  );
};

export default PublicationsList;
