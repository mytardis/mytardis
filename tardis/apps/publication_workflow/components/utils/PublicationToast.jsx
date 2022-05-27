import { Toast } from 'react-bootstrap';
import * as PropTypes from 'prop-types';
import React from 'react';

const PublicationToast = ({ onClose, show, toastMessage }) => (
  <Toast
    onClose={onClose}
    show={show}
    delay={5000}
    animation
    style={{
      position: 'absolute',
      top: window.pageYOffset,
      right: 10,
      zIndex: 9999,
    }}
    autohide
  >
    <Toast.Header closeButton>
      <span style={{ color: 'green' }}>
        <i className="fa fa-square mr-2" />
      </span>
      <strong className="mr-auto">Success</strong>
      <small />
    </Toast.Header>
    <Toast.Body>{toastMessage}</Toast.Body>
  </Toast>
);

PublicationToast.propTypes = {
  onClose: PropTypes.func.isRequired,
  show: PropTypes.bool.isRequired,
  toastMessage: PropTypes.string.isRequired,
};

export default PublicationToast;
