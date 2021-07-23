import React, { useEffect, useState } from 'react';
import {
  Card,
  Col, Form, Row, Table,
} from 'react-bootstrap';

import {
  fetchDatasetsForExperiment,
  fetchExperimentList,
} from '../../../../../assets/js/apps/tiles/components/utils/FetchData';

const SelectDatasetForm = ({ formik }) => {
  const [expList, setExpList] = useState([]);
  const [datasetList, setDatasetList] = useState([]);
  const [selectedDatasetList, setSelectedDatasetList] = useState(formik.values.selectedDatasets);
  const [selectedExperiment, setSelectedExperiment] = useState();

  const handleExpChange = (event) => {
    event.preventDefault();
    fetchDatasetsForExperiment(event.target.value).then(result => setDatasetList(result));
    setSelectedExperiment(expList[event.target.value]);
  };
  const handleDatasetSelectChange = (event) => {
    const selectedOptionsArray = [].slice.call(event.target.selectedOptions);
    let currentlySelectedDatasetList = [];
    selectedOptionsArray
      .map(item => (currentlySelectedDatasetList
        .push({
          experiment: selectedExperiment.title,
          experiment_id: selectedExperiment.id,
          dataset: {
            id: item.value,
            description: item.label.slice(0, item.label.length)
          },
        })));
    currentlySelectedDatasetList = selectedDatasetList.concat(currentlySelectedDatasetList);
    setSelectedDatasetList(currentlySelectedDatasetList);
    console.log(selectedDatasetList);
    // run field validation
    formik.validateField('selectedDatasets');
  };

  useEffect(() => {
    fetchExperimentList().then((data) => {
      setExpList(data);
      formik.setFieldValue('selectedDatasets', selectedDatasetList, false);
    });
  }, [selectedDatasetList]);
  return (
    <>
      <p>
        <strong>Select your data!</strong>
        {' '}
        Below is all the data
        you&apos;ve generated. Select the datasets you want to include in
        this publication.
      </p>
      <Card>
        <Card.Body>
          <Form.Group className="mb-3" controlId="formGroupTitle">
            <Form.Label>Publication Title</Form.Label>
            <Form.Control
              type="text"
              placeholder="concise description"
              name="publicationTitle"
              onChange={formik.handleChange}
              value={formik.values.publicationTitle}
              isValid={formik.touched.publicationTitle && !formik.errors.publicationTitle}
              isInvalid={!!formik.errors.publicationTitle}
            />
            <Form.Control.Feedback type="invalid">
              {formik.errors.publicationTitle}
            </Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="formGroupDescription">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              name="publicationDescription"
              rows={3}
              placeholder="Describe your publication..."
              onChange={formik.handleChange}
              value={formik.values.publicationDescription}
              isValid={formik.touched.publicationDescription
              && !formik.errors.publicationDescription
              }
              isInvalid={!!formik.errors.publicationDescription}
            />
            <Form.Control.Feedback type="invalid">
              {formik.errors.publicationDescription}
            </Form.Control.Feedback>
          </Form.Group>
          <Row>
            <Col className="col-md-6">
              <Form.Group className="mb-3" controlId="formGroupExperiment">
                <Form.Label>Select experiment</Form.Label>
                <Form.Control
                  as="select"
                  name="experimentDropDown"
                  onChange={handleExpChange}
                >
                  {expList.map((value, index) => (
                    <option
                      value={index}
                      key={value.id}
                    >
                      {value.title}
                    </option>
                  )) }
                </Form.Control>
              </Form.Group>
              <Form.Group className="mb-3" controlId="formGroupDatasets">
                <Form.Label>Select Datasets</Form.Label>
                <Form.Control
                  as="select"
                  multiple
                  onChange={handleDatasetSelectChange}
                >
                  {datasetList.map(value => (
                    <option
                      value={value.id}
                      key={value.id}
                    >
                      {value.description}
                    </option>
                  )) }
                </Form.Control>
              </Form.Group>
            </Col>
            <Form.Control
              as="input"
              type="hidden"
              name="selectedDatasets"
              value={formik.values.selectedDatasets}
              onChange={formik.handleChange}
              isValid={formik.touched.selectedDatasets
              && !formik.errors.selectedDatasets
              }
              isInvalid={!!formik.errors.selectedDatasets}
            />
            <Col className="col-md-6">
              <h4>Added Datasets</h4>
              <Table size="sm" responsive striped hover>
                <thead>
                  <tr>
                    <th>Experiment</th>
                    <th>Description</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {formik.values.selectedDatasets.map(item => (
                    <tr>
                      <td>{item.experiment}</td>
                      <td>{item.dataset.description}</td>
                      <td>
                        <span style={{ color: 'red' }}>
                          <i className="fa fa-trash" />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Col>
            <Form.Control.Feedback type="invalid" className="ml-3">
              {formik.errors.selectedDatasets}
            </Form.Control.Feedback>
          </Row>
          <Row>
            <Form.Group />
          </Row>
        </Card.Body>
      </Card>
    </>
  );
};
export default SelectDatasetForm;
