import React, { useEffect } from 'react'
import './SearchPage.css'
import { runSearch } from "./searchSlice";
import { useDispatch } from "react-redux";
import FilterSidebar from './FilterSidebar'
import ResultSection from './ResultSection'

export const SearchPage = () => {
    const dispatch = useDispatch();
    useEffect(() => {
        // Run a search to get initial results.
        dispatch(runSearch());
    },[dispatch]);
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

export default SearchPage;