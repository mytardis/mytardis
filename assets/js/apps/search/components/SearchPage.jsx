import React, { useState, useEffect } from 'react'
import './SearchPage.css'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import FilterSidebar from './FilterSidebar'
import ResultSection from './ResultSection'
import SearchInfoContext from './SearchInfoContext'
import Cookies from 'js-cookie';

export function PureSearchPage(){
    return (
            <Container fluid="xl" className="search-page">
                <h1>Search</h1>
                <Row className="search-screen">
                    <Col md={4}>
                        <FilterSidebar />
                    </Col>
                    <Col md={8}>
                        <ResultSection />
                    </Col>
                </Row>
            </Container>
    )
}

function getResultsFromResponse(response){
    // Grab the "_source" object out of each hit and also
    // add a type attribute to them.
    const hits = response.objects[0].hits,
        expResults = hits["experiments"].map( 
            exp => {
                const source = exp._source;
                Object.assign(source,{
                    type: 'experiment',
                    url:`/experiment/view/${source.id}/`
                });
                return source;
            }),
        dsResults = hits["datasets"].map(
            ds => {
                const source = ds._source;
                Object.assign(source,{
                    type: 'dataset',
                    url:`/dataset/view/${source.id}/`
                });
                return source;
            }),
        dfResults = hits["datafiles"].map(
            df => {
                const source = df._source;
                Object.assign(source,{
                    type: 'datafile',
                    url:`/datafile/view/${source.id}/`
                });
                return source;
            });
    return {
        experiment: expResults,
        dataset: dsResults,
        datafile: dfResults
    }
}

export default function SearchPage() {
    const updateSearch = (text) => {
        if (text === searchInfo.searchTerm){
            return;
        }
        onSearchChange({
            searchTerm: text,
            isLoading: true,
            error: null,
            results: null,
            updateSearch
        })
    }
    const [ searchInfo , onSearchChange ] = useState({
        searchTerm: null,
        isLoading: false,
        error:null,
        results:null,
        updateSearch
    });

    useEffect(() => {
        const searchTerm = searchInfo.searchTerm;
        fetch(`/api/v1/search_simple-search/?query=${searchTerm}`,{
            method: 'get',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
              'X-CSRFToken': Cookies.get('csrftoken'),
            },      
        }).then(response => {
            if (!response.ok) {
                throw new Error("An error on the server occurred.")
            }
            return response.json()
        })
        .then((data) => {
            const results = getResultsFromResponse(data);
            // Update results with hits.
            onSearchChange({
                searchTerm,
                isLoading: false,
                error: null,
                results,
                updateSearch
            });
        })
        .catch(error => {
            console.error("Error during search API call.", error);
            onSearchChange({
                searchTerm,
                isLoading: false,
                error,
                results: null,
                updateSearch
            })
        });

    },[searchInfo.searchTerm]);

    return (
        <SearchInfoContext.Provider value={searchInfo}>
            <PureSearchPage />
        </SearchInfoContext.Provider>
    )
}
