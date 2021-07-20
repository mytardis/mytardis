import React, {
  Fragment, useEffect, useState, useCallback,
} from 'react';
import PublicationButton from './PublicationButton';
import PublicationsList from './PublicationsList';
import FormModal from './FormModal';
import { fetchPubs } from './utils/FetchData';

const PublicationsHome = () => {
  const [releasedPubsList, setReleasePubsList] = useState([]);
  const [draftPubsList, setDraftPubsList] = useState([]);
  const [retractedPubsList, setRetractedPubsList] = useState([]);
  const [scheduledPubsList, setScheduledPubsList] = useState([]);
  const [, updateState] = useState();
  const forceUpdate = useCallback(() => updateState({}), []);
  const onPubUpdate = (pubType) => {
    // TODO only load specific pubType

    fetchPubs('draft').then((data) => {
      setDraftPubsList(data);
    });
    // falls through
    fetchPubs('released').then((data) => {
      setReleasePubsList(data);
    });
    // falls through
    fetchPubs('retracted').then((data) => {
      setRetractedPubsList(data);
    });
    // falls through
    fetchPubs('scheduled').then((data) => {
      setScheduledPubsList(data);
    });
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
      <FormModal onPubUpdate={onPubUpdate} />
      <PublicationsList
        releasedPubsList={releasedPubsList}
        draftPubsList={draftPubsList}
        scheduledPubsList={scheduledPubsList}
        retractedPubsList={retractedPubsList}
        onPubUpdate={onPubUpdate}
      />
    </Fragment>
  );
};
export default PublicationsHome;
