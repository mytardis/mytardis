import React, { useState } from 'react';
import { ErrorMessage, Field, FieldArray } from 'formik';
import {
  Col, Row, Form, FormGroup, Button, Table,
} from 'react-bootstrap';


const AtrributeAndLicensingForm = ({ formik }) => {
  const [authorRows, setAuthorRows] = useState(
    formik.values.authors ? formik.values.authors
      : [{ AuthorName: '', AuthorInstitution: '', AuthorEmail: '' }],
  );
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
  return (
    <>
      <h4>Authors</h4>
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
                      name={`authors.${idx}.AuthorName`}
                      autoComplete="name"
                      className={`form-control${authorErrors.AuthorName && authorTouched.AuthorName ? ' is-invalid' : ''}`}
                    />
                    <ErrorMessage name={`authors.${idx}.AuthorName`} component="div" className="invalid-feedback" />
                  </th>
                  <th>
                    <Field
                      placeholder="Institution"
                      type="text"
                      name={`authors.${idx}.AuthorInstitution`}
                      autoComplete="institution"
                      className={`form-control${authorErrors.AuthorInstitution && authorTouched.AuthorInstitution ? ' is-invalid' : ''}`}
                    />
                    <ErrorMessage name={`authors.${idx}.AuthorInstitution`} component="div" className="invalid-feedback" />
                  </th>
                  <th>
                    <Field
                      placeholder="Email"
                      type="text"
                      name={`authors.${idx}.AuthorEmail`}
                      autoComplete="email"
                      className={`form-control${authorErrors.AuthorEmail && authorTouched.AuthorEmail ? ' is-invalid' : ''}`}
                    />
                    <ErrorMessage name={`authors.${idx}.AuthorEmail`} component="div" className="invalid-feedback" />
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
        {/* <Row>
          <Col>
            <Form.Label>Name</Form.Label>
            <Form.Control
              placeholder="Author name"
              type="text"
              name="AuthorName"
              autoComplete="name"
              onChange={formik.handleChange}
              value={formik.values.AuthorName}
              isValid={formik.touched.AuthorName && !formik.errors.AuthorName}
              isInvalid={!!formik.errors.AuthorName}
            />
            <Form.Control.Feedback type="invalid">
              {formik.errors.AuthorName}
            </Form.Control.Feedback>
          </Col>
          <Col>
            <Form.Label>Institution</Form.Label>
            <Form.Control
              placeholder="Institution"
              type="text"
              name="AuthorInstitution"
              autoComplete="institution"
              onChange={formik.handleChange}
              value={formik.values.AuthorInstitution}
              isValid={formik.touched.AuthorInstitution && !formik.errors.AuthorInstitution}
              isInvalid={!!formik.errors.AuthorInstitution}
            />
            <Form.Control.Feedback type="invalid">
              {formik.errors.AuthorInstitution}
            </Form.Control.Feedback>
          </Col>
          <Col>
            <Form.Label>Email</Form.Label>
            <Form.Control
              placeholder="Email"
              type="text"
              name="AuthorEmail"
              autoComplete="email"
              onChange={formik.handleChange}
              value={formik.values.AuthorEmail}
              isValid={formik.touched.AuthorEmail && !formik.errors.AuthorEmail}
              isInvalid={!!formik.errors.AuthorEmail}
            />
            <Form.Control.Feedback type="invalid">
              {formik.errors.AuthorEmail}
            </Form.Control.Feedback>
          </Col>
          <Col />
        </Row> */}
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
      <hr className="mt-2 mb-3" />
      <h4>Acknowledgements</h4>
      <h5>Example acknowledgements</h5>
      <Form.Group className="mb-3" controlId="formGroupAcknowledgement">
        <Form.Control as="select">
          <option> Ack 1</option>
          <option> Ack 2</option>
          <option> Ack 3</option>
          <option> Ack 4</option>
          <option> Ack 5</option>
        </Form.Control>
      </Form.Group>
      <span className="small">Select an option from the list above for example text.</span>
      <Form.Group className="mb-3" controlId="formGroupDatasetDescription">
        <Form.Control
          as="textarea"
          rows={5}
          placeholder="Acknowledge funding agencies, facilities and other contributors here."
          name="AcknowledgementText"
          onChange={formik.handleChange}
          value={formik.values.AcknowledgementText}
        />
      </Form.Group>
    </>
  );
};

export default AtrributeAndLicensingForm;
