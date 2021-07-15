import 'core-js/stable';
import 'regenerator-runtime/runtime';
import Cookies from 'js-cookie';
import React from 'react';

async function SubmitFormData(data) {
  const payload = {
    publicationDescription: data.publicationDescription,
    publicationTitle: data.publicationTitle,
    authors: data.authors
      .map(item => (
        { email: item.AuthorEmail, name: item.AuthorName, institution: item.AuthorInstitution }
      )),
    acknowledge: data.consent,
    action: 'submit',
  };
  fetch('/apps/publication-workflow/form/', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
      'Content-Type': 'application/json',
    },
  }).then((resp) => {
    console.log(resp);
  });
}
const fetchPubs = async (pubType) => {
  switch (pubType) {
    case 'draft': { const response = await fetch('/apps/publication-workflow/draft_pubs_list');
      return response.json(); }
    default: { const response = await fetch('/apps/publication-workflow/released_pubs_list');
      return response.json(); }
    case 'scheduled': { const response = await fetch('/apps/publication-workflow/scheduled_pubs_list');
      return response.json(); }
    case 'retracted': { const response = await fetch('/apps/publication-workflow/retracted_pubs_list');
      return response.json(); }
  }
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
export { SubmitFormData, fetchPubs, deletePub };
