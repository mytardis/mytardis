import React, { Fragment, useState } from 'react';
import { Form, Formik } from 'formik';
import 'regenerator-runtime/runtime';
import {
  Button, ButtonGroup, Col, Row,
} from 'react-bootstrap';
import ProgressBar from './ProgressBar';
import SelectDatasetForm from '../Forms/SelectDatasetForm';
import AtrributeAndLicensingForm from '../Forms/AtrributeAndLicensingForm';
import ExtraInformationForm from '../Forms/ExtraInformationForm';
import LicensingAndReleaseForm from '../Forms/LicensingAndReleaseForm';


const Stepper = ({
  children, initialValues, onSubmit, onSave,
}) => {
  const [stepNumber, setStepNumber] = useState(0);
  const steps = React.Children.toArray(children);
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
    /* if (step.props.onSubmit) {
      // await step.props.onSubmit(values, bag);
    } */
    console.log(values);
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
        console.log('submitting form');
        step.props.onSubmit(values, bag);
      }
    });
    // await step.props.onSubmit(values, bag);
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
    >
      {formik => (
        <Form noValidate>
          <ProgressBar activeStep={stepNumber + 1} />
          {renderStepContent(formik, stepNumber)}
          <div style={{ display: 'flex' }}>
            {stepNumber > 0 && (
            <Button className="mr-2 mt-2" onClick={() => previous(formik.values)} type="button">
              Back
            </Button>
            )}
            <div>
              {!isLastStep ? (
                <Button disabled={formik.isSubmitting} type="submit" className="mt-2">
                  Next
                </Button>
              ) : <></>}
            </div>
          </div>
          <div>
            {isLastStep
              ? (
                <Row>
                  <Col>
                    <Button disabled={formik.isSubmitting} type="submit" className="mt-2 mr-2 float-right">
                      Submit
                    </Button>
                    <Button disabled={formik.isSubmitting} className="mt-2 mr-2 float-right" onClick={() => handleSave(formik.values, formik)}>
                      Save and Finish later
                    </Button>
                  </Col>

                </Row>
              ) : (
                <>
                  <Button disabled={formik.isSubmitting} className="mt-2 float-right" onClick={() => handleSave(formik.values, formik)}>
                    Save and Finish later
                  </Button>
                </>
              )

            }
          </div>
          {/* <Debug /> */}
        </Form>
      )}
    </Formik>
  );
};

export default Stepper;
