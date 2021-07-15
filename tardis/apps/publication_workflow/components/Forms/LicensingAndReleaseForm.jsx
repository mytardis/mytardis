import React, { useEffect, useState } from 'react';
import { Card, Form } from 'react-bootstrap';
import DateTime from 'react-datetime';
import moment from 'moment';
import 'react-datetime/css/react-datetime.css';


const LicensingAndReleaseForm = ({ formik }) => {
  const [licenses, setLicenses] = useState([]);
  const [selectedLicense, setSelectedLicense] = useState({});
  const [publicationDate, setPublicationDate] = useState('');
  const fetchLicenses = async () => {
    const response = await fetch('/apps/publication-workflow/licenses');
    return response.json();
  };
  const handleLicenseChange = (e) => {
    const currentSelectedLicense = licenses
      .find(license => license.id.toString() === e.target.value);
    setSelectedLicense(currentSelectedLicense);
    formik.setFieldValue('license', currentSelectedLicense.id, true);
  };
  const validDate = current => current.isSameOrAfter(DateTime.moment(), 'day');
  const handlePublicationDateChange = (value) => {
    setPublicationDate(moment(value, 'DD-MM-YYYY', true).isValid() ? value.toDate() : '');
    formik.setFieldValue('releaseDate', moment(value, 'DD-MM-YYYY', true).isValid() ? value.toDate() : '', true);
  };
  useEffect(() => {
    fetchLicenses().then((data) => {
      const licenseArray = [];
      licenseArray.push({ id: '-1', name: 'Select a license' });
      data.map(item => licenseArray.push(item));
      setLicenses(licenseArray);
      // setSelectedLicense(data[0]);
    });
  }, [selectedLicense]);
  return (
    <>
      <Card>
        <Card.Body>
          <Card className="mb-2">
            <Card.Body>
              <h4>Select a license</h4>
              <Form.Group className="mb-3" controlId="formGroupExperiment">
                <Form.Control as="select" onChange={handleLicenseChange}>
                  {licenses
                    .map(value => <option id={value.id} value={value.id}>{value.name}</option>)}
                </Form.Control>
              </Form.Group>
              <div>
                <h6>{selectedLicense.name}</h6>
                <img
                  alt={selectedLicense.name}
                  src={selectedLicense.image}
                  title={selectedLicense.name}
                  className="mr-2"
                />
                {selectedLicense.description}
                <a href={selectedLicense.url}>Read the full license here.</a>
              </div>
            </Card.Body>
          </Card>
          <Card className="mb-2">
            <Card.Body>
              <h4>Release date</h4>
              <p>
                What is the earliest date that this publication may be released,
                subject to any additional restrictions?
              </p>
              <DateTime
                id="select-release-date"
                inputProps={{ placeholder: 'Select release date' }}
                timeFormat={false}
                dateFormat="DD-MM-YYYY"
                isValidDate={validDate}
                value={publicationDate}
                name="releaseDate"
                onChange={handlePublicationDateChange}
                isInvalid={formik.errors.releaseDate}
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.releaseDate}
              </Form.Control.Feedback>
            </Card.Body>
          </Card>
          <Card>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Check
                  required
                  name="consent"
                  onChange={formik.handleChange}
                  isInvalid={!!formik.errors.consent}
                  feedback={formik.errors.consent}
                  className="mr-2"
                  label="I am authorised to publish the selected datasets with the license and
                embargo period selected and have received the appropriate consent from
                co-authors and other relevant parties."
                />
              </Form.Group>
            </Card.Body>
          </Card>

        </Card.Body>
      </Card>

    </>
  );
};

export default LicensingAndReleaseForm;
