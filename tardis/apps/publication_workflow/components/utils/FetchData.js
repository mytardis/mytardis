import 'core-js/stable';
import 'regenerator-runtime/runtime';
import Cookies from 'js-cookie';
import React from 'react';

const SubmitFormData = async (data, action, publicationId) => {
  let payload;
  if (Object.keys(data).length > 0) {
    payload = {
      publicationDescription: ('publicationDescription' in data ? data.publicationDescription : ''),
      publicationTitle: ('publicationTitle' in data ? data.publicationTitle : ''),
      addedDatasets: ('selectedDatasets' in data ? data.selectedDatasets : []),
      authors: ('authors' in data.authors ? data.authors.map(item => (
        { email: item.AuthorEmail, name: item.AuthorName, institution: item.AuthorInstitution }
      )) : []),
      acknowledge: ('consent' in data ? data.consent : false),
      action,
    };
  } else {
    payload = {
      action,
    };
  }

  if (publicationId) {
    payload = Object.assign(payload, { publicationId });
  }

  if (data.releaseDate !== '') {
    payload = Object.assign(payload, { embargo: data.releaseDate });
  }
  // format data for extra-info
  if (action === 'update-extra-info') {
    if ('extraInfo' in data) {
      payload = Object.assign(payload, { extraInfo: data.extraInfo });
    } else {
      let extraInfoData = {};
      data.selectedDatasets.forEach((item, idx) => {
        const extraInfoIndexKey = `0.${idx}`;
        const extraInfoIndexValue = {
          dataset: item.dataset.description,
          description: item.publication_dataset_description,
          schema: 'http://www.mytardis.org/schemas/publication/generic/',
        };
        const extraInfoObj = {};
        extraInfoObj[extraInfoIndexKey] = extraInfoIndexValue;
        extraInfoData = Object.assign(extraInfoData, extraInfoObj);
      });
      payload = Object.assign(payload, { extraInfo: extraInfoData });
    }
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
