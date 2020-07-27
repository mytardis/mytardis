import React from 'react'
import './SearchPage.css'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import FilterSidebar from './FilterSidebar'
import ResultSection from './ResultSection'

export const PureSearchPage = () => {
    return (
            <div className="search-page">
                <h1>Search</h1>
                <div className="search-screen">
                    <aside className="filter-column" md={4}>
                        <FilterSidebar />
                    </aside>
                    <main className="result-column" md={8}>
                        <ResultSection />
                    </main>
                </div>
            </div>
    )
}

export default PureSearchPage;