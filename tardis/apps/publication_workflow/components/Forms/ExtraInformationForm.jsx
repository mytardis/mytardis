import React from 'react';
import { Card, Form } from 'react-bootstrap';
import PropTypes from 'prop-types';

const ExtraInformationForm = ({ formik }) => {
  const handleDatasetDescriptionChange = (i, event) => {
    // if extraInfo
    if (Object.keys(formik.values.extraInfo).length > 0) {
      const updatedExtraInfo = {
        ...formik.values.extraInfo,
        [`${i}`]: { ...formik.values.extraInfo[`${i}`], description: event.target.value },
      };
      formik.setFieldValue('extraInfo', updatedExtraInfo);
    } else {
      // get selectedDatasetObject and add description value
      const { selectedDatasets } = formik.values;
      const updatedDataset = selectedDatasets[i];
      const updatedDatasetDescription = [{
        ...updatedDataset,
        publication_dataset_description: event.target.value,
      }];
      const res = selectedDatasets
        .map(obj => updatedDatasetDescription.find(o => o.dataset.id === obj.dataset.id) || obj);
      formik.setFieldValue('selectedDatasets', res, false);
    }
  };
  return (
    <>
      <h3>Dataset description</h3>
      <p>The following extra information is required based on your dataset selection:</p>
      {Object.keys(formik.values.extraInfo).length > 0
      // extra info is present
        ? Object.keys(formik.values.extraInfo).map(elem, idx => (
          <Card key={idx} className="mb-3">
            <Card.Body>
              <div>
                <h4>{formik.values.extraInfo[elem].dataset}</h4>
                <Form.Group className="mb-3" controlId="formGroupDatasetDescription">
                  <Form.Label>Description</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder="Describe your Dataset"
                    name={`datasetDescription_${elem}`}
                    onChange={e => handleDatasetDescriptionChange(elem, e)}
                    value={formik.values.extraInfo[elem].description}
                  />
                </Form.Group>
              </div>
            </Card.Body>
          </Card>
        ))
        : formik.values.selectedDatasets.map((item, idx) => (
          <Card key={idx} className="mb-3">
            <Card.Body>
              <div>
                <h4>{item.dataset.description}</h4>
                <Form.Group className="mb-3" controlId="formGroupDatasetDescription">
                  <Form.Label>Description</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder="Describe your Dataset"
                    name={`datasetDescription_${idx}`}
                    onChange={e => handleDatasetDescriptionChange(idx, e)}
                    value={formik.values.selectedDatasets[idx].publication_dataset_description}
                  />
                </Form.Group>
              </div>
            </Card.Body>
          </Card>
        ))
      }

    </>
  );
};

export default ExtraInformationForm;

ExtraInformationForm.propTypes = {
  formik: PropTypes.any.isRequired,
};
