import React, { Fragment, useState } from 'react';
import { Modal, Button, Toast } from 'react-bootstrap';
import * as Yup from 'yup';
import { ErrorMessage, Field } from 'formik';
import PublicationButton from './PublicationButton';
import Stepper from './Stepper/Stepper';
import Steps from './Stepper/Steps';
import SelectDatasetForm from './Forms/SelectDatasetForm';
import ExtraInformationForm from './Forms/ExtraInformationForm';
import AtrributeAndLicensingForm from './Forms/AtrributeAndLicensingForm';
import ProgressBarComponent from './Stepper/ProgressBar';
import { SubmitFormData } from './utils/FetchData';
import PublicationToast from './utils/PublicationToast';

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const FormModal = ({ onPubUpdate }) => {
  const [show, setShow] = useState(false);
  const [toastShow, setToastShow] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const handleClose = () => {
    setShow(false);
    // show message
    setToastMessage('Publication created successfully');
    setToastShow(true);
    // reload pub list
    onPubUpdate('');
  };
  const handleShow = () => setShow(true);
  return (
    <>
      <PublicationButton onclick={handleShow} />
      <PublicationToast
        show={toastShow}
        toastMessage={toastMessage}
        onClose={() => setToastShow(false)}
      />
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
            onSubmit={values => SubmitFormData(values, 'submit').then(() => {
              handleClose();
            })}
            modalFooter
          >
            <Steps
              onSubmit={values => SubmitFormData(values, 'update-dataset-selection').then(() => { handleClose(); })}
              validationSchema={Yup.object({
                publicationTitle: Yup.string().required('Publication title is required'),
                publicationDescription: Yup.string().required('Publication description is required'),
                selectedDatasets: Yup.array()
                  .required('Dataset is required')
                  .min(1, 'Select at least 1 dataset')
                  .of(
                    Yup.object().shape({
                      dataset_description: Yup.string(),
                      publication_dataset_description: Yup.string(),
                      dataset_id: Yup.string(),
                      exp: Yup.object().shape({
                        id: Yup.number(),
                        title: Yup.string(),
                      }),
                    }),
                  ),
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
        {/* <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button variant="primary" onClick={handleClose}>
            Save and Finish later
          </Button>
        </Modal.Footer> */}
      </Modal>
    </>
  );
};
export default FormModal;
