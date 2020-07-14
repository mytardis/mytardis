import React from 'react'
import './SearchPage.css'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import FilterSidebar from './FilterSidebar'
import ResultSection from './ResultSection'

export const PureSearchPage = () => {
    return (
            <Container fluid="xl" className="search-page">
                <h1>Search</h1>
                <Row className="search-screen">
                    <Col as="aside" className="filter-column" md={4}>
                        <FilterSidebar />
                    </Col>
                    <Col as="main" className="result-column" md={8}>
                        <ResultSection />
                    </Col>
                </Row>
            </Container>
    )
}

export default PureSearchPage;