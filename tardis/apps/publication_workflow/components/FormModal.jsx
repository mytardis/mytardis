import React, { Fragment, useEffect, useState } from 'react';
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

const FormModal = ({
  onPubUpdate, resumeDraftId, show, handleClose, initialData,
}) => {
  useEffect(() => {
  }, [resumeDraftId]);
  return (
    <>
      <Modal show={show} onHide={handleClose} size="lg">
        <Modal.Body>
          <Stepper
            initialValues={{
              publicationTitle: ('publicationTitle' in initialData ? initialData.publicationTitle : ''),
              publicationDescription: ('publicationDescription' in initialData ? initialData.publicationDescription : ''),
              selectedDatasets: ('addedDatasets' in initialData ? initialData.addedDatasets : []),
              extraInfo: ('extraInfo' in initialData ? initialData.extraInfo : {}),
              authors: ('authors' in initialData ? initialData.authors : []),
              acknowledgements: ('acknowledgements' in initialData ? initialData.acknowledgements : ''),
              license: ('selectedLicenseId' in initialData ? initialData.selectedLicenseId: ''),
              releaseDate: ('releaseDate' in initialData ? initialData.releaseDate: ''),
              consent: ('acknowledge' in initialData ? initialData.acknowledge: false),
            }}
            onSubmit={values => SubmitFormData(values, 'submit').then(() => {
              handleClose();
            })}
            modalFooter
          >
            <Steps
              onSubmit={(values) => {
                SubmitFormData(values, 'update-dataset-selection', resumeDraftId)
                  .then(() => { handleClose(); });
              }}
              validationSchema={Yup.object({
                publicationTitle: Yup.string().required('Publication title is required'),
                publicationDescription: Yup.string().required('Publication description is required'),
                selectedDatasets: Yup.array()
                  .required('Dataset is required')
                  .min(1, 'Select at least 1 dataset')
                  .of(
                    Yup.object().shape({
                      experiment: Yup.string(),
                      experiment_id: Yup.string(),
                      dataset: Yup.object().shape({
                        id: Yup.string(),
                        description: Yup.string(),
                      }),
                    }),
                  ),
              })}
            />
            <Steps
              onSubmit={(values) => {
                SubmitFormData(values, 'update-extra-info', resumeDraftId)
                  .then(() => { handleClose(); });
              }}
              validationSchema={Yup.object({
                extraInfo: Yup.object({}),
              })}
            />
            <Steps
              onSubmit={(values) => {
                SubmitFormData(values, 'update-attribution-and-licensing', resumeDraftId)
                  .then(() => { handleClose(); });
              }}
              validationSchema={Yup.object().shape({
                authors: Yup.array().of(
                  Yup.object().shape({
                    name: Yup.string().required('Author Name is required'),
                    institution: Yup.string(),
                    email: Yup.string().email('Invalid email address').required('Email is required'),
                  }),
                ),
                acknowledgements: Yup.string(),
              })}
            />
            <Steps
              onSubmit={(values) => {
                SubmitFormData(values, 'update-attribution-and-licensing', resumeDraftId)
                  .then(() => { handleClose(); });
              }}
              validationSchema={Yup.object({
                license: Yup.number().required('license is required'),
                releaseDate: Yup.date().required('Select release date'),
                consent: Yup.bool().required().oneOf([true], 'Please select checkbox to provide your consent'),
              })}
            />
          </Stepper>
        </Modal.Body>
      </Modal>
    </>
  );
};
export default FormModal;
