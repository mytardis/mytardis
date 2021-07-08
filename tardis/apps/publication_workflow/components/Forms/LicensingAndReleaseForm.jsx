import React from 'react';
import { Form } from 'react-bootstrap';


const LicensingAndReleaseForm = ({ formik }) => (

  <>
    <h3>Select a license</h3>
    <Form.Group className="mb-3" controlId="formGroupExperiment">
      <Form.Label>Select experiment</Form.Label>
      <Form.Control as="select">
        <option> Lic 1</option>
        <option> Lic 2</option>
        <option> Lci 3</option>
        <option> Lic 4</option>
        <option> Lic 5</option>
      </Form.Control>
    </Form.Group>
    <div>
      <h5>Lic 1</h5>
      <img alt="Lic 1" src="https://licensebuttons.net/l/by/4.0/88x31.png" />
      {'This licence lets others distribute, remix, tweak,\n'
        + '        and build upon your work, even commercially,\n'
        + '        as long as they credit you for the original creation.\n'
        + '        This is the most accommodating of licences offered under Creative Commons.'}
      <a href="https://creativecommons.org/licenses/by/4.0/">Read the full license here.</a>
    </div>
    <hr className="mt-2 mb-3" />
    <p>
      What is the earliest date that this publication may be released,
      subject to any additional restrictions?
    </p>
    <Form.Group className="mb-3">
      <input type="checkbox" />
      I am authorised to publish the selected datasets with the license and
      embargo period selected and have received the appropriate consent from
      co-authors and other relevant parties.
    </Form.Group>
  </>
);
export default LicensingAndReleaseForm;
