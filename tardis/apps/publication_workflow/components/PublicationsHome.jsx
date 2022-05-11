import React, {
  Fragment, useEffect, useState,
} from 'react';
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
  const onResumeDraft = (e, id) => {
    setResumeDraftId(id);
    // fetch  data
    SubmitFormData({}, 'resume', id).then((data) => {
      setInitialData(data);
      setShow(true);
    });
  };
  const handleShow = () => setShow(true);

  const onPubUpdate = () => {
    // TODO only load specific pubType
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
  };
  const handleClose = () => {
    setShow(false);
    // show message
    setToastMessage('Publication created successfully');
    setToastShow(true);
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

      <PublicationsList
        releasedPubsList={releasedPubsList}
        draftPubsList={draftPubsList}
        scheduledPubsList={scheduledPubsList}
        retractedPubsList={retractedPubsList}
        onPubUpdate={onPubUpdate}
        onResumeDraft={onResumeDraft}
        listViewType={listViewType}
      />
    </Fragment>
  );
};
export default PublicationsHome;
