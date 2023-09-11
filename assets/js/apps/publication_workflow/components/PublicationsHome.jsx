import React, { Fragment, useEffect, useState } from 'react';
import PublicationButton from './PublicationButton';
import PublicationsList from './PublicationsList';
import FormModal from './FormModal';
import { fetchPubs, SubmitFormData } from './utils/FetchData';
import PublicationToast from './utils/PublicationToast';

const PublicationsHome = () => {
  const [show, setShow] = useState(false);
  const [releasedPubsList, setReleasePubsList] = useState([]);
  const [draftPubsList, setDraftPubsList] = useState([]);
  const [retractedPubsList, setRetractedPubsList] = useState([]);
  const [scheduledPubsList, setScheduledPubsList] = useState([]);
  const [resumeDraftId, setResumeDraftId] = useState(0);
  const [initialData, setInitialData] = useState({});
  const [toastShow, setToastShow] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [listViewType, setListViewType] = useState('grid');
  const [message, setMessage] = useState('');

  const onResumeDraft = (e, id) => {
    setResumeDraftId(id);
    // fetch  data
    SubmitFormData({}, 'resume', id).then((data) => {
      setInitialData(data);
      setShow(true);
    });
  };
  const handleShow = () => setShow(true);

  const handleError = (err) => {
    setMessage((
      <div className="alert alert-danger">Could not fetch publications.</div>
    ));
  };

  const handlePublicationsListError = (err) => {
    setMessage((
      <div className="alert alert-danger">
        Could not complete the requested operation.
      </div>
    ));
    setShow(false);
  };

  const onPubUpdate = () => {
    setMessage('');

    // TODO only load specific pubType
    fetchPubs('draft').then((data) => {
      setDraftPubsList(data);
    }).catch(handleError);
    fetchPubs('released').then((data) => {
      setReleasePubsList(data);
    }).catch(handleError);
    fetchPubs('retracted').then((data) => {
      setRetractedPubsList(data);
    }).catch(handleError);
    fetchPubs('scheduled').then((data) => {
      setScheduledPubsList(data);
    }).catch(handleError);
  };
  const handleClose = (pubCreate = true) => {
    setMessage('');
    setShow(false);

    if (pubCreate) {
      // show message
      setToastMessage('Publication created successfully');
      setToastShow(true);
    }

    // reload pub list
    onPubUpdate('');
    // set resume draft id to 0
    setResumeDraftId(0);
    setInitialData({});
  };
  const setViewType = (e) => {
    setListViewType(e.target.id);
  };

  useEffect(() => {
    fetchPubs('draft').then((data) => {
      setDraftPubsList(data);
    }).catch(handleError);
    fetchPubs('released').then((data) => {
      setReleasePubsList(data);
    }).catch(handleError);
    fetchPubs('retracted').then((data) => {
      setRetractedPubsList(data);
    }).catch(handleError);
    fetchPubs('scheduled').then((data) => {
      setScheduledPubsList(data);
    }).catch(handleError);
  }, []);
  return (
    <Fragment>
      <PublicationToast
        show={toastShow}
        toastMessage={toastMessage}
        onClose={() => setToastShow(false)}
      />
      <PublicationButton onclick={handleShow} setViewType={setViewType} />
      <FormModal
        onPubUpdate={onPubUpdate}
        resumeDraftId={resumeDraftId}
        show={show}
        handleClose={handleClose}
        initialData={initialData}
      />
      {message}
      <PublicationsList
        releasedPubsList={releasedPubsList}
        draftPubsList={draftPubsList}
        scheduledPubsList={scheduledPubsList}
        retractedPubsList={retractedPubsList}
        onPubUpdate={onPubUpdate}
        onResumeDraft={onResumeDraft}
        listViewType={listViewType}
        onError={handlePublicationsListError}
      />
    </Fragment>
  );
};
export default PublicationsHome;
