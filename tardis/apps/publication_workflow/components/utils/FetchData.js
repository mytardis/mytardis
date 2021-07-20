import 'core-js/stable';
import 'regenerator-runtime/runtime';
import Cookies from 'js-cookie';
import React from 'react';

const SubmitFormData = async (data, action) => {
  let payload = {
    publicationDescription: data.publicationDescription,
    publicationTitle: data.publicationTitle,
    addedDatasets: [],
    authors: data.authors
      .map(item => (
        { email: item.AuthorEmail, name: item.AuthorName, institution: item.AuthorInstitution }
      )),
    acknowledge: data.consent,
    action,
  };
  if (data.releaseDate !== '') {
    payload = Object.assign(payload, { embargo: data.releaseDate });
  }
  const response = await fetch('/apps/publication-workflow/form/', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
      'Content-Type': 'application/json',
    },
  });
  return response.json();
};
const fetchPubs = async (pubType) => {
  const response = await fetch(`/apps/publication-workflow/${pubType}_pubs_list`);
  return response.json();
};

const deletePub = async (pubId) => {
  const response = await fetch(`/apps/publication-workflow/publication/delete/${pubId}/`,
    {
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
        'Content-Type': 'application/json',
      },
    });
  return response.json();
};

const retractPub = async (pubId) => {
  const response = await fetch(`/apps/publication-workflow/publication/retract/${pubId}/`,

    {
      method: 'POST',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
        'Content-Type': 'application/json',
      },
    });
  return response.json();
};
export {
  SubmitFormData, fetchPubs, deletePub, retractPub,
};
