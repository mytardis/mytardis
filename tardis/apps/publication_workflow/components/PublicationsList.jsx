import PropTypes from 'prop-types';
import React, { Fragment, useEffect, useState } from 'react';
import { Modal, Button } from 'react-bootstrap';
import PublicationCard from './PublicationCard';
import { deletePub, retractPub } from './utils/FetchData';
import PublicationToast from './utils/PublicationToast';


const PublicationsList = ({
  releasedPubsList,
  retractedPubsList,
  scheduledPubsList,
  draftPubsList,
  onPubUpdate,
  onResumeDraft,
  listViewType,
}) => {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [retractModalOpen, setRetractModalOpen] = useState(false);
  const [pubToDelete, setPubTodelete] = useState(-1);
  const [pubToRetract, setPubToRetract] = useState(-1);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('Publication deleted Successfully');

  const handleDelete = () => {
    deletePub(pubToDelete).then(() => {
      setDeleteModalOpen(false);
      setToastMessage('Publication deleted Successfully');
      setShowToast(true);
      onPubUpdate('draft');
    });
  };
  const handleRetract = () => {
    retractPub(pubToRetract).then(() => {
      setRetractModalOpen(false);
      setToastMessage('Publication retracted Successfully');
      setShowToast(true);
      onPubUpdate('');
    });
  };
  const handleDeleteClose = () => {
    setDeleteModalOpen(false);
  };
  const confirmDelete = (e, id) => {
    setDeleteModalOpen(true);
    setPubTodelete(id);
  };
  const ConfirmRetract = (e, id) => {
    setRetractModalOpen(true);
    setPubToRetract(id);
  };
  useEffect(() => {
  }, [releasedPubsList, retractedPubsList]);
  return (
    <Fragment>
      <Modal show={deleteModalOpen} onHide={() => handleDeleteClose}>
        <Modal.Header />
        <Modal.Body>
          Are you sure, you want to delete this publication?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setDeleteModalOpen(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={() => handleDelete()}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={retractModalOpen} onHide={() => setRetractModalOpen(false)}>
        <Modal.Header />
        <Modal.Body>
          Are you sure, you want to retract this publication?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setRetractModalOpen(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={() => handleRetract()}>
            Retract
          </Button>
        </Modal.Footer>
      </Modal>
      <PublicationToast
        onClose={() => setShowToast(false)}
        show={showToast}
        toastMessage={toastMessage}
      />
      <div className="row">
        {draftPubsList.length > 0 ? draftPubsList.map(item => (
          <PublicationCard
            key={item.id}
            publicationType="draft"
            data={item}
            handleDelete={confirmDelete}
            handleResume={onResumeDraft}
            colNum={listViewType === 'list' ? 12 : 4}
          />
        )) : <></>}
        {scheduledPubsList.length > 0 ? scheduledPubsList.map(item => (
          <PublicationCard
            key={item.id}
            publicationType="scheduled"
            data={item}
            colNum={listViewType === 'list' ? 12 : 4}
          />
        )) : <></>}
        {retractedPubsList.length > 0 ? retractedPubsList.map(item => (
          <PublicationCard
            key={item.id}
            publicationType="retracted"
            data={item}
            colNum={listViewType === 'list' ? 12 : 4}
          />
        )) : <></>}
        {releasedPubsList.length > 0 ? releasedPubsList.map(item => (
          <PublicationCard
            key={item.id}
            publicationType="released"
            data={item}
            handleRetract={ConfirmRetract}
            colNum={listViewType === 'list' ? 12 : 4}
          />
        )) : <></>}
      </div>
    </Fragment>
  );
};

export default PublicationsList;
PublicationsList.defaultProps = {
  draftPubsList: [],
  listViewType: [],
  onResumeDraft: () => {},
  releasedPubsList: [],
  retractedPubsList: [],
  scheduledPubsList: [],
};

PublicationsList.propTypes = {
  draftPubsList: PropTypes.array,
  listViewType: PropTypes.string,
  onPubUpdate: PropTypes.func.isRequired,
  onResumeDraft: PropTypes.func,
  releasedPubsList: PropTypes.array,
  retractedPubsList: PropTypes.array,
  scheduledPubsList: PropTypes.array,
};
