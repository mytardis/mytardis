import React from 'react';
import { Card, Form } from 'react-bootstrap';

const ExtraInformationForm = ({ formik }) => {
  const handleDatasetDescriptionChange = (i, event) => {
    // get selectedDatasetObject and add description value
    const { selectedDatasets } = formik.values;
    const updatedDataset = selectedDatasets[i];
    const updatedDatasetDescription = [{
      ...updatedDataset,
      publication_dataset_description: event.target.value,
    }];
    const res = selectedDatasets
      .map(obj => updatedDatasetDescription.find(o => o.dataset_id === obj.dataset_id) || obj);
    formik.setFieldValue('selectedDatasets', res, false);
    console.log(selectedDatasets);
  };
  return (
    <>
      <h3>Dataset description</h3>
      <p>The following extra information is required based on your dataset selection:</p>
      {formik.values.selectedDatasets.map((dataset, i) => (
        <Card className="mb-3">
          <Card.Body>
            <div key={dataset.dataset_id}>
              <h4>{dataset.dataset_description}</h4>
              <Form.Group className="mb-3" controlId="formGroupDatasetDescription">
                <Form.Label>Description</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  placeholder="Describe your Dataset"
                  name={`datasetDescription_${i}`}
                  onChange={e => handleDatasetDescriptionChange(i, e)}
                  key={formik.values.selectedDatasets[i]}
                  value={formik.values.selectedDatasets[i].publication_dataset_description}
                />
              </Form.Group>
            </div>
          </Card.Body>
        </Card>
      ))}
    </>
  );
};
export default ExtraInformationForm;
