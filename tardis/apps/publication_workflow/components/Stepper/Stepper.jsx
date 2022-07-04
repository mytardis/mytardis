import PropTypes from 'prop-types';
import React, { Fragment, useState } from 'react';
import { Form, Formik } from 'formik';
import 'regenerator-runtime/runtime';
import {
  Button, Col, Row,
} from 'react-bootstrap';
import ProgressBar from './ProgressBar';
import SelectDatasetForm from '../Forms/SelectDatasetForm';
import AtrributeAndLicensingForm from '../Forms/AtrributeAndLicensingForm';
import ExtraInformationForm from '../Forms/ExtraInformationForm';
import LicensingAndReleaseForm from '../Forms/LicensingAndReleaseForm';


const Stepper = ({
  children, initialValues, onSubmit, onClose
}) => {
  const [stepNumber, setStepNumber] = useState(0);
  const steps = React.Children.toArray(children.props.children);
  const [snapshot, setSnapshot] = useState(initialValues);

  const step = steps[stepNumber];
  const totalSteps = steps.length;
  const isLastStep = stepNumber === totalSteps - 1;

  const next = (values) => {
    setSnapshot(values);
    setStepNumber(Math.min(stepNumber + 1, totalSteps - 1));
  };

  const previous = (values) => {
    setSnapshot(values);
    setStepNumber(Math.max(stepNumber - 1, 0));
  };

  // eslint-disable-next-line consistent-return
  const handleSubmit = async (values, bag) => {
    if (isLastStep) {
      return onSubmit(values, bag);
    }
    bag.setTouched({});
    next(values);
  };
  const handleSave = async (values, bag) => {
    bag.setTouched({});
    await bag.validateForm().then((errors) => {
      if (Object.keys(errors).length === 0) {
        step.props.onSubmit(values, bag);
      }
    });
  };

  // handle close
  const handleClose = async () => {
    step.props.onClose()
  };

  const renderStepContent = (formik, activeStep) => {
    switch (activeStep) {
      case 0:
        return <SelectDatasetForm formik={formik} />;
      case 1:
        return <ExtraInformationForm formik={formik} />;
      case 2:
        return <AtrributeAndLicensingForm formik={formik} />;
      case 3:
        return <LicensingAndReleaseForm formik={formik} />;
      default:
        return <div>Not Found</div>;
    }
  };

  return (
    <Formik
      initialValues={snapshot}
      onSubmit={handleSubmit}
      validationSchema={step.props.validationSchema}
      onClose={handleClose}
    >
      {formik => (
        <Form noValidate>
          <ProgressBar activeStep={stepNumber + 1} />
          {renderStepContent(formik, stepNumber)}
          <Row>
            <Col>
              {stepNumber > 0 && (
                <Button className="me-2 mt-2" onClick={() => previous(formik.values)} type="button">
                  Back
                </Button>
              )}
              {!isLastStep ? (
                <Button disabled={formik.isSubmitting} type="submit" className="mt-2">
                  Next
                </Button>
              ) : <></>}
            </Col>
            <Col>
              {isLastStep
                ? (
                  <Row>
                    <Col>
                      <Button disabled={formik.isSubmitting} type="submit" className="mt-2 me-2 float-end">
                        Submit
                      </Button>
                      <Button disabled={formik.isSubmitting} className="mt-2 me-2 float-end" onClick={() => handleSave(formik.values, formik)}>
                        Save and Finish later
                      </Button>
                      <Button disabled={formik.isSubmitting} className="btn btn-danger mt-2 me-2 float-end" onClick={() => handleClose()}>
                        Close
                      </Button>
                    </Col>
                  </Row>
                ) : (
                  <>
                    <Button disabled={formik.isSubmitting} className="mt-2 float-end" onClick={() => handleSave(formik.values, formik)}>
                      Save and Finish later
                    </Button>
                    <Button disabled={formik.isSubmitting} className="btn btn-danger mt-2 me-2 float-end" onClick={() => handleClose()}>
                        Close
                    </Button>
                  </>
                )
              }
            </Col>
          </Row>
          {/* <Debug /> */}
        </Form>
      )}
    </Formik>
  );
};

export default Stepper;

Stepper.propTypes = {
  children: PropTypes.element.isRequired,
  initialValues: PropTypes.object.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};
