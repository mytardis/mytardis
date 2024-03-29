import React, { useEffect } from 'react';
import { Modal } from 'react-bootstrap';
import * as Yup from 'yup';
import PropTypes from 'prop-types';
import Stepper from './Stepper/Stepper';
import Steps from './Stepper/Steps';
import { SubmitFormData } from './utils/FetchData';

const FormModal = ({
  resumeDraftId, show, handleClose, initialData,
}) => {
  useEffect(() => {}, [resumeDraftId]);
  return (
    <>
      <Modal show={show} onHide={handleClose} size="lg" backdrop="static" keyboard={false}>
        <Modal.Body>
          <Stepper
            initialValues={{
              publicationTitle:
                'publicationTitle' in initialData
                  ? initialData.publicationTitle
                  : '',
              publicationDescription:
                'publicationDescription' in initialData
                  ? initialData.publicationDescription
                  : '',
              selectedDatasets:
                'addedDatasets' in initialData ? initialData.addedDatasets : [],
              extraInfo:
                'extraInfo' in initialData ? initialData.extraInfo : {},
              authors:
                'authors' in initialData
                  ? initialData.authors
                  : [{ name: '', institution: '', email: '' }],
              acknowledgements:
                'acknowledgements' in initialData
                  ? initialData.acknowledgements
                  : '',
              license:
                'selectedLicenseId' in initialData
                  ? initialData.selectedLicenseId
                  : null,
              releaseDate:
                'releaseDate' in initialData ? initialData.releaseDate : '',
              consent:
                'acknowledge' in initialData ? initialData.acknowledge : false,
            }}
            onSubmit={values => SubmitFormData(values, 'submit', resumeDraftId).then(() => {
              handleClose();
            })}
            onClose={() => {
              handleClose(false);
            }}
            modalFooter
          >
            <>
              <Steps
                onSubmit={(values) => {
                  SubmitFormData(
                    values,
                    'update-dataset-selection',
                    resumeDraftId,
                  ).then(() => {
                    handleClose();
                  });
                }}
                onClose={() => {
                  handleClose(false);
                }}
                validationSchema={Yup.object({
                  publicationTitle: Yup.string().required(
                    'Publication title is required',
                  ),
                  publicationDescription: Yup.string().required(
                    'Publication description is required',
                  ),
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
                  SubmitFormData(
                    values,
                    'update-extra-info',
                    resumeDraftId,
                  ).then(() => {
                    handleClose();
                  });
                }}
                onClose={() => {
                  handleClose(false);
                }}
                validationSchema={Yup.object({
                  extraInfo: Yup.object({}),
                })}
              />
              <Steps
                onSubmit={(values) => {
                  SubmitFormData(
                    values,
                    'update-attribution-and-licensing',
                    resumeDraftId,
                  ).then(() => {
                    handleClose();
                  });
                }}
                onClose={() => {
                  handleClose(false);
                }}
                validationSchema={Yup.object().shape({
                  authors: Yup.array().of(
                    Yup.object().shape({
                      name: Yup.string().required('Author Name is required'),
                      institution: Yup.string().required(
                        'Institution is required',
                      ),
                      email: Yup.string()
                        .email('Invalid email address')
                        .required('Email is required'),
                    }),
                  ),
                  acknowledgements: Yup.string(),
                })}
              />
              <Steps
                onSubmit={(values) => {
                  SubmitFormData(
                    values,
                    'update-attribution-and-licensing',
                    resumeDraftId,
                  ).then(() => {
                    handleClose();
                  });
                }}
                onClose={() => {
                  handleClose(false);
                }}
                validationSchema={Yup.object({
                  license: Yup.number().required('license is required'),
                  releaseDate: Yup.date().required('Select release date'),
                  consent: Yup.bool()
                    .required()
                    .oneOf(
                      [true],
                      'Please select checkbox to provide your consent',
                    ),
                })}
              />
            </>
          </Stepper>
        </Modal.Body>
      </Modal>
    </>
  );
};
export default FormModal;

FormModal.propTypes = {
  handleClose: PropTypes.func.isRequired,
  initialData: PropTypes.object.isRequired,
  resumeDraftId: PropTypes.number.isRequired,
  show: PropTypes.bool.isRequired,
};
