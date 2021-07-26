import React, { useState } from 'react';
import { ErrorMessage, Field, FieldArray } from 'formik';
import {
  Col, Row, Form, FormGroup, Button, Table, Card,
} from 'react-bootstrap';


const AtrributeAndLicensingForm = ({ formik }) => {
  const [authorRows, setAuthorRows] = useState(
    formik.values.authors ? formik.values.authors
      : [{ name: '', institution: '', email: '' }],
  );
  const [ackValue, setAckValue] = useState(0);
  const exampleAcknowledgements = [
    {
      agency: 'Select sample acknowledgement text',
      text: '',
    },
    {
      agency: 'Australian Research Council',
      text: 'This research was funded (partially or fully) by the Australian Government through the Australian Research Council.',
    },
    {
      agency: 'National Health and Medical Research Council',
      text: 'This research was funded (partially or fully) by the Australian Government through the National Health and Medical Research Council.',
    },
    {
      agency: 'Science and Industry Endowment Fund',
      text: 'This work is supported by the Science and Industry Endowment Fund.',
    },
    {
      agency: 'Multi-modal Australian ScienceS Imaging and Visualisation Environment',
      text: 'This work was supported by the Multi-modal Australian ScienceS Imaging and Visualisation Environment (MASSIVE) (www.massive.org.au).',
    }];
  const handleAddAuthor = () => {
    const newAuthRow = {};
    formik.setFieldValue('authors', [...authorRows], true);
    setAuthorRows([...authorRows, newAuthRow]);
  };
  const handleAuthorDelete = idx => () => {
    // remove specific row
    const allAuthorRows = [...authorRows];
    allAuthorRows.splice(idx, 1);
    // set author field values
    formik.setFieldValue('authors', allAuthorRows, true);
    setAuthorRows(allAuthorRows);
  };
  const handleAckChange = (e) => {
    setAckValue(e.target.value);
    // formik.setFieldValue('acknowledgment', { agency: exampleAcknowledgements[e.target.value].agency, text: exampleAcknowledgements[e.target.value].text });
    formik.setFieldValue('acknowledgements', exampleAcknowledgements[e.target.value].text);
  };
  return (
    <>
      <Card>
        <Card.Body>
          <Card className="mb-2">
            <Card.Body className="mb-3">
              <h4 className="ml-2">Authors</h4>
              <Table responsive striped bordered hover>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Institution</th>
                    <th>Email</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  <FieldArray name="authors">
                    {() => authorRows.map((item, idx) => {
                      const authorErrors = formik.errors.authors?.length
                  && formik.errors.authors[idx] || {};
                      const authorTouched = formik.touched.authors?.length
                  && formik.touched.authors[idx] || {};
                      return (
                        <tr key={idx}>
                          <th>
                            <Field
                              placeholder="Author name"
                              type="text"
                              name={`authors.${idx}.name`}
                              autoComplete="name"
                              className={`form-control${authorErrors.name && authorTouched.name ? ' is-invalid' : ''}`}
                            />
                            <ErrorMessage name={`authors.${idx}.name`} component="div" className="invalid-feedback" />
                          </th>
                          <th>
                            <Field
                              placeholder="Institution"
                              type="text"
                              name={`authors.${idx}.institution`}
                              autoComplete="institution"
                              className={`form-control${authorErrors.institution && authorTouched.institution ? ' is-invalid' : ''}`}
                            />
                            <ErrorMessage name={`authors.${idx}.AuthorInstitution`} component="div" className="invalid-feedback" />
                          </th>
                          <th>
                            <Field
                              placeholder="Email"
                              type="text"
                              name={`authors.${idx}.email`}
                              autoComplete="email"
                              className={`form-control${authorErrors.email && authorTouched.email ? ' is-invalid' : ''}`}
                            />
                            <ErrorMessage name={`authors.${idx}.email`} component="div" className="invalid-feedback" />
                          </th>
                          <th>
                            <span style={{ color: 'red' }} onClick={handleAuthorDelete(idx)}>
                              <i className="fa fa-trash" />
                            </span>
                          </th>
                        </tr>
                      );
                    })}
                  </FieldArray>

                </tbody>
              </Table>
              <FormGroup className="mb-3" controlId="formGroupAuthors">
                <Row className="justify-content-center">
                  <Button
                    variant="secondary"
                    size="sm"
                    title="Add Author"
                    className="mt-2 mb-2"
                    onClick={handleAddAuthor}
                  >
                    <i className="fa fa-plus mr-1" />
                    Add Author
                  </Button>
                </Row>
              </FormGroup>
            </Card.Body>
          </Card>
          <Card>
            <Card.Body>
              <h4>Acknowledgements</h4>
              <h6>Example acknowledgements</h6>
              <Form.Group className="mb-3" controlId="formGroupAcknowledgement">
                <Form.Control as="select" onChange={handleAckChange}>
                  {exampleAcknowledgements
                    .map((value, idx) => <option id={idx} value={idx}>{value.agency}</option>)}
                </Form.Control>
              </Form.Group>
              <span className="small">Select an option from the list above for example text.</span>
              <Form.Group className="mb-3" controlId="formGroupDatasetDescription">
                <Form.Control
                  as="textarea"
                  rows={5}
                  placeholder="Acknowledge funding agencies, facilities and other contributors here."
                  name="acknowledgements"
                  onChange={formik.handleChange}
                  value={formik.values.acknowledgements}
                />
              </Form.Group>
            </Card.Body>
          </Card>
        </Card.Body>
      </Card>
    </>
  );
};

export default AtrributeAndLicensingForm;
