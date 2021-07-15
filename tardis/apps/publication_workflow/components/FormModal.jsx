import React, { Fragment, useState } from 'react';
import { Modal, Button } from 'react-bootstrap';
import * as Yup from 'yup';
import { ErrorMessage, Field } from 'formik';
import PublicationButton from './PublicationButton';
import Stepper from './Stepper/Stepper';
import Steps from './Stepper/Steps';
import SelectDatasetForm from './Forms/SelectDatasetForm';
import ExtraInformationForm from './Forms/ExtraInformationForm';
import AtrributeAndLicensingForm from './Forms/AtrributeAndLicensingForm';
import ProgressBarComponent from './Stepper/ProgressBar';
import { SubmitFormData } from "./utils/FetchData";

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const FormModal = () => {
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  return (
    <>
      <PublicationButton onclick={handleShow} />
      <Modal show={show} onHide={handleClose} size="lg">
        <Modal.Body>
          <Stepper
            initialValues={{
              publicationTitle: '',
              publicationDescription: '',
              selectedDatasets: [],
              authors: [{ AuthorName: '', AuthorInstitution: '', AuthorEmail: '' }],
              acknowledgment: {},
              AcknowledgementText: '',
              license: '',
              releaseDate: '',
              consent: false,
            }}
            onSubmit={async values => SubmitFormData(values).then(() => handleClose())}
          >
            <Steps
              onSubmit={async values => sleep(50).then(() => console.log('step 1 submit', values))}
              validationSchema={Yup.object({
                publicationTitle: Yup.string().required('Publication title is required'),
                publicationDescription: Yup.string(),
                // selectedDatasets: Yup.object(),
              })}
            />
            <Steps
              onSubmit={async values => sleep(50).then(() => console.log('step 2 submit', values))}
              /* validationSchema={Yup.array().of(
                Yup.object({
                  datasetDescription: Yup.string().required('Dataset description is required'),
                }),
              )} */
            />
            <Steps
              onSubmit={async values => sleep(50).then(() => console.log('step 3 submit', values))}
              validationSchema={Yup.object().shape({
                authors: Yup.array().of(
                  Yup.object().shape({
                    AuthorName: Yup.string().required('Author Name is required'),
                    AuthorInstitution: Yup.string(),
                    AuthorEmail: Yup.string().email('Invalid email address').required('Email is required'),
                  }),
                ),
              })}
            />
            <Steps
              onSubmit={() => console.log('Step4 onsubmit')}
              validationSchema={Yup.object({
                license: Yup.number().required('license is required'),
                releaseDate: Yup.date().required('Select release date'),
                consent: Yup.bool().oneOf([true], 'Please select checkbox to provide your consent'),
              })}
            />
          </Stepper>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button variant="primary" onClick={handleClose}>
            Save and Finish later
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};
export default FormModal;
